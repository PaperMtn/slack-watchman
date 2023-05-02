import argparse
import datetime
import os
import sys
import time
import traceback
import yaml
from pathlib import Path
from typing import List

from . import sw_logger
from . import __version__
from . import slack_wrapper as slack
from . import signature_updater
from . import exceptions
from .models import (
    signature,
    user,
    workspace,
    post,
    conversation
)

SIGNATURES_PATH = (Path(__file__).parents[2] / 'watchman-signatures').resolve()
OUTPUT_LOGGER: sw_logger.JSONLogger


def load_signatures() -> List[signature.Signature]:
    """ Load signatures from YAML files
    Returns:
        List containing loaded definitions as Signatures objects
    """

    loaded_signatures = []
    try:
        for root, dirs, files in os.walk(SIGNATURES_PATH):
            for sig_file in files:
                sig_path = (Path(root) / sig_file).resolve()
                if sig_path.name.endswith('.yaml'):
                    loaded_def = signature.load_from_yaml(sig_path)
                    for sig in loaded_def:
                        if sig.status == 'enabled' and 'slack_std' in sig.watchman_apps:
                            loaded_signatures.append(sig)
        return loaded_signatures
    except Exception as e:
        raise e


def validate_conf(path: str, cookie: bool) -> bool:
    """ Check the file slack_watchman.conf exists

    Args:
        path: Path for the .config file
        cookie: Whether session:cookie auth is being used
    Returns:
        True if the required config settings are present, False if not
    """

    if not cookie:
        if not os.environ.get('SLACK_WATCHMAN_TOKEN'):
            if os.path.exists(f'{os.path.expanduser("~")}/slack_watchman.conf'):
                OUTPUT_LOGGER.log('WARNING', 'Legacy slack_watchman.conf file detected. Renaming to watchman.conf')
                os.rename(rf'{os.path.expanduser("~")}/slack_watchman.conf',
                          rf'{os.path.expanduser("~")}/watchman.conf')
                try:
                    with open(path) as yaml_file:
                        return yaml.safe_load(yaml_file)['slack_watchman']
                except:
                    raise exceptions.MisconfiguredConfFileError
            elif os.path.exists(path):
                try:
                    with open(path) as yaml_file:
                        return yaml.safe_load(yaml_file)['slack_watchman']
                except:
                    raise exceptions.MisconfiguredConfFileError
            else:
                try:
                    os.environ['SLACK_WATCHMAN_TOKEN']
                except:
                    raise exceptions.MissingEnvVarError('SLACK_WATCHMAN_TOKEN')
    else:
        if os.path.exists(f'{os.path.expanduser("~")}/slack_watchman.conf'):
            OUTPUT_LOGGER.log('WARNING', 'Legacy slack_watchman.conf file detected. Renaming to watchman.conf')
            os.rename(rf'{os.path.expanduser("~")}/slack_watchman.conf',
                      rf'{os.path.expanduser("~")}/watchman.conf')
            try:
                with open(path) as yaml_file:
                    return yaml.safe_load(yaml_file)['slack_watchman']
            except:
                raise exceptions.MisconfiguredConfFileError
        elif os.path.exists(path):
            try:
                with open(path) as yaml_file:
                    return yaml.safe_load(yaml_file)['slack_watchman']
            except:
                raise exceptions.MisconfiguredConfFileError
        else:
            try:
                os.environ['SLACK_WATCHMAN_COOKIE']
            except:
                raise exceptions.MissingEnvVarError('SLACK_WATCHMAN_COOKIE')

            try:
                os.environ['SLACK_WATCHMAN_URL']
            except:
                raise exceptions.MissingEnvVarError('SLACK_WATCHMAN_URL')


def search(slack_connection: slack.SlackAPI,
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
        messages = slack.find_messages(
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
        files = slack.find_files(
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


def init_logger(logging_type: str, debug: bool) -> sw_logger.JSONLogger or sw_logger.StdoutLogger:
    """ Create a logger object. Defaults to stdout if no option is given

    Args:
        logging_type: Type of logging to use
        debug: Whether to use debug level logging or not
    Returns:
        Logger object
    """

    if not logging_type or logging_type == 'stdout':
        return sw_logger.StdoutLogger(debug=debug)
    else:
        return sw_logger.JSONLogger(debug=debug)


def main():
    global OUTPUT_LOGGER
    try:
        OUTPUT_LOGGER = ''
        start_time = time.time()
        parser = argparse.ArgumentParser(description=__version__.__summary__)

        required = parser.add_argument_group('required arguments')
        required.add_argument('--timeframe', '-t', choices=['d', 'w', 'm', 'a'], dest='time',
                              help='How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time',
                              required=True)
        parser.add_argument('--output', '-o', choices=['json', 'stdout'], dest='logging_type',
                            help='Where to send results')
        parser.add_argument('--version', '-v', action='version',
                            version=f'Slack Watchman: {__version__.__version__}')
        parser.add_argument('--all', '-a', dest='everything', action='store_true',
                            help='Find secrets and PII')
        parser.add_argument('--users', '-u', dest='users', action='store_true',
                            help='Enumerate users and output them to .csv')
        parser.add_argument('--channels', '-c', dest='channels', action='store_true',
                            help='Enumerate channels and output them to .csv')
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

        conf_path = f'{os.path.expanduser("~")}/watchman.conf'
        validate_conf(conf_path, cookie)
        slack_con = slack.initiate_slack_connection(cookie)

        auth_data = slack_con.get_auth_test()
        calling_user = user.create_from_dict(
            slack_con.get_user_info(auth_data.get('user_id')).get('user'), True)

        workspace_information = workspace.create_from_dict(slack_con.get_workspace_info().get('team'))

        OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman started execution')
        OUTPUT_LOGGER.log('INFO', f'Version: {__version__.__version__}')
        OUTPUT_LOGGER.log('INFO', f'Created by: {__version__.__author__} - {__version__.__email__}')
        OUTPUT_LOGGER.log('INFO', f'Searching workspace: {workspace_information.name}')
        OUTPUT_LOGGER.log('INFO', f'Workspace URL: {workspace_information.url}')
        OUTPUT_LOGGER.log('INFO', 'Downloading signature file updates')
        signature_updater.SignatureUpdater(OUTPUT_LOGGER).update_signatures()
        OUTPUT_LOGGER.log('INFO', 'Importing signatures...')
        signature_list = load_signatures()
        OUTPUT_LOGGER.log('SUCCESS', f'{len(signature_list)} signatures loaded')
        if cookie:
            OUTPUT_LOGGER.log('SUCCESS', 'Successfully authenticated using cookie')
            OUTPUT_LOGGER.log('SUCCESS', f"This user's SESSION_TOKEN: {slack_con.session_token}")
        OUTPUT_LOGGER.log('SUCCESS',
                          f'You are authenticated to this workspace as: USER: {auth_data.get("user")}'
                          f' ID: {auth_data.get("user_id")}')
        OUTPUT_LOGGER.log('USER', calling_user, detect_type='User', notify_type='user')
        OUTPUT_LOGGER.log('WORKSPACE', workspace_information, detect_type='Workspace', notify_type='workspace')

        if users:
            OUTPUT_LOGGER.log('INFO', 'Enumerating users...')
            user_list = slack.get_users(slack_con, verbose)
            OUTPUT_LOGGER.log('SUCCESS', f'{len(user_list)} users discovered')
            OUTPUT_LOGGER.log('INFO', 'Writing to csv')
            sw_logger.export_csv('slack_users', user_list)
            OUTPUT_LOGGER.log(
                'SUCCESS',
                f'Users output to CSV file: {os.path.join(os.getcwd(), "slack_users.csv")}')

        if channels:
            OUTPUT_LOGGER.log('INFO', 'Enumerating channels...')
            channel_list = slack.get_channels(slack_con, verbose)
            OUTPUT_LOGGER.log('SUCCESS', f'{len(channel_list)} channels discovered')
            OUTPUT_LOGGER.log('INFO', 'Writing to csv')
            sw_logger.export_csv('slack_channels', channel_list)
            OUTPUT_LOGGER.log(
                'SUCCESS',
                f'Users output to CSV file: {os.path.join(os.getcwd(), "slack_channels.csv")}')

        if everything:
            OUTPUT_LOGGER.log('INFO', 'Searching for PII and Secrets')
            for signature in signature_list:
                for scope in signature.scope:
                    search(
                        slack_con,
                        signature,
                        timeframe,
                        scope,
                        verbose)
        elif secrets:
            OUTPUT_LOGGER.log('INFO', 'Searching for Secrets')
            for signature in [sig for sig in signature_list if sig.category == 'secrets']:
                for scope in signature.scope:
                    search(
                        slack_con,
                        signature,
                        timeframe,
                        scope,
                        verbose)
        else:
            OUTPUT_LOGGER.log('INFO', 'Searching for PII')
            for signature in [sig for sig in signature_list if sig.category == 'pii']:
                for scope in signature.scope:
                    search(
                        slack_con,
                        signature,
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
