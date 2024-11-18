import argparse
import datetime
import os
import sys
import time
import traceback
from importlib import metadata
from importlib.metadata import PackageMetadata
from typing import List

import yaml

from slack_watchman import (
    signature_downloader,
    exceptions,
    watchman_processor
)
from slack_watchman.clients.slack_client import SlackClient
from slack_watchman.loggers import (
    StdoutLogger,
    JSONLogger,
    export_csv,
    init_logger
)
from slack_watchman.models import (
    signature,
    user,
    workspace,
    post,
    conversation,
    auth_vars
)

OUTPUT_LOGGER: JSONLogger


def validate_conf(path: str, cookie_auth: bool) -> auth_vars.AuthVars:
    """ Validates configuration and authentication settings for Slack Watchman from either
        a config file or environment variables.
        Authentication tokens from Environment Variables take precedence over those
        from the config file.
        Additional configuration settings, such as suppressed signatures, are loaded from the config file.

    Args:
        path: Path for the .config file
        cookie_auth: Whether session:cookie auth is being used
    Returns:
        AuthVars object containing the authentication details
    Raises:
        MissingEnvVarError: If a required environment variable is not set
        MissingCookieEnvVarError: If required variables for cookie auth aren't set
        MisconfiguredConfFileError: If the config file is not valid
    """

    # Check for legacy config file and rename if necessary
    legacy_path = f'{os.path.expanduser("~")}/slack_watchman.conf'
    if os.path.exists(legacy_path):
        OUTPUT_LOGGER.log('WARNING', 'Legacy slack_watchman.conf file detected. Renaming to watchman.conf')
        os.rename(legacy_path, path)

    auth_info = auth_vars.AuthVars(
        token=None,
        cookie=None,
        url=None,
        disabled_signatures=None,
        cookie_auth=cookie_auth
    )

    # Check if config file exists
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as yaml_file:
                conf_details = yaml.safe_load(yaml_file)['slack_watchman']
                auth_info.disabled_signatures = conf_details.get('disabled_signatures')
        except Exception as e:
            raise exceptions.MisconfiguredConfFileError from e

    if not cookie_auth:
        # First try SLACK_WATCHMAN_TOKEN env var
        try:
            auth_info.token = os.environ['SLACK_WATCHMAN_TOKEN']
        except KeyError as e:
            # Failing that, try to get SLACK_WATCHMAN_TOKEN from config
            if conf_details.get('token'):
                auth_info.token = conf_details.get('token')
            else:
                raise exceptions.MissingEnvVarError('SLACK_WATCHMAN_TOKEN') from e
    else:
        # First try SLACK_WATCHMAN_COOKIE and SLACK_WATCHMAN_URL env vars
        try:
            auth_info.cookie = os.environ['SLACK_WATCHMAN_COOKIE']
            auth_info.url = os.environ['SLACK_WATCHMAN_URL']
        except KeyError as e:
            # Failing that, try to get SLACK_WATCHMAN_COOKIE and SLACK_WATCHMAN_URL from config
            if conf_details.get('cookie') and conf_details.get('url'):
                auth_info.cookie = conf_details.get('cookie')
                auth_info.url = conf_details.get('url')
            else:
                raise exceptions.MissingCookieEnvVarError(e.args[0])
    return auth_info


def supress_disabled_signatures(signatures: List[signature.Signature],
                                disabled_signatures: List[str]) -> List[signature.Signature]:
    """ Supress signatures that are disabled in the config file
    Args:
        signatures: List of signatures to filter
        disabled_signatures: List of signatures to disable
    Returns:
        List of signatures with disabled signatures removed
    """

    return [sig for sig in signatures if sig.id not in disabled_signatures]


def search(slack_connection: SlackClient,
           loaded_signature: signature.Signature,
           timeframe: int or str,
           scope: str,
           verbose: bool) -> None:
    """ Search either messages or files for matches from signatures.
    Findings are then filtered by RegEx, and any matches are output to
    the chosen logging mechanism.

    Args:
        slack_connection: Slack API object
        loaded_signature: Signature object which defines what to search for
        timeframe: How far back to search for
        scope: Where to search in Slack, e.g. files or messages
        verbose: Whether to use verbose logging or not
    """

    if scope == 'messages':
        OUTPUT_LOGGER.log('INFO', f'Searching for posts containing {loaded_signature.name}')
        messages = watchman_processor.find_messages(
            slack_connection,
            OUTPUT_LOGGER,
            loaded_signature,
            verbose,
            timeframe)
        if messages:
            for message in messages:
                OUTPUT_LOGGER.log(
                    'NOTIFY',
                    message,
                    scope=scope,
                    severity=loaded_signature.severity,
                    detect_type=loaded_signature.name,
                    notify_type='result')
    if scope == 'files':
        OUTPUT_LOGGER.log('INFO', f'Searching for posts containing {loaded_signature.name}')
        files = watchman_processor.find_files(
            slack_connection,
            OUTPUT_LOGGER,
            loaded_signature,
            verbose,
            timeframe)
        if files:
            for file in files:
                OUTPUT_LOGGER.log(
                    'NOTIFY',
                    file,
                    scope=scope,
                    severity=loaded_signature.severity,
                    detect_type=loaded_signature.name,
                    notify_type='result')


def unauthenticated_probe(workspace_domain: str,
                          project_metadata: PackageMetadata) -> None:
    """ Probe Slack for information about the workspace without authentication.

    Args:
        workspace_domain: Domain of the workspace
        project_metadata: Project metadata
    """

    OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman started execution')
    OUTPUT_LOGGER.log('INFO', f'Version: {project_metadata.get("version")}')
    OUTPUT_LOGGER.log('INFO', 'Created by: PaperMtn <papermtn@protonmail.com>')
    OUTPUT_LOGGER.log('SUCCESS', 'Running in probe mode')
    OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman will attempt an unauthenticated probe on the workspace '
                                 'and return any available authentication information.')
    OUTPUT_LOGGER.log('SUCCESS', f'Workspace: {workspace_domain}')
    try:
        domain_information = watchman_processor.find_auth_information(workspace_domain)
        if domain_information:
            OUTPUT_LOGGER.log('WORKSPACE_PROBE', domain_information, detect_type='Workspace Probe',
                              notify_type='workspace_probe')
            OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman probe finished execution. '
                                         'Run in full mode with token authentication to scan a workspace')
        else:
            OUTPUT_LOGGER.log('INFO', f'No information found for the workspace {workspace_domain}. '
                                      f'This may not be a Slack Workspace, or there may be no authentication'
                                      f' information available.')
            OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman probe finished execution. '
                                         'Run in full mode with token authentication to scan a workspace')
        sys.exit()
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        OUTPUT_LOGGER.log('CRITICAL', e)
        sys.exit(1)


# pylint: disable=too-many-locals, missing-function-docstring, global-variable-undefined
# pylint: disable=too-many-branches, disable=too-many-statements, global-statement
def main():
    global OUTPUT_LOGGER
    try:
        OUTPUT_LOGGER = ''
        start_time = time.time()
        project_metadata = metadata.metadata('slack-watchman')
        parser = argparse.ArgumentParser(description="Monitoring and enumerating Slack for exposed secrets")

        parser.add_argument('--timeframe', '-t', choices=['d', 'w', 'm', 'a'], dest='time', default='a',
                            help='How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time')
        parser.add_argument('--output', '-o', choices=['json', 'stdout'], dest='logging_type',
                            help='Where to send results')
        parser.add_argument('--version', '-v', action='version',
                            version=f'Slack Watchman: {project_metadata.get("version")}')
        parser.add_argument('--all', '-a', dest='everything', action='store_true',
                            help='Find secrets and PII')
        parser.add_argument('--users', '-u', dest='users', action='store_true',
                            help='Enumerate users and output them to .csv in the current working directory')
        parser.add_argument('--channels', '-c', dest='channels', action='store_true',
                            help='Enumerate channels and output them to .csv in the current working directory')
        parser.add_argument('--pii', '-p', dest='pii', action='store_true',
                            help='Find personal data: DOB, passport details, drivers licence, ITIN, SSN etc.')
        parser.add_argument('--secrets', '-s', dest='secrets', action='store_true',
                            help='Find exposed secrets: credentials, tokens etc.')
        parser.add_argument('--financial', dest='financial', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--tokens', dest='tokens', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--files', dest='files', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--custom', dest='custom', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--debug', '-d', dest='debug', action='store_true', help='Turn on debug level logging')
        parser.add_argument('--verbose', '-V', dest='verbose', action='store_true',
                            help='Turn on more verbose output for JSON logging. '
                                 'This includes more fields, but is larger')
        parser.add_argument('--cookie', dest='cookie', action='store_true',
                            help='Use cookie auth using Slack d cookie. '
                                 'REQUIRES either SLACK_WATCHMAN_COOKIE and SLACK_WATCHMAN_URL environment variables '
                                 'set, or both values set in watchman.conf')
        parser.add_argument('--probe', dest='probe_domain',
                            help='Perform an un-authenticated probe on a workspace for available'
                                 ' authentication options and other information. '
                                 'Enter workspace domain to probe')

        args = parser.parse_args()
        tm = args.time
        everything = args.everything
        users = args.users
        channels = args.channels
        logging_type = args.logging_type
        debug = args.debug
        verbose = args.verbose
        secrets = args.secrets
        pii = args.pii
        cookie = args.cookie
        probe_domain = args.probe_domain

        OUTPUT_LOGGER = init_logger(logging_type, debug)

        for deprecated_arg in ['financial', 'tokens', 'files', 'custom']:
            if vars(args).get(deprecated_arg):
                OUTPUT_LOGGER.log('WARNING', f'Argument `--{deprecated_arg}` is deprecated, and has been ignored')

        if tm == 'd':
            now = int(time.time())
            timeframe = time.strftime('%Y-%m-%d', time.localtime(now - 86400))
        elif tm == 'w':
            now = int(time.time())
            timeframe = time.strftime('%Y-%m-%d', time.localtime(now - 604800))
        elif tm == 'm':
            now = int(time.time())
            timeframe = time.strftime('%Y-%m-%d', time.localtime(now - 2592000))
        else:
            now = int(time.time())
            timeframe = time.strftime('%Y-%m-%d', time.localtime(now - 1576800000))

        if probe_domain:
            unauthenticated_probe(probe_domain, project_metadata)

        conf_path = f'{os.path.expanduser("~")}/watchman.conf'
        auth_info = validate_conf(conf_path, cookie)
        slack_con = watchman_processor.initiate_slack_connection(auth_info)

        auth_data = slack_con.get_auth_test()
        calling_user = user.create_from_dict(
            slack_con.get_user_info(auth_data.get('user_id')).get('user'), True)

        workspace_information = workspace.create_from_dict(slack_con.get_workspace_info().get('team'))

        OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman started execution')
        OUTPUT_LOGGER.log('INFO', f'Version: {project_metadata.get("version")}')
        OUTPUT_LOGGER.log('INFO', 'Created by: PaperMtn <papermtn@protonmail.com>')
        OUTPUT_LOGGER.log('INFO', f'Searching workspace: {workspace_information.name}')
        OUTPUT_LOGGER.log('INFO', f'Workspace URL: {workspace_information.url}')
        OUTPUT_LOGGER.log('INFO', 'Downloading and importing signatures...')
        signature_list = signature_downloader.SignatureDownloader(OUTPUT_LOGGER).download_signatures()
        signature_list = supress_disabled_signatures(signature_list, auth_info.disabled_signatures)
        if auth_info.disabled_signatures:
            OUTPUT_LOGGER.log('INFO', f'The following signatures have been suppressed: {auth_info.disabled_signatures}')
        OUTPUT_LOGGER.log('SUCCESS', f'{len(signature_list)} signatures loaded')
        if cookie:
            OUTPUT_LOGGER.log('SUCCESS', 'Successfully authenticated using cookie')
            OUTPUT_LOGGER.log('SUCCESS', f"This user's SESSION_TOKEN: {slack_con.session_token}")
        OUTPUT_LOGGER.log('SUCCESS',
                          f'You are authenticated to this workspace as: USER: {calling_user.display_name} '
                          f'- {calling_user.email} ID: {calling_user.id}')
        OUTPUT_LOGGER.log('USER', calling_user, detect_type='User', notify_type='user')
        OUTPUT_LOGGER.log('WORKSPACE', workspace_information, detect_type='Workspace', notify_type='workspace')
        OUTPUT_LOGGER.log('INFO', 'Finding workspace authentication options')
        workspace_auth = watchman_processor.find_auth_information(domain_url=workspace_information.url)
        if workspace_auth:
            OUTPUT_LOGGER.log('WORKSPACE_AUTH', workspace_auth, detect_type='Workspace Auth',
                              notify_type='workspace_auth')
        else:
            OUTPUT_LOGGER.log('INFO', 'No workspace authentication information found')

        if users:
            OUTPUT_LOGGER.log('INFO', 'Enumerating users...')
            user_list = watchman_processor.get_users(slack_con, verbose)
            OUTPUT_LOGGER.log('SUCCESS', f'{len(user_list)} users discovered')
            OUTPUT_LOGGER.log('INFO', 'Writing to csv')
            export_csv('slack_users', user_list)
            OUTPUT_LOGGER.log(
                'SUCCESS',
                f'Users output to CSV file: {os.path.join(os.getcwd(), "slack_users.csv")}')

        if channels:
            OUTPUT_LOGGER.log('INFO', 'Enumerating channels...')
            channel_list = watchman_processor.get_channels(slack_con, verbose)
            OUTPUT_LOGGER.log('SUCCESS', f'{len(channel_list)} channels discovered')
            OUTPUT_LOGGER.log('INFO', 'Writing to csv')
            export_csv('slack_channels', channel_list)
            OUTPUT_LOGGER.log(
                'SUCCESS',
                f'Users output to CSV file: {os.path.join(os.getcwd(), "slack_channels.csv")}')
            OUTPUT_LOGGER.log('INFO', 'Finding public Canvases')
            for channel in channel_list:
                if not channel.canvas_empty and channel.canvas_id:
                    canvas_information = {
                        'channel_name': channel.name,
                        'canvas_url': f'{workspace_information.url}canvas/{channel.id}'
                    }
                    OUTPUT_LOGGER.log('CANVAS', canvas_information, detect_type='Canvas',
                                      notify_type='canvas')
        if everything or not pii and not secrets:
            OUTPUT_LOGGER.log('INFO', 'Searching for PII and Secrets')
            for signature_object in signature_list:
                for scope in signature_object.scope:
                    search(
                        slack_con,
                        signature_object,
                        timeframe,
                        scope,
                        verbose)
        elif secrets:
            OUTPUT_LOGGER.log('INFO', 'Searching for Secrets')
            for signature_object in [sig for sig in signature_list if sig.category == 'secrets']:
                for scope in signature_object.scope:
                    search(
                        slack_con,
                        signature_object,
                        timeframe,
                        scope,
                        verbose)
        else:
            OUTPUT_LOGGER.log('INFO', 'Searching for PII')
            for signature_object in [sig for sig in signature_list if sig.category == 'pii']:
                for scope in signature_object.scope:
                    search(
                        slack_con,
                        signature_object,
                        timeframe,
                        scope,
                        verbose)

        OUTPUT_LOGGER.log('SUCCESS', f'Slack Watchman finished execution - Execution time:'
                                     f' {str(datetime.timedelta(seconds=time.time() - start_time))}')

    except TimeoutError as e:
        OUTPUT_LOGGER.log('ERROR', e)
        OUTPUT_LOGGER.log('DEBUG', traceback.format_exc())
    except Exception as e:
        OUTPUT_LOGGER.log('CRITICAL', e)
        OUTPUT_LOGGER.log('DEBUG', traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
