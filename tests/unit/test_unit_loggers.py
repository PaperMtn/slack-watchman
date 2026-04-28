from unittest.mock import MagicMock, patch, mock_open

import pytest

from slack_watchman.loggers import StdoutLogger, JSONLogger, export_csv, init_logger


@pytest.fixture
def mock_stdout_logger():
    """Fixture for StdoutLogger."""
    return StdoutLogger(debug=True)


@pytest.fixture
def mock_json_logger():
    """Fixture for JSONLogger."""
    return JSONLogger(debug=True)


@patch('sys.stdout.write', autospec=True)
def test_stdout_logger_log(mock_write, mock_stdout_logger):
    """Test logging functionality of StdoutLogger."""
    mock_stdout_logger.log('INFO', 'Test Message')
    # Extract the formatted output for assertion
    formatted_call = next(call for call in mock_write.mock_calls if 'Test Message' in str(call))
    assert 'Test Message' in str(formatted_call)


def test_stdout_logger_canvas_uses_canvas_level(mock_stdout_logger):
    """Canvas notify_type must dispatch to log_to_stdout with msg_level='CANVAS', not 'USER'."""
    canvas_payload = {
        'channel_name': 'general',
        'canvas_url': 'https://example.slack.com/canvases/abc',
    }
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', canvas_payload, notify_type='canvas')
        mock_log_to_stdout.assert_called_once()
        _, msg_level = mock_log_to_stdout.call_args[0]
        assert msg_level == 'CANVAS'


def test_stdout_logger_file_result_with_no_user(mock_stdout_logger):
    """File results where 'user' is None must not crash with AttributeError."""
    file_result = {
        'file': {
            'created': '2026-04-28',
            'name': 'secret.txt',
            'url_private_download': 'https://example.slack.com/files/private',
            'permalink_public': 'https://example.slack.com/files/public',
        },
        'user': None,
        'match_string': 'AKIAxxxx',
    }
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', file_result, notify_type='result')
        mock_log_to_stdout.assert_called_once()
        formatted_message, _ = mock_log_to_stdout.call_args[0]
        assert 'POST_TYPE: File' in formatted_message


def test_json_logger_log(mock_json_logger):
    """Test logging functionality of JSONLogger."""
    with patch.object(mock_json_logger.logger, 'info') as mock_info:
        mock_json_logger.log('INFO', 'Test JSON')
        # Validate the JSON-formatted log
        mock_info.assert_called_once()
        logged_message = mock_info.call_args[0][0]
        assert 'Test JSON' in logged_message


@patch('builtins.open', new_callable=mock_open)
@patch('csv.DictWriter')
def test_export_csv(mock_dict_writer, mock_open_file):
    """Test export_csv function."""
    class MockData:
        """Mock dataclass."""
        def __init__(self, id, name):
            self.id = id
            self.name = name

    mock_data = [MockData(id=1, name='Test1'), MockData(id=2, name='Test2')]

    mock_writer_instance = MagicMock()
    mock_dict_writer.return_value = mock_writer_instance

    # Run the export_csv function
    export_csv('test', mock_data)

    # Verify that open was called correctly with the filename 'test.csv'
    # mock_open_file.assert_called_once_with('test.csv', 'w', encoding='utf-8')
    # mock_dict_writer.assert_called_once()
    # mock_writer_instance.writeheader.assert_called_once()
    # assert mock_writer_instance.writerow.call_count == len(mock_data)


def test_init_logger_stdout():
    """Test init_logger function for StdoutLogger."""
    logger = init_logger(logging_type='stdout', debug=True)
    assert isinstance(logger, StdoutLogger)


def test_init_logger_json():
    """Test init_logger function for JSONLogger."""
    logger = init_logger(logging_type='json', debug=True)
    assert isinstance(logger, JSONLogger)


def test_init_logger_default():
    """Test init_logger function for default logger."""
    logger = init_logger(logging_type=None, debug=False)
    assert isinstance(logger, StdoutLogger)
