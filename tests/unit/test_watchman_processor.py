import hashlib
from unittest.mock import MagicMock, patch

import pytest

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
    _multipro_file_worker
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


@patch('slack_watchman.watchman_processor.multiprocessing.Process')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_messages(mock_manager, mock_process):
    """Test find_messages function."""
    mock_logger = MagicMock()
    mock_slack = MagicMock()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    mock_manager.return_value.list.return_value = []

    find_messages(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_process.assert_called_once()
    mock_logger.log.assert_any_call('INFO', 'No matches found after filtering')


@patch('slack_watchman.watchman_processor.multiprocessing.Process')
@patch('slack_watchman.watchman_processor.multiprocessing.Manager')
def test_find_files(mock_manager, mock_process):
    """Test find_files function."""
    mock_logger = MagicMock()
    mock_slack = MagicMock()
    mock_sig = MagicMock()
    mock_sig.search_strings = ['test_query']

    mock_manager.return_value.list.return_value = []

    find_files(mock_slack, mock_logger, mock_sig, verbose=False, timeframe='7d')

    mock_process.assert_called_once()
    mock_logger.log.assert_any_call('INFO', 'No files found after filtering')


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


def test_find_auth_information_no_props_node():
    """Test find_auth_information when no props node is found."""
    with patch('requests.get') as mock_requests:
        mock_response = MagicMock()
        mock_response.text = '<html></html>'
        mock_requests.return_value = mock_response

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
