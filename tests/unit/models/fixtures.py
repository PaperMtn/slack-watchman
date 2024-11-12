import pytest

from slack_watchman.models import (
    signature
)


class SlackMockData:
    SIGNATURE_DICT = {
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


@pytest.fixture
def mock_signature():
    return signature.create_from_dict(SlackMockData.SIGNATURE_DICT)
