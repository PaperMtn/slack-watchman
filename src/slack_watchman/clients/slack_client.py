import json
import re
import requests
import time
import urllib.parse
from typing import List, Dict

from requests.exceptions import HTTPError
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from slack_watchman import exceptions


class SlackClient(object):

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

        try:
            return re.search(regex, r)[0]
        except TypeError:
            raise exceptions.InvalidCookieError(self.url)
        except:
            raise

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