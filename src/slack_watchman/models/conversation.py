from dataclasses import dataclass
from typing import List, Dict, Optional

from slack_watchman.utils import convert_timestamp


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class Conversation:
    """ Class that defines Conversation objects. Conversations
    could be:
        - Direct messages
        - Multi-person direct messages
        - Private channels
        - Public channels
        - Slack connect channels"""

    id: str
    name: str
    created: int or float or str
    is_private: bool
    is_im: bool
    is_mpim: bool
    is_archived: bool
    is_general: bool
    creator: str
    name_normalized: str
    previous_names: List[str]
    purpose: str
    topic: str
    canvas_empty: Optional[bool]
    canvas_id: Optional[str]
    num_members: int
    is_member: bool
    is_pending_ext_shared: bool
    is_ext_shared: bool
    is_shared: bool
    is_org_shared: bool
    is_group: bool
    is_channel: bool

# pylint: disable=too-many-branches
    def __post_init__(self):
        if self.id and not isinstance(self.id, str):
            raise TypeError(f'Expected `id` to be of type str, received {type(self.name).__name__}')
        if self.name and not isinstance(self.name, str):
            raise TypeError(f'Expected `name` to be of type str, received {type(self.name).__name__}')
        if self.created and not isinstance(self.created, (float, int, str)):
            raise TypeError(f'Expected `created` to be of type str or int or '
                            f'float, received {type(self.name).__name__}')
        if self.is_private and not isinstance(self.is_private, bool):
            raise TypeError(f'Expected `is_private` to be of type bool, received {type(self.name).__name__}')
        if self.is_im and not isinstance(self.is_im, bool):
            raise TypeError(f'Expected `is_im` to be of type bool, received {type(self.name).__name__}')
        if self.is_mpim and not isinstance(self.is_mpim, bool):
            raise TypeError(f'Expected `is_mpim` to be of type bool, received {type(self.name).__name__}')
        if self.is_archived and not isinstance(self.is_archived, bool):
            raise TypeError(f'Expected `is_archived` to be of type bool, received {type(self.name).__name__}')
        if self.is_general and not isinstance(self.is_general, bool):
            raise TypeError(f'Expected `is_general` to be of type bool, received {type(self.name).__name__}')
        if self.creator and not isinstance(self.creator, str):
            raise TypeError(f'Expected `creator` to be of type str, received {type(self.name).__name__}')
        if self.name_normalized and not isinstance(self.name_normalized, str):
            raise TypeError(f'Expected `name_normalized` to be of type str, received {type(self.name).__name__}')
        if self.previous_names and not isinstance(self.previous_names, list):
            raise TypeError(f'Expected `previous_names` to be of type list, received {type(self.name).__name__}')
        if self.purpose and not isinstance(self.purpose, str):
            raise TypeError(f'Expected `purpose` to be of type str, received {type(self.name).__name__}')
        if self.topic and not isinstance(self.topic, str):
            raise TypeError(f'Expected `topic` to be of type str, received {type(self.name).__name__}')
        if self.canvas_empty and not isinstance(self.canvas_empty, bool):
            raise TypeError(f'Expected `canvas_empty` to be of type bool, received {type(self.name).__name__}')
        if self.canvas_id and not isinstance(self.canvas_id, str):
            raise TypeError(f'Expected `canvas_id` to be of type str, received {type(self.name).__name__}')
        if self.num_members and not isinstance(self.num_members, int):
            raise TypeError(f'Expected `num_members` to be of type int, received {type(self.name).__name__}')
        if self.is_member and not isinstance(self.is_member, bool):
            raise TypeError(f'Expected `is_member` to be of type bool, received {type(self.name).__name__}')
        if self.is_pending_ext_shared and not isinstance(self.is_pending_ext_shared, bool):
            raise TypeError(f'Expected `is_pending_ext_shared` to be of type bool, received {type(self.name).__name__}')
        if self.is_ext_shared and not isinstance(self.is_ext_shared, bool):
            raise TypeError(f'Expected `is_ext_shared` to be of type bool, received {type(self.name).__name__}')
        if self.is_shared and not isinstance(self.is_shared, bool):
            raise TypeError(f'Expected `is_shared` to be of type bool, received {type(self.name).__name__}')
        if self.is_org_shared and not isinstance(self.is_org_shared, bool):
            raise TypeError(f'Expected `is_org_shared` to be of type bool, received {type(self.name).__name__}')
        if self.is_group and not isinstance(self.is_group, bool):
            raise TypeError(f'Expected `is_group` to be of type bool, received {type(self.name).__name__}')
        if self.is_channel and not isinstance(self.is_channel, bool):
            raise TypeError(f'Expected `is_channel` to be of type bool, received {type(self.name).__name__}')


@dataclass(slots=True)
class ConversationSuccinct:
    """ Class that defines Conversation objects. Conversations
    could be:
        - Direct messages
        - Multi-person direct messages
        - Private channels
        - Public channels
        - Slack connect channels"""

    id: str
    name: str
    created: int or float or str
    is_private: bool
    is_im: bool
    is_mpim: bool
    is_archived: bool
    canvas_empty: Optional[bool]
    canvas_id: Optional[str]
    creator: str
    num_members: int

    def __post_init__(self):
        if self.is_private and not isinstance(self.is_private, bool):
            raise TypeError(f'Expected `is_private` to be of type bool, received {type(self.name).__name__}')
        if self.is_im and not isinstance(self.is_im, bool):
            raise TypeError(f'Expected `is_im` to be of type bool, received {type(self.name).__name__}')
        if self.is_mpim and not isinstance(self.is_mpim, bool):
            raise TypeError(f'Expected `is_mpim` to be of type bool, received {type(self.name).__name__}')
        if self.is_archived and not isinstance(self.is_archived, bool):
            raise TypeError(f'Expected `is_archived` to be of type bool, received {type(self.name).__name__}')
        if self.is_private and not isinstance(self.is_private, bool):
            raise TypeError(f'Expected `is_private` to be of type bool, received {type(self.name).__name__}')
        if self.is_im and not isinstance(self.is_im, bool):
            raise TypeError(f'Expected `is_im` to be of type bool, received {type(self.name).__name__}')
        if self.is_mpim and not isinstance(self.is_mpim, bool):
            raise TypeError(f'Expected `is_mpim` to be of type bool, received {type(self.name).__name__}')
        if self.is_archived and not isinstance(self.is_archived, bool):
            raise TypeError(f'Expected `is_archived` to be of type bool, received {type(self.name).__name__}')
        if self.canvas_empty and not isinstance(self.canvas_empty, bool):
            raise TypeError(f'Expected `canvas_empty` to be of type bool, received {type(self.name).__name__}')
        if self.canvas_id and not isinstance(self.canvas_id, str):
            raise TypeError(f'Expected `canvas_id` to be of type str, received {type(self.name).__name__}')
        if self.creator and not isinstance(self.creator, str):
            raise TypeError(f'Expected `creator` to be of type str, received {type(self.name).__name__}')
        if self.num_members and not isinstance(self.num_members, int):
            raise TypeError(f'Expected `num_members` to be of type int, received {type(self.name).__name__}')


def create_from_dict(conv_dict: Dict, verbose: bool) -> Conversation or ConversationSuccinct:
    """ Create a User object from a dict response from the Slack API

    Args:
        conv_dict: dict/JSON format data from Slack API
        verbose: Whether to use verbose logging or not
    Returns:
        A new Conversation object
    """

    if verbose:
        return Conversation(
            id=conv_dict.get('id'),
            name=conv_dict.get('name'),
            created=convert_timestamp(conv_dict.get('created')),
            num_members=conv_dict.get('num_members'),
            is_general=conv_dict.get('is_general'),
            is_private=conv_dict.get('is_private'),
            is_im=conv_dict.get('is_im'),
            is_mpim=conv_dict.get('is_mpim'),
            is_archived=conv_dict.get('is_archived'),
            creator=conv_dict.get('creator'),
            name_normalized=conv_dict.get('name_normalized'),
            is_ext_shared=conv_dict.get('is_ext_shared'),
            is_org_shared=conv_dict.get('is_org_shared'),
            is_shared=conv_dict.get('is_shared'),
            is_channel=conv_dict.get('is_channel'),
            is_group=conv_dict.get('is_group'),
            is_pending_ext_shared=conv_dict.get('is_pending_ext_shared'),
            previous_names=conv_dict.get('previous_names'),
            is_member=conv_dict.get('is_member'),
            purpose=conv_dict.get('purpose', {}).get('value'),
            canvas_empty=conv_dict.get('properties', {}).get('canvas', {}).get('is_empty'),
            canvas_id=conv_dict.get('properties', {}).get('canvas', {}).get('file_id'),
            topic=conv_dict.get('topic', {}).get('value')
        )
    else:
        return ConversationSuccinct(
            id=conv_dict.get('id'),
            name=conv_dict.get('name'),
            created=convert_timestamp(conv_dict.get('created')),
            num_members=conv_dict.get('num_members'),
            is_private=conv_dict.get('is_private'),
            is_im=conv_dict.get('is_im'),
            is_mpim=conv_dict.get('is_mpim'),
            is_archived=conv_dict.get('is_archived'),
            canvas_empty=conv_dict.get('properties', {}).get('canvas', {}).get('is_empty'),
            canvas_id=conv_dict.get('properties', {}).get('canvas', {}).get('file_id'),
            creator=conv_dict.get('creator'),
        )
