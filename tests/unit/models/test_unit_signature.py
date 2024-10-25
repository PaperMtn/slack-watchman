import pytest
from slack_watchman.models import signature

SIGNATURE_DICT = {
    'name': 'Akamai API Access Tokens',
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
def example_signature():
    return signature.create_from_dict(SIGNATURE_DICT)


def test_signature_initialisation(example_signature):
    # Test that the signature object is initialised
    assert isinstance(example_signature, signature.Signature)

    # Test that the signature object has the correct attributes
    assert example_signature.name == SIGNATURE_DICT.get('name')
    assert example_signature.status == SIGNATURE_DICT.get('status')
    assert example_signature.author == SIGNATURE_DICT.get('author')
    assert example_signature.date == SIGNATURE_DICT.get('date')
    assert example_signature.description == SIGNATURE_DICT.get('description')
    assert example_signature.severity == SIGNATURE_DICT.get('severity')
    assert example_signature.watchman_apps == SIGNATURE_DICT.get('watchman_apps')
    assert example_signature.category == SIGNATURE_DICT.get('watchman_apps').get('slack_std').get('category')


def test_field_type():
    # Test that correct error is raised when name is not a string
    signature_dict = SIGNATURE_DICT
    signature_dict['name'] = 123
    with pytest.raises(TypeError):
        test_signature = signature.create_from_dict(signature_dict)


def test_missing_field():
    temp_signature_dict = SIGNATURE_DICT.copy()
    del temp_signature_dict['name']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.name is None

    del temp_signature_dict['watchman_apps']
    test_signature = signature.create_from_dict(temp_signature_dict)
    assert test_signature.watchman_apps is None
