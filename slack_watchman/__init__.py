import argparse
import builtins
import os
import time
import yaml
from colorama import init, deinit
from termcolor import colored
from pathlib import Path

from slack_watchman import config as cfg
from slack_watchman import __about__ as a
from slack_watchman import slack_wrapper as slack
from slack_watchman import logger as logger

RULES_PATH = (Path(__file__).parent / 'rules').resolve()
OUTPUT_LOGGER = ''
WORKSPACE_NAME = ''


def validate_conf(path):
    """Check the file slack_watchman.conf exists"""

    if isinstance(OUTPUT_LOGGER, logger.StdoutLogger):
        print = OUTPUT_LOGGER.log_info
    else:
        print = builtins.print

    if os.environ.get('SLACK_WATCHMAN_TOKEN'):
        return True
    if os.path.exists(path):
        with open(path) as yaml_file:
            return yaml.safe_load(yaml_file).get('slack_watchman')
    if os.path.exists('{}/slack_watchman.conf'.format(os.path.expanduser('~'))):
        print('Legacy slack_watchman.conf file detected. Renaming to slack_watchman.conf')
        os.rename(r'{}/slack_watchman.conf'.format(os.path.expanduser('~')),
                  r'{}/watchman.conf'.format(os.path.expanduser('~')))
        with open(path) as yaml_file:
            return yaml.safe_load(yaml_file).get('slack_watchman')


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
        if file.name.endswith('.yaml') or file.name.endswith('.yml'):
            with open(file) as yaml_file:
                rule = yaml.safe_load(yaml_file)
                if rule.get('enabled'):
                    rules.append(rule)

    return rules


def log(results_output, scope, rule=None):
    if isinstance(OUTPUT_LOGGER, logger.StdoutLogger):
        print = OUTPUT_LOGGER.log_info
    else:
        print = builtins.print

    if isinstance(OUTPUT_LOGGER, logger.CSVLogger):
        if rule:
            OUTPUT_LOGGER.write_csv('exposed_{}'.format(rule.get('filename').split('.')[0]),
                                    scope,
                                    results_output)
        else:
            OUTPUT_LOGGER.write_csv('all', scope, results_output)
    else:
        if rule:
            for log_data in results_output:
                OUTPUT_LOGGER.log_notification(log_data, WORKSPACE_NAME, scope, rule.get('meta').get('name'),
                                               rule.get('meta').get('severity'))
            print('Results output to log')
        else:
            for log_data in results_output:
                OUTPUT_LOGGER.log_notification(log_data, WORKSPACE_NAME, scope, scope, 0)
            print('Results output to log')


def search(slack_conn, rule, tf, scope):
    if isinstance(OUTPUT_LOGGER, logger.StdoutLogger):
        print = OUTPUT_LOGGER.log_info
    else:
        print = builtins.print

    if scope == 'messages':
        print(colored(
            'Searching for {} containing {}'.format('posts', rule.get('meta').get('name')),
            'yellow'))
        messages = slack.find_messages(slack_conn, OUTPUT_LOGGER, rule, tf)
        if messages:
            log(messages, scope, rule=rule)
    if scope == 'files':
        print(colored('Searching for {}'.format(rule.get('meta').get('name')), 'yellow'))
        files = slack.find_files(slack_conn, OUTPUT_LOGGER, rule, tf)
        if files:
            log(files, scope, rule=rule)


def main():
    global OUTPUT_LOGGER, WORKSPACE_NAME
    try:
        init()

        parser = argparse.ArgumentParser(description=a.__summary__)

        required = parser.add_argument_group('required arguments')
        required.add_argument('--timeframe', choices=['d', 'w', 'm', 'a'], dest='time',
                              help='How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time',
                              required=True)
        parser.add_argument('--output', choices=['csv', 'file', 'stdout', 'stream'], dest='logging_type',
                              help='Where to send results')
        parser.add_argument('--version', action='version',
                            version='slack-watchman {}'.format(a.__version__))
        parser.add_argument('--all', dest='everything', action='store_true',
                            help='Find everything')
        parser.add_argument('--users', dest='users', action='store_true',
                            help='Find all users')
        parser.add_argument('--channels', dest='channels', action='store_true',
                            help='Find all channels')
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
        parser.add_argument('--custom', dest='custom', action='store_true',
                            help='Search for user defined custom search queries that you have created rules for')

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
        logging_type = args.logging_type

        if tm == 'd':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - cfg.DAY_TIMEFRAME))
        elif tm == 'w':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - cfg.WEEK_TIMEFRAME))
        elif tm == 'm':
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - cfg.MONTH_TIMEFRAME))
        else:
            now = int(time.time())
            tf = time.strftime('%Y-%m-%d', time.localtime(now - cfg.ALL_TIME))

        conf_path = '{}/watchman.conf'.format(os.path.expanduser('~'))
        if not validate_conf(conf_path):
            raise Exception(colored('SLACK_WATCHMAN_TOKEN environment variable or slack_watchman.conf file not detected. '
                                    '\nEnsure environment variable is set or a valid file is located in your home '
                                    'directory: {} ', 'red')
                            .format(os.path.expanduser('~')))
        else:
            config = validate_conf(conf_path)
            slack_con = slack.initiate_slack_connection()
            slack_con.validate_token()
            WORKSPACE_NAME = slack_con.get_workspace_name()

        print = builtins.print
        if logging_type:
            if logging_type == 'file':
                if os.environ.get('SLACK_WATCHMAN_LOG_PATH'):
                    OUTPUT_LOGGER = logger.FileLogger(os.environ.get('SLACK_WATCHMAN_LOG_PATH'))
                elif config.get('logging').get('file_logging').get('path') and \
                        os.path.exists(config.get('logging').get('file_logging').get('path')):
                    OUTPUT_LOGGER = logger.FileLogger(log_path=config.get('logging').get('file_logging').get('path'))
                else:
                    print('No config given, outputting slack_watchman.log file to home path')
                    OUTPUT_LOGGER = logger.FileLogger(log_path=os.path.expanduser('~'))
            elif logging_type == 'stdout':
                OUTPUT_LOGGER = logger.StdoutLogger()
            elif logging_type == 'stream':
                if os.environ.get('SLACK_WATCHMAN_HOST') and os.environ.get('SLACK_WATCHMAN_PORT'):
                    OUTPUT_LOGGER = logger.SocketJSONLogger(os.environ.get('SLACK_WATCHMAN_HOST'),
                                                            os.environ.get('SLACK_WATCHMAN_PORT'))
                elif config.get('logging').get('json_tcp').get('host') and \
                        config.get('logging').get('json_tcp').get('port'):
                    OUTPUT_LOGGER = logger.SocketJSONLogger(config.get('logging').get('json_tcp').get('host'),
                                                            config.get('logging').get('json_tcp').get('port'))
                else:
                    raise Exception("JSON TCP stream selected with no config")
            else:
                OUTPUT_LOGGER = logger.CSVLogger()
        else:
            print('No logging option selected, defaulting to CSV')
            OUTPUT_LOGGER = logger.CSVLogger()

        if not isinstance(OUTPUT_LOGGER, logger.StdoutLogger):
            print = builtins.print
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
            print('Searching workspace: {}'.format(WORKSPACE_NAME))
            print('Workspace URL: {}\n'.format(slack_con.get_workspace_domain()))
            print('Importing rules...')
            rules_list = load_rules()
            print('{} rules loaded'.format(len(rules_list)))
        else:
            OUTPUT_LOGGER.log_info('Slack Watchman started execution')
            OUTPUT_LOGGER.log_info('Searching workspace: {}'.format(WORKSPACE_NAME))
            OUTPUT_LOGGER.log_info('Workspace URL: {}'.format(slack_con.get_workspace_domain()))
            OUTPUT_LOGGER.log_info('Importing rules...')
            rules_list = load_rules()
            OUTPUT_LOGGER.log_info('{} rules loaded'.format(len(rules_list)))
            print = OUTPUT_LOGGER.log_info

        if everything:
            print('Getting everything...')
            print(colored('Getting users', 'yellow'))
            user_list = slack.get_users(slack.initiate_slack_connection())
            print(colored('Getting channels', 'yellow'))
            channel_list = slack.get_channels(slack.initiate_slack_connection())
            print(colored('Outputting all channels', 'yellow'))
            all_channels = slack.get_all_channels(OUTPUT_LOGGER, channel_list, tf)
            if all_channels:
                log(all_channels, 'channels')
            print(colored('Outputting all users', 'yellow'))
            all_users = slack.get_all_users(OUTPUT_LOGGER, user_list)
            if all_users:
                log(all_users, 'users')
            print(colored('Searching tokens', 'yellow'))
            for rule in rules_list:
                if 'tokens' in rule.get('category'):
                    for scope in rule.get('scope'):
                        search(slack.initiate_slack_connection(), rule, tf, scope)
            print(colored('Searching financial data', 'yellow'))
            for rule in rules_list:
                if 'financial' in rule.get('category'):
                    for scope in rule.get('scope'):
                        search(slack.initiate_slack_connection(), rule, tf, scope)
            print(colored('Searching files', 'yellow'))
            for rule in rules_list:
                if 'files' in rule.get('category'):
                    for scope in rule.get('scope'):
                        search(slack_con, rule, tf, scope)
            print(colored('Searching PII/Personal Data', 'yellow'))
            for rule in rules_list:
                if 'pii' in rule.get('category'):
                    for scope in rule.get('scope'):
                        search(slack_con, rule, tf, scope)
            print(colored('Searching custom strings', 'yellow'))
            for rule in rules_list:
                if 'custom' in rule.get('category'):
                    for scope in rule.get('scope'):
                        search(slack_con, rule, tf, scope)
        else:
            if users:
                print(colored('Getting users', 'yellow'))
                user_list = slack.get_users(slack_con)
                print(colored('Outputting all users', 'yellow'))
                all_users = slack.get_all_users(OUTPUT_LOGGER, user_list)
                if all_users:
                    log(all_users, 'users')
            if channels:
                print(colored('Getting channels', 'yellow'))
                channel_list = slack.get_channels(slack_con)
                print(colored('Outputting all channels', 'yellow'))
                all_channels = slack.get_all_channels(OUTPUT_LOGGER, channel_list, tf)
                if all_channels:
                    log(all_channels, 'channels')
            if tokens:
                print(colored('Searching tokens', 'yellow'))
                for rule in rules_list:
                    if 'tokens' in rule.get('category'):
                        for scope in rule.get('scope'):
                            search(slack_con, rule, tf, scope)
            if financial:
                print(colored('Searching financial data', 'yellow'))
                for rule in rules_list:
                    if 'financial' in rule.get('category'):
                        for scope in rule.get('scope'):
                            search(slack_con, rule, tf, scope)
            if files:
                print(colored('Searching files', 'yellow'))
                for rule in rules_list:
                    if 'files' in rule.get('category'):
                        for scope in rule.get('scope'):
                            search(slack_con, rule, tf, scope)
            if pii:
                print(colored('Searching PII/Personal Data', 'yellow'))
                for rule in rules_list:
                    if 'pii' in rule.get('category'):
                        for scope in rule.get('scope'):
                            search(slack_con, rule, tf, scope)
            if custom:
                print(colored('Searching custom strings', 'yellow'))
                for rule in rules_list:
                    if 'custom' in rule.get('category'):
                        for scope in rule.get('scope'):
                            search(slack_con, rule, tf, scope)

        print(colored('++++++Audit completed++++++', 'green'))

        deinit()

    except Exception as e:
        if isinstance(OUTPUT_LOGGER, logger.StdoutLogger):
            print = OUTPUT_LOGGER.log_info
        else:
            print = builtins.print
        print(colored(e, 'red'))


if __name__ == '__main__':
    main()
