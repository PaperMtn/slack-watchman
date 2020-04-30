import requests
import time
import configparser


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
        time.sleep(60)
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


def write_output(out_path, out_list):
    with open(out_path, 'w+') as f:
        for item in out_list:
            f.write(str(item) + '\n')


def get_users(token):
    """Return a list of all users in the instance"""

    cursor = ''
    results = []

    try:
        r = requests.get('https://slack.com/api/users.list',
                         params={'token': token, 'pretty': 1, 'limit': 1, 'cursor': cursor}).json()
        if str(r['ok']) == 'False':
            print('END: Unable to dump the user list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = 'https://slack.com/api/users.list'
                params = {'token': token, 'pretty': 1, 'limit': 200, 'cursor': cursor}
                r = requests.get(request_url, params=params).json()
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
        r = requests.get('https://slack.com/api/conversations.list',
                         params={'token': token, 'pretty': 1, 'limit': 1, 'cursor': cursor}).json()

        rate_limit_check(r)

        if str(r['ok']) == 'False':
            print('END: Unable to dump the channel list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = 'https://slack.com/api/conversations.list'
                params = {'token': token, 'pretty': 1, 'limit': 200, 'cursor': cursor}
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
        r = requests.get('https://slack.com/api/search.files',
                         params={'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100}).json()
        page_count_by_query[query] = (r['files']['pagination']['page_count'])
        print(page_count_by_query)

        for query, page_count in page_count_by_query.items():
            page = 1
            while page <= page_count:
                params = {'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100, 'page': str(page)}
                r = requests.get('https://slack.com/api/search.files',
                                 params=params).json()
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
        r = requests.get('https://slack.com/api/search.messages',
                         params={'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100}).json()
        page_count_by_query[query] = (r['messages']['pagination']['page_count'])
        print(page_count_by_query)

        for query, page_count in page_count_by_query.items():
            page = 1
            while page <= page_count:
                params = {'token': token, 'query': "\"{}\"".format(query), 'pretty': 1, 'count': 100, 'page': str(page)}
                r = requests.get('https://slack.com/api/search.messages',
                                 params=params).json()
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


def main():
    token = get_token()

    print(time.time())

    # user_list = get_users(token)
    channel_list = get_channels(token)
    # file_list = search_files(token, '.key')
    #
    # for i in file_list:
    #     print(i)
    #
    # message_list = search_messages(token, 's3:')
    #
    # for i in message_list:
    #     print(i)
    #
    # for i in channel_list:
    #     print(i)

    # admins = get_admins(user_list)
    # for i in admins:
    #     print(str(i['real_name']) + ' - ' + str(i['id']) + ' - ' + str(i['profile']['email']))
    #     # print(i)

    for i in get_external_shared(channel_list):
        if month_old(i['created']):
            print(i)
    #
    # for item in user_list:
    #     print(item)

    # write_output('/Users/andrew/slack-monitor/results.txt', user_list)
    # write_output('/Users/andrew/slack-monitor/channels.txt', channel_list)


if __name__ == '__main__':
    main()
