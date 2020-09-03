import itertools
import os
import re
import requests
import time
import configparser
import csv
from requests.exceptions import HTTPError

import watchman.definitions as d


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

            return response

        except HTTPError as http_error:
            if response.status_code == 429:
                print('Slack API rate limit reached - cooling off')
                time.sleep(90)
                return self.session.request(method, relative_url, params=params, data=data, verify=verify_ssl)
            else:
                print('HTTPError: {}'.format(http_error))
        except Exception as e:
            print(e)

    def validate_token(self):
        """Check that slack token is valid"""

        r = self.make_request('users.list').json()

        if not r.get('ok') and r.get('error') == 'invalid_auth':
            raise Exception('Invalid Slack API key')

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
        print('{} page(s) found for query: {}'.format(page_count_by_query.get(query), query))

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
        conf = configparser.ConfigParser()
        path = '{}/watchman.conf'.format(os.path.expanduser('~'))
        conf.read(path)
        token = conf.get('auth', 'slack_token')

    return SlackAPI(token)


def convert_timestamp(timestamp):
    """Converts epoch timestamp into human readable time"""

    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    output = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))

    return output


def deduplicate(input_list):
    """Removes duplicates where results are returned by multiple queries"""

    input_list.sort()
    return list(input_list for input_list, _ in itertools.groupby(input_list))


def write_csv(headers, path, input_list):
    """Writes input list to .csv. The headers are and output path are passed as variables"""

    with open('{}'.format(path), mode='w+', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(headers)
        for line in input_list:
            writer.writerow(line)

    csv_file.close()


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

    return slack.cursor_api_search('channels.list', 'channels')


def output_all_channels(channel_list, timeframe=d.ALL_TIME):
    """Write all channels to .csv"""

    results = []
    headers = ['created', 'id', 'name', 'description']
    out_path = os.getcwd()

    utc_time = time.strptime(timeframe, '%Y-%m-%d')
    epoch_timeframe = time.mktime(utc_time)

    for channel in channel_list:
        created = channel.get('created')
        if int(created) > epoch_timeframe:
            results.append([convert_timestamp(created),
                            channel.get('id'),
                            channel.get('name'),
                            channel.get('topic').get('value')])

    if results:
        path = '{}/all_channels.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} channels found'.format(len(results)))
        print('CSV written: {}'.format(path))


def output_all_users(user_list):
    """Write all users to .csv"""

    results = []
    headers = ['id', 'name', 'email']
    out_path = os.getcwd()

    for user in user_list:
        if 'email' in user.get('profile'):
            results.append([user.get('id'),
                            user.get('name'),
                            user.get('profile').get('email', 'NO EMAIL')])

    if results:
        path = '{}/all_users.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} users found'.format(len(results)))
        print('CSV written: {}'.format(path))


def get_admins(user_list):
    """Return all admin users from the input userlist"""

    results = []
    headers = ['id', 'name', 'email']
    out_path = os.getcwd()

    for user in user_list:
        if 'is_admin' in user.keys() and user.get('is_admin'):
            results.append([user.get('id'),
                            user.get('name'),
                            user.get('profile').get('email')])

    if results:
        path = '{}/admins.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} admin users found'.format(len(results)))
        print('CSV written: {}'.format(path))


def get_external_shared(channel_list, timeframe=d.ALL_TIME):
    """Return all external shared channels from the input channel list"""

    results = []
    headers = ['created', 'id', 'name', 'description']
    out_path = os.getcwd()

    utc_time = time.strptime(timeframe, '%Y-%m-%d')
    epoch_timeframe = time.mktime(utc_time)

    if channel_list:
        for channel in channel_list:
            created = channel.get('created')
            if 'is_ext_shared' in channel.keys() and channel.get('is_ext_shared') and int(created) > epoch_timeframe:
                results.append([convert_timestamp(created),
                                channel.get('id'),
                                channel.get('name'),
                                channel.get('topic').get('value')])

    if results:
        path = '{}/external_channels.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} external channels found'.format(len(results)))
        print('CSV written: {}'.format(path))
    else:
        print('No external channels')


def find_certificates(slack: SlackAPI, timeframe=d.ALL_TIME):
    """Look for certificate files in public channels by first searching for certificate file extensions
    these are then filtered down further to include only true certificate files
    Difference in logic means a specific function is required rather than using the generic find_files function
    """

    headers = ['timestamp', 'file_name', 'posted_by', 'preview', 'private_link']
    out_path = os.getcwd()
    results = []
    for query in d.CERTIFICATE_EXTENSIONS:
        message_list = slack.page_api_search(query, 'search.files', 'files', timeframe)
        for message in message_list:
            if 'text' in message.get('filetype') and query in message.get('name'):
                results.append([convert_timestamp(message.get('timestamp')),
                                message.get('name'),
                                message.get('username'),
                                message.get('preview'),
                                message.get('permalink')])
    if results:
        results = deduplicate(results)
        path = '{}/certificates.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} total matches found after filtering'.format(len(results)))
        print('CSV written: {}'.format(path))
    else:
        print('No matches found after filtering')


def find_messages(slack: SlackAPI, query_list, regex, file_name, timeframe=d.ALL_TIME):
    """Look in public channels by first searching for common terms in query list
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    out_path = os.getcwd()
    results = []
    for query in query_list:
        message_list = slack.page_api_search(query, 'search.messages', 'messages', timeframe)
        for message in message_list:
            r = re.compile(regex)
            if r.search(str(message.get('text'))):
                results.append([convert_timestamp(message.get('ts')),
                                message.get('channel').get('name'),
                                message.get('username'),
                                message.get('text'),
                                message.get('permalink')])
    if results:
        results = deduplicate(results)
        path = '{}/potential_{}.csv'.format(out_path, file_name)
        write_csv(headers, path, results)
        print('{} total matches found after filtering'.format(len(results)))
        print('CSV written: {}'.format(path))
    else:
        print('No matches found after filtering')


def find_files(slack: SlackAPI, query_list, file_name, timeframe=d.ALL_TIME):
    """Look for files in public channels by first searching for common terms for the file
    these are then filtered down further to include only files of those extensions"""

    headers = ['timestamp', 'file_name', 'posted_by', 'private_link']
    out_path = os.getcwd()
    results = []
    for query in query_list:
        message_list = slack.page_api_search(query, 'search.files', 'files', timeframe)
        for message in message_list:
            if query.replace('\"', '') in message.get('name'):
                results.append([convert_timestamp(message.get('timestamp')),
                                message.get('name'),
                                message.get('username'),
                                message.get('permalink')])
    if results:
        results = deduplicate(results)
        path = '{}/{}.csv'.format(out_path, file_name)
        write_csv(headers, path, results)
        print('{} total matches found after filtering'.format(len(results)))
        print('CSV written: {}'.format(path))
    else:
        print('No matches found after filtering')


def find_custom_queries(slack: SlackAPI, query_list, timeframe=d.ALL_TIME):
    """Look in public channels by first searching for common terms in query list
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    out_path = os.getcwd()
    results = []
    for query in query_list:
        message_list = slack.page_api_search(query, 'search.messages', 'messages', timeframe)
        for message in message_list:
            results.append([convert_timestamp(message.get('ts')),
                            message.get('channel').get('name'),
                            message.get('username'),
                            message.get('text'),
                            message.get('permalink')])
    if results:
        results = deduplicate(results)
        path = '{}/custom_strings.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} total matches found after filtering'.format(len(results)))
        print('CSV written: {}'.format(path))
    else:
        print('No matches found')
