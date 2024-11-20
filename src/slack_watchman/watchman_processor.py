import dataclasses
import hashlib
import json
import multiprocessing
import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from slack_watchman.clients.slack_client import SlackClient
from slack_watchman.loggers import StdoutLogger, JSONLogger
from slack_watchman.models import (
    signature,
    user,
    post,
    conversation,
    auth_vars
)
from slack_watchman.utils import deduplicate_results


def initiate_slack_connection(auth_info: auth_vars.AuthVars) -> SlackClient:
    """ Create a Slack API object to use for interacting with the Slack API
    First tries to get the API token from the environment variable(s):
        SLACK_WATCHMAN_TOKEN
        SLACK_WATCHMAN_COOKIE
        SLACK_WATCHMAN_URL

    Args:
        auth_info: Authentication details object
    Returns:
        Slack API object
    """

    if auth_info.cookie_auth:
        return SlackClient(cookie=auth_info.cookie, url=auth_info.url)
    return SlackClient(token=auth_info.token)


def get_users(slack: SlackClient, verbose: bool) -> List[user.User]:
    """ Return a list of all active users in the instance

    Args:
        slack: Slack API connection
        verbose: Whether to use verbose logging or not
    Returns:
        List of User objects
    """

    users = slack.cursor_api_search('users.list', 'members')

    return [user.create_from_dict(u, verbose) for u in users if not u.get('deleted')]


def get_channels(slack: SlackClient,
                 verbose: bool) -> List[conversation.Conversation] or List[conversation.ConversationSuccinct]:
    """ Return a list of all channels in the instance

    Args:
        slack: Slack API object
        verbose: Whether to use verbose logging
    Returns:
        List of Conversation objects
    """

    conversations = slack.cursor_api_search('conversations.list', 'channels')
    return [conversation.create_from_dict(item, verbose) for item in conversations]


def find_messages(slack: SlackClient,
                  logger: JSONLogger | StdoutLogger,
                  sig: signature.Signature,
                  verbose: bool,
                  timeframe: str) -> List[Dict]:
    """ Look in public channels by first searching for common terms in query list
        then trimming this list down using a regex search

    Args:
        slack: Slack API object
        logger: Logging object
        sig: Signature object defining what to search for
        verbose: whether to use verbose logging or not
        timeframe: How far back to search
    Returns:
        List of dictionaries with results
    """

    try:
        results = multiprocessing.Manager().list()
        potential_matches = multiprocessing.Manager().list()

        processes = []

        for query in sig.search_strings:
            p = multiprocessing.Process(
                target=_multipro_message_worker,
                args=(
                    slack,
                    sig,
                    query,
                    verbose,
                    timeframe
                ),
                kwargs={
                    'results': results,
                    'potential_matches': potential_matches
                }
            )
            processes.append(p)
            p.start()

        for process in processes:
            process.join()

        if potential_matches:
            logger.log('INFO', f'{sum(potential_matches)} potential matches found')

        if results:
            results = deduplicate_results(results)
            logger.log('SUCCESS', f'{len(results)} total matches found after filtering')
            return results
        else:
            logger.log('INFO', 'No matches found after filtering')
    except Exception as e:
        logger.log('CRITICAL', e)


# pylint: disable=too-many-locals
def _multipro_message_worker(slack: SlackClient,
                             sig: signature.Signature,
                             query: str,
                             verbose: bool,
                             timeframe: str,
                             **kwargs):
    message_list = slack.page_api_search(query, 'search.messages', 'messages', timeframe)
    kwargs.get('potential_matches').append(len(message_list))
    for message in message_list:
        for pattern in sig.patterns:
            r = re.compile(pattern)
            if r.search(str(message.get('text'))):
                if message.get('user'):
                    user_dict = slack.get_user_info(message.get('user')).get('user')
                    u = user.create_from_dict(user_dict, verbose)
                else:
                    u = message.get('username')

                if message.get('channel').get('id'):
                    channel_dict = slack.get_conversation_info(message.get('channel').get('id')).get('channel')
                    c = conversation.create_from_dict(channel_dict, verbose)
                else:
                    c = None

                message['user'] = u
                message['conversation'] = c
                match_string = r.search(str(message.get('text'))).group(0)
                message = post.create_message_from_dict(message)

                watchman_id = hashlib.md5(f'{match_string}.{message.timestamp}'.encode()).hexdigest()
                results_dict = {
                    'match_string': match_string,
                    'message': message,
                    'watchman_id': watchman_id
                }

                kwargs.get('results').append(results_dict)
    return kwargs.get('results'), kwargs.get('potential_matches')


def find_files(slack: SlackClient,
               logger: JSONLogger | StdoutLogger,
               sig: signature.Signature,
               verbose: bool,
               timeframe: str) -> List[Dict]:
    """ Look for files in public channels by first searching for common terms for the file
    these are then filtered down further to include only files of those extensions

    Args:
        slack: Slack API object
        logger: Logging object
        sig: Signature object defining what to search for
        verbose: Whether to use verbose logging or not
        timeframe: How far back to search
    Returns:
        List of dictionaries with results
    """

    try:
        results = multiprocessing.Manager().list()
        potential_matches = multiprocessing.Manager().list()

        processes = []

        for query in sig.search_strings:
            p = multiprocessing.Process(
                target=_multipro_file_worker,
                args=(
                    slack,
                    sig,
                    query,
                    verbose,
                    timeframe
                ),
                kwargs={
                    'results': results,
                    'potential_matches': potential_matches
                }
            )
            processes.append(p)
            p.start()

        for process in processes:
            process.join()

        if potential_matches:
            logger.log('INFO', f'{sum(potential_matches)} potential matches found')

        if results:
            results = deduplicate_results(results)
            logger.log('SUCCESS', f'{len(results)} total files found after filtering')
            return results
        else:
            logger.log('INFO', 'No files found after filtering')

    except Exception as e:
        logger.log('CRITICAL', e)


def _multipro_file_worker(slack: SlackClient,
                          sig: signature.Signature,
                          query: str,
                          verbose: bool,
                          timeframe: str,
                          **kwargs):
    message_list = slack.page_api_search(query, 'search.files', 'files', timeframe)
    kwargs.get('potential_matches').append(len(message_list))
    for file_dict in message_list:
        if sig.file_types:
            for file_type in sig.file_types:
                if query.replace('\"', '').lower() in file_dict.get('name').lower() \
                        and file_type.lower() in file_dict.get('filetype').lower():
                    if file_dict.get('user') and not dataclasses.is_dataclass(file_dict.get('user')):
                        user_dict = slack.get_user_info(file_dict.get('user')).get('user')
                        u = user.create_from_dict(user_dict, verbose)
                    else:
                        u = None

                    f = post.create_file_from_dict(file_dict)
                    watchman_id = hashlib.md5(f'{f.created}.{f.permalink_public}'.encode()).hexdigest()
                    results_dict = {
                        'file': f,
                        'user': u,
                        'watchman_id': watchman_id
                    }
                    kwargs.get('results').append(results_dict)
        else:
            if query.replace('\"', '').lower() in file_dict.get('name').lower():
                if file_dict.get('user'):
                    user_dict = slack.get_user_info(file_dict.get('user')).get('user')
                    u = user.create_from_dict(user_dict, verbose)
                else:
                    u = None

                f = post.create_file_from_dict(file_dict)
                watchman_id = hashlib.md5(f'{f.created}.{f.permalink_public}'.encode()).hexdigest()
                results_dict = {
                    'file': f,
                    'user': u,
                    'watchman_id': watchman_id
                }

                kwargs.get('results').append(results_dict)
    return kwargs.get('results'), kwargs.get('potential_matches')


def find_auth_information(domain_url: str) -> Dict[str, List[str]] | None:
    """ Get domain authentication information from the Slack workspace

    Slack returns the domains that can be used to create accounts on the workspace
    as well as any OAuth providers that are allowed.

    Args:
        domain_url: URL of domain to enumerate
    Returns:
        A dictionary with results or None if no results
    """

    response = requests.get(domain_url, timeout=60)
    soup = BeautifulSoup(response.text, 'html.parser')
    props_node = soup.find('div', {'id': 'props_node'})

    if props_node:
        data_props = props_node.get('data-props')
        props_data = json.loads(data_props)

        output = {
            'formatted_email_domains': props_data.get('formattedEmailDomains', None),
            'join_url': f'https://join.slack.com/t/{props_data.get("teamDomain")}/signup',
            'user_oauth': [
                'google' if props_data.get('userOauth', {}).get('google', {}).get('enabled', False) else None,
                'apple' if props_data.get('userOauth', {}).get('apple', {}).get('enabled', False) else None
            ],
            'paid_team': props_data.get('isPaidTeam', None),
            'team_name': props_data.get('teamName', None),
            'team_id': props_data.get('encodedTeamId', None),
            'standard_auth_enabled': props_data.get('isNormalAuthMode', None),
            'sso_enabled': props_data.get('isSSOAuthMode', None),
            'two_factor_required': props_data.get('twoFactorRequired', None)
        }
        if output.get('formatted_email_domains') == '':
            output['formatted_email_domains'] = 'N/A'
            output['join_url'] = 'N/A'

        return output
