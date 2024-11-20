from unittest.mock import patch, MagicMock

import pytest
import requests

from slack_watchman import exceptions
from slack_watchman.clients.slack_client import SlackClient


@patch('slack_watchman.clients.slack_client.requests.get')
def test_get_session_token_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = 'xoxb-1234567890-abcdef'
    mock_get.return_value = mock_response

    client = SlackClient(cookie='mock_cookie', url='https://slack.com')
    session_token = client._get_session_token()

    assert session_token == 'xoxb-1234567890-abcdef'
    mock_get.assert_called_with('https://slack.com', cookies=client.cookie_dict, timeout=60)


@patch('slack_watchman.clients.slack_client.requests.get')
def test_get_session_token_invalid_cookie(mock_get):
    mock_response = MagicMock()
    mock_response.text = ''
    mock_get.return_value = mock_response

    with pytest.raises(exceptions.InvalidCookieError):
        client = SlackClient(cookie='invalid_cookie', url='https://slack.com')


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_success(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'ok': True, 'data': 'some_value'}
    mock_request.return_value = mock_response

    client = SlackClient(token='mock_token')
    response = client._make_request('test_endpoint')

    assert response.json() == {'ok': True, 'data': 'some_value'}
    mock_request.assert_called_once_with(
        'GET',
        'https://slack.com/api/test_endpoint',
        params=None,
        data=None,
        cookies={},
        verify=True,
        timeout=30
    )


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_http_error(mock_request):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('HTTP Error')
    mock_request.return_value = mock_response

    client = SlackClient(token='mock_token')

    with pytest.raises(requests.exceptions.HTTPError):
        client._make_request('test_endpoint')


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_rate_limit(mock_request):
    # Simulate rate limit response
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {'ok': False, 'error': 'rate_limited'}
    mock_request.side_effect = [mock_response, MagicMock(status_code=200, json=lambda: {'ok': True})]

    client = SlackClient(token='mock_token')

    with patch('time.sleep', return_value=None) as mock_sleep:
        try:
            response = client._make_request('test_endpoint')
            assert response.status_code == 200
        except exceptions.SlackAPIError as e:
            assert 'rate_limited' in str(e)


@patch('slack_watchman.clients.slack_client.SlackClient._make_request')
def test_get_user_info(mock_make_request):
    mock_make_request.return_value.json.return_value = {'ok': True, 'user': {'id': 'U123', 'name': 'Test User'}}

    client = SlackClient(token='mock_token')
    user_info = client.get_user_info('U123')

    assert user_info == {'ok': True, 'user': {'id': 'U123', 'name': 'Test User'}}
    mock_make_request.assert_called_once_with('users.info', params={'user': 'U123'})


@patch('slack_watchman.clients.slack_client.SlackClient._make_request')
def test_get_conversation_info(mock_make_request):
    mock_make_request.return_value.json.return_value = {'ok': True, 'channel': {'id': 'C123', 'name': 'general'}}

    client = SlackClient(token='mock_token')
    conversation_info = client.get_conversation_info('C123')

    assert conversation_info == {'ok': True, 'channel': {'id': 'C123', 'name': 'general'}}
    mock_make_request.assert_called_once_with('conversations.info', params={'channel': 'C123'})


@patch('slack_watchman.clients.slack_client.SlackClient._make_request')
def test_get_workspace_info(mock_make_request):
    mock_make_request.return_value.json.return_value = {'ok': True, 'team': {'id': 'T123', 'name': 'Test Workspace'}}

    client = SlackClient(token='mock_token')
    workspace_info = client.get_workspace_info()

    assert workspace_info == {'ok': True, 'team': {'id': 'T123', 'name': 'Test Workspace'}}
    mock_make_request.assert_called_once_with('team.info')


@patch('slack_watchman.clients.slack_client.SlackClient._make_request')
def test_get_auth_test(mock_make_request):
    mock_make_request.return_value.json.return_value = {'ok': True, 'user_id': 'U123', 'team': 'Test Workspace'}

    client = SlackClient(token='mock_token')
    auth_test = client.get_auth_test()

    assert auth_test == {'ok': True, 'user_id': 'U123', 'team': 'Test Workspace'}
    mock_make_request.assert_called_once_with('auth.test')
