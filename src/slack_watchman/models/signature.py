import datetime
from dataclasses import dataclass
from typing import (
    List,
    Dict,
    Any,
    Union
)


@dataclass(frozen=True, slots=True)
class TestCases:
    """Class that handles loaded test cases objects. These
    are used to validate whether regex patterns are valid."""

    match_cases: List[str]
    fail_cases: List[str]

    def __post_init__(self):
        """Validate types of fields after initialisation."""
        expected_types = {
            'match_cases': list,
            'fail_cases': list,
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type.__name__}, '
                    f'received {type(value).__name__}')


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True, slots=True)
class Signature:
    """Class that handles loaded signature objects. Signatures
    define what to search for in Slack and where to search for it.
    They also contain regex patterns to validate data that is found."""

    name: str
    id: str
    status: str
    author: str
    date: Union[str, datetime.date, datetime.datetime]
    version: str
    description: str
    severity: Union[int, str]
    watchman_apps: Dict[str, Any]
    category: str
    scope: List[str]
    file_types: List[str]
    test_cases: TestCases
    search_strings: List[str]
    patterns: List[str]

    def __post_init__(self):
        """Validate types of fields after initialisation."""
        expected_types = {
            'name': str,
            'id': str,
            'status': str,
            'author': str,
            'date': (str, datetime.date, datetime.datetime),
            'version': str,
            'description': str,
            'severity': (int, str),
            'watchman_apps': dict,
            'category': str,
            'scope': list,
            'file_types': list,
            'test_cases': TestCases,
            'search_strings': list,
            'patterns': list,
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type}, '
                    f'received {type(value).__name__}')


def create_from_dict(signature_dict: Dict[str, Any]) -> Signature:
    """ Create a Signature object from a dictionary

    Args:
        signature_dict: dict/JSON object signature
    Returns:
        Signature
    """

    return Signature(
        name=signature_dict.get('name'),
        id=signature_dict.get('id'),
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
