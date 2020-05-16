import calendar
import os
import re
import requests
import time
import configparser
import csv

import watchman.definitions as d


def get_token():
    """Get Slack API token from environment or .conf file"""

    try:
        token = os.environ['SLACK_WATCHMAN_TOKEN']
    except KeyError:
        conf = configparser.ConfigParser()
        path = '{}/slack_watchman.conf'.format(os.path.expanduser('~'))
        conf.read(path)
        token = conf.get('auth', 'slack_token')

    return token


def rate_limit_check(response):
    """Checks to see whether you have hit the Slack API rate limit.
    These limits are tiered, so are variable"""

    if not response['ok'] and response['error'] == 'ratelimited':
        print('Slack API rate limit reached - cooling off')
        time.sleep(90)
        return True
    else:
        return False


def convert_timestamp(timestamp):
    """Converts epoch timestamp into human readable time"""

    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    output = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))

    return output


def format_query(query):
    """Helper to strip special characters from filepaths"""

    illegal_chars = [' ', '*', ':', '"', '<', '>', '/', '\\', '|', '?']
    for i in illegal_chars:
        if i in query:
            query = query.replace(i, '_')

    return query


def write_csv(headers, path, input_list):
    """Writes input list to .csv. The headers are and output path are passed as variables"""

    with open('{}'.format(path), mode='w+', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(headers)
        for line in input_list:
            writer.writerow(line)

    csv_file.close()


def get_users():
    """Return a list of all active users in the instance"""

    cursor = ''
    results = []
    token = get_token()

    try:
        while True:
            r = requests.get('https://slack.com/api/users.list',
                             params={'token': token, 'pretty': 1, 'limit': 1, 'cursor': cursor}).json()
            if not rate_limit_check(r):
                break

        if str(r['ok']) == 'False':
            print('END: Unable to dump the user list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = 'https://slack.com/api/users.list'
                params = {'token': token, 'pretty': 1, 'limit': 200, 'cursor': cursor}
                r = requests.get(request_url, params=params).json()
                if rate_limit_check(r):
                    break
                for value in r['members']:
                    cursor = r['response_metadata']['next_cursor']
                    if not value['deleted']:
                        results.append(value)
    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def get_channels():
    """Return a list of all channels in the instance"""

    cursor = ''
    results = []
    token = get_token()

    try:
        while True:
            r = requests.get('https://slack.com/api/conversations.list',
                             params={'token': token, 'pretty': 1, 'limit': 1, 'cursor': cursor}).json()
            if not rate_limit_check(r):
                break

        if str(r['ok']) == 'False':
            print('END: Unable to dump the channel list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = 'https://slack.com/api/conversations.list'
                params = {'token': token, 'pretty': 1, 'limit': 1000, 'cursor': cursor}
                r = requests.get(request_url, params=params).json()
                rate_limit_check(r)
                for value in r['channels']:
                    cursor = r['response_metadata']['next_cursor']
                    results.append(value)
    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def output_all_channels(channel_list, timeframe=d.ALL_TIME):
    """Write all channels to .csv"""

    results = []
    headers = ['created', 'id', 'name', 'description']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for channel in channel_list:
        if channel['created'] > now - timeframe:
            results.append([convert_timestamp(channel['created']),
                            channel['id'],
                            channel['name'],
                            channel['topic']['value']])

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
        if 'email' in user['profile']:
            results.append([user['id'],
                            user['name'],
                            user['profile']['email']])
        else:
            results.append([user['id'],
                            user['name'],
                            'NO EMAIL'])

    if results:
        path = '{}/all_users.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} users found'.format(len(results)))
        print('CSV written: {}'.format(path))


def search_files(query):
    """Return a list of all files that match the given query"""

    page_count_by_query = {}
    results = []
    token = get_token()

    try:
        while True:
            r = requests.get('https://slack.com/api/search.files',
                             params={'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100}).json()
            if not rate_limit_check(r):
                break

        page_count_by_query[query] = (r['files']['pagination']['page_count'])
        print('{} page(s) found for query: {}'.format(page_count_by_query.get(query), query))

        for query, page_count in page_count_by_query.items():
            page = 1
            while page <= page_count:
                params = {'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100, 'page': str(page)}
                r = requests.get('https://slack.com/api/search.files',
                                 params=params).json()
                if rate_limit_check(r):
                    break
                for value in r['files']['matches']:
                    results.append(value)
                page += 1

    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def search_messages(query):
    """Return a list of all messages that match the given query"""

    page_count_by_query = {}
    results = []
    token = get_token()

    try:
        while True:
            r = requests.get('https://slack.com/api/search.messages',
                             params={'token': token, 'query': query, 'pretty': 1, 'count': 100}).json()
            if not rate_limit_check(r):
                break

        page_count_by_query[query] = (r['messages']['pagination']['page_count'])
        print('{} page(s) found for query: {}'.format(page_count_by_query.get(query), query))

        for query, page_count in page_count_by_query.items():
            page = 1
            while page <= page_count:
                params = {'token': token, 'query': query, 'pretty': 1, 'count': 100,
                          'page': str(page)}
                r = requests.get('https://slack.com/api/search.messages',
                                 params=params).json()
                if rate_limit_check(r):
                    break

                for value in r['messages']['matches']:
                    results.append(value)
                page += 1

    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def get_admins(user_list):
    """Return all admin users from the input userlist"""

    results = []
    headers = ['id', 'name', 'email']
    out_path = os.getcwd()

    for user in user_list:
        if 'is_admin' in user.keys() and user['is_admin']:
            results.append([user['id'],
                            user['name'],
                            user['profile']['email']])

    if results:
        path = '{}/admins.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} admin users found'.format(len(results)))
        print('CSV written: {}'.format(path))


def get_external_shared(channel_list, timeframe=d.ALL_TIME):
    """Return all external shared channels from the input channel list"""

    results = []
    headers = ['created', 'id', 'name', 'description']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for channel in channel_list:
        if 'is_ext_shared' in channel.keys() and channel['is_ext_shared'] and channel['created'] > now - timeframe:
            results.append([convert_timestamp(channel['created']),
                            channel['id'],
                            channel['name'],
                            channel['topic']['value']])

    if results:
        path = '{}/external_channels.csv'.format(out_path)
        write_csv(headers, path, results)
        print('{} external channels found'.format(len(results)))
        print('CSV written: {}'.format(path))


def find_keys(timeframe=d.ALL_TIME):
    """Look for private keys in public channels by first searching for common terms for private keys
    then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.PRIVATE_KEYS:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.PRIVATE_KEYS_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/private_keys_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_certificates(timeframe=d.ALL_TIME):
    """Look for certificate files in public channels by first searching for certificate file extensions
    these are then filtered down further to include only true certificate files"""

    headers = ['timestamp', 'file_name', 'posted_by', 'preview', 'private_link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.CERTIFICATE_EXTENSIONS:
        message_list = search_files(query)
        results = []
        for message in message_list:
            timestamp = message['timestamp']
            if 'text' in message['filetype'] and query in message['name'] and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['timestamp']),
                                message['name'],
                                message['username'],
                                message['preview'],
                                message['permalink']])
        if results:
            path = '{}/certificates_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_aws_credentials(timeframe=d.ALL_TIME):
    """Look for AWS credentials in public channels by first searching for common AWS key phrases
    these are then filtered down by regex"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.AWS_KEYS_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.AWS_KEYS_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/aws_credentials_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_gcp_credentials(timeframe=d.ALL_TIME):
    """Look for GCP credential files in public channels by first searching for certificate file extensions
    these are then filtered down further to include only true certificate files"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.GCP_CREDENTIAL_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.GCP_CREDENTIAL_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/gcp_credentials_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_google_credentials(timeframe=d.ALL_TIME):
    """Look for Google credentials in public channels by first searching for common Goole key phrases
    these are then filtered down by regex"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.GOOGLE_API_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.GOOGLE_API_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/google_api_keys_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_slack_tokens(timeframe=d.ALL_TIME):
    """Look for Slack tokens in public channels by first searching for Slack token prefixes
    these are then filtered down by regex"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.SLACK_KEY_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.SLACK_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])

        if results:
            path = '{}/slack_token_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_malicious_files(timeframe=d.ALL_TIME):
    """Look for interesting files in public channels by first searching for file extensions
    these are then filtered down further to include only files of those extensions"""

    headers = ['timestamp', 'file_name', 'posted_by', 'private_link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.FILE_EXTENSIONS:
        message_list = search_files(query)
        results = []
        for message in message_list:
            timestamp = message['timestamp']
            if query in message['name'] and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['timestamp']),
                                message['name'],
                                message['username'],
                                message['permalink']])
        if results:
            path = '{}/interesting_files_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_passwords(timeframe=d.ALL_TIME):
    """Look for passwords in public channels by first searching for common terms for passwords
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.PASSWORD_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.PASSWORD_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/potential_leaked_passwords_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))


def find_card_details(timeframe=d.ALL_TIME):
    """Look for card details in public channels by first searching for common terms for cards
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel_name', 'posted_by', 'content', 'link']
    now = calendar.timegm(time.gmtime())
    out_path = os.getcwd()

    for query in d.BANK_CARD_QUERIES:
        message_list = search_messages(query)
        results = []
        for message in message_list:
            r = re.compile(d.BANK_CARD_REGEX)
            timestamp = message['ts'].split('.', 1)[0]
            if r.search(str(message)) and int(timestamp) > now - timeframe:
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            path = '{}/potential_leaked_bank_cards_{}.csv'.format(out_path, format_query(query))
            write_csv(headers, path, results)
            print('{} matches found for {}'.format(len(results), query))
            print('CSV written: {}'.format(path))
