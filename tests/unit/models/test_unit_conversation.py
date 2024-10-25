import pytest
from slack_watchman.models import conversation
from slack_watchman.utils import convert_timestamp

CONVERSATION_DICT = {
    'id': 'C1234567890',
    'name': 'Example Conversation',
    'created': 1643723400,
    'num_members': 10,
    'is_general': True,
    'is_private': False,
    'is_im': False,
    'is_mpim': False,
    'is_archived': False,
    'creator': 'U1234567890',
    'name_normalized': 'example-conversation',
    'is_ext_shared': False,
    'is_org_shared': False,
    'is_shared': False,
    'is_channel': True,
    'is_group': False,
    'is_pending_ext_shared': False,
    'previous_names': ['old-name'],
    'is_member': True,
    'purpose': {
        'value': 'This is an example conversation'
    },
    'properties': {
        'canvas': {
            'is_empty': False,
            'file_id': 'CAN1234567890'
        }
    },
    'canvas_empty': False,
    'canvas_id': 'some-canvas-id',
    'topic': {'value': 'This is an example topic'}
}

CONVERSATION_SUCCINCT_DICT = {
    'id': 'C1234567890',
    'name': 'Example Conversation',
    'created': 1643723400,
    'num_members': 10,
    'is_private': False,
    'is_im': False,
    'is_mpim': False,
    'is_archived': False,
    'properties': {
        'canvas': {
            'is_empty': False,
            'file_id': 'CAN1234567890'
        }
    },
    'creator': 'U1234567890'
}

CONVERSATION_MISSING_FIELDS = {
    'id': 'C1234567890',
    'name': 'Example Conversation',
}


@pytest.fixture
def example_conversation():
    return conversation.create_from_dict(CONVERSATION_DICT, verbose=True)


@pytest.fixture
def example_conversation_succinct():
    return conversation.create_from_dict(CONVERSATION_SUCCINCT_DICT, verbose=False)


@pytest.fixture
def example_conversation_missing_fields():
    return conversation.create_from_dict(CONVERSATION_MISSING_FIELDS, verbose=True)


def test_conversation_initialisation(example_conversation):
    # Test that the Conversation object is of the correct type
    assert isinstance(example_conversation, conversation.Conversation)

    # Test that the Conversation object has the correct attributes
    assert example_conversation.id == CONVERSATION_DICT.get('id')
    assert example_conversation.name == CONVERSATION_DICT.get('name')
    assert example_conversation.created == convert_timestamp(CONVERSATION_DICT.get('created'))
    assert example_conversation.num_members == CONVERSATION_DICT.get('num_members')
    assert example_conversation.is_general == CONVERSATION_DICT.get('is_general')
    assert example_conversation.is_private == CONVERSATION_DICT.get('is_private')
    assert example_conversation.is_im == CONVERSATION_DICT.get('is_im')
    assert example_conversation.is_mpim == CONVERSATION_DICT.get('is_mpim')
    assert example_conversation.is_archived == CONVERSATION_DICT.get('is_archived')
    assert example_conversation.creator == CONVERSATION_DICT.get('creator')
    assert example_conversation.name_normalized == CONVERSATION_DICT.get('name_normalized')
    assert example_conversation.is_ext_shared == CONVERSATION_DICT.get('is_ext_shared')
    assert example_conversation.is_org_shared == CONVERSATION_DICT.get('is_org_shared')
    assert example_conversation.is_shared == CONVERSATION_DICT.get('is_shared')
    assert example_conversation.is_channel == CONVERSATION_DICT.get('is_channel')
    assert example_conversation.is_group == CONVERSATION_DICT.get('is_group')
    assert example_conversation.is_pending_ext_shared == CONVERSATION_DICT.get('is_pending_ext_shared')
    assert example_conversation.previous_names == CONVERSATION_DICT.get('previous_names')
    assert example_conversation.is_member == CONVERSATION_DICT.get('is_member')
    assert example_conversation.purpose == CONVERSATION_DICT.get('purpose').get('value')
    assert example_conversation.canvas_empty == CONVERSATION_DICT.get('properties').get('canvas').get('is_empty')
    assert example_conversation.canvas_id == CONVERSATION_DICT.get('properties').get('canvas').get('file_id')
    assert example_conversation.topic == CONVERSATION_DICT.get('topic').get('value')


def test_conversation_succinct_initialisation(example_conversation_succinct):
    # Test that the Conversation object is of the correct type
    assert isinstance(example_conversation_succinct, conversation.ConversationSuccinct)

    # Test that the Conversation object has the correct attributes
    assert example_conversation_succinct.id == CONVERSATION_SUCCINCT_DICT.get('id')
    assert example_conversation_succinct.name == CONVERSATION_SUCCINCT_DICT.get('name')
    assert example_conversation_succinct.created == convert_timestamp(CONVERSATION_SUCCINCT_DICT.get('created'))
    assert example_conversation_succinct.num_members == CONVERSATION_SUCCINCT_DICT.get('num_members')
    assert example_conversation_succinct.is_private == CONVERSATION_SUCCINCT_DICT.get('is_private')
    assert example_conversation_succinct.is_im == CONVERSATION_SUCCINCT_DICT.get('is_im')
    assert example_conversation_succinct.is_mpim == CONVERSATION_SUCCINCT_DICT.get('is_mpim')
    assert example_conversation_succinct.is_archived == CONVERSATION_SUCCINCT_DICT.get('is_archived')
    assert example_conversation_succinct.creator == CONVERSATION_SUCCINCT_DICT.get('creator')
    assert example_conversation_succinct.canvas_empty == CONVERSATION_SUCCINCT_DICT.get('properties').get('canvas').get('is_empty')
    assert example_conversation_succinct.canvas_id == CONVERSATION_SUCCINCT_DICT.get('properties').get('canvas').get('file_id')


def test_conversation_missing_fields(example_conversation_missing_fields):
    # Test that the Conversation object is of the correct type
    assert isinstance(example_conversation_missing_fields, conversation.Conversation)

    # Test that the Conversation object has the correct attributes
    assert example_conversation_missing_fields.id is CONVERSATION_MISSING_FIELDS.get('id')
    assert example_conversation_missing_fields.name == CONVERSATION_MISSING_FIELDS.get('name')
    assert example_conversation_missing_fields.created is None
    assert example_conversation_missing_fields.num_members is None
    assert example_conversation_missing_fields.is_private is None
    assert example_conversation_missing_fields.is_im is None
    assert example_conversation_missing_fields.is_mpim is None
    assert example_conversation_missing_fields.is_archived is None
    assert example_conversation_missing_fields.creator is None
    assert example_conversation_missing_fields.canvas_empty is None
    assert example_conversation_missing_fields.canvas_id is None


def test_field_type():
    # Test that correct error is raised when id is not a string
    conversation_dict = CONVERSATION_DICT
    conversation_dict['id'] = 123
    with pytest.raises(TypeError):
        test_conversation = conversation.create_from_dict(conversation_dict, verbose=True)


def test_missing_field():
    temp_conversation_dict = CONVERSATION_DICT.copy()
    del temp_conversation_dict['id']
    test_conversation = conversation.create_from_dict(temp_conversation_dict, verbose=True)
    assert test_conversation.id is None
