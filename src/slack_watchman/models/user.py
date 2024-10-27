from dataclasses import dataclass
from typing import Dict

from slack_watchman.utils import convert_timestamp


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
    tz_offset: str or int
    title: str
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    updated: int or float or str
    has_2fa: bool

    def __post_init__(self):
        if self.id and not isinstance(self.id, str):
            raise TypeError(f'Expected `id` to be of type str, received {type(self.name).__name__}')
        if self.name and not isinstance(self.name, str):
            raise TypeError(f'Expected `name` to be of type str, received {type(self.name).__name__}')
        if self.email and not isinstance(self.email, str):
            raise TypeError(f'Expected `email` to be of type str, received {type(self.name).__name__}')
        if self.deleted and not isinstance(self.deleted, bool):
            raise TypeError(f'Expected `deleted` to be of type bool, received {type(self.name).__name__}')
        if self.real_name and not isinstance(self.real_name, str):
            raise TypeError(f'Expected `real_name` to be of type str, received {type(self.name).__name__}')
        if self.first_name and not isinstance(self.first_name, str):
            raise TypeError(f'Expected `first_name` to be of type str, received {type(self.name).__name__}')
        if self.last_name and not isinstance(self.last_name, str):
            raise TypeError(f'Expected `last_name` to be of type str, received {type(self.name).__name__}')
        if self.phone and not isinstance(self.phone, str):
            raise TypeError(f'Expected `phone` to be of type str, received {type(self.name).__name__}')
        if self.skype and not isinstance(self.skype, str):
            raise TypeError(f'Expected `skype` to be of type str, received {type(self.name).__name__}')
        if self.display_name and not isinstance(self.display_name, str):
            raise TypeError(f'Expected `display_name` to be of type str, received {type(self.name).__name__}')
        if self.tz and not isinstance(self.tz, str):
            raise TypeError(f'Expected `tz` to be of type str, received {type(self.name).__name__}')
        if self.tz_label and not isinstance(self.tz_label, str):
            raise TypeError(f'Expected `tz_label` to be of type str, received {type(self.name).__name__}')
        if self.tz_offset and not (isinstance(self.tz_offset, str) or isinstance(self.tz_offset, int)):
            raise TypeError(f'Expected `tz_offset` to be of type str or int, received {type(self.name).__name__}')
        if self.title and not isinstance(self.title, str):
            raise TypeError(f'Expected `title` to be of type str, received {type(self.name).__name__}')
        if self.is_admin and not isinstance(self.is_admin, bool):
            raise TypeError(f'Expected `is_admin` to be of type bool, received {type(self.name).__name__}')
        if self.is_owner and not isinstance(self.is_owner, bool):
            raise TypeError(f'Expected `is_owner` to be of type bool, received {type(self.name).__name__}')
        if self.is_primary_owner and not isinstance(self.is_primary_owner, bool):
            raise TypeError(f'Expected `is_primary_owner` to be of type bool, received {type(self.name).__name__}')
        if self.is_restricted and not isinstance(self.is_restricted, bool):
            raise TypeError(f'Expected `is_restricted` to be of type bool, received {type(self.name).__name__}')
        if self.is_ultra_restricted and not isinstance(self.is_ultra_restricted, bool):
            raise TypeError(f'Expected `is_ultra_restricted` to be of type bool, received {type(self.name).__name__}')
        if self.is_bot and not isinstance(self.is_bot, bool):
            raise TypeError(f'Expected `is_bot` to be of type bool, received {type(self.name).__name__}')
        if self.updated and not (isinstance(self.updated, int) or
                                 isinstance(self.updated, float) or
                                 isinstance(self.updated, str)):
            raise TypeError(f'Expected `updated` to be of type int, float or str, received {type(self.name).__name__}')
        if self.has_2fa and not isinstance(self.has_2fa, bool):
            raise TypeError(f'Expected `has_2fa` to be of type bool, received {type(self.name).__name__}')


@dataclass(slots=True)
class UserSuccinct(object):
    """ Class that defines User objects for Slack users"""

    id: str
    name: str
    email: str
    display_name: str
    has_2fa: bool
    is_admin: str

    def __post_init__(self):
        if self.id and not isinstance(self.id, str):
            raise TypeError(f'Expected `id` to be of type str, received {type(self.name).__name__}')
        if self.name and not isinstance(self.name, str):
            raise TypeError(f'Expected `name` to be of type str, received {type(self.name).__name__}')
        if self.email and not isinstance(self.email, str):
            raise TypeError(f'Expected `email` to be of type str, received {type(self.name).__name__}')
        if self.display_name and not isinstance(self.display_name, str):
            raise TypeError(f'Expected `display_name` to be of type str, received {type(self.name).__name__}')
        if self.has_2fa and not isinstance(self.has_2fa, bool):
            raise TypeError(f'Expected `has_2fa` to be of type bool, received {type(self.name).__name__}')
        if self.is_admin and not isinstance(self.is_admin, bool):
            raise TypeError(f'Expected `is_admin` to be of type bool, received {type(self.name).__name__}')


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
