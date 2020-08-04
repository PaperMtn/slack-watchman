import argparse
import os
import requests
import time
from colorama import init, deinit
from termcolor import colored

from watchman import audit
from watchman import definitions as d
from watchman import __about__ as a


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


def import_custom_queries(custom_queries):
    """Import a .txt file containing user defined searches"""

    queries = []

    with open(custom_queries) as infile:
        for line in infile:
            queries.append(line.strip())

    return queries


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
        print('Searching workspace: {}\n'.format(audit.get_workspace_domain()))

        conf_path = '{}/watchman.conf'.format(os.path.expanduser('~'))

        if not validate_conf(conf_path):
            raise Exception(colored('SLACK_WATCHMAN_TOKEN environment variable or watchman.conf file not detected. '
                                    '\nEnsure environment variable is set or a valid file is located in your home '
                                    'directory: {} ', 'red')
                            .format(os.path.expanduser('~')))
        else:
            validate_token()

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
            print(colored('Getting AWS credentials\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.AWS_KEYS_QUERIES, d.AWS_KEYS_REGEX, 'aws_credentials', tf)
            print(colored('Getting GCP credentials\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.GCP_CREDENTIAL_QUERIES, d.GCP_CREDENTIAL_REGEX, 'gcp_credentials', tf)
            print(colored('Getting Google API keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.GOOGLE_API_QUERIES, d.GOOGLE_API_REGEX, 'google_api_keys', tf)
            print(colored('Getting private keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.PRIVATE_KEYS_QUERIES, d.PRIVATE_KEYS_REGEX, 'private_keys', tf)
            print(colored('Getting bank card details\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.BANK_CARD_QUERIES, d.BANK_CARD_REGEX, 'leaked_bank_cards', tf)
            print(colored('Getting PayPal Braintree details\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.PAYPAL_QUERIES, d.PAYPAL_REGEX, 'leaked_paypal_details', tf)
            print(colored('Getting certificate files\n+++++++++++++++++++++', 'yellow'))
            audit.find_certificates(tf)
            print(colored('Getting Slack tokens\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.SLACK_KEY_QUERIES, d.SLACK_API_REGEX, 'slack_token', tf)
            print(colored('Getting Slack webhooks\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.SLACK_WEBHOOK_QUERIES, d.SLACK_WEBHOOK_REGEX, 'slack_webhooks', tf)
            print(colored('Getting Twitter keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.TWITTER_QUERIES, d.TWITTER_REGEX, 'twitter_tokens', tf)
            print(colored('Finding passwords\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.PASSWORD_QUERIES, d.PASSWORD_REGEX, 'leaked_passwords', tf)
            print(colored('Finding interesting files\n+++++++++++++++++++++', 'yellow'))
            audit.find_files(d.FILE_EXTENSIONS, 'interesting_files', tf)
            print(colored('Finding dates of birth\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.DOB_QUERIES, d.DOB_REGEX, 'dates_of_birth', tf)
            print(colored('Finding passport details\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.PASSPORT_QUERIES, d.PASSPORT_REGEX, 'passport_numbers', tf)
            print(colored('Getting Facebook access tokens\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.FACEBOOK_QUERIES, d.FACEBOOK_ACCESS_TOKEN_REGEX, 'facebook_tokens', tf)
            print(colored('Getting Facebook secret keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.FACEBOOK_QUERIES, d.FACEBOOK_SECRET_REGEX, 'facebook_keys', tf)
            print(colored('Getting GitHub API keys\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.GITHUB_QUERIES, d.GITHUB_REGEX, 'github_tokens', tf)
            print(colored('Finding national insurance numbers\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.NI_NUMBER_QUERIES, d.NI_NUMBER_REGEX, 'leaked_ni_numbers', tf)
            print(colored('Finding US social security numbers\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.SSN_US_QUERIES, d.SSN_US_REGEX, 'leaked_us_ssn', tf)
            print(colored('Getting IBAN numbers\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.IBAN_QUERIES, d.IBAN_REGEX, 'leaked_iban_numbers', tf)
            print(colored('Getting CUSIP numbers\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.CUSIP_QUERIES, d.CUSIP_REGEX, 'leaked_cusip_numbers', tf)
            print(colored('Finding UK drivers licence numbers\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.DRIVERS_LICENCE_UK_QUERIES, d.DRIVERS_LICENCE_UK_REGEX,
                                'leaked_uk_drivers_licence_numbers', tf)
            print(colored('Finding individual taxpayer identification number\n+++++++++++++++++++++', 'yellow'))
            audit.find_messages(d.ITIN_QUERIES, d.ITIN_REGEX, 'leaked_itin_numbers', tf)
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
                print(colored('Getting bearer tokens\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.BEARER_TOKEN_QUERIES, d.BEARER_TOKEN_REGEX, 'bearer_tokens', tf)
                print(colored('Getting AWS credentials\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.AWS_KEYS_QUERIES, d.AWS_KEYS_REGEX, 'aws_credentials', tf)
                print(colored('Getting GCP credentials\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.GCP_CREDENTIAL_QUERIES, d.GCP_CREDENTIAL_REGEX, 'gcp_credentials', tf)
                print(colored('Getting Google API keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.GOOGLE_API_QUERIES, d.GOOGLE_API_REGEX, 'google_api_keys', tf)
                print(colored('Getting Slack tokens\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.SLACK_KEY_QUERIES, d.SLACK_API_REGEX, 'slack_token', tf)
                print(colored('Getting Slack webhooks\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.SLACK_WEBHOOK_QUERIES, d.SLACK_WEBHOOK_REGEX, 'slack_webhooks', tf)
                print(colored('Getting private keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.PRIVATE_KEYS_QUERIES, d.PRIVATE_KEYS_REGEX, 'private_keys', tf)
                print(colored('Getting Twitter keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.TWITTER_QUERIES, d.TWITTER_REGEX, 'twitter_tokens', tf)
                print(colored('Getting Facebook access tokens\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.FACEBOOK_QUERIES, d.FACEBOOK_ACCESS_TOKEN_REGEX, 'facebook_tokens', tf)
                print(colored('Getting Facebook secret keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.FACEBOOK_QUERIES, d.FACEBOOK_SECRET_REGEX, 'facebook_keys', tf)
                print(colored('Getting GitHub API keys\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.GITHUB_QUERIES, d.GITHUB_REGEX, 'github_tokens', tf)
            if financial:
                print(colored('Getting CUSIP numbers\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.CUSIP_QUERIES, d.CUSIP_REGEX, 'leaked_cusip_numbers', tf)
                print(colored('Getting IBAN numbers\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.IBAN_QUERIES, d.IBAN_REGEX, 'leaked_iban_numbers', tf)
                print(colored('Getting bank card details\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.BANK_CARD_QUERIES, d.BANK_CARD_REGEX, 'leaked_bank_cards', tf)
                print(colored('Getting PayPal Braintree details\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.PAYPAL_QUERIES, d.PAYPAL_REGEX, 'leaked_paypal_details', tf)
            if files:
                print(colored('Getting certificate files\n+++++++++++++++++++++', 'yellow'))
                audit.find_certificates(tf)
                print(colored('Finding interesting files\n+++++++++++++++++++++', 'yellow'))
                audit.find_files(d.FILE_EXTENSIONS, 'interesting_files', tf)
            if pii:
                print(colored('Finding individual taxpayer identification number\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.ITIN_QUERIES, d.ITIN_REGEX, 'leaked_itin_numbers', tf)
                print(colored('Finding UK drivers licence numbers\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.DRIVERS_LICENCE_UK_QUERIES, d.DRIVERS_LICENCE_UK_REGEX,
                                    'leaked_uk_drivers_licence_numbers', tf)
                print(colored('Finding national insurance numbers\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.NI_NUMBER_QUERIES, d.NI_NUMBER_REGEX, 'leaked_ni_numbers', tf)
                print(colored('Finding US social security numbers\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.SSN_US_QUERIES, d.SSN_US_REGEX, 'leaked_us_ssn', tf)
                print(colored('Finding dates of birth\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.DOB_QUERIES, d.DOB_REGEX, 'dates_of_birth', tf)
                print(colored('Finding passport details\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.PASSPORT_QUERIES, d.PASSPORT_REGEX, 'passport_numbers', tf)
                print(colored('Finding passwords\n+++++++++++++++++++++', 'yellow'))
                audit.find_messages(d.PASSWORD_QUERIES, d.PASSWORD_REGEX, 'leaked_passwords', tf)
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
