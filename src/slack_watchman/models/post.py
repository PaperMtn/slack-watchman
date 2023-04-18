import time
from dataclasses import dataclass
from typing import List, Dict

from . import conversation
from . import user


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
class File(object):
    id: str
    team: str
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
    shares: List


@dataclass(slots=True)
class Message(object):
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
        created=_convert_timestamp(message_dict.get('ts')),
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
        team=file_dict.get('source_team'),
        created=_convert_timestamp(file_dict.get('created')),
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
