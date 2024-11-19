import copy

import pytest

from fixtures import (
    SlackMockData,
    mock_message,
    mock_file,
    mock_user,
    mock_conversation,
    mock_user_succinct,
    mock_conversation_succinct
)
from slack_watchman.models import post
from slack_watchman.utils import convert_timestamp


def test_message_initialisation(mock_message, mock_user, mock_conversation):
    # Test that the Message object is of the correct type
    assert isinstance(mock_message, post.Message)

    # Test that the Message object has the correct attributes
    assert mock_message.id == SlackMockData.MOCK_MESSAGE_DICT.get('iid')
    assert mock_message.team == SlackMockData.MOCK_MESSAGE_DICT.get('team')
    assert mock_message.created == convert_timestamp(SlackMockData.MOCK_MESSAGE_DICT.get('ts'))
    assert mock_message.user == mock_user
    assert mock_message.text == SlackMockData.MOCK_MESSAGE_DICT.get('text')
    assert mock_message.type == SlackMockData.MOCK_MESSAGE_DICT.get('type')
    assert mock_message.permalink == SlackMockData.MOCK_MESSAGE_DICT.get('permalink')
    assert mock_message.blocks == SlackMockData.MOCK_MESSAGE_DICT.get('blocks')
    assert mock_message.timestamp == SlackMockData.MOCK_MESSAGE_DICT.get('ts')
    assert mock_message.conversation == mock_conversation


def test_message_initialisation_succinct(mock_user_succinct, mock_conversation_succinct):
    # Create a message with succinct user and conversation objects
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['user'] = mock_user_succinct
    message_dict['conversation'] = mock_conversation_succinct
    mock_message = post.create_message_from_dict(message_dict)

    # Test that the Message object is of the correct type
    assert isinstance(mock_message, post.Message)

    # Test that the Message object has the correct attributes
    assert mock_message.id == SlackMockData.MOCK_MESSAGE_DICT.get('iid')
    assert mock_message.team == SlackMockData.MOCK_MESSAGE_DICT.get('team')
    assert mock_message.created == convert_timestamp(SlackMockData.MOCK_MESSAGE_DICT.get('ts'))
    assert mock_message.user == mock_user_succinct
    assert mock_message.text == SlackMockData.MOCK_MESSAGE_DICT.get('text')
    assert mock_message.type == SlackMockData.MOCK_MESSAGE_DICT.get('type')
    assert mock_message.permalink == SlackMockData.MOCK_MESSAGE_DICT.get('permalink')
    assert mock_message.blocks == SlackMockData.MOCK_MESSAGE_DICT.get('blocks')
    assert mock_message.timestamp == SlackMockData.MOCK_MESSAGE_DICT.get('ts')
    assert mock_message.conversation == mock_conversation_succinct


def test_message_initialisation_missing_fields():
    # Create a dict containing message information
    message_dict = {
        'iid': 'C1234567890',
        'team': 'T1234567890',
    }

    mock_message = post.create_message_from_dict(message_dict)
    # Test that the Message object is of the correct type
    assert isinstance(mock_message, post.Message)

    # Test that the Message object has the correct attributes
    assert mock_message.id == message_dict.get('iid')
    assert mock_message.team == message_dict.get('team')
    assert mock_message.created is None
    assert mock_message.user is None
    assert mock_message.text is None
    assert mock_message.type is None
    assert mock_message.permalink is None
    assert mock_message.blocks is None
    assert mock_message.timestamp is None
    assert mock_message.conversation is None


def test_message_field_type():
    # Test that the correct error is raised when id is not a string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['iid'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when team is not a string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['team'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when created is not an int, float, or string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['ts'] = [1, 2, 3]
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when text is not a string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['text'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when type is not a string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['type'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when permalink is not a string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['permalink'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when blocks is not a List of Dicts
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['blocks'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when timestamp is not an int, float, or string
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['ts'] = [1, 2, 3]
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)

    # Test that the correct error is raised when conversation is not a Conversation object
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['conversation'] = 123
    with pytest.raises(TypeError):
        test_message = post.create_message_from_dict(message_dict)


def test_file_initialisation(mock_file, mock_user):
    # Test that the File object is of the correct type
    assert isinstance(mock_file, post.File)

    # Test that the File object has the correct attributes
    assert mock_file.id == SlackMockData.MOCK_FILE_DICT.get('id')
    assert mock_file.created == convert_timestamp(SlackMockData.MOCK_FILE_DICT.get('created'))
    assert mock_file.user == mock_user
    assert mock_file.name == SlackMockData.MOCK_FILE_DICT.get('name')
    assert mock_file.title == SlackMockData.MOCK_FILE_DICT.get('title')
    assert mock_file.mimetype == SlackMockData.MOCK_FILE_DICT.get('mimetype')
    assert mock_file.filetype == SlackMockData.MOCK_FILE_DICT.get('filetype')
    assert mock_file.pretty_type == SlackMockData.MOCK_FILE_DICT.get('pretty_type')
    assert mock_file.editable == SlackMockData.MOCK_FILE_DICT.get('editable')
    assert mock_file.size == SlackMockData.MOCK_FILE_DICT.get('size')
    assert mock_file.mode == SlackMockData.MOCK_FILE_DICT.get('mode')
    assert mock_file.is_public == SlackMockData.MOCK_FILE_DICT.get('is_public')
    assert mock_file.public_url_shared == SlackMockData.MOCK_FILE_DICT.get('public_url_shared')
    assert mock_file.url_private == SlackMockData.MOCK_FILE_DICT.get('url_private')
    assert mock_file.url_private_download == SlackMockData.MOCK_FILE_DICT.get('url_private_download')
    assert mock_file.permalink == SlackMockData.MOCK_FILE_DICT.get('permalink')
    assert mock_file.permalink_public == SlackMockData.MOCK_FILE_DICT.get('permalink_public')
    assert mock_file.shares == SlackMockData.MOCK_FILE_DICT.get('shares')

    # Test the user object has the correct attributes
    assert mock_file.user.id == SlackMockData.MOCK_USER_DICT.get('id')
    assert mock_file.user.name == SlackMockData.MOCK_USER_DICT.get('name')
    assert mock_file.user.deleted == SlackMockData.MOCK_USER_DICT.get('deleted')
    assert mock_file.user.real_name == SlackMockData.MOCK_USER_DICT.get('real_name')
    assert mock_file.user.tz == SlackMockData.MOCK_USER_DICT.get('tz')
    assert mock_file.user.tz_label == SlackMockData.MOCK_USER_DICT.get('tz_label')
    assert mock_file.user.tz_offset == SlackMockData.MOCK_USER_DICT.get('tz_offset')
    assert mock_file.user.title == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('title')
    assert mock_file.user.phone == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('phone')
    assert mock_file.user.skype == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('skype')
    assert mock_file.user.display_name == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('display_name')
    assert mock_file.user.email == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('email')
    assert mock_file.user.first_name == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('first_name')
    assert mock_file.user.last_name == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('last_name')
    assert mock_file.user.is_admin == SlackMockData.MOCK_USER_DICT.get('is_admin')
    assert mock_file.user.is_owner == SlackMockData.MOCK_USER_DICT.get('is_owner')
    assert mock_file.user.is_primary_owner == SlackMockData.MOCK_USER_DICT.get('is_primary_owner')
    assert mock_file.user.is_restricted == SlackMockData.MOCK_USER_DICT.get('is_restricted')
    assert mock_file.user.is_ultra_restricted == SlackMockData.MOCK_USER_DICT.get('is_ultra_restricted')
    assert mock_file.user.is_bot == SlackMockData.MOCK_USER_DICT.get('is_bot')
    assert mock_file.user.updated == convert_timestamp(SlackMockData.MOCK_USER_DICT.get('updated'))
    assert mock_file.user.has_2fa == SlackMockData.MOCK_USER_DICT.get('has_2fa')


def test_file_initialisation_succinct(mock_user_succinct):
    # Create a file with succinct user object
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['user'] = mock_user_succinct
    mock_file = post.create_file_from_dict(file_dict)

    # Test that the File object is of the correct type
    assert isinstance(mock_file, post.File)

    # Test that the File object has the correct attributes
    assert mock_file.id == SlackMockData.MOCK_FILE_DICT.get('id')
    assert mock_file.created == convert_timestamp(SlackMockData.MOCK_FILE_DICT.get('created'))
    assert mock_file.user == mock_user_succinct
    assert mock_file.name == SlackMockData.MOCK_FILE_DICT.get('name')
    assert mock_file.title == SlackMockData.MOCK_FILE_DICT.get('title')
    assert mock_file.mimetype == SlackMockData.MOCK_FILE_DICT.get('mimetype')
    assert mock_file.filetype == SlackMockData.MOCK_FILE_DICT.get('filetype')
    assert mock_file.pretty_type == SlackMockData.MOCK_FILE_DICT.get('pretty_type')
    assert mock_file.editable == SlackMockData.MOCK_FILE_DICT.get('editable')
    assert mock_file.size == SlackMockData.MOCK_FILE_DICT.get('size')
    assert mock_file.mode == SlackMockData.MOCK_FILE_DICT.get('mode')
    assert mock_file.is_public == SlackMockData.MOCK_FILE_DICT.get('is_public')
    assert mock_file.public_url_shared == SlackMockData.MOCK_FILE_DICT.get('public_url_shared')
    assert mock_file.url_private == SlackMockData.MOCK_FILE_DICT.get('url_private')
    assert mock_file.url_private_download == SlackMockData.MOCK_FILE_DICT.get('url_private_download')
    assert mock_file.permalink == SlackMockData.MOCK_FILE_DICT.get('permalink')
    assert mock_file.permalink_public == SlackMockData.MOCK_FILE_DICT.get('permalink_public')
    assert mock_file.shares == SlackMockData.MOCK_FILE_DICT.get('shares')

    # Test the succinct user object
    assert mock_file.user.id == SlackMockData.MOCK_USER_DICT.get('id')
    assert mock_file.user.name == SlackMockData.MOCK_USER_DICT.get('name')
    assert mock_file.user.display_name == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('display_name')
    assert mock_file.user.has_2fa == SlackMockData.MOCK_USER_DICT.get('has_2fa')
    assert mock_file.user.is_admin == SlackMockData.MOCK_USER_DICT.get('is_admin')
    assert mock_file.user.email == SlackMockData.MOCK_USER_DICT.get('profile', {}).get('email')


def test_file_initialisation_missing_fields():
    # Create a dict containing file information
    file_dict = {
        'id': 'F1234567890',
        'name': 'Example File',
    }

    mock_file = post.create_file_from_dict(file_dict)
    # Test that the File object is of the correct type
    assert isinstance(mock_file, post.File)

    # Test that the File object has the correct attributes
    assert mock_file.id == file_dict.get('id')
    assert mock_file.name == file_dict.get('name')
    assert mock_file.created is None
    assert mock_file.user is None
    assert mock_file.title is None
    assert mock_file.mimetype is None
    assert mock_file.filetype is None
    assert mock_file.pretty_type is None
    assert mock_file.editable is None
    assert mock_file.size is None
    assert mock_file.mode is None
    assert mock_file.is_public is None
    assert mock_file.public_url_shared is None
    assert mock_file.url_private is None
    assert mock_file.url_private_download is None
    assert mock_file.permalink is None
    assert mock_file.permalink_public is None
    assert mock_file.shares is None
    

def test_file_field_types():
    # Test that the correct error is raised when id is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['id'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when created is not an int, float, or string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['created'] = {'key': 'value'}
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when user is not a User object
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['user'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when name is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['name'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when title is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['title'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when mimetype is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['mimetype'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when filetype is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['filetype'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when pretty_type is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['pretty_type'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when editable is not a bool
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['editable'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when size is not an int, float, or string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['size'] = [1, 2, 3]
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when mode is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['mode'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when is_public is not a bool
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['is_public'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when public_url_shared is not a bool
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['public_url_shared'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when url_private is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['url_private'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when url_private_download is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['url_private_download'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when permalink is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['permalink'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)

    # Test that the correct error is raised when permalink_public is not a string
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['permalink_public'] = 123
    with pytest.raises(TypeError):
        test_file = post.create_file_from_dict(file_dict)
