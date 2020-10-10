import builtins
import json
import os
import re
import requests
import time
import yaml
from requests.exceptions import HTTPError

from slack_watchman import config as cfg
from slack_watchman import logger


class ScopeError(Exception):
    pass


class SlackAPI(object):

    def __init__(self, token):
        self.token = token
        self.base_url = 'https://slack.com/api'
        self.per_page = 100
        self.count = 100
        self.limit = 1
        self.pretty = 1
        self.session = session = requests.session()
        session.mount(self.base_url, requests.adapters.HTTPAdapter())
        session.headers.update({'Connection': 'keep-alive, close',
                                'Authorization': 'Bearer {}'.format(self.token),
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                                    AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'})

    def make_request(self, url, params=None, data=None, method='GET', verify_ssl=True):
        try:
            relative_url = '/'.join((self.base_url, url))
            response = self.session.request(method, relative_url, params=params, data=data, verify=verify_ssl)
            response.raise_for_status()

            if not response.json().get('ok') and response.json().get('error') == 'missing_scope':
                raise ScopeError()
            else:
                return response

        except HTTPError as http_error:
            if response.status_code == 429:
                print('Slack API rate limit reached - cooling off')
                time.sleep(90)
                return self.session.request(method, relative_url, params=params, data=data, verify=verify_ssl)
            else:
                raise HTTPError('HTTPError: {}'.format(http_error))
        except ScopeError:
            raise ScopeError('Missing required scope: {}'.format(response.json().get('needed')))
        except Exception as e:
            raise Exception(e)

    def validate_token(self):
        """Check that slack token is valid"""

        r = self.make_request('users.list').json()

        if not r.get('ok') and r.get('error') == 'invalid_auth':
            raise Exception('Invalid Slack API key')

    def get_user_info(self, user_id):
        """Get the user for the given ID"""

        params = {
            'user': user_id
        }

        r = self.make_request('users.info', params=params).json()

        if str(r.get('ok')) == 'False':
            print('END: Unable to get the user: ' + str(r.get('error')))
            return None
        else:
            return r

    def get_workspace_name(self):
        """Returns the name of the workspace you are searching"""

        r = self.make_request('team.info').json()

        if str(r.get('ok')) == 'False':
            print('END: Unable to get the workspace name. Slack error: ' + str(r.get('error')))
            return None
        else:
            return r.get('team').get('name')

    def get_workspace_domain(self):
        """Returns the domain of the workspace you are searching"""

        r = self.make_request('team.info').json()

        if str(r.get('ok')) == 'False':
            print('END: Unable to get the workspace domain. Slack error: ' + str(r.get('error')))
        else:
            return 'https://{}.slack.com/'.format(r.get('team').get('domain'))

    def page_api_search(self, query, url, scope, timeframe):
        """Wrapper for Slack API methods that use page number based pagination"""

        page_count_by_query = {}
        results = []
        params = {
            'query': 'after:{} {}'.format(timeframe, query),
            'pretty': self.pretty,
            'count': self.count
        }

        r = self.make_request(url, params=params).json()
        for value in r.get(scope).get('matches'):
            results.append(value)

        page_count_by_query[query] = (r.get(scope).get('pagination').get('page_count'))

        for query, page_count in page_count_by_query.items():
            page = 1
            while page <= page_count:
                params['page'] = str(page)
                r = self.make_request(url, params=params).json()
                for value in r.get(scope).get('matches'):
                    results.append(value)
                page += 1

        return results

    def cursor_api_search(self, url, scope, ):
        """Wrapper for Slack API methods that use cursor based pagination"""

        results = []
        params = {
            'pretty': self.pretty,
            'limit': self.limit,
            'cursor': ''
        }

        r = self.make_request(url, params=params).json()
        for value in r.get(scope):
            results.append(value)

        if str(r.get('ok')) == 'False':
            print('END: Unable to dump the user list. Slack error: ' + str(r.get('error')))
        else:
            cursor = r.get('response_metadata').get('next_cursor')
            while str(r.get('ok')) == 'True' and cursor:
                params['limit'], params['cursor'] = 200, cursor
                r = self.make_request(url, params=params).json()
                for value in r.get(scope):
                    cursor = r.get('response_metadata').get('next_cursor')
                    results.append(value)

        return results


def initiate_slack_connection():
    try:
        token = os.environ['SLACK_WATCHMAN_TOKEN']
    except KeyError:
        with open('{}/watchman.conf'.format(os.path.expanduser('~'))) as yaml_file:
            config = yaml.safe_load(yaml_file)

        token = config.get('slack_watchman').get('token')

    return SlackAPI(token)


def convert_timestamp(timestamp):
    """Converts epoch timestamp into human readable time"""

    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    output = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))

    return output


def deduplicate(input_list):
    """Removes duplicates where results are returned by multiple queries"""

    list_of_strings = [json.dumps(d, sort_keys=True) for d in input_list]
    list_of_strings = set(list_of_strings)
    return [json.loads(s) for s in list_of_strings]


def get_users(slack: SlackAPI):
    """Return a list of all active users in the instance"""

    results = []
    users = slack.cursor_api_search('users.list', 'members')
    for value in users:
        if not value.get('deleted'):
            results.append(value)

    return results


def get_channels(slack: SlackAPI):
    """Return a list of all channels in the instance"""

    return slack.cursor_api_search('conversations.list', 'channels')


def get_all_channels(log_handler, channel_list, timeframe=cfg.ALL_TIME):
    """Write all channels to .csv"""

    results = []
    utc_time = time.strptime(timeframe, '%Y-%m-%d')
    epoch_timeframe = time.mktime(utc_time)

    if isinstance(log_handler, logger.StdoutLogger):
        print = log_handler.log_info
    else:
        print = builtins.print

    for channel in channel_list:
        created = channel.get('created')
        if int(created) > epoch_timeframe:
            results_dict = {
                'channel_id': channel.get('id'),
                'channel_name': channel.get('name'),
                'topic': channel.get('topic').get('value'),
                'creator': channel.get('creator'),
                'created': convert_timestamp(created),
                'is_archived': channel.get('is_archived'),
                'number_of_members': channel.get('num_members'),
                'is_ext_shared': channel.get('is_ext_shared')
            }

            results.append(results_dict)

    if results:
        results = deduplicate(results)
        print('{} channels found'.format(len(results)))
        return results
    else:
        print('No matches found after filtering')


def get_all_users(log_handler, user_list):
    """Write all users to .csv"""

    results = []

    if isinstance(log_handler, logger.StdoutLogger):
        print = log_handler.log_info
    else:
        print = builtins.print

    for user in user_list:
        results_dict = {
            'user_id': user.get('id'),
            'user_name': user.get('name'),
            'email': user.get('profile').get('email', ''),
            'team_id': user.get('team_id'),
            'updated': user.get('updated'),
            'deleted': user.get('deleted'),
            'has_2fa': user.get('has_2fa'),
            'is_admin': user.get('is_admin')
        }

        results.append(results_dict)

    if results:
        results = deduplicate(results)
        print('{} users found'.format(len(results)))
        return results
    else:
        print('No matches found after filtering')


def find_messages(slack: SlackAPI, log_handler, rule, timeframe=cfg.ALL_TIME):
    """Look in public channels by first searching for common terms in query list
        then trimming this list down using a regex search"""

    results = []

    if isinstance(log_handler, logger.StdoutLogger):
        print = log_handler.log_info
    else:
        print = builtins.print

    for query in rule.get('strings'):
        message_list = slack.page_api_search(query, 'search.messages', 'messages', timeframe)
        print('{} messages found matching: {}'.format(len(message_list), query.replace('"', '')))
        for message in message_list:
            r = re.compile(rule.get('pattern'))
            if r.search(str(message.get('text'))):
                results_dict = {
                    'message_id': message.get('iid'),
                    'timestamp': convert_timestamp(message.get('ts')),
                    'channel_name': message.get('channel').get('name'),
                    'posted_by': message.get('username'),
                    'match_string': r.search(str(message.get('text'))).group(0),
                    'text': message.get('text'),
                    'permalink': message.get('permalink')
                }

                results.append(results_dict)
    if results:
        results = deduplicate(results)
        print('{} total matches found after filtering'.format(len(results)))
        return results
    else:
        print('No matches found after filtering')


def find_files(slack: SlackAPI, log_handler, rule, timeframe=cfg.ALL_TIME):
    """Look for files in public channels by first searching for common terms for the file
    these are then filtered down further to include only files of those extensions"""
    results = []
    if isinstance(log_handler, logger.StdoutLogger):
        print = log_handler.log_info
    else:
        print = builtins.print
    for query in rule.get('strings'):
        message_list = slack.page_api_search(query, 'search.files', 'files', timeframe)
        print('{} files found matching: {}'.format(len(message_list), query.replace('"', '')))
        for fl in message_list:
            if rule.get('file_types'):
                for file_type in rule.get('file_types'):
                    if query.replace('\"', '').lower() in fl.get('name').lower() \
                            and file_type.lower() in fl.get('filetype').lower():
                        user = slack.get_user_info(fl.get('user'))
                        results_dict = {
                            'file_id': fl.get('id'),
                            'timestamp': convert_timestamp(fl.get('timestamp')),
                            'name': fl.get('name'),
                            'mimetype': fl.get('mimetype'),
                            'file_type': fl.get('filetype'),
                            'posted_by': user.get('user').get('name'),
                            'created': fl.get('created'),
                            'preview': fl.get('preview'),
                            'permalink': fl.get('permalink')
                        }
                        results.append(results_dict)
            else:
                if query.replace('\"', '').lower() in fl.get('name').lower():
                    user = slack.get_user_info(fl.get('user'))
                    results_dict = {
                        'file_id': fl.get('id'),
                        'timestamp': convert_timestamp(fl.get('timestamp')),
                        'name': fl.get('name'),
                        'mimetype': fl.get('mimetype'),
                        'file_type': fl.get('filetype'),
                        'posted_by': user.get('user').get('name'),
                        'created': fl.get('created'),
                        'preview': fl.get('preview'),
                        'permalink': fl.get('permalink')
                    }
                    results.append(results_dict)
    if results:
        results = deduplicate(results)
        print('{} total matches found after filtering'.format(len(results)))
        return results
    else:
        print('No matches found after filtering')
