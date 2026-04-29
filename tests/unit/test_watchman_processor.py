import hashlib
from unittest.mock import MagicMock, patch

import pytest

from slack_watchman import watchman_processor
from slack_watchman.clients.slack_client import SlackClient
from slack_watchman.models import user, auth_vars, signature
from slack_watchman.watchman_processor import (
    initiate_slack_connection,
    get_users,
    get_channels,
    find_messages,
    find_files,
    find_auth_information,
    _multipro_message_worker,
    _multipro_file_worker,
    _resolve_file_user,
)


@pytest.fixture
def mock_auth_vars():
    """Mock auth_vars fixture."""
    return auth_vars.AuthVars(
        token='mock_token',
        cookie='mock_cookie',
        url='https://slack.com',
        disabled_signatures=[],
        cookie_auth=False)


def test_initiate_slack_connection_token(mock_auth_vars):
    """Test initiate_slack_connection using token-based auth."""
    slack_client = initiate_slack_connection(mock_auth_vars)
    assert isinstance(slack_client, SlackClient)
    assert slack_client.token == 'mock_token'


@patch('slack_watchman.watchman_processor.SlackClient')
def test_initiate_slack_connection_cookie(mock_slack_client, mock_auth_vars):
    """Test initiate_slack_connection using cookie-based auth."""
    mock_auth_vars.cookie_auth = True
    slack_client = initiate_slack_connection(mock_auth_vars)
    mock_slack_client.assert_called_once_with(cookie='mock_cookie', url='https://slack.com')


@patch('slack_watchman.watchman_processor.SlackClient')
def test_get_users(mock_slack_client):
    """Test get_users function."""
    mock_slack = MagicMock()
    mock_slack.cursor_api_search.return_value = [
        {'id': 'U123', 'deleted': False},
        {'id': 'U456', 'deleted': True},  # Deleted user should be ignored
    ]
    mock_slack_client.return_value = mock_slack
    users = get_users(mock_slack, verbose=False)

    assert len(users) == 1
    assert isinstance(users[0], user.UserSuccinct)
    mock_slack.cursor_api_search.assert_called_once_with('users.list', 'members')


@patch('slack_watchman.watchman_processor.SlackClient')
def test_get_channels(mock_slack_client):
    """Test get_channels function."""
    mock_slack = MagicMock()
    mock_slack.cursor_api_search.return_value = [
        {'id': 'C123', 'name': 'general'},
        {'id': 'C456', 'name': 'random'},
    ]
    mock_slack_client.return_value = mock_slack
    channels = get_channels(mock_slack, verbose=False)

    assert len(channels) == 2
    mock_slack.cursor_api_search.assert_called_once_with('conversations.list', 'channels')


def _mock_manager_lists(mock_manager, results=None, potential_matches=None, errors=None):
    """Wire a `with multiprocessing.Manager() as m:` mock so `m.list()` returns
    the supplied lists in order (results, potential_matches, errors)."""
    inner = mock_manager.return_value.__enter__.return_value
    inner.list.side_effect = [
        [] if results is None else results,
        [] if potential_matches is None else potential_matches,
        [] if errors is None else errors,
    ]
    return inner


def _make_mock_slack(token='xoxp-token', url='https://example.slack.com',
                     session_token='xoxc-session', cookie_dict=None):
    """Build a minimal SlackClient-shaped mock with the auth attributes
    `_slack_init_args` reads."""
    mock_slack = MagicMock()
    mock_slack.token = token
    mock_slack.url = url
    mock_slack.session_token = session_token
    mock_slack.cookie_dict = {} if cookie_dict is None else cookie_dict
    return mock_slack


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages(mock_manager, mock_pool):
    """No-match runs log the empty-result message and return []."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager)

    result = find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    mock_logger.log.assert_any_call('INFO', 'No matches found after filtering')
    # Annotated `-> List[Dict]`: must be [], not None.
    assert result == []


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_returns_empty_list_on_exception(mock_manager, mock_pool):
    """When the outer block raises, `find_messages` still honours its
    `List[Dict]` annotation and returns []."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    mock_manager.side_effect = RuntimeError('manager exploded')

    result = find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    assert result == []
    critical_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'CRITICAL']
    assert len(critical_calls) == 1


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_logs_worker_errors(mock_manager, mock_pool):
    """find_messages logs an ERROR for each error captured by a worker."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager, errors=[{
        'signature': 'test_sig',
        'query': 'test_query',
        'error': "RuntimeError('upstream blew up')"
    }])

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    error_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'ERROR']
    assert len(error_calls) == 1
    msg = error_calls[0].args[1]
    assert 'test_sig' in msg
    assert 'test_query' in msg
    assert 'upstream blew up' in msg


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_uses_single_manager_context(mock_manager, mock_pool):
    """find_messages opens exactly one Manager context (and exits it) per call."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager)

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    assert mock_manager.call_count == 1
    assert mock_manager.return_value.__enter__.call_count == 1
    assert mock_manager.return_value.__exit__.call_count == 1


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_pool_initargs_carry_parent_credentials(mock_manager, mock_pool):
    """The pool initializer receives the parent client's token, url,
    session_token and cookie_dict, so each worker can rebuild a SlackClient
    without redoing the cookie -> session_token HTTP roundtrip."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack(
        token='xoxp-token',
        url='https://example.slack.com',
        session_token='xoxc-session',
        cookie_dict={'d': 'quoted-cookie'},
    )
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager)

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    pool_kwargs = mock_pool.call_args.kwargs
    assert pool_kwargs['initializer'] is watchman_processor._init_worker_client
    assert pool_kwargs['initargs'] == (
        'xoxp-token',
        'https://example.slack.com',
        'xoxc-session',
        {'d': 'quoted-cookie'},
    )


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_pool_size_is_capped(mock_manager, mock_pool):
    """A signature with many search strings does not spawn one process per
    string. The pool is capped at `_DEFAULT_POOL_SIZE`."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = [f'q{i}' for i in range(50)]

    _mock_manager_lists(mock_manager)

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    pool_kwargs = mock_pool.call_args.kwargs
    assert pool_kwargs['processes'] == watchman_processor._DEFAULT_POOL_SIZE


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages_pool_size_matches_short_query_list(mock_manager, mock_pool):
    """When there are fewer queries than the pool cap, only spawn one
    worker per query."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['q1', 'q2', 'q3']

    _mock_manager_lists(mock_manager)

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    pool_kwargs = mock_pool.call_args.kwargs
    assert pool_kwargs['processes'] == 3


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files(mock_manager, mock_pool):
    """No-match runs log the empty-result message and return []."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager)

    result = find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    mock_logger.log.assert_any_call('INFO', 'No files found after filtering')
    # Annotated `-> List[Dict]`: must be [], not None.
    assert result == []


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files_returns_empty_list_on_exception(mock_manager, mock_pool):
    """When the outer block raises, `find_files` still honours its
    `List[Dict]` annotation and returns []."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    mock_manager.side_effect = RuntimeError('manager exploded')

    result = find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    assert result == []
    critical_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'CRITICAL']
    assert len(critical_calls) == 1


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files_logs_worker_errors(mock_manager, mock_pool):
    """find_files logs an ERROR for each error captured by a worker."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager, errors=[{
        'signature': 'test_sig',
        'query': 'test_query',
        'error': "RuntimeError('upstream blew up')"
    }])

    find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    error_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'ERROR']
    assert len(error_calls) == 1
    msg = error_calls[0].args[1]
    assert 'test_sig' in msg
    assert 'test_query' in msg
    assert 'upstream blew up' in msg


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files_uses_single_manager_context(mock_manager, mock_pool):
    """find_files opens exactly one Manager context (and exits it) per call."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    _mock_manager_lists(mock_manager)

    find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_pool.assert_called_once()
    assert mock_manager.call_count == 1
    assert mock_manager.return_value.__enter__.call_count == 1
    assert mock_manager.return_value.__exit__.call_count == 1


@patch('slack_watchman.watchman_processor.multiprocessing.Pool')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files_pool_size_is_capped(mock_manager, mock_pool):
    """find_files also caps the pool at `_DEFAULT_POOL_SIZE`."""
    mock_logger = MagicMock()
    mock_slack = _make_mock_slack()
    mock_sig = MagicMock()
    mock_sig.search_strings = [f'q{i}' for i in range(50)]

    _mock_manager_lists(mock_manager)

    find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    pool_kwargs = mock_pool.call_args.kwargs
    assert pool_kwargs['processes'] == watchman_processor._DEFAULT_POOL_SIZE


def test_init_worker_client_constructs_slack_client_without_session_lookup(monkeypatch):
    """`_init_worker_client` must construct a SlackClient using the supplied
    session_token + cookie_dict, *without* hitting the workspace URL to
    re-extract a session token."""

    fetched = []

    def boom(self):
        fetched.append(self.url)
        raise AssertionError(
            '_init_worker_client must not call _get_session_token in workers'
        )

    monkeypatch.setattr(SlackClient, '_get_session_token', boom)

    watchman_processor._init_worker_client(
        token=None,
        url='https://example.slack.com',
        session_token='xoxc-session',
        cookie_dict={'d': 'quoted-cookie'},
    )
    try:
        assert watchman_processor._WORKER_SLACK_CLIENT is not None
        assert watchman_processor._WORKER_SLACK_CLIENT.session_token == 'xoxc-session'
        assert watchman_processor._WORKER_SLACK_CLIENT.cookie_dict == {'d': 'quoted-cookie'}
        assert watchman_processor._WORKER_SLACK_CLIENT.url == 'https://example.slack.com'
        assert fetched == []
    finally:
        watchman_processor._WORKER_SLACK_CLIENT = None


@patch('requests.get')
@patch('slack_watchman.watchman_processor.BeautifulSoup')
def test_find_auth_information(mock_bs, mock_requests):
    """Test find_auth_information function."""
    mock_response = MagicMock()
    mock_response.text = ("<html><div id='props_node' data-props='{\"teamDomain\": \"example\", \"isPaidTeam\": "
                          "true}'></div></html>")
    mock_requests.return_value = mock_response

    mock_soup = MagicMock()
    mock_props_node = MagicMock()
    mock_props_node.get.return_value = '{"teamDomain": "example", "isPaidTeam": true}'
    mock_soup.find.return_value = mock_props_node
    mock_bs.return_value = mock_soup

    auth_info = find_auth_information('https://example.slack.com')

    assert auth_info['team_name'] is None
    assert auth_info['paid_team'] is True
    assert auth_info['join_url'] == 'https://join.slack.com/t/example/signup'

    # The return type was annotated `Dict[str, List[str]] | None` but the
    # payload mixes lists, bools, strings and None — the annotation has
    # been widened to `Dict[str, Any] | None`. Lock that in by asserting
    # the returned dict really is heterogeneous.
    value_types = {type(v) for v in auth_info.values()}
    assert bool in value_types
    assert str in value_types
    assert list in value_types
    assert type(None) in value_types


def test_find_auth_information_no_props_node():
    """Test find_auth_information when no props node is found."""
    with patch('requests.get') as mock_requests:
        mock_response = MagicMock()
        mock_response.text = '<html></html>'
        mock_requests.return_value = mock_response

        result = find_auth_information('https://example.slack.com')
        assert result is None


def test_find_auth_information_returns_none_on_request_exception():
    """A network failure must not propagate. Pre-fix the unauthenticated
    scrape would raise out of `find_auth_information` and abort the
    entire authenticated scan in `__init__.py:311`."""
    import requests as _requests
    mock_logger = MagicMock()
    with patch('requests.get', side_effect=_requests.ConnectionError('boom')):
        result = find_auth_information('https://example.slack.com', logger=mock_logger)

    assert result is None
    warning_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'WARNING']
    assert len(warning_calls) == 1
    assert 'example.slack.com' in warning_calls[0].args[1]


@patch('slack_watchman.watchman_processor.BeautifulSoup')
@patch('requests.get')
def test_find_auth_information_returns_none_on_invalid_json(mock_requests, mock_bs):
    """A `data-props` blob that isn't valid JSON must return None
    instead of propagating `JSONDecodeError`."""
    mock_response = MagicMock()
    mock_response.text = '<html></html>'
    mock_requests.return_value = mock_response

    mock_props_node = MagicMock()
    mock_props_node.get.return_value = 'not-json{'
    mock_soup = MagicMock()
    mock_soup.find.return_value = mock_props_node
    mock_bs.return_value = mock_soup

    mock_logger = MagicMock()
    result = find_auth_information('https://example.slack.com', logger=mock_logger)

    assert result is None
    warning_calls = [c for c in mock_logger.log.call_args_list if c.args[0] == 'WARNING']
    assert len(warning_calls) == 1


def test_find_auth_information_returns_none_without_logger():
    """The logger argument is optional — failures still don't propagate
    when no logger is supplied (this preserves the existing test
    contract that passes only `domain_url`)."""
    import requests as _requests
    with patch('requests.get', side_effect=_requests.Timeout('slow')):
        result = find_auth_information('https://example.slack.com')

    assert result is None


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
def test_multipro_message_worker(mock_post, mock_conversation, mock_user):
    """Unit test for _multipro_message_worker function."""

    # Mock input data
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.patterns = [r'secret']

    query = 'test_query'
    verbose = False
    timeframe = '7d'

    # Mock Slack API message response
    mock_slack.page_api_search.return_value = [
        {'text': 'This contains a secret', 'user': 'U123', 'channel': {'id': 'C123'}},
        {'text': 'No match here', 'user': 'U456', 'channel': {'id': 'C456'}}
    ]

    # Mock user and conversation creation
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_conversation.create_from_dict.return_value = 'MockConversation'
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1234567890')

    # Mock multiprocessing lists
    results = []
    potential_matches = []

    # Run the function
    _multipro_message_worker(
        slack=mock_slack,
        sig=mock_sig,
        query=query,
        verbose=verbose,
        timeframe=timeframe,
        results=results,
        potential_matches=potential_matches
    )

    # Assertions
    assert len(potential_matches) == 1
    assert potential_matches[0] == 2  # Two messages were returned by Slack API

    assert len(results) == 1
    result = results[0]
    assert result['match_string'] == 'secret'
    assert result['message'] == mock_post.create_message_from_dict.return_value

    # Verify that user and conversation were created correctly
    mock_user.create_from_dict.assert_called_once_with(
        mock_slack.get_user_info.return_value.get.return_value,
        verbose
    )
    mock_conversation.create_from_dict.assert_called_once_with(
        mock_slack.get_conversation_info.return_value.get.return_value,
        verbose
    )

    # Verify that the correct watchman_id was created
    expected_watchman_id = hashlib.md5(f'secret.1234567890'.encode()).hexdigest()
    assert result['watchman_id'] == expected_watchman_id


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
def test_multipro_message_worker_compiles_patterns_once(
    mock_post, mock_conversation, mock_user
):
    """`re.compile` should run once per signature pattern, not once per
    (message, pattern) pair. Pre-fix the call sat inside the per-message
    loop, so a worker processing 100 messages with 3 patterns would
    compile 300 times instead of 3."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.patterns = [r'secret', r'token']

    mock_slack.page_api_search.return_value = [
        {'text': 'has a secret', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'has a token', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'nothing here', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'another secret', 'user': 'U1', 'channel': {'id': 'C1'}},
    ]
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_conversation.create_from_dict.return_value = 'MockConversation'
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1')

    with patch('slack_watchman.watchman_processor.re.compile',
               wraps=watchman_processor.re.compile) as mock_compile:
        _multipro_message_worker(
            slack=mock_slack,
            sig=mock_sig,
            query='test_query',
            verbose=False,
            timeframe='7d',
            results=[],
            potential_matches=[],
            errors=[],
        )

    assert mock_compile.call_count == len(mock_sig.patterns)


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
def test_multipro_message_worker_searches_text_once_per_pattern(
    mock_post, mock_conversation, mock_user
):
    """`Pattern.search` should be called once per (message, pattern), not
    twice. Pre-fix the worker called search() once for the truthy check
    and a second time on the matching path to extract `.group(0)`."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.patterns = [r'secret']

    # Two matching messages × one pattern × one search call each = 2.
    # Pre-fix this would have been 4 (2 calls per matching message).
    mock_slack.page_api_search.return_value = [
        {'text': 'has a secret here', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'another secret line', 'user': 'U1', 'channel': {'id': 'C1'}},
    ]
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_conversation.create_from_dict.return_value = 'MockConversation'
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1')

    real_compile = watchman_processor.re.compile
    compiled = []

    def tracking_compile(pattern):
        c = real_compile(pattern)
        wrapper = MagicMock(wraps=c)
        compiled.append(wrapper)
        return wrapper

    with patch('slack_watchman.watchman_processor.re.compile',
               side_effect=tracking_compile):
        _multipro_message_worker(
            slack=mock_slack,
            sig=mock_sig,
            query='test_query',
            verbose=False,
            timeframe='7d',
            results=[],
            potential_matches=[],
            errors=[],
        )

    total_searches = sum(c.search.call_count for c in compiled)
    assert total_searches == 2


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
@pytest.mark.parametrize(
    "missing_text_message",
    [
        {'user': 'U1', 'channel': {'id': 'C1'}},                  # 'text' key absent
        {'text': None, 'user': 'U1', 'channel': {'id': 'C1'}},    # 'text' explicitly None
        {'text': '', 'user': 'U1', 'channel': {'id': 'C1'}},      # 'text' empty string
    ],
    ids=['text_missing', 'text_none', 'text_empty'],
)
def test_multipro_message_worker_skips_messages_with_no_text(
    mock_post, mock_conversation, mock_user, missing_text_message
):
    """Messages with no text must not be regex-searched. Pre-fix the
    worker did `str(message.get('text'))`, which made `None` -> the
    literal string `'None'`; a permissive signature regex (here, the
    pattern `r'None'`) would then false-positive match a message that
    has no real text behind it."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.patterns = [r'None']

    mock_slack.page_api_search.return_value = [missing_text_message]
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_conversation.create_from_dict.return_value = 'MockConversation'
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1')

    results = []
    errors = []

    _multipro_message_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='test_query',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=[],
        errors=errors,
    )

    assert errors == []
    assert results == []
    # No user/channel resolution should happen for a skipped message.
    mock_slack.get_user_info.assert_not_called()
    mock_slack.get_conversation_info.assert_not_called()


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
@pytest.mark.parametrize(
    "channel_value",
    [
        None,                # channel is explicitly None
        {},                  # channel is present but empty
        {'id': None},        # channel.id is None
    ],
    ids=['channel_is_none', 'channel_is_empty', 'channel_id_is_none']
)
def test_multipro_message_worker_handles_missing_channel(
    mock_post, mock_conversation, mock_user, channel_value
):
    """Worker does not crash when 'channel' is missing/None or 'id' is None.

    Without the guard, `message.get('channel').get('id')` raises AttributeError,
    which (combined with the worker's outer try/except) would silently drop the
    rest of the worker's matches.
    """
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.patterns = [r'secret']

    mock_slack.page_api_search.return_value = [
        {'text': 'This contains a secret', 'user': 'U123', 'channel': channel_value},
    ]

    mock_user.create_from_dict.return_value = 'MockUser'
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1234567890')

    results = []
    potential_matches = []
    errors = []

    _multipro_message_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='test_query',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=potential_matches,
        errors=errors,
    )

    assert errors == []
    assert len(results) == 1
    # No conversation should be resolved when channel id is unavailable
    mock_conversation.create_from_dict.assert_not_called()
    mock_slack.get_conversation_info.assert_not_called()


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.conversation')
@patch('slack_watchman.watchman_processor.post')
def test_multipro_message_worker_caches_user_and_channel_lookups(
    mock_post, mock_conversation, mock_user
):
    """A worker that sees the same user/channel ID across multiple matches
    must only call `get_user_info` / `get_conversation_info` once per ID."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.patterns = [r'secret']

    # Three matches: U1/C1 appears twice, U2/C2 once. Expect 2 user.info
    # calls and 2 conversation.info calls (not 3 of each).
    mock_slack.page_api_search.return_value = [
        {'text': 'a secret', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'another secret', 'user': 'U1', 'channel': {'id': 'C1'}},
        {'text': 'one more secret', 'user': 'U2', 'channel': {'id': 'C2'}},
    ]
    mock_user.create_from_dict.side_effect = lambda d, v: f"User({d.get('id') or d})"
    mock_conversation.create_from_dict.side_effect = lambda d, v: f"Conv({d.get('id') or d})"
    mock_post.create_message_from_dict.return_value = MagicMock(timestamp='1')

    results = []
    _multipro_message_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='secret',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=[],
        errors=[],
    )

    assert len(results) == 3
    assert mock_slack.get_user_info.call_count == 2
    assert mock_slack.get_conversation_info.call_count == 2
    user_call_args = sorted(c.args[0] for c in mock_slack.get_user_info.call_args_list)
    channel_call_args = sorted(c.args[0] for c in mock_slack.get_conversation_info.call_args_list)
    assert user_call_args == ['U1', 'U2']
    assert channel_call_args == ['C1', 'C2']


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.post')
@pytest.mark.parametrize(
    "file_types",
    [['zip'], None],
    ids=['with_file_types', 'no_file_types'],
)
def test_multipro_file_worker_caches_user_lookups(mock_post, mock_user, file_types):
    """A worker that sees the same file owner across multiple matches must
    only call `get_user_info` once per user ID. Covers both the file_types
    and no-file_types branches."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.file_types = file_types

    mock_slack.page_api_search.return_value = [
        {'name': 'a.zip', 'filetype': 'zip', 'user': 'U1'},
        {'name': 'b.zip', 'filetype': 'zip', 'user': 'U1'},
        {'name': 'c.zip', 'filetype': 'zip', 'user': 'U2'},
    ]
    mock_user.create_from_dict.side_effect = lambda d, v: f"User({d.get('id') or d})"
    mock_post.create_file_from_dict.return_value = MagicMock(
        created='2024-01-01', permalink_public='https://example.com/file'
    )

    results = []
    _multipro_file_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='zip',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=[],
        errors=[],
    )

    assert len(results) == 3
    assert mock_slack.get_user_info.call_count == 2
    user_call_args = sorted(c.args[0] for c in mock_slack.get_user_info.call_args_list)
    assert user_call_args == ['U1', 'U2']


def test_multipro_message_worker_captures_exception():
    """Worker exceptions are appended to the shared errors list rather than propagating."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_slack.page_api_search.side_effect = RuntimeError('upstream blew up')

    results = []
    potential_matches = []
    errors = []

    _multipro_message_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='test_query',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=potential_matches,
        errors=errors,
    )

    assert results == []
    assert potential_matches == []
    assert len(errors) == 1
    assert errors[0]['signature'] == 'test_sig'
    assert errors[0]['query'] == 'test_query'
    assert 'upstream blew up' in errors[0]['error']


def test_multipro_message_worker_reraises_when_no_errors_list():
    """When no errors list is supplied (e.g. direct unit-test invocation), the exception propagates."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_slack.page_api_search.side_effect = RuntimeError('upstream blew up')

    with pytest.raises(RuntimeError, match='upstream blew up'):
        _multipro_message_worker(
            slack=mock_slack,
            sig=mock_sig,
            query='test_query',
            verbose=False,
            timeframe='7d',
            results=[],
            potential_matches=[],
        )


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.post')
@pytest.mark.parametrize(
    "file_types, expected_results_count, expected_potential_matches, expected_filetype",
    [
        (['zip'], 1, 2, 'zip'),  # File type provided
        (None, 1, 2, None)        # File type not provided
    ]
)
def test_multipro_file_worker(mock_post, mock_user, file_types, expected_results_count, expected_potential_matches, expected_filetype):
    """Parameterized unit test for _multipro_file_worker function."""

    # Mock input data
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.file_types = file_types

    query = '.zip'
    verbose = False
    timeframe = '7d'

    # Mock Slack API file response
    mock_slack.page_api_search.return_value = [
        {'name': 'Test Zip.zip', 'filetype': 'zip', 'user': 'U123'},
        {'name': 'Other File.doc', 'filetype': 'doc', 'user': 'U456'},  # Does not match file_types if provided
    ]

    # Mock user creation
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_post.create_file_from_dict.return_value = MagicMock(created='2024-01-01', permalink_public='https://example.com/file')

    # Mock multiprocessing lists
    results = []
    potential_matches = []

    # Run the function
    _multipro_file_worker(
        slack=mock_slack,
        sig=mock_sig,
        query=query,
        verbose=verbose,
        timeframe=timeframe,
        results=results,
        potential_matches=potential_matches
    )

    # Assertions
    assert len(potential_matches) == 1  # There should be one entry for the files searched
    assert potential_matches[0] == expected_potential_matches  # Two files were returned by Slack API

    assert len(results) == expected_results_count  # Only one file matches the type (zip) if file_types is provided
    result = results[0]
    assert result['file'] == mock_post.create_file_from_dict.return_value
    assert result['user'] == 'MockUser'

    # Verify that user was created correctly
    mock_user.create_from_dict.assert_called_once_with(
        mock_slack.get_user_info.return_value.get.return_value,
        verbose
    )

    # Verify that the correct watchman_id was created
    expected_watchman_id = hashlib.md5(f'2024-01-01.https://example.com/file'.encode()).hexdigest()
    assert result['watchman_id'] == expected_watchman_id


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.post')
@pytest.mark.parametrize(
    "file_dict, file_types",
    [
        ({'name': None, 'filetype': 'zip', 'user': 'U1'}, ['zip']),
        ({'name': 'something.zip', 'filetype': None, 'user': 'U1'}, ['zip']),
        ({'name': None, 'filetype': None, 'user': 'U1'}, ['zip']),
        ({'name': None, 'filetype': 'zip', 'user': 'U1'}, None),
        ({'filetype': 'zip', 'user': 'U1'}, ['zip']),  # 'name' key absent
        ({'name': 'something.zip', 'user': 'U1'}, ['zip']),  # 'filetype' key absent
    ],
    ids=[
        'name_none_with_filetypes',
        'filetype_none_with_filetypes',
        'both_none_with_filetypes',
        'name_none_no_filetypes',
        'name_missing_with_filetypes',
        'filetype_missing_with_filetypes',
    ]
)
def test_multipro_file_worker_handles_null_name_and_filetype(
    mock_post, mock_user, file_dict, file_types
):
    """File worker does not crash when 'name' or 'filetype' is None or missing.

    Slack files in deleted/redacted/tombstoned states can return null name
    or filetype. Without the guard, calling `.lower()` on None raises
    AttributeError, which (combined with the worker's outer try/except)
    silently drops the rest of the worker's matches.
    """
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.file_types = file_types

    mock_slack.page_api_search.return_value = [file_dict]
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_post.create_file_from_dict.return_value = MagicMock(
        created='2024-01-01', permalink_public='https://example.com/file'
    )

    results = []
    potential_matches = []
    errors = []

    _multipro_file_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='zip',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=potential_matches,
        errors=errors,
    )

    assert errors == []
    assert potential_matches == [1]
    # Files with null/missing name or filetype shouldn't match — but they also
    # shouldn't crash the worker.
    assert results == []


@patch('slack_watchman.watchman_processor.user')
@patch('slack_watchman.watchman_processor.post')
def test_multipro_file_worker_emits_one_result_per_file(mock_post, mock_user):
    """A file whose filetype substring-matches multiple `sig.file_types`
    entries should still produce exactly one entry on the shared results
    list. Without the fix, the per-file_type loop appended a duplicate
    result_dict for every matching file_type, which dedup later collapsed
    but only after wasting IPC and memory."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    # Both 'zip' and 'ip' substring-match the file's filetype 'zip'.
    mock_sig.file_types = ['zip', 'ip']

    mock_slack.page_api_search.return_value = [
        {'name': 'secrets.zip', 'filetype': 'zip', 'user': 'U1'},
    ]
    mock_user.create_from_dict.return_value = 'MockUser'
    mock_post.create_file_from_dict.return_value = MagicMock(
        created='2024-01-01', permalink_public='https://example.com/file'
    )

    results = []
    _multipro_file_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='zip',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=[],
        errors=[],
    )

    assert len(results) == 1


@patch('slack_watchman.watchman_processor.user')
def test_resolve_file_user_resolves_plain_id_in_both_branches(mock_user):
    """Both `_multipro_file_worker` branches now share `_resolve_file_user`,
    so a plain user ID resolves identically whether `sig.file_types` is set
    or not. This locks in the symmetry that issue #120 called out: the
    file_types branch previously had a defensive `is_dataclass` check that
    the no-file_types branch lacked, which meant the two paths could
    diverge on edge inputs. The asymmetric guard is gone and both branches
    fan in to the same helper."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_user.create_from_dict.side_effect = lambda d, v: f"User({d.get('id') or d})"
    file_dict = {'user': 'U1'}

    cache_a: dict = {}
    cache_b: dict = {}
    result_a = _resolve_file_user(mock_slack, file_dict, verbose=False, cache=cache_a)
    result_b = _resolve_file_user(mock_slack, file_dict, verbose=False, cache=cache_b)

    assert result_a == result_b
    assert mock_slack.get_user_info.call_count == 2
    assert all(c.args[0] == 'U1' for c in mock_slack.get_user_info.call_args_list)


def test_resolve_file_user_returns_none_without_lookup_when_user_missing():
    """Empty/missing `user` should short-circuit before any API call."""
    mock_slack = MagicMock(spec=SlackClient)

    assert _resolve_file_user(mock_slack, {}, verbose=False, cache={}) is None
    assert _resolve_file_user(mock_slack, {'user': None}, verbose=False, cache={}) is None
    assert _resolve_file_user(mock_slack, {'user': ''}, verbose=False, cache={}) is None
    mock_slack.get_user_info.assert_not_called()


def test_multipro_file_worker_captures_exception():
    """File worker exceptions are appended to the shared errors list rather than propagating."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.name = 'test_sig'
    mock_sig.file_types = None
    mock_slack.page_api_search.side_effect = RuntimeError('upstream blew up')

    results = []
    potential_matches = []
    errors = []

    _multipro_file_worker(
        slack=mock_slack,
        sig=mock_sig,
        query='test_query',
        verbose=False,
        timeframe='7d',
        results=results,
        potential_matches=potential_matches,
        errors=errors,
    )

    assert results == []
    assert potential_matches == []
    assert len(errors) == 1
    assert errors[0]['signature'] == 'test_sig'
    assert errors[0]['query'] == 'test_query'
    assert 'upstream blew up' in errors[0]['error']


def test_multipro_file_worker_reraises_when_no_errors_list():
    """When no errors list is supplied, the exception propagates."""
    mock_slack = MagicMock(spec=SlackClient)
    mock_sig = MagicMock(spec=signature.Signature)
    mock_sig.file_types = None
    mock_slack.page_api_search.side_effect = RuntimeError('upstream blew up')

    with pytest.raises(RuntimeError, match='upstream blew up'):
        _multipro_file_worker(
            slack=mock_slack,
            sig=mock_sig,
            query='test_query',
            verbose=False,
            timeframe='7d',
            results=[],
            potential_matches=[],
        )
