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
from typing import Any, Dict, List, ClassVar, Protocol

from colorama import Fore, Back, Style, init

from slack_watchman.utils import EnhancedJSONEncoder

_TYPE_COLORER = re.compile(r'([A-Z]{3,})', re.VERBOSE)
_HEADER_WORDS = re.compile(r'([A-Z_0-9]{2,}:)\s', re.VERBOSE)

# msg_level -> (color, style, symbol). symbol=None leaves msg_level untouched.
_LEVEL_STYLES: Dict[str, tuple] = {
    'NOTIFY': (Fore.CYAN, Style.NORMAL, None),
    'INFO': (Fore.WHITE, Style.DIM, '-'),
    'WORKSPACE': (Fore.LIGHTBLUE_EX, Style.NORMAL, '+'),
    'WORKSPACE_AUTH': (Fore.LIGHTGREEN_EX, Style.NORMAL, '!'),
    'WORKSPACE_PROBE': (Fore.LIGHTGREEN_EX, Style.NORMAL, '!'),
    'USER': (Fore.RED, Style.NORMAL, '+'),
    'CANVAS': (Fore.LIGHTMAGENTA_EX, Style.NORMAL, '+'),
    'WARNING': (Fore.YELLOW, Style.NORMAL, '!'),
    'SUCCESS': (Fore.LIGHTGREEN_EX, Style.NORMAL, '>>'),
    'DEBUG': (Fore.WHITE, Style.DIM, '#'),
    'ERROR': (Fore.MAGENTA, Style.NORMAL, None),
    'CRITICAL': (Fore.RED, Style.NORMAL, None),
    'RESULT': (Fore.LIGHTGREEN_EX, Style.NORMAL, '!'),
}
_DEFAULT_LEVEL_STYLE = (Fore.WHITE, Style.NORMAL, None)


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
        elif notify_type == "workspace_auth":
            message = f'WORKSPACE_AUTH: \n' \
                      f'    APPROVED_DOMAINS: {message.get("formatted_email_domains")}  \n' \
                      f'    OAUTH_PROVIDERS: {message.get("user_oauth")} \n' \
                      f'    STANDARD_AUTH: {message.get("standard_auth_enabled")} \n' \
                      f'    SSO_ENABLED: {message.get("sso_enabled")} \n' \
                      f'    TWO_FACTOR_REQUIRED: {message.get("two_factor_required")}'
            msg_level = 'WORKSPACE_AUTH'
        elif notify_type == "workspace_probe":
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
        elif notify_type == "user":
            message = f'USER: \n' \
                      f'    ID: {message.get("id")}  \n' \
                      f'    NAME: {message.get("display_name")}  \n' \
                      f'    EMAIL: {message.get("email")}  \n' \
                      f'    JOB_TITLE: {message.get("title")} \n' \
                      f'    ADMIN: {message.get("is_admin")} \n' \
                      f'    OWNER: {message.get("is_owner")} \n' \
                      f'    HAS_2FA: {message.get("has_2fa")}'
            msg_level = 'USER'
        elif notify_type == "canvas":
            message = f'CANVAS: \n' \
                      f'    CHANNEL: {message.get("channel_name")}  \n' \
                      f'    CANVAS_URL: {message.get("canvas_url")}'
            msg_level = 'CANVAS'
        elif notify_type == "result":
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
                file_user = message.get('user') or {}
                message = 'POST_TYPE: File' \
                          f'    POSTED_BY: {file_user.get("display_name")} ' \
                          f'- {file_user.get("email")}' \
                          f'    CREATED: {message.get("file").get("created")} \n' \
                          f'    FILE_NAME: {message.get("file").get("name")} \n' \
                          f'    PRIVATE_URL: {message.get("file").get("url_private_download")} \n' \
                          f'    PUBLIC_PERMALINK: {message.get("file").get("permalink_public")} \n' \
                          f'    -----'
            msg_level = 'RESULT'
        # Retrying log_to_stdout with the same arguments would fail the
        # same way every time, so log the failure once and drop the
        # message rather than spinning on a doomed retry (#92).
        try:
            self.log_to_stdout(message, msg_level)
        except Exception as e:
            print(f"slack_watchman: failed to log message ({msg_level}): {e}")

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
            color, style, symbol = _LEVEL_STYLES.get(msg_level, _DEFAULT_LEVEL_STYLE)
            if symbol is not None:
                msg_level = symbol

            # Make log level word/symbol coloured
            msg_level = _TYPE_COLORER.sub(color + r'\1' + color, msg_level.lower())
            # Make header words coloured
            message = _HEADER_WORDS.sub(color + Style.BRIGHT + r'\1 ' + Fore.WHITE + Style.NORMAL, str(message))
            sys.stdout.write(
                f"{reset_all}{style}[{color}{msg_level}{Fore.WHITE}]{style} {message}{Fore.WHITE}{Style.NORMAL}\n")
        except Exception:
            if self.debug:
                traceback.print_exc()
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


class JSONLogger:
    """ Custom logger class for JSON logging"""

    def __init__(self, name: str = 'Slack Watchman', **kwargs):
        self.name = name
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
        # logging.getLogger() returns a process-wide singleton, so guard
        # addHandler to avoid stacking duplicate handlers when JSONLogger
        # is instantiated more than once in the same process.
        if not self.logger.handlers:
            self.logger.addHandler(self.handler)
        else:
            self.handler = self.logger.handlers[0]
        if kwargs.get('debug'):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

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
        elif level.upper() == 'WORKSPACE_PROBE':
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
