import argparse
import os
import requests
from colorama import init, deinit
from termcolor import colored

from watchman import audit
from watchman import definitions as d
from watchman import __about__ as a


def validate_conf(path):
    """Check the file slack_watchman.conf exists"""

    if os.environ.get('SLACK_WATCHMAN_TOKEN') or os.path.exists(path):
        return True


def validate_token():
    """Check that slack token is valid"""
    token = audit.get_token()

    r = requests.get('https://slack.com/api/users.list',
                     params={'token': token,
                             'pretty': 1,
                             'limit': 1,
                             'cursor': ''}).json()
    if not r['ok'] and r['error'] == 'invalid_auth':
        raise Exception('Invalid Slack API key')


def main():
    try:
        init()

        parser = argparse.ArgumentParser(description=a.__summary__)

        parser.add_argument('--timeframe', choices=['d', 'w', 'm', 'a'], dest='time',
                            help='How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time',
                            required=True)
        parser.add_argument('--version', action='version',
                            version='slack-watchman {}'.format(a.__version__))
        parser.add_argument('--all', dest='everything', action='store_true',
                            help='Find everything')
        parser.add_argument('-U', '--users', dest='users', action='store_true',
                            help='Find all users, including admins')
        parser.add_argument('-C', '--channels', dest='channels', action='store_true',
                            help='Find all channels, including external shared channels')
        parser.add_argument('-a', dest='aws', action='store_true',
                            help='Look for AWS keys')
        parser.add_argument('-g', dest='gcp', action='store_true',
                            help='Look for GCP keys')
        parser.add_argument('-G', dest='google', action='store_true',
                            help='Look for Google API keys')
        parser.add_argument('-s', dest='slack', action='store_true',
                            help='Look for Slack tokens')
        parser.add_argument('-p', dest='priv', action='store_true',
                            help='Look for private keys')
        parser.add_argument('-c', dest='card', action='store_true',
                            help='Look for card details')
        parser.add_argument('-t', dest='cert', action='store_true',
                            help='Look for certificate files')
        parser.add_argument('-f', dest='files', action='store_true',
                            help='Look for interesting files')
        parser.add_argument('-P', dest='passwords', action='store_true',
                            help='Look for passwords')

        args = parser.parse_args()
        time = args.time
        everything = args.everything
        users = args.users
        channels = args.channels
        aws = args.aws
        gcp = args.gcp
        google = args.google
        slack = args.slack
        priv = args.priv
        card = args.card
        cert = args.cert
        files = args.files
        passwords = args.passwords

        if time == 'd':
            tf = d.DAY_TIMEFRAME
        elif time == 'w':
            tf = d.WEEK_TIMEFRAME
        elif time == 'm':
            tf = d.MONTH_TIMEFRAME
        else:
            tf = d.ALL_TIME

        print(colored('''
      _            _      _  __        ___  _____ ____ _   _ __  __    _    _   _
  ___| | __ _  ___| | __ | | \ \      / / \|_   _/ ___| | | |  \/  |  / \  | \ | |
 / __| |/ _` |/ __| |/ / | |  \ \ /\ / / _ \ | || |   | |_| | |\/| | / _ \ |  \| |
 \__ \ | (_| | (__|   <  | |   \ V  V / ___ \| || |___|  _  | |  | |/ ___ \| |\  |
 |___/_|\__,_|\___|_|\_\ | |    \_/\_/_/   \_\_| \____|_| |_|_|  |_/_/   \_\_| \_|
                         |_|

                         ''', 'yellow'))

        conf_path = '{}/slack_watchman.conf'.format(os.path.expanduser('~'))

        if not validate_conf(conf_path):
            raise Exception(colored('SLACK_WATCHMAN_TOKEN envvar or slack_watchman.conf file not detected.'
                            '\nEnsure envvar is set or a valid file is located in your home directory: {}', 'red')
                            .format(os.path.expanduser('~')))
        else:
            validate_token(conf_path)

        if everything:
            print('You want everything? I like you...')
            print(colored('+++++++++++++++++++++', 'yellow'))
            print(colored('Getting users\n+++++++++++++++++++++', 'yellow'))
            user_list = audit.get_users()
            print(colored('Getting channels\n+++++++++++++++++++++', 'yellow'))
            channel_list = audit.get_channels()
            print(colored('Getting admin users\n+++++++++++++++++++++', 'yellow'))
            audit.get_admins(user_list)
            print(colored('Outputting all channels\n+++++++++++++++++++++', 'yellow'))
            audit.output_all_channels(channel_list, tf)
            print(colored('Outputting all users\n+++++++++++++++++++++', 'yellow'))
            audit.output_all_users(user_list)
            print(colored('Outputting all externally shared channels\n+++++++++++++++++++++', 'yellow'))
            audit.get_external_shared(channel_list, tf)
            print(colored('Getting AWS credentials\n+++++++++++++++++++++', 'yellow'))
            audit.find_aws_credentials(tf)
            print(colored('Getting GCP credentials\n+++++++++++++++++++++', 'yellow'))
            audit.find_gcp_credentials(tf)
            print(colored('Getting Google API keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_google_credentials(tf)
            print(colored('Getting private keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_keys(tf)
            print(colored('Getting bank card details\n+++++++++++++++++++++', 'yellow'))
            audit.find_card_details(tf)
            print(colored('Getting certificate files\n+++++++++++++++++++++', 'yellow'))
            audit.find_certificates(tf)
            print(colored('Getting Slack tokens\n+++++++++++++++++++++', 'yellow'))
            audit.find_slack_tokens(tf)
            print(colored('Finding passwords\n+++++++++++++++++++++', 'yellow'))
            audit.find_passwords(tf)
            print(colored('Finding interesting files\n+++++++++++++++++++++', 'yellow'))
            audit.find_malicious_files(tf)
        else:
            if users:
                print(colored('Getting users\n+++++++++++++++++++++', 'yellow'))
                user_list = audit.get_users()
                print(colored('Getting admin users\n+++++++++++++++++++++', 'yellow'))
                audit.get_admins(user_list)
                print(colored('Outputting all users\n+++++++++++++++++++++', 'yellow'))
                audit.output_all_users(user_list)
            if channels:
                print(colored('Getting channels\n+++++++++++++++++++++', 'yellow'))
                channel_list = audit.get_channels()
                print(colored('Outputting all channels\n+++++++++++++++++++++', 'yellow'))
                audit.output_all_channels(channel_list, tf)
                print(colored('Outputting all externally shared channels\n+++++++++++++++++++++', 'yellow'))
                audit.get_external_shared(channel_list, tf)
            if aws:
                print(colored('Getting AWS credentials\n+++++++++++++++++++++', 'yellow'))
                audit.find_aws_credentials(tf)
            if gcp:
                print(colored('Getting GCP credentials\n+++++++++++++++++++++', 'yellow'))
                audit.find_gcp_credentials(tf)
            if google:
                print(colored('Getting Google API keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_google_credentials(tf)
            if slack:
                print(colored('Getting Slack tokens\n+++++++++++++++++++++', 'yellow'))
                audit.find_slack_tokens(tf)
            if priv:
                print(colored('Getting private keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_keys(tf)
            if card:
                print(colored('Getting bank card details\n+++++++++++++++++++++', 'yellow'))
                audit.find_card_details(tf)
            if cert:
                print(colored('Getting certificate files\n+++++++++++++++++++++', 'yellow'))
                audit.find_certificates(tf)
            if files:
                print(colored('Finding interesting files\n+++++++++++++++++++++', 'yellow'))
                audit.find_malicious_files(tf)
            if passwords:
                print(colored('Finding passwords\n+++++++++++++++++++++', 'yellow'))
                audit.find_passwords(tf)

        print(colored('++++++Audit completed++++++', 'green'))

        deinit()

    except Exception as e:
        print(colored(e, 'red'))


if __name__ == '__main__':
    main()
