from unittest.mock import patch, MagicMock

import pytest
import requests

from slack_watchman import exceptions
from slack_watchman.clients.slack_client import SlackClient, _parse_retry_after


def _make_429_response(retry_after=None):
    """Helper to build a mock 429 response that triggers raise_for_status."""
    response = MagicMock()
    response.status_code = 429
    response.headers = {'Retry-After': retry_after} if retry_after is not None else {}
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        '429 Too Many Requests'
    )
    return response


def _make_ok_response(payload=None):
    """Helper to build a mock 200 response with an `ok: True` JSON body."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload or {'ok': True}
    return response


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


@patch('slack_watchman.clients.slack_client.requests.get')
def test_init_session_token_skips_workspace_lookup(mock_get):
    """When `session_token` and `cookie_dict` are supplied, the constructor
    must not hit the workspace URL to re-extract a session token. This is
    used to rebuild the client inside Pool worker processes without
    repeating the cookie -> session_token roundtrip."""
    client = SlackClient(
        url='https://example.slack.com',
        session_token='xoxc-already-have-this',
        cookie_dict={'d': 'pre-quoted-cookie'},
    )

    assert client.session_token == 'xoxc-already-have-this'
    assert client.cookie_dict == {'d': 'pre-quoted-cookie'}
    assert client.session.headers['Authorization'] == 'Bearer xoxc-already-have-this'
    mock_get.assert_not_called()


def test_init_cookie_dict_is_defensive_copy():
    """Mutating the dict supplied via `cookie_dict` after construction must
    not mutate the client's internal state."""
    incoming = {'d': 'value'}
    client = SlackClient(
        url='https://example.slack.com',
        session_token='xoxc-session',
        cookie_dict=incoming,
    )
    incoming['d'] = 'mutated'
    assert client.cookie_dict == {'d': 'value'}


def test_init_token_takes_precedence_over_session_token():
    """When both `token` and `session_token` are supplied, bearer-token auth
    wins (token takes the Authorization header)."""
    client = SlackClient(
        token='xoxp-bearer',
        session_token='xoxc-session',
    )
    assert client.session.headers['Authorization'] == 'Bearer xoxp-bearer'


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


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 90),
        ('30', 30),
        ('0', 0),
        ('not-a-number', 90),
        ('-5', 0),  # Negative values clamped to 0
        (15, 15),   # Already an int
    ],
)
def test_parse_retry_after(value, expected):
    """`_parse_retry_after` handles the value forms Slack and naive callers send."""
    assert _parse_retry_after(value) == expected


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_429_honours_retry_after(mock_request):
    """A 429 response with `Retry-After` set should sleep for that many seconds and retry."""
    mock_request.side_effect = [
        _make_429_response(retry_after='5'),
        _make_ok_response(),
    ]

    client = SlackClient(token='mock_token')

    with patch('slack_watchman.clients.slack_client.time.sleep') as mock_sleep:
        response = client._make_request('test_endpoint')

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(5)
    assert mock_request.call_count == 2


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_429_falls_back_when_retry_after_missing(mock_request):
    """No `Retry-After` header → fall back to the configured default (90s)."""
    mock_request.side_effect = [
        _make_429_response(retry_after=None),
        _make_ok_response(),
    ]

    client = SlackClient(token='mock_token')

    with patch('slack_watchman.clients.slack_client.time.sleep') as mock_sleep:
        response = client._make_request('test_endpoint')

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(90)


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_429_then_429_then_success(mock_request):
    """A second consecutive 429 must also be retried, not raised as HTTPError.

    Previously the retry path bypassed `_make_request` and called
    `self.session.request(...)` inline, so a second 429 propagated as an
    HTTPError and the result was lost.
    """
    mock_request.side_effect = [
        _make_429_response(retry_after='1'),
        _make_429_response(retry_after='2'),
        _make_ok_response(),
    ]

    client = SlackClient(token='mock_token')

    with patch('slack_watchman.clients.slack_client.time.sleep') as mock_sleep:
        response = client._make_request('test_endpoint')

    assert response.status_code == 200
    assert mock_request.call_count == 3
    assert mock_sleep.call_args_list[0].args == (1,)
    assert mock_sleep.call_args_list[1].args == (2,)


@patch('slack_watchman.clients.slack_client.requests.Session.request')
def test_make_request_429_retries_exhausted(mock_request):
    """Persistent 429s should eventually raise an informative HTTPError."""
    # Always return 429 — should exhaust retries.
    mock_request.side_effect = [_make_429_response(retry_after='1') for _ in range(10)]

    client = SlackClient(token='mock_token')

    with patch('slack_watchman.clients.slack_client.time.sleep'):
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            client._make_request('test_endpoint')

    assert 'retries exhausted' in str(excinfo.value)


def test_cursor_api_search_advances_cursor_on_empty_page():
    """`cursor_api_search` must advance the cursor every iteration, even when a page
    returns an empty `scope` list. The previous implementation only updated `cursor`
    inside the inner per-item loop, so an empty page left `cursor` stuck on the
    previous value and the while loop would re-request the same cursor forever."""
    pages = [
        {
            'ok': 'True',
            'members': [{'id': 'U1'}],
            'response_metadata': {'next_cursor': 'cursor-2'},
        },
        {
            'ok': 'True',
            'members': [],
            'response_metadata': {'next_cursor': 'cursor-3'},
        },
        {
            'ok': 'True',
            'members': [{'id': 'U2'}],
            'response_metadata': {'next_cursor': ''},
        },
    ]
    seen_cursors = []

    def fake_make_request(_url, params=None, **_kwargs):
        seen_cursors.append(params['cursor'])
        response = MagicMock()
        response.json.return_value = pages[len(seen_cursors) - 1]
        return response

    client = SlackClient(token='mock_token')
    with patch.object(client, '_make_request', side_effect=fake_make_request):
        results = client.cursor_api_search('users.list', 'members')

    assert results == [{'id': 'U1'}, {'id': 'U2'}]
    assert seen_cursors == ['', 'cursor-2', 'cursor-3']


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
