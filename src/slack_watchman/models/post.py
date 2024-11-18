from dataclasses import dataclass
from typing import List, Dict, Any

from slack_watchman.models import conversation, user
from slack_watchman.utils import convert_timestamp


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class File:
    """ Slack File object """
    id: str
    created: int or float or str
    user: user.User or user.UserSuccinct or str
    name: str
    title: str
    mimetype: str
    filetype: str
    pretty_type: str
    editable: bool
    size: int or float
    mode: str
    is_public: bool
    public_url_shared: bool
    url_private: str
    url_private_download: str
    permalink: str
    permalink_public: str
    shares: Dict[Any, Any]

    # pylint: disable=too-many-branches
    def __post_init__(self):
        if self.id and not isinstance(self.id, str):
            raise TypeError(f'Expected `id` to be of type str, received {type(self.id).__name__}')
        if self.created and not isinstance(self.created, (float, int, str)):
            raise TypeError(
                f'Expected `created` to be of type str or int or float, received {type(self.created).__name__}')
        if self.user and not isinstance(self.user, (str, user.User, user.UserSuccinct)):
            raise TypeError(f'Expected `user` to be of type User or '
                            f'UserSuccinct or str, received {type(self.user).__name__}')
        if self.name and not isinstance(self.name, str):
            raise TypeError(f'Expected `name` to be of type str, received {type(self.name).__name__}')
        if self.title and not isinstance(self.title, str):
            raise TypeError(f'Expected `title` to be of type str, received {type(self.title).__name__}')
        if self.mimetype and not isinstance(self.mimetype, str):
            raise TypeError(f'Expected `mimetype` to be of type str, received {type(self.mimetype).__name__}')
        if self.filetype and not isinstance(self.filetype, str):
            raise TypeError(f'Expected `filetype` to be of type str, received {type(self.filetype).__name__}')
        if self.pretty_type and not isinstance(self.pretty_type, str):
            raise TypeError(f'Expected `pretty_type` to be of type str, received {type(self.pretty_type).__name__}')
        if self.editable and not isinstance(self.editable, bool):
            raise TypeError(f'Expected `editable` to be of type bool, received {type(self.editable).__name__}')
        if self.size and not isinstance(self.size, (float, int, str)):
            raise TypeError(f'Expected `size` to be of type str or int or float, received {type(self.size).__name__}')
        if self.mode and not isinstance(self.mode, str):
            raise TypeError(f'Expected `mode` to be of type str, received {type(self.mode).__name__}')
        if self.is_public and not isinstance(self.is_public, bool):
            raise TypeError(f'Expected `is_public` to be of type bool, received {type(self.is_public).__name__}')
        if self.public_url_shared and not isinstance(self.public_url_shared, bool):
            raise TypeError(
                f'Expected `public_url_shared` to be of type bool, received {type(self.public_url_shared).__name__}')
        if self.url_private and not isinstance(self.url_private, str):
            raise TypeError(f'Expected `url_private` to be of type str, received {type(self.url_private).__name__}')
        if self.url_private_download and not isinstance(self.url_private_download, str):
            raise TypeError(
                f'Expected `url_private_download` to be of type str, '
                f'received {type(self.url_private_download).__name__}')
        if self.permalink and not isinstance(self.permalink, str):
            raise TypeError(f'Expected `permalink` to be of type str, received {type(self.permalink).__name__}')
        if self.permalink_public and not isinstance(self.permalink_public, str):
            raise TypeError(
                f'Expected `permalink_public` to be of type str, received {type(self.permalink_public).__name__}')
        if self.shares and not isinstance(self.shares, dict):
            raise TypeError(f'Expected `shares` to be of type dict, received {type(self.shares).__name__}')


@dataclass(slots=True)
class Message:
    """ Slack Message object """
    id: str
    team: str
    created: int or float or str
    user: user.User or user.UserSuccinct or str
    text: str
    type: str
    permalink: str
    blocks: List[Dict]
    timestamp: int or float or str
    conversation: conversation.Conversation or conversation.ConversationSuccinct

    def __post_init__(self):
        if self.id and not isinstance(self.id, str):
            raise TypeError(f'Expected `id` to be of type str, received {type(self.id).__name__}')
        if self.team and not isinstance(self.team, str):
            raise TypeError(f'Expected `team` to be of type str, received {type(self.team).__name__}')
        if self.created and not isinstance(self.created, (float, int, str)):
            raise TypeError(
                f'Expected `created` to be of type str or int or float, received {type(self.created).__name__}')
        if self.user and not isinstance(self.user, (str, user.User, user.UserSuccinct)):
            raise TypeError(
                f'Expected `user` to be of type User or UserSuccinct or str, received {type(self.user).__name__}')
        if self.text and not isinstance(self.text, str):
            raise TypeError(f'Expected `text` to be of type str, received {type(self.text).__name__}')
        if self.type and not isinstance(self.type, str):
            raise TypeError(f'Expected `type` to be of type str, received {type(self.type).__name__}')
        if self.permalink and not isinstance(self.permalink, str):
            raise TypeError(f'Expected `permalink` to be of type str, received {type(self.permalink).__name__}')
        if self.blocks and not isinstance(self.blocks, list):
            raise TypeError(f'Expected `blocks` to be of type list, received {type(self.blocks).__name__}')
        if self.timestamp and not isinstance(self.timestamp, (float, int, str)):
            raise TypeError(
                f'Expected `timestamp` to be of type str or int or float, received {type(self.timestamp).__name__}')
        if self.conversation and not isinstance(self.conversation,
                                                (conversation.Conversation, conversation.ConversationSuccinct)):
            raise TypeError(
                f'Expected `conversation` to be of type Conversation or '
                f'ConversationSuccinct, received {type(self.conversation).__name__}')


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
