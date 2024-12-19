import pytest

from slack_watchman.exceptions import (
    MissingEnvVarError,
    MissingCookieEnvVarError,
    MisconfiguredConfFileError,
    MissingConfigVariable,
    InvalidCookieError,
    SlackScopeError,
    SlackAPIError,
    SlackAPIRateLimit,
    MissingCookieAuthError
)


def test_missing_env_var_error():
    env_var = 'TEST_ENV_VAR'
    exc = MissingEnvVarError(env_var)
    assert exc.env_var == env_var
    assert exc.message == f'Missing Environment Variable: {env_var}'
    with pytest.raises(MissingEnvVarError, match=f'Missing Environment Variable: {env_var}'):
        raise exc


def test_missing_cookie_env_var_error():
    env_var = 'COOKIE_ENV_VAR'
    exc = MissingCookieEnvVarError(env_var)
    assert exc.env_var == env_var
    assert exc.message == (
        f'Cookie authentication has been selected, but missing '
        f'required environment variable: {env_var}'
    )
    with pytest.raises(MissingCookieEnvVarError, match=f'Cookie authentication has been selected, but missing'):
        raise exc


def test_misconfigured_conf_file_error():
    exc = MisconfiguredConfFileError()
    assert exc.message == "The file watchman.conf doesn't contain config details for Slack Watchman"
    with pytest.raises(MisconfiguredConfFileError, match="The file watchman.conf doesn't contain config details"):
        raise exc


def test_missing_config_variable():
    config_entry = 'test_entry'
    exc = MissingConfigVariable(config_entry)
    assert exc.config_entry == config_entry
    assert exc.message == f'Missing variable in the config file: {config_entry}'
    with pytest.raises(MissingConfigVariable, match=f'Missing variable in the config file: {config_entry}'):
        raise exc


def test_invalid_cookie_error():
    domain = 'example.com'
    exc = InvalidCookieError(domain)
    assert exc.message == (
        "The cookie may not be valid or, if it is valid,"
        f" the user it belongs to cant authenticate to the Slack workspace {domain}"
    )
    with pytest.raises(InvalidCookieError, match='The cookie may not be valid or, if it is valid'):
        raise exc


def test_slack_scope_error():
    scope = 'users:read'
    exc = SlackScopeError(scope)
    assert exc.scope == scope
    assert exc.message == f'Slack API token is missing the required scope: {scope}'
    with pytest.raises(SlackScopeError, match=f'Slack API token is missing the required scope: {scope}'):
        raise exc


def test_slack_api_error():
    error_message = 'invalid_auth'
    exc = SlackAPIError(error_message)
    assert exc.error_message == error_message
    assert exc.message == f'Slack API error: {error_message}'
    with pytest.raises(SlackAPIError, match=f'Slack API error: {error_message}'):
        raise exc


def test_slack_api_rate_limit():
    exc = SlackAPIRateLimit()
    assert exc.message == 'Slack API rate limit reached - cooling off'
    with pytest.raises(SlackAPIRateLimit, match='Slack API rate limit reached - cooling off'):
        raise exc


def test_missing_cookie_auth_error():
    exc = MissingCookieAuthError()
    assert exc.message == (
        'Cookie authentication has been selected, but missing no authentication data '
        'has been provided. Please set the environment variables SLACK_WATCHMAN_COOKIE and '
        'SLACK_WATCHMAN_URL'
    )
    with pytest.raises(MissingCookieAuthError, match='Cookie authentication has been selected, but missing'):
        raise exc
