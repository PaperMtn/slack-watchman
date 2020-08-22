import argparse
import os
import time
import yaml
from colorama import init, deinit
from termcolor import colored
from pathlib import Path

from watchman import audit
from watchman import definitions as d
from watchman import __about__ as a

RULES_PATH = (Path(__file__).parent / 'rules').resolve()


def validate_conf(path):
    """Check the file watchman.conf exists"""

    if os.environ.get('SLACK_WATCHMAN_TOKEN'):
        return True
    if os.path.exists(path):
        return True
    if os.path.exists('{}/slack_watchman.conf'.format(os.path.expanduser('~'))):
        print('Legacy slack_watchman.conf file detected. Renaming to watchman.conf')
        os.rename(r'{}/slack_watchman.conf'.format(os.path.expanduser('~')),
                  r'{}/watchman.conf'.format(os.path.expanduser('~')))
        return True


def import_custom_queries(custom_queries):
    """Import a .txt file containing user defined searches"""

    queries = []

    with open(custom_queries) as infile:
        for line in infile:
            queries.append(line.strip())

    return queries


def load_rules():
    rules = []
    for file in os.scandir(RULES_PATH):
        if file.name.endswith('.yaml'):
            with open(file) as yaml_file:
                rule = yaml.safe_load(yaml_file)
                if rule['enabled']:
                    rules.append(rule)

    return rules


def search(rule, tf, scope):
    if scope == 'messages':
        print(colored('Searching for {} containing {}\n+++++++++++++++++++++'.format('posts', rule['meta']['name']),
                      'yellow'))
        audit.find_messages(rule['strings'], rule['pattern'], 'exposed_{}'.format(rule['filename'].split('.')[0]),
                            tf)
    if scope == 'files':
        print(colored('Searching for {}\n+++++++++++++++++++++'.format(rule['meta']['name']),
                      'yellow'))
        audit.find_messages(rule['strings'], rule['pattern'], 'exposed_{}'.format(rule['filename'].split('.')[0]),
                            tf)


def main():
    try:
        init()

        parser = argparse.ArgumentParser(description=a.__summary__)

        required = parser.add_argument_group('required arguments')
        required.add_argument('--timeframe', choices=['d', 'w', 'm', 'a'], dest='time',
                              help='How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time',
                              required=True)
        parser.add_argument('--version', action='version',
                            version='slack-watchman {}'.format(a.__version__))
        parser.add_argument('--all', dest='everything', action='store_true',
                            help='Find everything')
        parser.add_argument('--users', dest='users', action='store_true',
                            help='Find all users, including admins')
        parser.add_argument('--channels', dest='channels', action='store_true',
                            help='Find all channels, including external shared channels')
        parser.add_argument('--pii', dest='pii', action='store_true',
                            help='Find personal data: Passwords, DOB, passport details, drivers licence, ITIN, SSN')
        parser.add_argument('--financial', dest='financial', action='store_true',
                            help='Find financial data: Card details, PayPal Braintree tokens, IBAN numbers,'
                                 ' CUSIP numbers')
        parser.add_argument('--tokens', dest='tokens', action='store_true',
                            help='Find tokens: Private keys, AWS, GCP, Google API, Slack, Slack webhooks,'
                                 ' Facebook, Twitter, GitHub')
        parser.add_argument('--files', dest='files', action='store_true',
                            help='Find files: Certificates, interesting/malicious files')
        parser.add_argument('--custom', dest='custom',
                            help='Search for user defined custom search queries. Provide path '
                                 'to .txt file containing one search per line')

        args = parser.parse_args()
        tm = args.time
        everything = args.everything
        users = args.users
        channels = args.channels
        pii = args.pii
        financial = args.financial
        tokens = args.tokens
        files = args.files
        custom = args.custom

        if tm == 'd':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - d.DAY_TIMEFRAME))
        elif tm == 'w':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - d.WEEK_TIMEFRAME))
        elif tm == 'm':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - d.MONTH_TIMEFRAME))
        else:
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - d.ALL_TIME))

        print(colored('''
  #####
 #     # #        ##    ####  #    #
 #       #       #  #  #    # #   #
  #####  #      #    # #      ####
       # #      ###### #      #  #
 #     # #      #    # #    # #   #
  #####  ###### #    #  ####  #    #

 #     #    #    #######  #####  #     # #     #    #    #     #
 #  #  #   # #      #    #     # #     # ##   ##   # #   ##    #
 #  #  #  #   #     #    #       #     # # # # #  #   #  # #   #
 #  #  # #     #    #    #       ####### #  #  # #     # #  #  #
 #  #  # #######    #    #       #     # #     # ####### #   # #
 #  #  # #     #    #    #     # #     # #     # #     # #    ##
  ## ##  #     #    #     #####  #     # #     # #     # #     #''', 'yellow'))
        print('Version: {}\n'.format(a.__version__))
        print('Searching workspace: {}'.format(audit.get_workspace_name()))
        print('Workspace URL: {}\n'.format(audit.get_workspace_domain()))
        print('Importing rules...')
        rules_list = load_rules()
        print('{} rules loaded'.format(len(rules_list)))
        conf_path = '{}/watchman.conf'.format(os.path.expanduser('~'))

        if not validate_conf(conf_path):
            raise Exception(colored('SLACK_WATCHMAN_TOKEN environment variable or watchman.conf file not detected. '
                                    '\nEnsure environment variable is set or a valid file is located in your home '
                                    'directory: {} ', 'red')
                            .format(os.path.expanduser('~')))
        else:
            audit.validate_token()

        if everything:
            print('Getting everything...')
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
            print(colored('Searching tokens', 'yellow'))
            print(colored('+++++++++++++++++++++', 'yellow'))
            for rule in rules_list:
                if 'tokens' in rule['category']:
                    for scope in rule['scope']:
                        search(rule, tf, scope)
            print(colored('Searching financial data', 'yellow'))
            print(colored('+++++++++++++++++++++', 'yellow'))
            for rule in rules_list:
                if 'financial' in rule['category']:
                    for scope in rule['scope']:
                        search(rule, tf, scope)
            print(colored('Searching files', 'yellow'))
            print(colored('+++++++++++++++++++++', 'yellow'))
            for rule in rules_list:
                if 'files' in rule['category']:
                    for scope in rule['scope']:
                        search(rule, tf, scope)
            print(colored('Searching PII/Personal Data', 'yellow'))
            print(colored('+++++++++++++++++++++', 'yellow'))
            for rule in rules_list:
                if 'pii' in rule['category']:
                    for scope in rule['scope']:
                        search(rule, tf, scope)
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
            if tokens:
                print(colored('Searching tokens', 'yellow'))
                print(colored('+++++++++++++++++++++', 'yellow'))
                for rule in rules_list:
                    if 'tokens' in rule['category']:
                        for scope in rule['scope']:
                            search(rule, tf, scope)
            if financial:
                print(colored('Searching financial data', 'yellow'))
                print(colored('+++++++++++++++++++++', 'yellow'))
                for rule in rules_list:
                    if 'financial' in rule['category']:
                        for scope in rule['scope']:
                            search(rule, tf, scope)
            if files:
                print(colored('Searching files', 'yellow'))
                print(colored('+++++++++++++++++++++', 'yellow'))
                for rule in rules_list:
                    if 'files' in rule['category']:
                        for scope in rule['scope']:
                            search(rule, tf, scope)
            if pii:
                print(colored('Searching PII/Personal Data', 'yellow'))
                print(colored('+++++++++++++++++++++', 'yellow'))
                for rule in rules_list:
                    if 'pii' in rule['category']:
                        for scope in rule['scope']:
                            search(rule, tf, scope)
        if custom:
            if os.path.exists(custom):
                queries = import_custom_queries(custom)
                print(colored('Searching for user input strings\n+++++++++++++++++++++', 'yellow'))
                audit.find_custom_queries(queries, tf)
            else:
                print(colored('Custom query file does not exist', 'red'))

        print(colored('++++++Audit completed++++++', 'green'))

        deinit()

    except Exception as e:
        print(colored(e, 'red'))


if __name__ == '__main__':
    main()
