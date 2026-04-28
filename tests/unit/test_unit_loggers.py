import json
from unittest.mock import MagicMock, patch, mock_open

import pytest

from colorama import Fore

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


@pytest.mark.parametrize(
    "notify_type, payload, expected_level",
    [
        ("workspace", {"id": "T1", "name": "Acme", "domain": "acme", "url": "https://acme.slack.com"}, "WORKSPACE"),
        (
            "workspace_auth",
            {
                "formatted_email_domains": "acme.com",
                "user_oauth": True,
                "standard_auth_enabled": True,
                "sso_enabled": False,
                "two_factor_required": False,
            },
            "WORKSPACE_AUTH",
        ),
        (
            "workspace_probe",
            {
                "team_name": "Acme",
                "team_id": "T1",
                "paid_team": True,
                "formatted_email_domains": "acme.com",
                "join_url": "https://acme.slack.com",
                "user_oauth": True,
                "standard_auth_enabled": True,
                "sso_enabled": False,
                "two_factor_required": False,
            },
            "WORKSPACE_PROBE",
        ),
        (
            "user",
            {
                "id": "U1",
                "display_name": "alice",
                "email": "alice@acme.com",
                "title": "Engineer",
                "is_admin": False,
                "is_owner": False,
                "has_2fa": True,
            },
            "USER",
        ),
        ("canvas", {"channel_name": "general", "canvas_url": "https://acme.slack.com/canvases/abc"}, "CANVAS"),
    ],
)
def test_stdout_logger_notify_type_routing(mock_stdout_logger, notify_type, payload, expected_level):
    """Each notify_type must route to its own msg_level and not bleed into siblings."""
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', payload, notify_type=notify_type)
        mock_log_to_stdout.assert_called_once()
        _, msg_level = mock_log_to_stdout.call_args[0]
        assert msg_level == expected_level


@pytest.mark.parametrize(
    "msg_level, expected_color",
    [
        ('NOTIFY', Fore.CYAN),
        ('INFO', Fore.WHITE),
        ('WORKSPACE', Fore.LIGHTBLUE_EX),
        ('WORKSPACE_AUTH', Fore.LIGHTGREEN_EX),
        ('WORKSPACE_PROBE', Fore.LIGHTGREEN_EX),
        ('USER', Fore.RED),
        ('CANVAS', Fore.LIGHTMAGENTA_EX),
        ('WARNING', Fore.YELLOW),
        ('SUCCESS', Fore.LIGHTGREEN_EX),
        ('DEBUG', Fore.WHITE),
        ('ERROR', Fore.MAGENTA),
        ('CRITICAL', Fore.RED),
        ('RESULT', Fore.LIGHTGREEN_EX),
    ],
)
@patch('sys.stdout.write', autospec=True)
def test_stdout_logger_level_styles(mock_write, mock_stdout_logger, msg_level, expected_color):
    """Each known msg_level must render with its mapped colour from _LEVEL_STYLES."""
    mock_stdout_logger.log_to_stdout('payload', msg_level)
    output = ''.join(str(call.args[0]) for call in mock_write.mock_calls if call.args)
    assert expected_color in output


def test_stdout_logger_regexes_not_compiled_per_call(mock_stdout_logger):
    """The colourising regexes should be hoisted to module level, not recompiled on every log call."""
    with patch('slack_watchman.loggers.re.compile') as mock_compile:
        mock_stdout_logger.log_to_stdout('Test Message', 'INFO')
        mock_compile.assert_not_called()


def test_stdout_logger_formatting_error_does_not_exit_in_debug(mock_stdout_logger):
    """A formatting failure inside log_to_stdout must not terminate the process, even in debug mode."""
    with patch('slack_watchman.loggers.sys.exit') as mock_exit:
        # msg_level=None falls through every branch, then .lower() raises AttributeError
        # inside the try/except, exercising the debug-mode failure path.
        mock_stdout_logger.log_to_stdout('payload', None)
        mock_exit.assert_not_called()


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


def test_json_logger_does_not_inherit_from_logger():
    """JSONLogger should not subclass logging.Logger; it composes one via self.logger."""
    import logging as _logging
    assert not issubclass(JSONLogger, _logging.Logger)


def test_json_logger_does_not_stack_handlers_across_instances():
    """Re-instantiating JSONLogger must not add duplicate handlers to the singleton logger."""
    import logging as _logging
    # Reset shared singleton to a clean baseline for the test.
    shared = _logging.getLogger('Slack Watchman')
    shared.handlers.clear()

    first = JSONLogger(debug=False)
    second = JSONLogger(debug=False)

    assert first.logger is second.logger
    assert len(first.logger.handlers) == 1


@pytest.mark.parametrize(
    "level, expected_method, other_methods",
    [
        ('WARNING', 'warning', ['error', 'critical']),
        ('ERROR', 'error', ['warning', 'critical']),
        ('CRITICAL', 'critical', ['warning', 'error']),
    ],
)
def test_json_logger_severity_levels_route_to_matching_method(mock_json_logger, level, expected_method, other_methods):
    """WARNING/ERROR/CRITICAL must call the matching logger method, not collapse to .critical()."""
    with patch.object(mock_json_logger.logger, expected_method) as expected_mock, \
         patch.object(mock_json_logger.logger, other_methods[0]) as other_a, \
         patch.object(mock_json_logger.logger, other_methods[1]) as other_b:
        mock_json_logger.log(level, 'something went wrong')
        expected_mock.assert_called_once()
        assert expected_mock.call_args[0][0] == 'something went wrong'
        other_a.assert_not_called()
        other_b.assert_not_called()


def test_json_logger_workspace_probe_emits_correct_envelope(mock_json_logger):
    """WORKSPACE_PROBE must produce a JSON envelope with level=WORKSPACE_PROBE and message=payload."""
    payload = {'team_name': 'Acme', 'team_id': 'T1'}
    with patch.object(mock_json_logger.handler.stream, 'write') as mock_write:
        mock_json_logger.log('WORKSPACE_PROBE', payload)
    output = ''.join(call.args[0] for call in mock_write.mock_calls if call.args)
    parsed = json.loads(output.strip())
    assert parsed['level'] == 'WORKSPACE_PROBE'
    assert parsed['message'] == payload


def test_json_logger_does_not_swap_formatter_per_call(mock_json_logger):
    """The handler formatter should be installed once at construction, not mutated per log call."""
    with patch.object(mock_json_logger.handler, 'setFormatter') as mock_set_formatter:
        mock_json_logger.log('INFO', 'hello')
        mock_json_logger.log('WORKSPACE_PROBE', {'team_id': 'T1'})
        mock_json_logger.log('NOTIFY', {'match': 'x'}, scope='messages', severity='HIGH', detect_type='aws_keys')
        mock_set_formatter.assert_not_called()


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
    import dataclasses as _dc

    @_dc.dataclass
    class MockData:
        """Mock dataclass."""
        id: int
        name: str

    mock_data = [MockData(id=1, name='Test1'), MockData(id=2, name='Test2')]

    mock_writer_instance = MagicMock()
    mock_dict_writer.return_value = mock_writer_instance

    # Run the export_csv function
    assert export_csv('test', mock_data) is True


def test_export_csv_does_not_double_close_file():
    """The `with open(...)` block closes the file; export_csv must not call close() a second time."""
    import dataclasses as _dc

    @_dc.dataclass
    class Row:
        id: int

    rows = [Row(id=1)]
    fake_file = MagicMock()
    fake_file.__enter__.return_value = fake_file
    fake_file.__exit__.return_value = False

    with patch('builtins.open', return_value=fake_file):
        export_csv('once', rows)

    # The `with` block invokes __exit__ which closes the file; export_csv
    # should not also call .close() explicitly afterwards.
    fake_file.close.assert_not_called()


def test_export_csv_empty_input_returns_false_and_writes_nothing():
    """Empty export_data must not crash on export_data[0] and must not open a file."""
    with patch('builtins.open', new_callable=mock_open) as mock_open_file:
        result = export_csv('empty', [])
    assert result is False
    mock_open_file.assert_not_called()


def test_export_csv_returns_false_on_write_failure():
    """When the underlying open() raises, export_csv must signal failure rather than silently swallow."""
    import dataclasses as _dc

    @_dc.dataclass
    class Row:
        id: int
        name: str

    rows = [Row(id=1, name='alice')]

    with patch('builtins.open', side_effect=OSError('disk full')):
        assert export_csv('does_not_matter', rows) is False


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
