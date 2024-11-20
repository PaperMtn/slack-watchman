import copy

import pytest

from slack_watchman.models import (
    signature,
    auth_vars,
    workspace,
    user,
    conversation,
    post
)


class SlackMockData:
    MOCK_SIGNATURE_DICT = {
        'name': 'Akamai API Access Tokens',
        'id': 'akamai_api_access_tokens',
        'status': 'enabled',
        'author': 'PaperMtn',
        'date': '2023-12-22',
        'description': 'Detects exposed Akamai API Access tokens',
        'severity': '90',
        'notes': None,
        'references': None,
        'watchman_apps': {
            'slack_std': {
                'category': 'secrets',
                'scope': [
                    'messages'
                ],
                'file_types': None,
                'search_strings': [
                    'akab-'
                ]
            }
        },
        'test_cases': {
            'match_cases': [
                'client_token: akab-rWdcwwASNbe9fcGk-00qwecOueticOXxA'
            ],
            'fail_cases': [
                'host: akab-fakehost.akamaiapis.net'
            ]
        },
        'patterns': [
            'akab-[0-9a-zA-Z]{16}-[0-9a-zA-Z]{16}'
        ]
    }

    MOCK_AUTH_VARS_DICT = {
        'token': 'xoxp-1234',
        'cookie': 'xoxd-1234',
        'url': 'https://slack.com',
        'disabled_signatures': ['tokens_generic_access_tokens', 'tokens_generic_bearer_tokens'],
        'cookie_auth': True
    }

    MOCK_WORKSPACE_DICT = {
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

    MOCK_CONVERSATION_DICT = {
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

    MOCK_USER_DICT = {
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

    MOCK_MESSAGE_DICT = {
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

    MOCK_FILE_DICT = {
        'id': 'F1234567890',
        'created': 1643723400,
        'user': MOCK_USER_DICT,
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


@pytest.fixture
def mock_signature():
    return signature.create_from_dict(SlackMockData.MOCK_SIGNATURE_DICT)


@pytest.fixture
def mock_auth_vars():
    return auth_vars.AuthVars(**SlackMockData.MOCK_AUTH_VARS_DICT)


@pytest.fixture
def mock_workspace():
    return workspace.create_from_dict(SlackMockData.MOCK_WORKSPACE_DICT)


@pytest.fixture
def mock_conversation():
    return conversation.create_from_dict(SlackMockData.MOCK_CONVERSATION_DICT, verbose=True)


@pytest.fixture
def mock_conversation_succinct():
    return conversation.create_from_dict(SlackMockData.MOCK_CONVERSATION_DICT, verbose=False)


@pytest.fixture
def mock_user():
    return user.create_from_dict(SlackMockData.MOCK_USER_DICT, verbose=True)


@pytest.fixture
def mock_user_succinct():
    return user.create_from_dict(SlackMockData.MOCK_USER_DICT, verbose=False)


@pytest.fixture
def mock_message(mock_user, mock_conversation):
    message_dict = copy.deepcopy(SlackMockData.MOCK_MESSAGE_DICT)
    message_dict['user'] = mock_user
    message_dict['conversation'] = mock_conversation
    return post.create_message_from_dict(message_dict)


@pytest.fixture
def mock_file(mock_user):
    file_dict = copy.deepcopy(SlackMockData.MOCK_FILE_DICT)
    file_dict['user'] = mock_user
    return post.create_file_from_dict(file_dict)
