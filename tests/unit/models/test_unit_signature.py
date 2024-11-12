import pytest
from slack_watchman.models import signature
from fixtures import SlackMockData, mock_signature


def test_signature_initialisation(mock_signature):
    # Test that the signature object is initialised
    assert isinstance(mock_signature, signature.Signature)

    # Test that the signature object has the correct attributes
    assert mock_signature.name == SlackMockData.SIGNATURE_DICT.get('name')
    assert mock_signature.id == SlackMockData.SIGNATURE_DICT.get('id')
    assert mock_signature.status == SlackMockData.SIGNATURE_DICT.get('status')
    assert mock_signature.author == SlackMockData.SIGNATURE_DICT.get('author')
    assert mock_signature.date == SlackMockData.SIGNATURE_DICT.get('date')
    assert mock_signature.description == SlackMockData.SIGNATURE_DICT.get('description')
    assert mock_signature.severity == SlackMockData.SIGNATURE_DICT.get('severity')
    assert mock_signature.watchman_apps == SlackMockData.SIGNATURE_DICT.get('watchman_apps')
    assert mock_signature.category == SlackMockData.SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('category')


def test_field_type():
    # Test that correct error is raised when name is not a string
    signature_dict = SlackMockData.SIGNATURE_DICT
    signature_dict['name'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)


def test_missing_field():
    temp_signature_dict = SlackMockData.SIGNATURE_DICT.copy()
    del temp_signature_dict['name']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.name is None

    del temp_signature_dict['watchman_apps']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.watchman_apps is None
