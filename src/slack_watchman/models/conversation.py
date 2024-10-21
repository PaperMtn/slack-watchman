from dataclasses import dataclass
from typing import List, Dict, Optional

from slack_watchman.utils import convert_timestamp


@dataclass(slots=True)
class Conversation(object):
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


@dataclass(slots=True)
class ConversationSuccinct(object):
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
