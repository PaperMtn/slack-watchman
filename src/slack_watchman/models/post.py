from dataclasses import dataclass
from typing import (
    List,
    Dict,
    Any,
    Union
)

from slack_watchman.models import conversation, user
from slack_watchman.utils import convert_timestamp


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class File:
    """Slack File object"""
    id: str
    created: Union[int, float, str]
    user: Union[user.User, user.UserSuccinct]
    name: str
    title: str
    mimetype: str
    filetype: str
    pretty_type: str
    editable: bool
    size: Union[int, float, str]
    mode: str
    is_public: bool
    public_url_shared: bool
    url_private: str
    url_private_download: str
    permalink: str
    permalink_public: str
    shares: Dict[Any, Any]

    def __post_init__(self):
        """Validate types of fields after initialisation."""
        expected_types = {
            'id': str,
            'created': (int, float, str),
            'user': (user.User, user.UserSuccinct),
            'name': str,
            'title': str,
            'mimetype': str,
            'filetype': str,
            'pretty_type': str,
            'editable': bool,
            'size': (int, float, str),
            'mode': str,
            'is_public': bool,
            'public_url_shared': bool,
            'url_private': str,
            'url_private_download': str,
            'permalink': str,
            'permalink_public': str,
            'shares': dict,
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type}, '
                    f'received {type(value).__name__}'
                )


@dataclass(slots=True)
class Message:
    """Slack Message object"""
    id: str
    team: str
    created: Union[int, float, str]
    user: Union[user.User, user.UserSuccinct, str]
    text: str
    type: str
    permalink: str
    blocks: List[Dict]
    timestamp: Union[int, float, str]
    conversation: Union[conversation.Conversation, conversation.ConversationSuccinct]

    def __post_init__(self):
        """Validate types of fields after initialisation."""
        expected_types = {
            'id': str,
            'team': str,
            'created': (int, float, str),
            'user': (user.User, user.UserSuccinct, str),
            'text': str,
            'type': str,
            'permalink': str,
            'blocks': list,
            'timestamp': (int, float, str),
            'conversation': (conversation.Conversation, conversation.ConversationSuccinct),
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type}, '
                    f'received {type(value).__name__}'
                )


def create_message_from_dict(message_dict: Dict) -> Message:
    """ Create a Message post object from a dict containing JSON data from
    the Slack API

    Args:
        message_dict: dict containing post information from the Slack API
    Returns:
        Message object for the post
    """

    return Message(
        id=message_dict.get('iid'),
        team=message_dict.get('team'),
        created=convert_timestamp(message_dict.get('ts')),
        timestamp=message_dict.get('ts'),
        conversation=message_dict.get('conversation'),
        user=message_dict.get('user'),
        text=message_dict.get('text'),
        type=message_dict.get('type'),
        permalink=message_dict.get('permalink'),
        blocks=message_dict.get('blocks'),
    )


def create_file_from_dict(file_dict: Dict) -> File:
    """ Create a File post object from a dict containing JSON data from
    the Slack API

    Args:
        file_dict: dict containing post information from the Slack API
    Returns:
        File object for the post
    """
    return File(
        id=file_dict.get('id'),
        created=convert_timestamp(file_dict.get('created')),
        user=file_dict.get('user'),
        name=file_dict.get('name'),
        title=file_dict.get('title'),
        mimetype=file_dict.get('mimetype'),
        filetype=file_dict.get('filetype'),
        pretty_type=file_dict.get('pretty_type'),
        editable=file_dict.get('editable'),
        size=file_dict.get('size'),
        mode=file_dict.get('mode'),
        is_public=file_dict.get('is_public'),
        public_url_shared=file_dict.get('public_url_shared'),
        url_private=file_dict.get('url_private'),
        url_private_download=file_dict.get('url_private_download'),
        permalink=file_dict.get('permalink'),
        permalink_public=file_dict.get('permalink_public'),
        shares=file_dict.get('shares')
    )
