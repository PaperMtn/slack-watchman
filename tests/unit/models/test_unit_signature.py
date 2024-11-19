import copy

import pytest

from fixtures import SlackMockData, mock_signature
from slack_watchman.models import signature


def test_signature_initialisation(mock_signature):
    # Test that the signature object is initialised
    assert isinstance(mock_signature, signature.Signature)

    # Test that the signature object has the correct attributes
    assert mock_signature.name == SlackMockData.MOCK_SIGNATURE_DICT.get('name')
    assert mock_signature.id == SlackMockData.MOCK_SIGNATURE_DICT.get('id')
    assert mock_signature.status == SlackMockData.MOCK_SIGNATURE_DICT.get('status')
    assert mock_signature.author == SlackMockData.MOCK_SIGNATURE_DICT.get('author')
    assert mock_signature.date == SlackMockData.MOCK_SIGNATURE_DICT.get('date')
    assert mock_signature.description == SlackMockData.MOCK_SIGNATURE_DICT.get('description')
    assert mock_signature.severity == SlackMockData.MOCK_SIGNATURE_DICT.get('severity')
    assert mock_signature.watchman_apps == SlackMockData.MOCK_SIGNATURE_DICT.get('watchman_apps')
    assert mock_signature.scope == SlackMockData.MOCK_SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('scope')
    assert mock_signature.category == SlackMockData.MOCK_SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('category')
    assert mock_signature.file_types == SlackMockData.MOCK_SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('file_types')
    assert mock_signature.search_strings == SlackMockData.MOCK_SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('search_strings')


def test_field_type():
    # Test that correct error is raised when name is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['name'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when id is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['id'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when status is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['status'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when author is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['author'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when date is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['date'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when severity is not a string or int
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['severity'] = 5.0
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when watchman_apps is not a dict
    signature_dict_temp = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict_temp['watchman_apps'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when scope is not a list
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['watchman_apps']['slack_std']['category'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when search_strings is not a list
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['watchman_apps']['slack_std']['search_strings'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when patterns is not a list
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['patterns'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when version is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['version'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)

    # Test that correct error is raised when description is not a string
    signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    signature_dict['description'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)


def test_missing_field():
    temp_signature_dict = copy.deepcopy(SlackMockData.MOCK_SIGNATURE_DICT)
    del temp_signature_dict['name']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.name is None

    del temp_signature_dict['watchman_apps']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.watchman_apps is None
