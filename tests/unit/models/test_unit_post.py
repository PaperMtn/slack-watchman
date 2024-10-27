import pytest
from slack_watchman.models import post, user, conversation
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

USER_DICT = {
    'id': 'U1234567890',
    'name': 'Robert Baratheon',
    'deleted': False,
    'real_name': 'Robert Baratheon',
    'tz': 'Westeros/Kings Landing',
    'tz_label': 'Westeros Standard Time',
    'tz_offset': -18000,
    'profile': {
        'title': 'King of the Andals and the First Men',
        'phone': '+447123456789',
        'skype': 'bobbyb',
        'display_name': 'Robert Baratheon',
        'email': 'r.baratheon@me.com',
        'first_name': 'Robert',
        'last_name': 'Baratheon',
    },
    'is_admin': True,
    'is_owner': False,
    'is_primary_owner': False,
    'is_restricted': False,
    'is_ultra_restricted': False,
    'is_bot': False,
    'updated': 1643723400,
    'has_2fa': True
}

USER_SUCCINCT_DICT = {
    'id': 'U1234567890',
    'name': 'Joe Bloggs'
}

MESSAGE_DICT = {
    'iid': '1234567890',
    'team': 'T1234567890',
    'ts': '1643723400.1234567890',
    'conversation': None,
    'user': None,
    'text': 'This is a test message',
    'type': 'message',
    'permalink': 'https://example.slack.com/archives/C1234567890/p1234567890',
    'blocks': []
}

FILE_DICT = {
    'id': 'F1234567890',
    'created': 1643723400,
    'user': USER_DICT,
    'name': 'example_file.txt',
    'title': 'Example File',
    'mimetype': 'text/plain',
    'filetype': 'txt',
    'pretty_type': 'Text File',
    'editable': True,
    'size': 1024,
    'mode': 'hosted',
    'is_public': False,
    'public_url_shared': False,
    'url_private': 'https://example.slack.com/files/U1234567890/F1234567890/example_file.txt',
    'url_private_download': 'https://example.slack.com/files/U1234567890/F1234567890/example_file.txt?mode=download',
    'permalink': 'https://example.slack.com/files/U1234567890/F1234567890/example_file.txt',
    'permalink_public': 'https://example.slack.com/files/U1234567890/F1234567890/example_file.txt',
    'shares': {}
}

MESSAGE_DICT_MISSING_FIELDS = {
    'iid': '1234567890',
    'team': 'T1234567890',
    'ts': '1643723400.1234567890',
    'text': 'This is a test message',
    'type': 'message',
    'blocks': []
}

FILE_DICT_MISSING_FIELDS = {
    'id': 'F1234567890',
    'name': 'example_file.txt',
    'title': 'Example File',
    'mimetype': 'text/plain',
    'filetype': 'txt',
}


@pytest.fixture
def example_user():
    return user.create_from_dict(USER_DICT, verbose=True)


@pytest.fixture
def example_user_succinct():
    return user.create_from_dict(USER_SUCCINCT_DICT, verbose=False)


@pytest.fixture
def example_conversation():
    return conversation.create_from_dict(CONVERSATION_DICT, verbose=False)


@pytest.fixture
def example_conversation_succinct():
    return conversation.create_from_dict(CONVERSATION_SUCCINCT_DICT, verbose=True)


@pytest.fixture
def example_message(example_user, example_conversation):
    temp_message_dict = MESSAGE_DICT.copy()
    temp_message_dict['conversation'] = example_conversation
    temp_message_dict['user'] = example_user
    return post.create_message_from_dict(temp_message_dict)


@pytest.fixture
def example_message_succinct_values(example_user_succinct, example_conversation_succinct):
    temp_message_dict = MESSAGE_DICT.copy()
    temp_message_dict['conversation'] = example_conversation_succinct
    temp_message_dict['user'] = example_user_succinct
    return post.create_message_from_dict(temp_message_dict)


@pytest.fixture
def example_file(example_user):
    temp_file_dict = FILE_DICT.copy()
    temp_file_dict['user'] = example_user
    return post.create_file_from_dict(temp_file_dict)


@pytest.fixture
def example_file_succinct_values(example_user_succinct):
    temp_file_dict = FILE_DICT.copy()
    temp_file_dict['user'] = example_user_succinct
    return post.create_file_from_dict(temp_file_dict)


@pytest.fixture
def example_file_missing_fields():
    return post.create_file_from_dict(FILE_DICT_MISSING_FIELDS)


@pytest.fixture
def example_message_missing_fields(example_user, example_conversation):
    return post.create_message_from_dict(MESSAGE_DICT_MISSING_FIELDS)


def test_message_initialisation(example_message, example_user, example_conversation):
    # Test that the Message object is of the correct type
    assert isinstance(example_message, post.Message)

    # Test that the Message object has the correct attributes
    assert example_message.id == MESSAGE_DICT.get('iid')
    assert example_message.team == MESSAGE_DICT.get('team')
    assert example_message.created == convert_timestamp(MESSAGE_DICT.get('ts'))
    assert example_message.user == example_user
    assert example_message.text == MESSAGE_DICT.get('text')
    assert example_message.type == MESSAGE_DICT.get('type')
    assert example_message.permalink == MESSAGE_DICT.get('permalink')
    assert example_message.blocks == MESSAGE_DICT.get('blocks')
    assert example_message.timestamp == MESSAGE_DICT.get('ts')
    assert example_message.conversation == example_conversation


def test_message_initialisation_succinct(example_message_succinct_values,
                                         example_user_succinct,
                                         example_conversation_succinct):
    # Test that the Message object is of the correct type, even when using succinct values
    assert isinstance(example_message_succinct_values, post.Message)

    # Test that the Message object has the correct attributes
    assert example_message_succinct_values.id == MESSAGE_DICT.get('iid')
    assert example_message_succinct_values.team == MESSAGE_DICT.get('team')
    assert example_message_succinct_values.created == convert_timestamp(MESSAGE_DICT.get('ts'))
    assert example_message_succinct_values.user == example_user_succinct
    assert example_message_succinct_values.text == MESSAGE_DICT.get('text')
    assert example_message_succinct_values.type == MESSAGE_DICT.get('type')
    assert example_message_succinct_values.permalink == MESSAGE_DICT.get('permalink')
    assert example_message_succinct_values.blocks == MESSAGE_DICT.get('blocks')
    assert example_message_succinct_values.timestamp == MESSAGE_DICT.get('ts')
    assert example_message_succinct_values.conversation == example_conversation_succinct


def test_message_initialisation_missing_fields(example_message_missing_fields):
    # Test that the Message object is of the correct type
    assert isinstance(example_message_missing_fields, post.Message)

    # Test that the Message object has the correct attributes
    assert example_message_missing_fields.id is MESSAGE_DICT_MISSING_FIELDS.get('iid')
    assert example_message_missing_fields.team is MESSAGE_DICT_MISSING_FIELDS.get('team')
    assert example_message_missing_fields.text is MESSAGE_DICT_MISSING_FIELDS.get('text')
    assert example_message_missing_fields.type is MESSAGE_DICT_MISSING_FIELDS.get('type')
    assert example_message_missing_fields.blocks is MESSAGE_DICT_MISSING_FIELDS.get('blocks')
    assert example_message_missing_fields.permalink is None
    assert example_message_missing_fields.timestamp is MESSAGE_DICT_MISSING_FIELDS.get('ts')
    assert example_message_missing_fields.conversation is None
    assert example_message_missing_fields.user is None


def test_message_field_type():
    # Test that the correct error is raised when id is not a string
    message_dict = MESSAGE_DICT.copy()
    message_dict['iid'] = 123
    with pytest.raises(TypeError):
        post.create_message_from_dict(message_dict)


def test_file_initialisation(example_file, example_user):
    # Test that the File object is of the correct type
    assert isinstance(example_file, post.File)

    # Test that the File object has the correct attributes
    assert example_file.id == FILE_DICT.get('id')
    assert example_file.created == convert_timestamp(FILE_DICT.get('created'))
    assert example_file.user == example_user
    assert example_file.name == FILE_DICT.get('name')
    assert example_file.title == FILE_DICT.get('title')
    assert example_file.mimetype == FILE_DICT.get('mimetype')
    assert example_file.filetype == FILE_DICT.get('filetype')
    assert example_file.pretty_type == FILE_DICT.get('pretty_type')
    assert example_file.editable == FILE_DICT.get('editable')
    assert example_file.size == FILE_DICT.get('size')
    assert example_file.mode == FILE_DICT.get('mode')
    assert example_file.is_public == FILE_DICT.get('is_public')
    assert example_file.public_url_shared == FILE_DICT.get('public_url_shared')
    assert example_file.url_private == FILE_DICT.get('url_private')
    assert example_file.url_private_download == FILE_DICT.get('url_private_download')
    assert example_file.permalink == FILE_DICT.get('permalink')
    assert example_file.permalink_public == FILE_DICT.get('permalink_public')
    assert example_file.shares == FILE_DICT.get('shares')


def test_file_initialisation_succinct(example_file_succinct_values, example_user_succinct):
    # Test that the File object is of the correct type, even when using succinct values
    assert isinstance(example_file_succinct_values, post.File)

    # Test that the File object has the correct attributes
    assert example_file_succinct_values.id == FILE_DICT.get('id')
    assert example_file_succinct_values.created == convert_timestamp(FILE_DICT.get('created'))
    assert example_file_succinct_values.user == example_user_succinct
    assert example_file_succinct_values.name == FILE_DICT.get('name')
    assert example_file_succinct_values.title == FILE_DICT.get('title')
    assert example_file_succinct_values.mimetype == FILE_DICT.get('mimetype')
    assert example_file_succinct_values.filetype == FILE_DICT.get('filetype')
    assert example_file_succinct_values.pretty_type == FILE_DICT.get('pretty_type')


def test_file_initialisation_missing_fields(example_file_missing_fields):
    # Test that the File object is of the correct type
    assert isinstance(example_file_missing_fields, post.File)

    # Test that the File object has the correct attributes
    assert example_file_missing_fields.id is FILE_DICT_MISSING_FIELDS.get('id')
    assert example_file_missing_fields.created is convert_timestamp(FILE_DICT_MISSING_FIELDS.get('created'))
    assert example_file_missing_fields.name is FILE_DICT_MISSING_FIELDS.get('name')
    assert example_file_missing_fields.title is FILE_DICT_MISSING_FIELDS.get('title')
    assert example_file_missing_fields.mimetype is FILE_DICT_MISSING_FIELDS.get('mimetype')
    assert example_file_missing_fields.filetype is FILE_DICT_MISSING_FIELDS.get('filetype')
    assert example_file_missing_fields.pretty_type is FILE_DICT_MISSING_FIELDS.get('pretty_type')
    assert example_file_missing_fields.editable is None
    assert example_file_missing_fields.size is None
    assert example_file_missing_fields.mode is None
    assert example_file_missing_fields.is_public is None
    assert example_file_missing_fields.public_url_shared is None
    assert example_file_missing_fields.url_private is None
    assert example_file_missing_fields.url_private_download is None
    assert example_file_missing_fields.permalink is None
    assert example_file_missing_fields.permalink_public is None
    assert example_file_missing_fields.shares is None
    assert example_file_missing_fields.user is None


def test_file_field_type():
    # Test that the correct error is raised when id is not a string
    file_dict = FILE_DICT.copy()
    file_dict['id'] = 123
    with pytest.raises(TypeError):
        post.create_file_from_dict(file_dict)
