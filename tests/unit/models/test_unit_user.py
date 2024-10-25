import pytest
from slack_watchman.models import user

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

@pytest.fixture
def example_user():
    return user.create_from_dict(USER_DICT, verbose=True)


@pytest.fixture
def example_user_succinct():
    return user.create_from_dict(USER_DICT, verbose=False)


def test_user_initialisation(example_user):

    # Test that the User object is of the correct type
    assert isinstance(example_user, user.User)

    # Test that the User object has the correct attributes
    assert example_user.id == USER_DICT.get('id')
    assert example_user.name == USER_DICT.get('name')
    assert example_user.deleted == USER_DICT.get('deleted')
    assert example_user.real_name == USER_DICT.get('real_name')
    assert example_user.tz == USER_DICT.get('tz')
    assert example_user.tz_label == USER_DICT.get('tz_label')
    assert example_user.tz_offset == USER_DICT.get('tz_offset')
    assert example_user.title == USER_DICT.get('profile').get('title')
    assert example_user.phone == USER_DICT.get('profile').get('phone')
    assert example_user.skype == USER_DICT.get('profile').get('skype')
    assert example_user.display_name == USER_DICT.get('profile').get('display_name')
    assert example_user.email == USER_DICT.get('profile').get('email')
    assert example_user.first_name == USER_DICT.get('profile').get('first_name')
    assert example_user.last_name == USER_DICT.get('profile').get('last_name')
    assert example_user.is_admin == USER_DICT.get('is_admin')
    assert example_user.is_owner == USER_DICT.get('is_owner')
    assert example_user.is_primary_owner == USER_DICT.get('is_primary_owner')
    assert example_user.is_restricted == USER_DICT.get('is_restricted')
    assert example_user.is_ultra_restricted == USER_DICT.get('is_ultra_restricted')
    assert example_user.is_bot == USER_DICT.get('is_bot')
    assert example_user.updated == user.convert_timestamp(USER_DICT.get('updated'))
    assert example_user.has_2fa == USER_DICT.get('has_2fa')


def test_user_succinct_initialisation(example_user_succinct):

    # Test that the UserSuccinct object is of the correct type
    assert isinstance(example_user_succinct, user.UserSuccinct)

    # Test that the UserSuccinct object has the correct attributes
    assert example_user_succinct.id == USER_DICT.get('id')
    assert example_user_succinct.name == USER_DICT.get('name')
    assert example_user_succinct.display_name == USER_DICT.get('profile').get('display_name')
    assert example_user_succinct.has_2fa == USER_DICT.get('has_2fa')
    assert example_user_succinct.is_admin == USER_DICT.get('is_admin')
    assert example_user_succinct.email == USER_DICT.get('profile').get('email')


def test_user_creation_with_missing_fields():
    # Test that a User object is created
    user_obj = user.create_from_dict(USER_SUCCINCT_DICT, verbose=True)

    # Test that the User object is of the correct type
    assert isinstance(user_obj, user.User)

    # Test that the User object has the correct attributes
    assert user_obj.id == USER_SUCCINCT_DICT.get('id')
    assert user_obj.name == USER_SUCCINCT_DICT.get('name')
    assert user_obj.deleted is None
    assert user_obj.real_name is None
    assert user_obj.tz is None
    assert user_obj.tz_label is None
    assert user_obj.tz_offset is None
