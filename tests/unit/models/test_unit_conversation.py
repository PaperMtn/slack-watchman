import copy

import pytest

from fixtures import SlackMockData, mock_conversation, mock_conversation_succinct
from slack_watchman.models import conversation
from slack_watchman.utils import convert_timestamp


def test_conversation_initialisation(mock_conversation):
    # Test that the Conversation object is of the correct type
    assert isinstance(mock_conversation, conversation.Conversation)

    # Test that the Conversation object has the correct attributes
    assert mock_conversation.id == SlackMockData.MOCK_CONVERSATION_DICT.get('id')
    assert mock_conversation.name == SlackMockData.MOCK_CONVERSATION_DICT.get('name')
    assert mock_conversation.created == convert_timestamp(SlackMockData.MOCK_CONVERSATION_DICT.get('created'))
    assert mock_conversation.num_members == SlackMockData.MOCK_CONVERSATION_DICT.get('num_members')
    assert mock_conversation.is_general == SlackMockData.MOCK_CONVERSATION_DICT.get('is_general')
    assert mock_conversation.is_private == SlackMockData.MOCK_CONVERSATION_DICT.get('is_private')
    assert mock_conversation.is_im == SlackMockData.MOCK_CONVERSATION_DICT.get('is_im')
    assert mock_conversation.is_mpim == SlackMockData.MOCK_CONVERSATION_DICT.get('is_mpim')
    assert mock_conversation.is_archived == SlackMockData.MOCK_CONVERSATION_DICT.get('is_archived')
    assert mock_conversation.creator == SlackMockData.MOCK_CONVERSATION_DICT.get('creator')
    assert mock_conversation.name_normalized == SlackMockData.MOCK_CONVERSATION_DICT.get('name_normalized')
    assert mock_conversation.is_ext_shared == SlackMockData.MOCK_CONVERSATION_DICT.get('is_ext_shared')
    assert mock_conversation.is_org_shared == SlackMockData.MOCK_CONVERSATION_DICT.get('is_org_shared')
    assert mock_conversation.is_shared == SlackMockData.MOCK_CONVERSATION_DICT.get('is_shared')
    assert mock_conversation.is_channel == SlackMockData.MOCK_CONVERSATION_DICT.get('is_channel')
    assert mock_conversation.is_group == SlackMockData.MOCK_CONVERSATION_DICT.get('is_group')
    assert mock_conversation.is_pending_ext_shared == SlackMockData.MOCK_CONVERSATION_DICT.get('is_pending_ext_shared')
    assert mock_conversation.previous_names == SlackMockData.MOCK_CONVERSATION_DICT.get('previous_names')
    assert mock_conversation.is_member == SlackMockData.MOCK_CONVERSATION_DICT.get('is_member')
    assert mock_conversation.purpose == SlackMockData.MOCK_CONVERSATION_DICT.get('purpose').get('value')
    assert (mock_conversation.canvas_empty == SlackMockData.MOCK_CONVERSATION_DICT.get('properties').get('canvas')
            .get('is_empty'))
    assert (mock_conversation.canvas_id == SlackMockData.MOCK_CONVERSATION_DICT.get('properties').get('canvas')
            .get('file_id'))
    assert mock_conversation.topic == SlackMockData.MOCK_CONVERSATION_DICT.get('topic').get('value')


def test_conversation_missing_fields():
    # Create a conversation dictionary with missing fields
    conversation_dict = {
        'id': 'C123',
        'name': 'General'
    }

    # Create a Conversation object from the conversation dictionary
    test_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    # Assert that the Conversation object has the correct attributes
    assert test_conversation.id == 'C123'
    assert test_conversation.name == 'General'
    assert test_conversation.created is None
    assert test_conversation.num_members is None
    assert test_conversation.is_general is None
    assert test_conversation.is_private is None
    assert test_conversation.is_im is None
    assert test_conversation.is_mpim is None
    assert test_conversation.is_archived is None
    assert test_conversation.creator is None
    assert test_conversation.name_normalized is None
    assert test_conversation.is_ext_shared is None
    assert test_conversation.is_org_shared is None
    assert test_conversation.is_shared is None
    assert test_conversation.is_channel is None
    assert test_conversation.is_group is None
    assert test_conversation.is_pending_ext_shared is None
    assert test_conversation.previous_names is None
    assert test_conversation.is_member is None
    assert test_conversation.purpose is None
    assert test_conversation.canvas_empty is None
    assert test_conversation.canvas_id is None
    assert test_conversation.topic is None


def test_conversation_field_types(mock_conversation):
    assert isinstance(mock_conversation.id, str)
    assert isinstance(mock_conversation.name, str)
    assert isinstance(mock_conversation.created, (int, float, str))
    assert isinstance(mock_conversation.num_members, int)
    assert isinstance(mock_conversation.is_general, bool)
    assert isinstance(mock_conversation.is_private, bool)
    assert isinstance(mock_conversation.is_im, bool)
    assert isinstance(mock_conversation.is_mpim, bool)
    assert isinstance(mock_conversation.is_archived, bool)
    assert isinstance(mock_conversation.creator, str)
    assert isinstance(mock_conversation.name_normalized, str)
    assert isinstance(mock_conversation.is_ext_shared, bool)
    assert isinstance(mock_conversation.is_org_shared, bool)
    assert isinstance(mock_conversation.is_shared, bool)
    assert isinstance(mock_conversation.is_channel, bool)
    assert isinstance(mock_conversation.is_group, bool)
    assert isinstance(mock_conversation.is_pending_ext_shared, bool)
    assert isinstance(mock_conversation.previous_names, list)
    assert isinstance(mock_conversation.is_member, bool)
    assert isinstance(mock_conversation.purpose, str)
    assert isinstance(mock_conversation.canvas_empty, (bool, type(None)))
    assert isinstance(mock_conversation.canvas_id, (str, type(None)))
    assert isinstance(mock_conversation.topic, str)


def test_conversation_incorrect_field_types():
    # Test with incorrect field types
    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['id'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['name'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['created'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_private'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_im'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_mpim'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_archived'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_general'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['creator'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['name_normalized'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['previous_names'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['purpose']['value'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['topic']['value'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['properties']['canvas']['is_empty'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['properties']['canvas']['file_id'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['num_members'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_member'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_pending_ext_shared'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_ext_shared'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_shared'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_org_shared'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_group'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_channel'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)


def test_conversation_succinct_initialisation(mock_conversation_succinct):
    # Test the Conversation object is of the correct type
    assert isinstance(mock_conversation_succinct, conversation.ConversationSuccinct)

    # Test the Conversation object has the correct attributes
    assert mock_conversation_succinct.id == SlackMockData.MOCK_CONVERSATION_DICT.get('id')
    assert mock_conversation_succinct.name == SlackMockData.MOCK_CONVERSATION_DICT.get('name')
    assert mock_conversation_succinct.created == convert_timestamp(SlackMockData.MOCK_CONVERSATION_DICT.get('created'))
    assert mock_conversation_succinct.num_members == SlackMockData.MOCK_CONVERSATION_DICT.get('num_members')
    assert mock_conversation_succinct.is_private == SlackMockData.MOCK_CONVERSATION_DICT.get('is_private')
    assert mock_conversation_succinct.is_im == SlackMockData.MOCK_CONVERSATION_DICT.get('is_im')
    assert mock_conversation_succinct.is_mpim == SlackMockData.MOCK_CONVERSATION_DICT.get('is_mpim')
    assert mock_conversation_succinct.is_archived == SlackMockData.MOCK_CONVERSATION_DICT.get('is_archived')
    assert (mock_conversation_succinct.canvas_empty == SlackMockData.MOCK_CONVERSATION_DICT.get('properties')
            .get('canvas').get('is_empty'))
    assert (mock_conversation_succinct.canvas_id == SlackMockData.MOCK_CONVERSATION_DICT.get('properties')
            .get('canvas').get('file_id'))
    assert mock_conversation_succinct.creator == SlackMockData.MOCK_CONVERSATION_DICT.get('creator')


def test_conversation_succinct_missing_fields():
    # Create a conversation dictionary with missing fields
    conversation_dict = {
        'id': 'C123',
        'name': 'General'
    }

    # Create a Conversation object from the conversation dictionary
    test_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    # Assert that the Conversation object has the correct attributes
    assert test_conversation.id == 'C123'
    assert test_conversation.name == 'General'
    assert test_conversation.created is None
    assert test_conversation.num_members is None
    assert test_conversation.is_private is None
    assert test_conversation.is_im is None
    assert test_conversation.is_mpim is None
    assert test_conversation.is_archived is None
    assert test_conversation.canvas_empty is None
    assert test_conversation.canvas_id is None
    assert test_conversation.creator is None


def test_conversation_succinct_field_types():
    # Create a conversation dictionary with incorrect field types
    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['id'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['name'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['created'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['num_members'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_private'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_im'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_mpim'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['is_archived'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['creator'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['properties']['canvas']['is_empty'] = 123
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)

    conversation_dict = copy.deepcopy(SlackMockData.MOCK_CONVERSATION_DICT)
    conversation_dict['properties']['canvas']['file_id'] = {'foo': 'bar'}
    with pytest.raises(TypeError):
        mock_conversation = conversation.create_from_dict(conversation_dict, verbose=True)
