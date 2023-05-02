import hashlib
import json
import logging
import multiprocessing
import os
import re
import requests
import time
import dataclasses
import yaml
import urllib.parse
from typing import List, Dict

from requests.exceptions import HTTPError
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from . import sw_logger
from . import exceptions
from .models import (
    signature,
    user,
    post,
    conversation
)


class SlackAPI(object):

    def __init__(self,
                 token: str = None,
                 cookie: str = None,
                 url: str = None):
        self.token = token
        self.session_token = None
        self.url = url
        self.base_url = 'https://slack.com/api'
        self.count = 100
        self.limit = 100
        self.pretty = 1
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                                        AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'
        if cookie:
            self.cookie_dict = {
                'd': urllib.parse.quote(urllib.parse.unquote(cookie))
            }
        else:
            self.cookie_dict = {}

        self.session = session = requests.session()
        session.mount(
            self.base_url,
            HTTPAdapter(
                pool_connections=10,
                pool_maxsize=10,
                max_retries=Retry(total=5, backoff_factor=0.2)))

        if self.token:
            session.headers.update({
                'Connection': 'keep-alive, close',
                'Authorization': f'Bearer {self.token}',
                'User-Agent': self.user_agent
            })
        else:
            self.session_token = self._get_session_token()
            session.headers.update({
                'Connection': 'keep-alive, close',
                'Authorization': f'Bearer {self.session_token}',
                'User-Agent': self.user_agent
            })

    def _get_session_token(self) -> str:

        r = requests.get(self.url, cookies=self.cookie_dict).text
        regex = '(xox[a-zA-Z]-[a-zA-Z0-9-]+)'

        return re.search(regex, r)[0]

    def _make_request(self, url, params=None, data=None, method='GET', verify_ssl=True):
        try:
            relative_url = '/'.join((self.base_url, url))
            response = self.session.request(
                method,
                relative_url,
                params=params,
                data=data,
                cookies=self.cookie_dict,
                verify=verify_ssl,
                timeout=30)
            response.raise_for_status()

            if not response.json().get('ok') and response.json().get('error') == 'missing_scope':
                raise exceptions.SlackScopeError(response.json().get('needed'))
            elif not response.json().get('ok'):
                raise exceptions.SlackAPIError(response.json().get('error'))
            else:
                return response

        except HTTPError as http_error:
            if response.status_code == 429:
                print('WARNING', 'Slack API rate limit reached - cooling off')
                time.sleep(90)
                return self.session.request(
                    method,
                    relative_url,
                    params=params,
                    data=data,
                    cookies=self.cookie_dict,
                    verify=verify_ssl,
                    timeout=30)
            else:
                raise HTTPError(f'HTTPError: {http_error}')
        except:
            raise

    def _get_pages(self, url, scope, params):
        first_page = self._make_request(url, params).json()
        yield first_page
        num_pages = first_page.get(scope).get('pagination').get('page_count')

        for page in range(2, num_pages + 1):
            params['page'] = str(page)
            next_page = self._make_request(url, params=params).json()
            yield next_page

    def page_api_search(self,
                        query: str,
                        url: str,
                        scope: str,
                        timeframe: str or int) -> List[Dict]:
        """ Wrapper for Slack API methods that use page number based pagination

        Args:
            query: Search to carry out in Slack API
            url: API endpoint to use
            scope: What to search for, e.g. files or messages
            timeframe: How far back to search
        Returns:
            A list of dict objects with responses
        """

        results = []
        params = {
            'query': f'after:{timeframe} {query}',
            'pretty': self.pretty,
            'count': self.count
        }

        for page in self._get_pages(url, scope, params):
            for value in page.get(scope).get('matches'):
                results.append(value)

        return results

    def cursor_api_search(self, url: str, scope: str) -> List[Dict]:
        """ Wrapper for Slack API methods that use cursor based pagination

        Args:
            url: API endpoint to use
            scope: What to search for, e.g. files or messages
        Returns:
            A list of dict objects with responses
        """

        results = []
        params = {
            'pretty': self.pretty,
            'limit': self.limit,
            'cursor': ''
        }

        r = self._make_request(url, params=params).json()
        for value in r.get(scope):
            results.append(value)

        if str(r.get('ok')) == 'False':
            raise exceptions.SlackAPIError(r.get('error'))
        else:
            cursor = r.get('response_metadata').get('next_cursor')
            while str(r.get('ok')) == 'True' and cursor:
                params['limit'], params['cursor'] = 200, cursor
                r = self._make_request(url, params=params).json()
                for value in r.get(scope):
                    cursor = r.get('response_metadata').get('next_cursor')
                    results.append(value)

        return results

    def get_user_info(self, user_id: str) -> json:
        """ Get the user for the given ID

        Args:
            user_id: ID of the user to return
        Returns:
            JSON object with user information
        """

        params = {
            'user': user_id
        }

        return self._make_request('users.info', params=params).json()

    def get_conversation_info(self, conversation_id: str) -> json:
        """ Get the conversation for the given ID

        Args:
            conversation_id: ID of the conversation to return
        Returns:
            JSON object with conversation information
        """

        params = {
            'channel': conversation_id
        }

        return self._make_request('conversations.info', params=params).json()

    def get_workspace_info(self) -> str or None:
        """ Returns the information of the workspace the token is associated with

        Returns:
            JSON object with workspace information
        """

        return self._make_request('team.info').json()

    def get_auth_test(self) -> str or None:
        """ Carries out an auth test against the calling token, and replies with
        user information

        Returns:
            JSON object with auth test response
        """

        return self._make_request('auth.test').json()


def _convert_timestamp(timestamp: int) -> str:
    """ Converts epoch timestamp into human-readable time

    Args:
        timestamp: Epoch formatted timestamp
    Returns:
        String time in the format %Y-%m-%d %H:%M:%S
    """

    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    output = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))

    return output


def _deduplicate(input_list: list) -> List[Dict]:
    """ Removes duplicates where results are returned by multiple queries
    Nested class handles JSON encoding for dataclass objects

    Args:
        input_list: List of dataclass objects
    Returns:
        List of JSON objects with duplicates removed
    """

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

    json_set = {json.dumps(dictionary, sort_keys=True, cls=EnhancedJSONEncoder) for dictionary in input_list}

    deduped_list = [json.loads(t) for t in json_set]
    return {match.get('watchman_id'): match for match in reversed(deduped_list)}.values()


def initiate_slack_connection(cookie: bool) -> SlackAPI:
    """ Create a Slack API object to use for interacting with the Slack API
    First tries to get the API token from the environment variable(s):
        SLACK_WATCHMAN_TOKEN
        SLACK_WATCHMAN_COOKIE
        SLACK_WATCHMAN_URL

    Args:
        cookie: Whether cookie auth is being used
    Returns:
        Slack API object
    """

    if not cookie:
        try:
            token = os.environ['SLACK_WATCHMAN_TOKEN']
        except KeyError:
            with open(f'{os.path.expanduser("~")}/watchman.conf') as yaml_file:
                config = yaml.safe_load(yaml_file)
            try:
                token = config['slack_watchman']['token']
            except:
                raise exceptions.MissingConfigVariable('token')
        return SlackAPI(token=token)
    else:
        try:
            cookie = os.environ['SLACK_WATCHMAN_COOKIE']
            url = os.environ['SLACK_WATCHMAN_URL']
        except KeyError:
            with open(f'{os.path.expanduser("~")}/watchman.conf') as yaml_file:
                config = yaml.safe_load(yaml_file)
            try:
                cookie = config['slack_watchman']['cookie']
            except:
                raise exceptions.MissingConfigVariable('cookie')
            try:
                url = config['slack_watchman']['url']
            except:
                raise exceptions.MissingConfigVariable('url')
        return SlackAPI(cookie=cookie, url=url)


def get_users(slack: SlackAPI, verbose: bool) -> List[user.User]:
    """ Return a list of all active users in the instance

    Args:
        slack: Slack API connection
        verbose: Whether to use verbose logging or not
    Returns:
        List of User objects
    """

    results = []
    users = slack.cursor_api_search('users.list', 'members')
    for value in users:
        if not value.get('deleted'):
            results.append(user.create_from_dict(value, verbose))

    return results


def get_channels(slack: SlackAPI,
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


def find_messages(slack: SlackAPI,
                  logger: sw_logger.JSONLogger,
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
            results = _deduplicate(results)
            logger.log('SUCCESS', f'{len(results)} total matches found after filtering')
            return results
        else:
            logger.log('INFO', 'No matches found after filtering')

    except Exception as e:
        logger.log('CRITICAL', e)


def _multipro_message_worker(slack: SlackAPI,
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


def find_files(slack: SlackAPI,
               logger: sw_logger.JSONLogger,
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
            results = _deduplicate(results)
            logger.log('SUCCESS', f'{len(results)} total files found after filtering')
            return results
        else:
            logger.log('INFO', 'No files found after filtering')

    except Exception as e:
        logger.log('CRITICAL', e)


def _multipro_file_worker(slack: SlackAPI,
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
