from dataclasses import dataclass
from typing import Union, Dict

from slack_watchman.utils import convert_timestamp


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class User:
    """Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    deleted: bool
    real_name: str
    first_name: str
    last_name: str
    phone: str
    skype: str
    display_name: str
    tz: str
    tz_label: str
    tz_offset: Union[str, int]
    title: str
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    updated: Union[int, float, str]
    has_2fa: bool

    def __post_init__(self):
        """Validates the types of fields after initialization."""

        expected_types = {
            'id': str,
            'name': str,
            'email': str,
            'deleted': bool,
            'real_name': str,
            'first_name': str,
            'last_name': str,
            'phone': str,
            'skype': str,
            'display_name': str,
            'tz': str,
            'tz_label': str,
            'tz_offset': (str, int),
            'title': str,
            'is_admin': bool,
            'is_owner': bool,
            'is_primary_owner': bool,
            'is_restricted': bool,
            'is_ultra_restricted': bool,
            'is_bot': bool,
            'updated': (int, float, str),
            'has_2fa': bool,
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type}, '
                    f'received {type(value).__name__}')


@dataclass(slots=True)
class UserSuccinct:
    """Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    display_name: str
    has_2fa: bool
    is_admin: bool

    def __post_init__(self):
        """Validate types of fields after initialization."""
        expected_types = {
            'id': str,
            'name': str,
            'email': str,
            'display_name': str,
            'has_2fa': bool,
            'is_admin': bool,
        }

        # Loop through attributes and validate types
        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type.__name__}, '
                    f'received {type(value).__name__}')


def create_from_dict(user_dict: Dict,
                     verbose: bool) -> User or UserSuccinct:
    """ Create a User object from a dict response from the Slack API

    Args:
        verbose: Whether to output a full User object, or use
            less verbose succinct class
        user_dict: dict/JSON format data from Slack API
    Returns:
        A new User object
    """

    if verbose:
        return User(
            id=user_dict.get('id'),
            name=user_dict.get('name'),
            deleted=user_dict.get('deleted'),
            real_name=user_dict.get('real_name'),
            tz=user_dict.get('tz'),
            tz_label=user_dict.get('tz_label'),
            tz_offset=user_dict.get('tz_offset'),
            title=user_dict.get('profile', {}).get('title'),
            phone=user_dict.get('profile', {}).get('phone'),
            skype=user_dict.get('profile', {}).get('skype'),
            display_name=user_dict.get('profile', {}).get('display_name'),
            email=user_dict.get('profile', {}).get('email'),
            first_name=user_dict.get('profile', {}).get('first_name'),
            last_name=user_dict.get('profile', {}).get('last_name'),
            is_admin=user_dict.get('is_admin'),
            is_owner=user_dict.get('is_owner'),
            is_primary_owner=user_dict.get('is_primary_owner'),
            is_restricted=user_dict.get('is_restricted'),
            is_ultra_restricted=user_dict.get('is_ultra_restricted'),
            is_bot=user_dict.get('is_bot'),
            updated=convert_timestamp(user_dict.get('updated')),
            has_2fa=user_dict.get('has_2fa')
        )
    else:
        return UserSuccinct(
            id=user_dict.get('id'),
            name=user_dict.get('name'),
            display_name=user_dict.get('profile', {}).get('display_name'),
            has_2fa=user_dict.get('has_2fa'),
            is_admin=user_dict.get('is_admin'),
            email=user_dict.get('profile', {}).get('email')
        )
