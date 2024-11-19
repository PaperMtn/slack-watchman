import copy

import pytest

from fixtures import mock_workspace, SlackMockData
from slack_watchman.models import workspace


def test_workspace_initialisation(mock_workspace):
    # Test that the Workspace object is of the correct type
    assert isinstance(mock_workspace, workspace.Workspace)

    # Test that the Workspace object has the correct attributes
    assert mock_workspace.id == SlackMockData.MOCK_WORKSPACE_DICT.get('id')
    assert mock_workspace.name == SlackMockData.MOCK_WORKSPACE_DICT.get('name')
    assert mock_workspace.domain == SlackMockData.MOCK_WORKSPACE_DICT.get('domain')
    assert mock_workspace.url == SlackMockData.MOCK_WORKSPACE_DICT.get('url')
    assert mock_workspace.email_domain == SlackMockData.MOCK_WORKSPACE_DICT.get('email_domain')
    assert mock_workspace.is_verified == SlackMockData.MOCK_WORKSPACE_DICT.get('is_verified')
    assert mock_workspace.discoverable == SlackMockData.MOCK_WORKSPACE_DICT.get('discoverable')
    assert mock_workspace.enterprise_id == SlackMockData.MOCK_WORKSPACE_DICT.get('enterprise_id')
    assert mock_workspace.enterprise_domain == SlackMockData.MOCK_WORKSPACE_DICT.get('enterprise_domain')
    assert mock_workspace.enterprise_name == SlackMockData.MOCK_WORKSPACE_DICT.get('enterprise_name')


def test_workspace_initialisation_with_missing_fields(mock_workspace):
    # Test that the Workspace object is of the correct type
    temp_workspace_dict = {
        'name': 'test_workspace',
        'id': 'T1234567890'
    }

    mock_workspace = workspace.create_from_dict(temp_workspace_dict)

    assert isinstance(mock_workspace, workspace.Workspace)

    # Test that the Workspace object has the correct attributes
    assert mock_workspace.id == temp_workspace_dict.get('id')
    assert mock_workspace.name == temp_workspace_dict.get('name')
    assert mock_workspace.domain is None
    assert mock_workspace.url is None
    assert mock_workspace.email_domain is None
    assert mock_workspace.is_verified is None
    assert mock_workspace.discoverable is None
    assert mock_workspace.enterprise_id is None
    assert mock_workspace.enterprise_domain is None
    assert mock_workspace.enterprise_name is None


def test_field_type():
    # Test that the correct errors are raised when incorrect field types are provided.
    # This is only for the required fields

    # Test that correct error is raised when name is not a string
    workspace_dict = copy.deepcopy(SlackMockData.MOCK_WORKSPACE_DICT)
    workspace_dict['name'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)

    # Test that correct error is raised when id is not a string
    workspace_dict = copy.deepcopy(SlackMockData.MOCK_WORKSPACE_DICT)
    workspace_dict['id'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)

    # Test that correct error is raised when domain is not a string
    workspace_dict = copy.deepcopy(SlackMockData.MOCK_WORKSPACE_DICT)
    workspace_dict['domain'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)

    # Test that correct error is raised when url is not a string
    workspace_dict = copy.deepcopy(SlackMockData.MOCK_WORKSPACE_DICT)
    workspace_dict['url'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)

    # Test that correct error is raised when email_domain is not a string
    workspace_dict = copy.deepcopy(SlackMockData.MOCK_WORKSPACE_DICT)
    workspace_dict['email_domain'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)
