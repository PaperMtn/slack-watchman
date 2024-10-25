import datetime
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True, slots=True)
class TestCases:
    match_cases: List[str]
    fail_cases: List[str]

    def __post_init__(self):
        if self.match_cases and not isinstance(self.match_cases, list):
            raise TypeError(f'Expected `match_cases` to be of type list, received {type(self.match_cases).__name__}')
        if self.fail_cases and not isinstance(self.fail_cases, list):
            raise TypeError(f'Expected `fail_cases` to be of type list, received {type(self.fail_cases).__name__}')


@dataclass(frozen=True, slots=True)
class Signature:
    """ Class that handles loaded signature objects. Signatures
    define what to search for in Slack and where to search for it.
    They also contain regex patterns to validate data that is found"""

    name: str
    status: str
    author: str
    date: str | datetime.date | datetime.datetime
    version: str
    description: str
    severity: int or str
    watchman_apps: Dict[str, Any]
    category: str
    scope: List[str]
    file_types: List[str]
    test_cases: TestCases
    search_strings: List[str]
    patterns: List[str]

    def __post_init__(self):
        if self.name and not isinstance(self.name, str):
            raise TypeError(f'Expected `name` to be of type str, received {type(self.name).__name__}')
        if self.status and not isinstance(self.status, str):
            raise TypeError(f'Expected `status` to be of type str, received {type(self.status).__name__}')
        if self.author and not isinstance(self.author, str):
            raise TypeError(f'Expected `author` to be of type str, received {type(self.author).__name__}')
        if self.date and not (isinstance(self.date, datetime.date)
                              or isinstance(self.date, str)
                              or isinstance(self.date, datetime.datetime)):
            raise TypeError(f'Expected `date` to be of type str, received {type(self.date).__name__}')
        if self.version and not isinstance(self.version, str):
            raise TypeError(f'Expected `version` to be of type str, received {type(self.version).__name__}')
        if self.description and not isinstance(self.description, str):
            raise TypeError(f'Expected `description` to be of type str, received {type(self.description).__name__}')
        if self.severity and not (isinstance(self.severity, int) or isinstance(self.severity, str)):
            raise TypeError(f'Expected `severity` to be of type int or str, received {type(self.severity).__name__}')
        if self.watchman_apps and not isinstance(self.watchman_apps, dict):
            raise TypeError(
                f'Expected `watchman_apps` to be of type dict, received {type(self.watchman_apps).__name__}')
        if self.category and not isinstance(self.category, str):
            raise TypeError(f'Expected `category` to be of type str, received {type(self.category).__name__}')
        if self.scope and not isinstance(self.scope, list):
            raise TypeError(f'Expected `scope` to be of type list, received {type(self.scope).__name__}')
        if self.file_types and not isinstance(self.file_types, list):
            raise TypeError(f'Expected `file_types` to be of type list, received {type(self.file_types).__name__}')
        if self.test_cases and not isinstance(self.test_cases, TestCases):
            raise TypeError(f'Expected `test_cases` to be of type TestCases, received {type(self.test_cases).__name__}')
        if self.search_strings and not isinstance(self.search_strings, list):
            raise TypeError(
                f'Expected `search_strings` to be of type list, received {type(self.search_strings).__name__}')
        if self.patterns and not isinstance(self.patterns, list):
            raise TypeError(f'Expected `patterns` to be of type list, received {type(self.patterns).__name__}')


def create_from_dict(signature_dict: Dict[str, Any]) -> Signature:
    """ Create a Signature object from a dictionary

    Args:
        signature_dict: dict/JSON object signature
    Returns:
        Signature
    """

    return Signature(
        name=signature_dict.get('name'),
        status=signature_dict.get('status'),
        author=signature_dict.get('author'),
        date=signature_dict.get('date'),
        version=signature_dict.get('version'),
        description=signature_dict.get('description'),
        severity=signature_dict.get('severity'),
        watchman_apps=signature_dict.get('watchman_apps'),
        category=signature_dict.get('watchman_apps', {}).get('slack_std', {}).get('category'),
        scope=signature_dict.get('watchman_apps', {}).get('slack_std', {}).get('scope'),
        file_types=signature_dict.get('watchman_apps', {}).get('slack_std', {}).get('file_types'),
        test_cases=TestCases(
            match_cases=signature_dict.get('test_cases', {}).get('match_cases'),
            fail_cases=signature_dict.get('test_cases', {}).get('fail_cases')
        ),
        search_strings=signature_dict.get('watchman_apps', {}).get('slack_std', {}).get('search_strings'),
        patterns=signature_dict.get('patterns'))
