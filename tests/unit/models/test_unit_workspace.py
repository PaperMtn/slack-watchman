import pytest
from slack_watchman.models import workspace

WORKSPACE_ONE_DICT = {
    'id': 'T1234567890',
    'name': 'Example Workspace',
    'domain': 'example.com',
    'url': 'https://example.com',
    'email_domain': 'example.com',
    'is_verified': True,
    'discoverable': False,
    'enterprise_id': 'E1234567890',
    'enterprise_domain': 'example.enterprise.com',
    'enterprise_name': 'Example Enterprise',
}

WORKSPACE_MISSING_FIELDS_DICT = {
    'id': 'T1234567890',
    'name': 'Example Workspace',
}


@pytest.fixture
def example_workspace_one():
    return workspace.create_from_dict(WORKSPACE_ONE_DICT)


@pytest.fixture
def example_workspace_missing_fields():
    return workspace.create_from_dict(WORKSPACE_MISSING_FIELDS_DICT)


def test_workspace_initialisation(example_workspace_one):
    # Test that the Workspace object is of the correct type
    assert isinstance(example_workspace_one, workspace.Workspace)

    # Test that the Workspace object has the correct attributes
    assert example_workspace_one.id == WORKSPACE_ONE_DICT.get('id')
    assert example_workspace_one.name == WORKSPACE_ONE_DICT.get('name')
    assert example_workspace_one.domain == WORKSPACE_ONE_DICT.get('domain')
    assert example_workspace_one.url == WORKSPACE_ONE_DICT.get('url')
    assert example_workspace_one.email_domain == WORKSPACE_ONE_DICT.get('email_domain')
    assert example_workspace_one.is_verified == WORKSPACE_ONE_DICT.get('is_verified')
    assert example_workspace_one.discoverable == WORKSPACE_ONE_DICT.get('discoverable')
    assert example_workspace_one.enterprise_id == WORKSPACE_ONE_DICT.get('enterprise_id')
    assert example_workspace_one.enterprise_domain == WORKSPACE_ONE_DICT.get('enterprise_domain')
    assert example_workspace_one.enterprise_name == WORKSPACE_ONE_DICT.get('enterprise_name')


def test_workspace_initialisation_with_missing_fields(example_workspace_missing_fields):
    # Test that the Workspace object is of the correct type
    assert isinstance(example_workspace_missing_fields, workspace.Workspace)

    # Test that the Workspace object has the correct attributes
    assert example_workspace_missing_fields.id == WORKSPACE_MISSING_FIELDS_DICT.get('id')
    assert example_workspace_missing_fields.name == WORKSPACE_MISSING_FIELDS_DICT.get('name')
    assert example_workspace_missing_fields.domain is None
    assert example_workspace_missing_fields.url is None
    assert example_workspace_missing_fields.email_domain is None
    assert example_workspace_missing_fields.is_verified is None
    assert example_workspace_missing_fields.discoverable is None
    assert example_workspace_missing_fields.enterprise_id is None
    assert example_workspace_missing_fields.enterprise_domain is None
    assert example_workspace_missing_fields.enterprise_name is None


def test_field_type():
    # Test that correct error is raised when name is not a string
    workspace_dict = WORKSPACE_ONE_DICT
    workspace_dict['name'] = 123
    with pytest.raises(TypeError):
        test_workspace = workspace.create_from_dict(workspace_dict)


def test_default_values(example_workspace_missing_fields):
    # Test that default fields are correctly applied
    assert example_workspace_missing_fields.is_verified is None
    assert example_workspace_missing_fields.discoverable is None
    assert example_workspace_missing_fields.enterprise_id is None
    assert example_workspace_missing_fields.enterprise_domain is None
    assert example_workspace_missing_fields.enterprise_name is None
