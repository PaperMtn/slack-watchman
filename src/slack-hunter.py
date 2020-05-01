import re
import requests
import time
import configparser
import csv

PRIVATE_KEYS = ["BEGIN DSA PRIVATE",
                "BEGIN EC PRIVATE",
                "BEGIN OPENSSH PRIVATE",
                "BEGIN PGP PRIVATE",
                "BEGIN RSA PRIVATE"]
PASSWORD_QUERIES = ["password:",
                    "password is",
                    "pwd",
                    "passwd"]
BANK_CARD_QUERIES = ['cvv',
                     'card',
                     'cardno',
                     '"card no:"',
                     '"card number:"',
                     '4026*',
                     '417500*',
                     '4508*',
                     '4844*',
                     '4913*',
                     '4917*']
FILE_EXTENSIONS = ['.exe',
                   '.zip',
                   '.doc',
                   '.docx',
                   '.docm',
                   '.xls',
                   '.xlsx'
                   '.xlsm',
                   '.conf']
CERTIFICATE_EXTENSIONS = ['.key',
                          '.p12',
                          '.pem',
                          '.pfx',
                          '.pkcs12']
CREDENTIAL_EXTENSIONS = ['.json']
AWS_KEYS_QUERIES = ['ASIA*', 'AKIA*']

PRIVATE_KEYS_REGEX = r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)"
PASSWORD_REGEX = r"(?i)(password\s*[`=:\"]+\s*[^\s]+|password is\s*[`=:\"]*\s*[^\s]+|pwd\s*[`=:\"]*\s*[^\s]+|passwd\s*[`=:\"]+\s*[^\s]+)"
BANK_CARD_REGEX = r"^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$|^4[0-9]{12}(?:[0-9]{3})?$|^3[47][0-9]{13}$|^6(?:011|5[0-9]{2})[0-9]{12}$|^(?:2131|1800|35\d{3})\d{11}$"
AWS_KEYS_REGEX = r"(?!com/archives/[A-Z0-9]{9}/p[0-9]{16})((?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])|(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9]))"

def get_token():
    """Get Slack API token from .conf file"""

    conf = configparser.ConfigParser()
    conf.read('../config/keys.conf')
    token = conf.get('auth', 'slack_user_token')

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


def week_old(created_time):
    """Epoch time check for newer than 7 days"""

    if created_time > time.time() - 604800:
        return True
    else:
        return False


def month_old(created_time):
    """Epoch time check for newer than 30 days"""

    if created_time > time.time() - 2592000:
        return True
    else:
        return False


def convert_timestamp(timestamp):
    """Converts epoch timestamp into human readable time"""
    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    output = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))

    return output


def write_output(out_path, out_list):
    with open(out_path, 'w+') as f:
        for item in out_list:
            f.write(str(item) + '\n')


def write_csv(headers, filepath, input_list):
    with open('{}.csv'.format(filepath), mode='w+') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(headers)
        for line in input_list:
            writer.writerow(line)

    csv_file.close()


def get_users(token):
    """Return a list of all active users in the instance"""

    cursor = ''
    results = []

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


def get_channels(token):
    """Return a list of all channels in the instance"""

    cursor = ''
    results = []

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


def search_files(token, query):
    """Return a list of all files that match the given query"""

    page_count_by_query = {}
    results = []

    try:
        while True:
            r = requests.get('https://slack.com/api/search.files',
                             params={'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100}).json()
            if not rate_limit_check(r):
                break

        page_count_by_query[query] = (r['files']['pagination']['page_count'])
        print(page_count_by_query)

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


def search_messages(token, query):
    """Return a list of all messages that match the given query"""

    page_count_by_query = {}
    results = []

    try:
        while True:
            r = requests.get('https://slack.com/api/search.messages',
                             params={'token': token, 'query': query, 'pretty': 1, 'count': 100}).json()
            if not rate_limit_check(r):
                break

        page_count_by_query[query] = (r['messages']['pagination']['page_count'])
        print(page_count_by_query)

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

    for i in user_list:
        if 'is_admin' in i.keys() and i['is_admin']:
            results.append(i)

    return results


def get_external_shared(channel_list):
    """Return all external shared channels from the input channel list"""

    results = []

    for i in channel_list:
        if 'is_ext_shared' in i.keys() and i['is_ext_shared']:
            results.append(i)

    return results


def find_keys(token):
    """Look for private keys in public channels by first searching for common terms for private keys
    then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel-name', 'posted_by', 'content', 'link']

    for query in PRIVATE_KEYS:
        message_list = search_messages(token, query)
        results = []
        for message in message_list:
            r = re.compile(PRIVATE_KEYS_REGEX)
            if r.search(str(message)):
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['attachments'][0]['fallback'],
                                message['permalink']])
        if results:
            write_csv(headers,
                      '/Users/andrew/Desktop/private_keys_{}'.format(query).replace(' ', '_'),
                      results)


def find_certificates(token):
    """Look for certificate files in public channels by first searching for certificate file extensions
    these are then filtered down further to include only true certificate files"""

    headers = ['timestamp', 'file_name', 'posted_by', 'preview', 'private_link']

    for query in CERTIFICATE_EXTENSIONS:
        message_list = search_files(token, query)
        results = []
        for message in message_list:
            if 'text' in message['filetype'] and query in message['name']:
                results.append([convert_timestamp(message['timestamp']),
                                message['name'],
                                message['username'],
                                message['preview'],
                                message['permalink']])
        if results:
            write_csv(headers,
                      '/Users/andrew/Desktop/certificates_{}'.format(query).replace(' ', '_'),
                      results)


def find_gcp_credentials(token):
    """Look for GCP credential files in public channels by first searching for certificate file extensions
    these are then filtered down further to include only true certificate files"""

    headers = ['timestamp', 'file_name', 'posted_by', 'preview', 'private_link']

    for query in CREDENTIAL_EXTENSIONS:
        message_list = search_files(token, query)
        results = []
        for message in message_list:
            if 'javascript' in message['filetype'] and '"project_id"' in message['name']:
                results.append([convert_timestamp(message['timestamp']),
                                message['name'],
                                message['username'],
                                message['preview'],
                                message['permalink']])
        if results:
            write_csv(headers, '/Users/andrew/Desktop/gcp_credentials', results)


def find_aws_credentials(token):
    """Look for AWS credentials in public channels by first searching for common AWS key phrases
    these are then filtered down by regex"""

    headers = ['timestamp', 'channel-name', 'posted_by', 'content', 'link']

    for query in AWS_KEYS_QUERIES:
        message_list = search_messages(token, query)
        results = []
        for message in message_list:
            r = re.compile(AWS_KEYS_REGEX)
            if r.search(str(message)):
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            write_csv(headers,
                      '/Users/andrew/Desktop/aws_credentials{}'.format(query).replace(' ', '_'),
                      results)


def find_passwords(token):
    """Look for passwords in public channels by first searching for common terms for private keys
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel-name', 'posted_by', 'content', 'link']

    for query in PASSWORD_QUERIES:
        message_list = search_messages(token, query)
        results = []
        for message in message_list:
            r = re.compile(PASSWORD_REGEX)
            if r.search(str(message)):
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            write_csv(headers,
                      '/Users/andrew/Desktop/potential_leaked_passwords_{}'.format(query).replace(' ', '_').replace(':',
                                                                                                                    ''),
                      results)


def find_card_details(token):
    """Look for passwords in public channels by first searching for common terms for private keys
        then trimming this list down using a regex search"""

    headers = ['timestamp', 'channel-name', 'posted_by', 'content', 'link']

    for query in BANK_CARD_QUERIES:
        message_list = search_messages(token, query)
        results = []
        for message in message_list:
            r = re.compile(BANK_CARD_REGEX)
            if r.search(str(message)):
                results.append([convert_timestamp(message['ts']),
                                message['channel']['name'],
                                message['username'],
                                message['text'],
                                message['permalink']])
        if results:
            write_csv(headers,
                      '/Users/andrew/Desktop/potential_leaked_bank_cards_{}'.format(query).replace(' ', '_').replace(
                          ':', ''),
                      results)


def main():
    token = get_token()

    # user_list = get_users(token)
    # channel_list = get_channels(token)

    # find_keys(token)
    # find_passwords(token)
    # find_card_details(token)
    # find_certificates(token)
    # find_gcp_credentials(token)
    find_aws_credentials(token)

    # file_list = search_files(token, '.json')
    # for i in file_list:
    #     print(i)
    # message_list = search_messages(token, '4917*')
    #
    # for i in message_list:
    #     print(i)

    # for i in channel_list:
    #     print(i)

    # admins = get_admins(user_list)
    # for i in admins:
    #     print(str(i['real_name']) + ' - ' + str(i['id']) + ' - ' + str(i['profile']['email']))
    #
    # for i in get_external_shared(channel_list):
    #     if month_old(i['created']):
    #         print(i)

    # for item in user_list:
    #     print(item)

    # write_output('/Users/andrew/slack-hunter/results.txt', message_list)
    # write_output('/Users/andrew/slack-monitor/channels.txt', channel_list)


if __name__ == '__main__':
    main()
