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

_DEFAULT_POOL_SIZE = 8

# Each worker process holds its own SlackClient, constructed once by
# `_init_worker_client` when the pool starts up. Workers read it via the
# module-level global rather than receiving the parent's pickled client.
_WORKER_SLACK_CLIENT: SlackClient | None = None


def _slack_init_args(slack: SlackClient) -> tuple:
    """ Extract the credentials needed to rebuild a SlackClient inside a
    worker process.

    Args:
        slack: The parent process's SlackClient
    Returns:
        Tuple of `(token, url, session_token, cookie_dict)` suitable for
        passing as `Pool(initargs=...)`
    """
    return (slack.token, slack.url, slack.session_token, dict(slack.cookie_dict))


def _init_worker_client(token, url, session_token, cookie_dict) -> None:
    """ Pool initializer: build one SlackClient per worker process.

    Skips the workspace-URL roundtrip in `_get_session_token` because the
    parent has already done it; `session_token` and `cookie_dict` carry the
    pre-extracted credentials.
    """
    global _WORKER_SLACK_CLIENT  # pylint: disable=global-statement
    _WORKER_SLACK_CLIENT = SlackClient(
        token=token,
        url=url,
        session_token=session_token,
        cookie_dict=cookie_dict,
    )


def _pool_run_message(args) -> None:
    """ Pool task wrapper: forward to `_multipro_message_worker` using the
    worker-local SlackClient set up by `_init_worker_client`.
    """
    sig, query, verbose, timeframe, results, potential_matches, errors = args
    _multipro_message_worker(
        _WORKER_SLACK_CLIENT, sig, query, verbose, timeframe,
        results=results, potential_matches=potential_matches, errors=errors,
    )


def _pool_run_file(args) -> None:
    """ Pool task wrapper: forward to `_multipro_file_worker` using the
    worker-local SlackClient set up by `_init_worker_client`.
    """
    sig, query, verbose, timeframe, results, potential_matches, errors = args
    _multipro_file_worker(
        _WORKER_SLACK_CLIENT, sig, query, verbose, timeframe,
        results=results, potential_matches=potential_matches, errors=errors,
    )


def _resolve_file_user(slack: SlackClient, file_dict: Dict, verbose: bool,
                       cache: Dict) -> object:
    """ Resolve a file's owner via `users.info`, caching by user ID.

    Args:
        slack: SlackClient used for the lookup
        file_dict: Raw file dict from `search.files`
        verbose: Whether to populate verbose model fields
        cache: Per-worker dict, keyed by user ID; mutated in place
    Returns:
        Resolved User dataclass, or None when the file has no owner
    """
    user_id = file_dict.get('user')
    if not user_id:
        return None
    if user_id not in cache:
        user_dict = slack.get_user_info(user_id).get('user')
        cache[user_id] = user.create_from_dict(user_dict, verbose)
    return cache[user_id]


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
        with multiprocessing.Manager() as manager:
            results = manager.list()
            potential_matches = manager.list()
            errors = manager.list()

            pool_size = max(1, min(_DEFAULT_POOL_SIZE, len(sig.search_strings)))
            tasks = [
                (sig, query, verbose, timeframe, results, potential_matches, errors)
                for query in sig.search_strings
            ]
            with multiprocessing.Pool(
                processes=pool_size,
                initializer=_init_worker_client,
                initargs=_slack_init_args(slack),
            ) as pool:
                pool.map(_pool_run_message, tasks)

            for err in errors:
                logger.log(
                    'ERROR',
                    f"Worker failed for signature '{err.get('signature')}' "
                    f"query '{err.get('query')}': {err.get('error')}"
                )

            if potential_matches:
                logger.log('INFO', f'{sum(potential_matches)} potential matches found')

            if results:
                results = deduplicate_results(results)
                logger.log('SUCCESS', f'{len(results)} total matches found after filtering')
                return results
            logger.log('INFO', 'No matches found after filtering')
            return []
    except Exception as e:  # pylint: disable=broad-except
        logger.log('CRITICAL', e)
        return []


# pylint: disable=too-many-locals,too-many-nested-blocks
def _multipro_message_worker(slack: SlackClient,
                             sig: signature.Signature,
                             query: str,
                             verbose: bool,
                             timeframe: str,
                             **kwargs):
    errors = kwargs.get('errors')
    try:
        message_list = slack.page_api_search(query, 'search.messages', 'messages', timeframe)
        kwargs.get('potential_matches').append(len(message_list))
        # Per-worker caches: each unique user/channel ID is resolved once and
        # reused for every subsequent match in this worker.
        user_cache: Dict = {}
        channel_cache: Dict = {}
        compiled_patterns = [re.compile(pattern) for pattern in sig.patterns]
        for message in message_list:
            text = message.get('text')
            if not text:
                continue
            for r in compiled_patterns:
                match = r.search(text)
                if match:
                    user_id = message.get('user')
                    if user_id:
                        if user_id not in user_cache:
                            user_dict = slack.get_user_info(user_id).get('user')
                            user_cache[user_id] = user.create_from_dict(user_dict, verbose)
                        u = user_cache[user_id]
                    else:
                        u = message.get('username')

                    channel_id = (message.get('channel') or {}).get('id')
                    if channel_id:
                        if channel_id not in channel_cache:
                            channel_dict = slack.get_conversation_info(channel_id).get('channel')
                            channel_cache[channel_id] = conversation.create_from_dict(
                                channel_dict, verbose
                            )
                        c = channel_cache[channel_id]
                    else:
                        c = None

                    message['user'] = u
                    message['conversation'] = c
                    match_string = match.group(0)
                    message = post.create_message_from_dict(message)

                    watchman_id = hashlib.md5(f'{match_string}.{message.timestamp}'.encode()).hexdigest()
                    results_dict = {
                        'match_string': match_string,
                        'message': message,
                        'watchman_id': watchman_id
                    }

                    kwargs.get('results').append(results_dict)
        return kwargs.get('results'), kwargs.get('potential_matches')
    except Exception as e:  # pylint: disable=broad-except
        if errors is None:
            raise
        errors.append({
            'signature': getattr(sig, 'name', None),
            'query': query,
            'error': repr(e)
        })
        return None


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
        with multiprocessing.Manager() as manager:
            results = manager.list()
            potential_matches = manager.list()
            errors = manager.list()

            pool_size = max(1, min(_DEFAULT_POOL_SIZE, len(sig.search_strings)))
            tasks = [
                (sig, query, verbose, timeframe, results, potential_matches, errors)
                for query in sig.search_strings
            ]
            with multiprocessing.Pool(
                processes=pool_size,
                initializer=_init_worker_client,
                initargs=_slack_init_args(slack),
            ) as pool:
                pool.map(_pool_run_file, tasks)

            for err in errors:
                logger.log(
                    'ERROR',
                    f"Worker failed for signature '{err.get('signature')}' "
                    f"query '{err.get('query')}': {err.get('error')}"
                )

            if potential_matches:
                logger.log('INFO', f'{sum(potential_matches)} potential matches found')

            if results:
                results = deduplicate_results(results)
                logger.log('SUCCESS', f'{len(results)} total files found after filtering')
                return results
            logger.log('INFO', 'No files found after filtering')
            return []

    except Exception as e:  # pylint: disable=broad-except
        logger.log('CRITICAL', e)
        return []


# pylint: disable=too-many-nested-blocks
def _multipro_file_worker(slack: SlackClient,
                          sig: signature.Signature,
                          query: str,
                          verbose: bool,
                          timeframe: str,
                          **kwargs):
    errors = kwargs.get('errors')
    try:
        message_list = slack.page_api_search(query, 'search.files', 'files', timeframe)
        kwargs.get('potential_matches').append(len(message_list))
        # Per-worker cache: each unique file owner is resolved once.
        user_cache: Dict = {}
        for file_dict in message_list:
            name = (file_dict.get('name') or '').lower()
            filetype = (file_dict.get('filetype') or '').lower()
            if sig.file_types:

                if query.replace('\"', '').lower() in name and any(
                        file_type.lower() in filetype for file_type in sig.file_types):
                    u = _resolve_file_user(slack, file_dict, verbose, user_cache)

                    f = post.create_file_from_dict(file_dict)
                    watchman_id = hashlib.md5(f'{f.created}.{f.permalink_public}'.encode()).hexdigest()
                    results_dict = {
                        'file': f,
                        'user': u,
                        'watchman_id': watchman_id
                    }
                    kwargs.get('results').append(results_dict)
            else:
                if query.replace('\"', '').lower() in name:
                    u = _resolve_file_user(slack, file_dict, verbose, user_cache)

                    f = post.create_file_from_dict(file_dict)
                    watchman_id = hashlib.md5(f'{f.created}.{f.permalink_public}'.encode()).hexdigest()
                    results_dict = {
                        'file': f,
                        'user': u,
                        'watchman_id': watchman_id
                    }

                    kwargs.get('results').append(results_dict)
        return kwargs.get('results'), kwargs.get('potential_matches')
    except Exception as e:  # pylint: disable=broad-except
        if errors is None:
            raise
        errors.append({
            'signature': getattr(sig, 'name', None),
            'query': query,
            'error': repr(e)
        })
        return None


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
