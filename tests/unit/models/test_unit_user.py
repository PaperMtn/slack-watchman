import copy

import pytest

from fixtures import SlackMockData, mock_user, mock_user_succinct
from slack_watchman.models import user
from slack_watchman.utils import convert_timestamp


def test_user_initialisation(mock_user):
    # Test that the User object is of the correct type
    assert isinstance(mock_user, user.User)

    # Test that the User object has the correct attributes
    assert mock_user.id == SlackMockData.MOCK_USER_DICT.get('id')
    assert mock_user.name == SlackMockData.MOCK_USER_DICT.get('name')
    assert mock_user.email == SlackMockData.MOCK_USER_DICT.get('profile').get('email')
    assert mock_user.deleted == SlackMockData.MOCK_USER_DICT.get('deleted')
    assert mock_user.real_name == SlackMockData.MOCK_USER_DICT.get('real_name')
    assert mock_user.first_name == SlackMockData.MOCK_USER_DICT.get('profile').get('first_name')
    assert mock_user.last_name == SlackMockData.MOCK_USER_DICT.get('profile').get('last_name')
    assert mock_user.phone == SlackMockData.MOCK_USER_DICT.get('profile').get('phone')
    assert mock_user.skype == SlackMockData.MOCK_USER_DICT.get('profile').get('skype')
    assert mock_user.display_name == SlackMockData.MOCK_USER_DICT.get('profile').get('display_name')
    assert mock_user.tz == SlackMockData.MOCK_USER_DICT.get('tz')
    assert mock_user.tz_label == SlackMockData.MOCK_USER_DICT.get('tz_label')
    assert mock_user.tz_offset == SlackMockData.MOCK_USER_DICT.get('tz_offset')
    assert mock_user.is_admin == SlackMockData.MOCK_USER_DICT.get('is_admin')
    assert mock_user.is_owner == SlackMockData.MOCK_USER_DICT.get('is_owner')
    assert mock_user.is_bot == SlackMockData.MOCK_USER_DICT.get('is_bot')
    assert mock_user.updated == convert_timestamp(SlackMockData.MOCK_USER_DICT.get('updated'))
    assert mock_user.has_2fa == SlackMockData.MOCK_USER_DICT.get('has_2fa')
    assert mock_user.title == SlackMockData.MOCK_USER_DICT.get('profile').get('title')
    assert mock_user.is_primary_owner == SlackMockData.MOCK_USER_DICT.get('is_primary_owner')
    assert mock_user.is_restricted == SlackMockData.MOCK_USER_DICT.get('is_restricted')
    assert mock_user.is_ultra_restricted == SlackMockData.MOCK_USER_DICT.get('is_ultra_restricted')


def test_user_initialisation_missing_fields():
    # Create a User object with missing fields
    user_dict = {
        'id': 'U12345',
        'name': 'joe',
    }

    mock_user_object = user.create_from_dict(user_dict, verbose=True)

    # Test that the User object is of the correct type
    assert isinstance(mock_user_object, user.User)

    # Test that the User object has the correct attributes
    assert mock_user_object.id == 'U12345'
    assert mock_user_object.name == 'joe'
    assert mock_user_object.email is None
    assert mock_user_object.deleted is None
    assert mock_user_object.real_name is None
    assert mock_user_object.first_name is None
    assert mock_user_object.last_name is None
    assert mock_user_object.phone is None
    assert mock_user_object.skype is None
    assert mock_user_object.display_name is None
    assert mock_user_object.tz is None
    assert mock_user_object.tz_label is None
    assert mock_user_object.tz_offset is None
    assert mock_user_object.is_admin is None
    assert mock_user_object.is_owner is None
    assert mock_user_object.is_bot is None
    assert mock_user_object.updated is None
    assert mock_user_object.has_2fa is None
    assert mock_user_object.title is None
    assert mock_user_object.is_primary_owner is None
    assert mock_user_object.is_restricted is None
    assert mock_user_object.is_ultra_restricted is None


def test_user_field_types():
    # Test that the correct errors are raised when incorrect field types are provided.

    # Test that correct error is raised when id is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['id'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when email is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['email'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when deleted is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['deleted'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when real_name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['real_name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when first_name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['first_name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when last_name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['last_name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when phone is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['phone'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when skype is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['skype'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when display_name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['display_name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when tz is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['tz'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when tz_label is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['tz_label'] = {'timezone': 123}
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when tz_offset is not a string or int
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['tz_offset'] = [123]
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when title is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['title'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_admin is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_admin'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_owner is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_owner'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_primary_owner is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_primary_owner'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_restricted is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_restricted'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_ultra_restricted is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_ultra_restricted'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_bot is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_bot'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when has_2fa is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['has_2fa'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when updated is not an int, float, or string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['updated'] = {'key': 'value'}
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)


def test_user_succinct_initialisation(mock_user_succinct):
    # Test that the UserSuccinct object is of the correct type
    assert isinstance(mock_user_succinct, user.UserSuccinct)

    # Test that the UserSuccinct object has the correct attributes
    assert mock_user_succinct.id == SlackMockData.MOCK_USER_DICT.get('id')
    assert mock_user_succinct.name == SlackMockData.MOCK_USER_DICT.get('name')
    assert mock_user_succinct.display_name == SlackMockData.MOCK_USER_DICT.get('profile').get('display_name')
    assert mock_user_succinct.has_2fa == SlackMockData.MOCK_USER_DICT.get('has_2fa')
    assert mock_user_succinct.is_admin == SlackMockData.MOCK_USER_DICT.get('is_admin')
    assert mock_user_succinct.email == SlackMockData.MOCK_USER_DICT.get('profile').get('email')


def test_user_succinct_missing_fields():
    # Create a user dictionary with missing fields
    user_dict = {
        'id': 'U123',
        'name': 'John Doe'
    }

    # Create a UserSuccinct object from the user dictionary
    user_succinct = user.create_from_dict(user_dict, verbose=False)

    # Assert that the UserSuccinct object has the correct attributes
    assert user_succinct.id == 'U123'
    assert user_succinct.name == 'John Doe'
    assert user_succinct.display_name is None
    assert user_succinct.has_2fa is None
    assert user_succinct.is_admin is None
    assert user_succinct.email is None


def test_user_succinct_field_types():
    # Test that the correct errors are raised when incorrect field types are provided.

    # Test that correct error is raised when id is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['id'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when display_name is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['display_name'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when has_2fa is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['has_2fa'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when is_admin is not a boolean
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['is_admin'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)

    # Test that correct error is raised when email is not a string
    user_dict = copy.deepcopy(SlackMockData.MOCK_USER_DICT)
    user_dict['profile']['email'] = 123
    with pytest.raises(TypeError):
        test_user = user.create_from_dict(user_dict, verbose=True)
