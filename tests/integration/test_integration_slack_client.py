import os

import pytest

from slack_watchman.clients.slack_client import SlackClient


@pytest.fixture
def slack_client():
    """Fixture to create a SlackClient instance using environment variables."""
    token = os.getenv('INT_TEST_SLACK_API_TOKEN')
    url = os.getenv('INT_TEST_SLACK_WORKSPACE_URL')
    cookie = os.getenv('INT_TEST_SLACK_API_COOKIE')
    return SlackClient(token=token, url=url, cookie=cookie)


@pytest.mark.integration
def test_get_user_info_integration(slack_client):
    """Integration test for getting user info from Slack."""
    user_id = os.getenv('INT_TEST_SLACK_TEST_USER_ID')
    if not user_id:
        pytest.skip('INT_TEST_SLACK_TEST_USER_ID environment variable not set')

    user_info = slack_client.get_user_info(user_id)
    assert user_info.get('ok') is True
    assert user_info.get('user').get('id') == user_id


@pytest.mark.integration
def test_get_conversation_info_integration(slack_client):
    """Integration test for getting conversation info from Slack."""
    conversation_id = os.getenv('INT_TEST_SLACK_TEST_CONVERSATION_ID')
    if not conversation_id:
        pytest.skip('INT_TEST_SLACK_TEST_CONVERSATION_ID environment variable not set')

    conversation_info = slack_client.get_conversation_info(conversation_id)
    assert conversation_info.get('ok') is True
    assert conversation_info.get('channel').get('id') == conversation_id


@pytest.mark.integration
def test_get_workspace_info_integration(slack_client):
    """Integration test for getting workspace info from Slack."""
    workspace_info = slack_client.get_workspace_info()
    assert workspace_info.get('ok') is True
    assert 'team' in workspace_info


@pytest.mark.integration
def test_get_auth_test_integration(slack_client):
    """Integration test for auth test in Slack."""
    auth_test = slack_client.get_auth_test()
    assert auth_test.get('ok') is True
    assert 'user_id' in auth_test
    assert 'team' in auth_test


@pytest.mark.integration
def test_cursor_api_search_integration(slack_client):
    """Integration test for cursor-based search."""
    results = slack_client.cursor_api_search('conversations.list', 'channels')
    assert isinstance(results, list)
    assert len(results) > 0
    assert 'id' in results[0]


@pytest.mark.integration
def test_page_api_search_integration(slack_client):
    """Integration test for page-based search."""
    results = slack_client.page_api_search(
        query='test',
        url='search.messages',
        scope='messages',
        timeframe='30d'
    )
    assert isinstance(results, list)


if __name__ == '__main__':
    pytest.main()
