import time
from dataclasses import dataclass
from typing import Dict


def _convert_timestamp(timestamp: str or int) -> str or None:
    """ Converts epoch timestamp into human-readable time

    Args:
        timestamp: epoch timestamp in seconds
    Returns:
        String time in the format YYYY-mm-dd hh:mm:ss
    """

    if timestamp:
        if isinstance(timestamp, str):
            timestamp = timestamp.split('.', 1)[0]

        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))
    else:
        return None


@dataclass(slots=True)
class User(object):
    """ Class that defines User objects for Slack users"""

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
    tz_offset: str
    title: str
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    updated: int or float or str
    has_2fa: bool


@dataclass(slots=True)
class UserSuccinct(object):
    """ Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    display_name: str
    has_2fa: str
    is_admin: str


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
            title=user_dict.get('profile').get('title'),
            phone=user_dict.get('profile').get('phone'),
            skype=user_dict.get('profile').get('skype'),
            display_name=user_dict.get('profile').get('display_name'),
            email=user_dict.get('profile').get('email'),
            first_name=user_dict.get('profile').get('first_name'),
            last_name=user_dict.get('profile').get('last_name'),
            is_admin=user_dict.get('is_admin'),
            is_owner=user_dict.get('is_owner'),
            is_primary_owner=user_dict.get('is_primary_owner'),
            is_restricted=user_dict.get('is_restricted'),
            is_ultra_restricted=user_dict.get('is_ultra_restricted'),
            is_bot=user_dict.get('is_bot'),
            updated=_convert_timestamp(user_dict.get('updated')),
            has_2fa=user_dict.get('has_2fa')
        )
    else:
        return UserSuccinct(
            id=user_dict.get('id'),
            name=user_dict.get('name'),
            display_name=user_dict.get('profile').get('display_name'),
            has_2fa=user_dict.get('has_2fa'),
            is_admin=user_dict.get('is_admin'),
            email=user_dict.get('profile').get('email')
        )
