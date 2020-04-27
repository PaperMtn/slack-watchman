import requests
import time
import configparser


def get_token():
    conf = configparser.ConfigParser()
    conf.read('../config/keys.conf')
    token = conf.get('auth', 'slack_api_token')

    return token


def rate_limit_check(response):
    if not response['ok'] and response['error'] == 'ratelimited':
        print('Slack API rate limit reached')
        time.sleep(60)
        return True
    else:
        return False


def write_output(out_path, out_list):
    with open(out_path, 'w+') as f:
        for item in out_list:
            f.write(str(item) + '\n')


def get_users(token):
    cursor = ''
    results = []

    try:
        # while True:
        r = requests.get("https://slack.com/api/users.list",
                         params=dict(token=token, pretty=1, limit=1, cursor=cursor)).json()
        # if not rate_limit_check(r):
        #     break
        if str(r['ok']) == 'False':
            print('END: Unable to dump the user list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = "https://slack.com/api/users.list"
                params = dict(token=token, pretty=1, limit=200, cursor=cursor)
                r = requests.get(request_url, params=params).json()
                for value in r['members']:
                    cursor = r['response_metadata']['next_cursor']
                    if not value['deleted']:
                        results.append(value)
    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def get_channels(token):
    cursor = ''
    results = []

    try:
        r = requests.get("https://slack.com/api/conversations.list",
                         params=dict(token=token, pretty=1, limit=1, cursor=cursor)).json()

        if str(r['ok']) == 'False':
            print('END: Unable to dump the channel list. Slack error: ' + str(r['error']))
        else:
            cursor = r['response_metadata']['next_cursor']
            while str(r['ok']) == 'True' and cursor:
                request_url = "https://slack.com/api/conversations.list"
                params = dict(token=token, pretty=1, limit=200, cursor=cursor)
                r = requests.get(request_url, params=params).json()
                for value in r['channels']:
                    cursor = r['response_metadata']['next_cursor']
                    results.append(value)
    except requests.exceptions.RequestException as exception:
        print(exception)

    return results


def get_admins(user_list):
    results = []

    for i in user_list:
        if 'is_admin' in i.keys() and i['is_admin']:
            results.append(i)

    return results


def get_external_shared(channel_list):
    results = []

    for i in channel_list:
        if 'is_ext_shared' in i.keys() and i['is_ext_shared']:
            results.append(i)

    return results


def main():
    token = get_token()
    # user_list = get_users(token)
    channel_list = get_channels(token)

    # for i in channel_list:
    #     print(i)

    # admins = get_admins(user_list)
    # for i in admins:
    #     print(i['real_name'])

    for i in get_external_shared(channel_list):
        print(i)

    # for item in user_list:
    #     print(item)

    # write_output('/Users/andrew/slack-monitor/results.txt', user_list)
    # write_output('/Users/andrew/slack-monitor/channels.txt', channel_list)


if __name__ == '__main__':
    main()
