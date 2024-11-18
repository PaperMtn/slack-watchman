import csv
import dataclasses
import json
import logging
import logging.handlers
import os
import re
import sys
import traceback
from collections.abc import Mapping
from logging import Logger
from typing import Any, Dict, List, ClassVar, Protocol

from colorama import Fore, Back, Style, init

from slack_watchman.utils import EnhancedJSONEncoder


class StdoutLogger:
    """ Class for logging to stdout. """

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug')
        self.print_header()
        init()

    # pylint: disable=too-many-branches
    def log(self,
            msg_level: str,
            message: Any,
            **kwargs) -> None:
        """ Log to stdout

        Args:
            msg_level: Level message to log
            message: Message data to log
        """

        notify_type = kwargs.get('notify_type')

        if not self.debug and msg_level == 'DEBUG':
            return

        if dataclasses.is_dataclass(message):
            message = dataclasses.asdict(message)

        if notify_type == "workspace":
            message = f'WORKSPACE: \n' \
                      f'    ID: {message.get("id")}  \n' \
                      f'    NAME: {message.get("name")}  \n' \
                      f'    DOMAIN: {message.get("domain")}  \n' \
                      f'    URL: {message.get("url")}'
            msg_level = 'WORKSPACE'
        if notify_type == "workspace_auth":
            message = f'WORKSPACE_AUTH: \n' \
                      f'    APPROVED_DOMAINS: {message.get("formatted_email_domains")}  \n' \
                      f'    OAUTH_PROVIDERS: {message.get("user_oauth")} \n' \
                      f'    STANDARD_AUTH: {message.get("standard_auth_enabled")} \n' \
                      f'    SSO_ENABLED: {message.get("sso_enabled")} \n' \
                      f'    TWO_FACTOR_REQUIRED: {message.get("two_factor_required")}'
            msg_level = 'WORKSPACE_AUTH'
        if notify_type == "workspace_probe":
            message = f'WORKSPACE_PROBE_INFORMATION: \n' \
                      f'    TEAM_NAME: {message.get("team_name")}  \n' \
                      f'    TEAM_ID: {message.get("team_id")}  \n' \
                      f'    PAID_TEAM: {message.get("paid_team")}  \n' \
                      f'    APPROVED_DOMAINS: {message.get("formatted_email_domains")}  \n' \
                      f'    JOIN_URL: {message.get("join_url")}  \n' \
                      f'    OAUTH_PROVIDERS: {message.get("user_oauth")} \n' \
                      f'    STANDARD_AUTH: {message.get("standard_auth_enabled")} \n' \
                      f'    SSO_ENABLED: {message.get("sso_enabled")} \n' \
                      f'    TWO_FACTOR_REQUIRED: {message.get("two_factor_required")}'
            msg_level = 'WORKSPACE_PROBE'
        if notify_type == "user":
            message = f'USER: \n' \
                      f'    ID: {message.get("id")}  \n' \
                      f'    NAME: {message.get("display_name")}  \n' \
                      f'    EMAIL: {message.get("email")}  \n' \
                      f'    JOB_TITLE: {message.get("title")} \n' \
                      f'    ADMIN: {message.get("is_admin")} \n' \
                      f'    OWNER: {message.get("is_owner")} \n' \
                      f'    HAS_2FA: {message.get("has_2fa")}'
            msg_level = 'USER'
        if notify_type == "canvas":
            message = f'CANVAS: \n' \
                      f'    CHANNEL: {message.get("channel_name")}  \n' \
                      f'    CANVAS_URL: {message.get("canvas_url")}'
            msg_level = 'USER'
        if notify_type == "result":
            if message.get('message'):
                if message.get('message').get('conversation').get('is_im'):
                    conversation_type = 'Direct Message'
                elif message.get('message').get('conversation').get('is_private'):
                    conversation_type = 'Private Channel'
                else:
                    conversation_type = 'Public Channel'

                if isinstance(message.get('message').get('user'), Mapping):
                    user = f"{message.get('message', {}).get('user', {}).get('display_name')} -" \
                           f" {message.get('message', {}).get('user', {}).get('email')}"
                else:
                    user = message.get('message').get('user')

                message = 'POST_TYPE: Message' \
                          f'    POSTED_ON: {message.get("message").get("created")} \n' \
                          f'    POSTED_BY: {user} \n' \
                          f'    CONVERSATION: {message.get("message").get("conversation").get("name")}' \
                          f'    CONVERSATION_TYPE: {conversation_type}\n' \
                          f'    URL: {message.get("message").get("permalink")} \n' \
                          f'    POTENTIAL_SECRET: {message.get("match_string")} \n' \
                          f'    -----'

            elif message.get('file'):
                message = 'POST_TYPE: File' \
                          f'    POSTED_BY: {message.get("user", {}).get("display_name")} ' \
                          f'- {message.get("user").get("email")}' \
                          f'    CREATED: {message.get("file").get("created")} \n' \
                          f'    FILE_NAME: {message.get("file").get("name")} \n' \
                          f'    PRIVATE_URL: {message.get("file").get("url_private_download")} \n' \
                          f'    PUBLIC_PERMALINK: {message.get("file").get("permalink_public")} \n' \
                          f'    -----'
            msg_level = 'RESULT'
        try:
            self.log_to_stdout(message, msg_level)
        except Exception as e:
            print(e)
            self.log_to_stdout(message, msg_level)

    # pylint: disable=too-many-statements
    def log_to_stdout(self,
                      message: Any,
                      msg_level: str) -> None:
        """ Log to stdout

        Args:
            msg_level: Level message to log
            message: Message data to log
        Returns:
            None
        """

        try:

            reset_all = Style.NORMAL + Fore.RESET + Back.RESET
            key_color = Fore.WHITE
            base_color = Fore.WHITE
            high_color = Fore.WHITE
            style = Style.NORMAL

            if msg_level == "NOTIFY":
                base_color = Fore.CYAN
                high_color = Fore.CYAN
                key_color = Fore.CYAN
                style = Style.NORMAL
            elif msg_level == 'INFO':
                base_color = Fore.WHITE
                high_color = Fore.WHITE
                key_color = Fore.WHITE
                style = Style.DIM
                msg_level = '-'
            elif msg_level == 'WORKSPACE':
                base_color = Fore.LIGHTBLUE_EX
                high_color = Fore.LIGHTBLUE_EX
                key_color = Fore.LIGHTBLUE_EX
                style = Style.NORMAL
                msg_level = '+'
            elif msg_level == 'WORKSPACE_AUTH':
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                msg_level = '!'
            elif msg_level == 'WORKSPACE_PROBE':
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                msg_level = '!'
            elif msg_level == 'USER':
                base_color = Fore.RED
                high_color = Fore.RED
                key_color = Fore.RED
                style = Style.NORMAL
                msg_level = '+'
            elif msg_level == 'WARNING':
                base_color = Fore.YELLOW
                high_color = Fore.YELLOW
                key_color = Fore.YELLOW
                style = Style.NORMAL
                msg_level = '!'
            elif msg_level == "SUCCESS":
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                msg_level = '>>'
            elif msg_level == "DEBUG":
                base_color = Fore.WHITE
                high_color = Fore.WHITE
                key_color = Fore.WHITE
                style = Style.DIM
                msg_level = '#'
            elif msg_level == "ERROR":
                base_color = Fore.MAGENTA
                high_color = Fore.MAGENTA
                key_color = Fore.MAGENTA
                style = Style.NORMAL
            elif msg_level == "CRITICAL":
                base_color = Fore.RED
                high_color = Fore.RED
                key_color = Fore.RED
                style = Style.NORMAL
            elif msg_level == "RESULT":
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                msg_level = '!'

            # Make log level word/symbol coloured
            type_colorer = re.compile(r'([A-Z]{3,})', re.VERBOSE)
            msg_level = type_colorer.sub(high_color + r'\1' + base_color, msg_level.lower())
            # Make header words coloured
            header_words = re.compile(r'([A-Z_0-9]{2,}:)\s', re.VERBOSE)
            message = header_words.sub(key_color + Style.BRIGHT + r'\1 ' + Fore.WHITE + Style.NORMAL, str(message))
            sys.stdout.write(
                f"{reset_all}{style}[{base_color}{msg_level}{Fore.WHITE}]{style} {message}{Fore.WHITE}{Style.NORMAL}\n")
        except Exception:
            if self.debug:
                traceback.print_exc()
                sys.exit(1)
            print('Formatting error')

    @staticmethod
    def print_header() -> None:
        """ Prints the header for the logger"""
        print(" ".ljust(79) + Style.BRIGHT)

        print(Fore.MAGENTA + Style.BRIGHT +
              """
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠾⠛⢉⣉⣉⣉⡉⠛⠷⣦⣄⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠋⣠⣴⣿⣿⣿⣿⣿⡿⣿⣶⣌⠹⣷⡀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠁⣴⣿⣿⣿⣿⣿⣿⣿⣿⣆⠉⠻⣧⠘⣷⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠈⠀⢹⡇⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⢸⣿⠛⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⢸⡇⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣷⠀⢿⡆⠈⠛⠻⠟⠛⠉⠀⠀⠀⠀⠀⠀⣾⠃⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣧⡀⠻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠃⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⠿⣦⣄⠀⠀⠀⠀⠀⠀⠀⣀⣴⠟⠁⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣦⠀⠀⠈⠉⠛⠓⠲⠶⠖⠚⠋⠉⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⣠⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀ ⠈⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        """ + Style.RESET_ALL
              )
        print('   Slack Watchman     ')
        print(Style.DIM + '   Slack enumeration and exposed secrets detection tool      ' + Style.RESET_ALL)
        print('  ')
        print(Style.BRIGHT + '   by PaperMtn - GNU General Public License')
        print(' '.ljust(79) + Fore.GREEN)


class JSONLogger(Logger):
    """ Custom logger class for JSON logging"""

    def __init__(self, name: str = 'Slack Watchman', **kwargs):
        super().__init__(name)
        self.notify_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "NOTIFY", "scope": "%(scope)s", "severity": '
            '"%(severity)s", "detection_type": "%(type)s", "detection_data": %(message)s}')
        self.info_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
        self.success_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "SUCCESS", "message": "%(message)s"}')
        self.user_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "USER", "message": %(message)s}')
        self.workspace_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "WORKSPACE", "message": %(message)s}')
        self.workspace_auth_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "WORKSPACE_AUTH", "message": %(message)s}')
        self.workspace_probe_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "WORKSPACE_PROBE", "message": %(message)s}')
        self.canvas_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "CANVAS", "message": %(message)s}')
        self.logger = logging.getLogger(self.name)
        self.handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.handler)
        if kwargs.get('debug'):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    # def bind(self):
    #     pass

    def log(self,
            level: str,
            msg: str or Dict,
            **kwargs):
        if level.upper() == 'NOTIFY':
            self.handler.setFormatter(self.notify_format)
            self.logger.info(
                json.dumps(
                    msg,
                    cls=EnhancedJSONEncoder),
                extra={
                    'scope': kwargs.get('scope', ''),
                    'type': kwargs.get('detect_type', ''),
                    'severity': kwargs.get('severity', '')})
        elif level.upper() == 'INFO':
            self.handler.setFormatter(self.info_format)
            self.logger.info(msg)
        elif level.upper() == 'DEBUG':
            self.handler.setFormatter(self.info_format)
            self.logger.debug(msg)
        elif level.upper() == 'USER':
            self.handler.setFormatter(self.user_format)
            self.logger.info(json.dumps(
                msg,
                cls=EnhancedJSONEncoder))
        elif level.upper() == 'CANVAS':
            self.handler.setFormatter(self.canvas_format)
            self.logger.info(json.dumps(
                msg,
                cls=EnhancedJSONEncoder))
        elif level.upper() == 'WORKSPACE':
            self.handler.setFormatter(self.workspace_format)
            self.logger.info(json.dumps(
                msg,
                cls=EnhancedJSONEncoder))
        elif level.upper() == 'WORKSPACE_AUTH':
            self.handler.setFormatter(self.workspace_auth_format)
            self.logger.info(json.dumps(
                msg,
                cls=EnhancedJSONEncoder))
        elif level.upper() == 'WORKSPACE_PROBE_INFORMATION':
            self.handler.setFormatter(self.workspace_probe_format)
            self.logger.info(json.dumps(
                msg,
                cls=EnhancedJSONEncoder))
        elif level.upper() == 'SUCCESS':
            self.handler.setFormatter(self.success_format)
            self.logger.info(msg)
        else:
            self.handler.setFormatter(self.info_format)
            self.logger.critical(msg)


# pylint: disable=missing-class-docstring
class IsDataclass(Protocol):
    __dataclass_fields__: ClassVar[Dict]


def export_csv(csv_name: str, export_data: List[IsDataclass]) -> None:
    """ Export the data passed in a dataclass to CSV file

    Args:
        csv_name: Name of the CSV file to create
        export_data: Dataclass object to create CSV from
    """
    try:
        headers = dataclasses.asdict(export_data[0]).keys()
        with open(f'{os.path.join(os.getcwd(), csv_name)}.csv', 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for item in export_data:
                writer.writerow(dataclasses.asdict(item))
        f.close()
    except Exception as e:
        print(e)


def init_logger(logging_type: str, debug: bool) -> JSONLogger | StdoutLogger:
    """ Create a logger object. Defaults to stdout if no option is given

    Args:
        logging_type: Type of logging to use
        debug: Whether to use debug level logging or not
    Returns:
        Logger object
    """

    if not logging_type or logging_type == 'stdout':
        return StdoutLogger(debug=debug)
    else:
        return JSONLogger(debug=debug)
