from fixtures import SlackMockData, mock_auth_vars
from slack_watchman.models import auth_vars


def test_auth_vars_initialisation(mock_auth_vars):
    # Test that the auth_vars object is initialised
    assert isinstance(mock_auth_vars, auth_vars.AuthVars)

    # Test that the auth_vars object has the correct attributes
    assert mock_auth_vars.token == SlackMockData.AUTH_VARS_DICT.get('token')
    assert mock_auth_vars.cookie == SlackMockData.AUTH_VARS_DICT.get('cookie')
    assert mock_auth_vars.url == SlackMockData.AUTH_VARS_DICT.get('url')
    assert mock_auth_vars.disabled_signatures == SlackMockData.AUTH_VARS_DICT.get('disabled_signatures')
    assert mock_auth_vars.cookie_auth == SlackMockData.AUTH_VARS_DICT.get('cookie_auth')
