import dataclasses
import json
import logging
from unittest.mock import MagicMock, patch, mock_open

import pytest

from colorama import Fore

from slack_watchman.loggers import StdoutLogger, JSONLogger, export_csv, init_logger


@pytest.fixture(autouse=True)
def _reset_slack_watchman_logger():
    """Clear the process-wide 'Slack Watchman' logger between tests so handler
    state set up by one JSONLogger instance does not leak into the next."""
    shared = logging.getLogger('Slack Watchman')
    shared.handlers.clear()
    yield
    shared.handlers.clear()


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


def test_stdout_logger_skips_debug_when_not_debug_mode():
    """StdoutLogger.log must short-circuit on DEBUG when self.debug is False."""
    logger = StdoutLogger(debug=False)
    with patch.object(logger, 'log_to_stdout') as mock_log_to_stdout:
        logger.log('DEBUG', 'should not appear')
        mock_log_to_stdout.assert_not_called()


def test_stdout_logger_converts_dataclass_message(mock_stdout_logger):
    """A dataclass passed as `message` should be converted to a dict before formatting."""
    @dataclasses.dataclass
    class Payload:
        id: str
        name: str
        domain: str
        url: str

    payload = Payload(id='T1', name='Acme', domain='acme', url='https://acme.slack.com')
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', payload, notify_type='workspace')
        mock_log_to_stdout.assert_called_once()
        formatted_message, _ = mock_log_to_stdout.call_args[0]
        # Workspace formatter pulls fields by .get(), which only works on a dict.
        # If the dataclass→dict conversion didn't happen we'd see "None" for every field.
        assert 'ID: T1' in formatted_message
        assert 'NAME: Acme' in formatted_message


def test_stdout_logger_result_message_with_mapping_user(mock_stdout_logger):
    """`notify_type='result'` with a message body and a Mapping user should render display_name + email."""
    result = {
        'message': {
            'created': '2026-04-28',
            'permalink': 'https://example.slack.com/archives/C1/p1',
            'conversation': {
                'is_im': False,
                'is_private': True,
                'name': 'engineering',
            },
            'user': {'display_name': 'alice', 'email': 'alice@acme.com'},
        },
        'match_string': 'AKIAxxxx',
    }
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', result, notify_type='result')
        formatted_message, msg_level = mock_log_to_stdout.call_args[0]
    assert msg_level == 'RESULT'
    assert 'POST_TYPE: Message' in formatted_message
    assert 'POSTED_BY: alice - alice@acme.com' in formatted_message
    assert 'CONVERSATION_TYPE: Private Channel' in formatted_message


def test_stdout_logger_result_message_in_public_channel(mock_stdout_logger):
    """A result message that is neither an IM nor private should be labelled 'Public Channel'."""
    result = {
        'message': {
            'created': '2026-04-28',
            'permalink': 'https://example.slack.com/archives/C1/p1',
            'conversation': {'is_im': False, 'is_private': False, 'name': 'general'},
            'user': {'display_name': 'alice', 'email': 'alice@acme.com'},
        },
        'match_string': 'AKIAxxxx',
    }
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', result, notify_type='result')
        formatted_message, _ = mock_log_to_stdout.call_args[0]
    assert 'CONVERSATION_TYPE: Public Channel' in formatted_message


def test_stdout_logger_result_with_neither_message_nor_file(mock_stdout_logger):
    """A 'result' notify_type with neither a 'message' nor 'file' key should still emit at RESULT level."""
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', {'something_else': True}, notify_type='result')
        _, msg_level = mock_log_to_stdout.call_args[0]
    assert msg_level == 'RESULT'


def test_stdout_logger_result_message_with_string_user(mock_stdout_logger):
    """When the message user is a plain string (not a Mapping) it should be rendered verbatim."""
    result = {
        'message': {
            'created': '2026-04-28',
            'permalink': 'https://example.slack.com/archives/C1/p1',
            'conversation': {'is_im': True, 'is_private': False, 'name': 'dm'},
            'user': 'U-LEGACY',
        },
        'match_string': 'AKIAxxxx',
    }
    with patch.object(mock_stdout_logger, 'log_to_stdout') as mock_log_to_stdout:
        mock_stdout_logger.log('NOTIFY', result, notify_type='result')
        formatted_message, _ = mock_log_to_stdout.call_args[0]
    assert 'POSTED_BY: U-LEGACY' in formatted_message
    assert 'CONVERSATION_TYPE: Direct Message' in formatted_message


def test_stdout_logger_log_swallows_log_to_stdout_failure(mock_stdout_logger, capsys):
    """If log_to_stdout raises, .log() should print a contextual error and not propagate."""
    with patch.object(mock_stdout_logger, 'log_to_stdout', side_effect=RuntimeError('boom')):
        mock_stdout_logger.log('INFO', 'message')  # must not raise
    captured = capsys.readouterr()
    assert 'failed to log message' in captured.out


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


def test_stdout_logger_formatting_error_in_non_debug_mode_prints_fallback(capsys):
    """When debug is off, a formatting failure should print 'Formatting error' and continue."""
    logger = StdoutLogger(debug=False)
    capsys.readouterr()  # discard the header banner so it doesn't pollute the assertion
    logger.log_to_stdout('payload', None)  # msg_level=None triggers AttributeError on .lower()
    captured = capsys.readouterr()
    assert 'Formatting error' in captured.out


def test_print_header_does_not_raise():
    """Smoke test: print_header should run without raising."""
    StdoutLogger.print_header()


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
    assert not issubclass(JSONLogger, logging.Logger)


def test_json_logger_does_not_stack_handlers_across_instances():
    """Re-instantiating JSONLogger must not add duplicate handlers to the singleton logger."""
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


def test_json_logger_debug_routes_to_logger_debug(mock_json_logger):
    """DEBUG level must go through self.logger.debug, not .info."""
    with patch.object(mock_json_logger.logger, 'debug') as mock_debug, \
         patch.object(mock_json_logger.logger, 'info') as mock_info:
        mock_json_logger.log('DEBUG', 'debugging')
        mock_debug.assert_called_once()
        assert mock_debug.call_args[0][0] == 'debugging'
        mock_info.assert_not_called()


def test_json_logger_notify_envelope_has_detection_fields(mock_json_logger):
    """A NOTIFY emission must produce a JSON envelope with scope/severity/detection_type/detection_data."""
    payload = {'match_string': 'AKIAxxxx', 'signature_id': 'aws_keys'}
    with patch.object(mock_json_logger.handler.stream, 'write') as mock_write:
        mock_json_logger.log(
            'NOTIFY',
            payload,
            scope='messages',
            severity='HIGH',
            detect_type='aws_keys',
        )
    output = ''.join(call.args[0] for call in mock_write.mock_calls if call.args)
    parsed = json.loads(output.strip())
    assert parsed['level'] == 'NOTIFY'
    assert parsed['scope'] == 'messages'
    assert parsed['severity'] == 'HIGH'
    assert parsed['detection_type'] == 'aws_keys'
    assert parsed['detection_data'] == payload
    assert 'message' not in parsed


def test_json_logger_reuses_existing_handler_when_already_configured():
    """If the singleton logger already has a handler, JSONLogger should adopt it instead of stacking."""
    shared = logging.getLogger('Slack Watchman')
    pre_existing = logging.StreamHandler()
    shared.addHandler(pre_existing)

    instance = JSONLogger(debug=False)

    assert instance.handler is pre_existing
    assert shared.handlers == [pre_existing]
    # The shared handler must have the new formatter installed.
    assert pre_existing.formatter is instance.formatter


def test_json_logger_debug_kwarg_sets_level(mock_json_logger):
    """debug=True should put the underlying logger at DEBUG level."""
    assert mock_json_logger.logger.level == logging.DEBUG


def test_json_logger_default_level_is_info():
    """debug=False (the default) should put the underlying logger at INFO level."""
    instance = JSONLogger(debug=False)
    assert instance.logger.level == logging.INFO


@dataclasses.dataclass
class _CsvRow:
    """Reusable dataclass row for export_csv tests."""
    id: int
    name: str


@patch('builtins.open', new_callable=mock_open)
@patch('csv.DictWriter')
def test_export_csv_writes_header_and_rows_in_order(mock_dict_writer, mock_open_file):
    """export_csv must open the file, write a header, and write each row in input order."""
    rows = [_CsvRow(id=1, name='Test1'), _CsvRow(id=2, name='Test2')]
    writer_mock = MagicMock()
    mock_dict_writer.return_value = writer_mock

    assert export_csv('test', rows) is True

    mock_open_file.assert_called_once()
    open_args, open_kwargs = mock_open_file.call_args
    assert open_args[0].endswith('test.csv')
    assert open_args[1] == 'w'
    assert open_kwargs == {'encoding': 'utf-8'}

    mock_dict_writer.assert_called_once()
    _, dw_kwargs = mock_dict_writer.call_args
    assert list(dw_kwargs['fieldnames']) == ['id', 'name']

    writer_mock.writeheader.assert_called_once()
    assert writer_mock.writerow.call_count == len(rows)
    written_rows = [call.args[0] for call in writer_mock.writerow.mock_calls]
    assert written_rows == [
        {'id': 1, 'name': 'Test1'},
        {'id': 2, 'name': 'Test2'},
    ]


def test_export_csv_does_not_double_close_file():
    """The `with open(...)` block closes the file; export_csv must not call close() a second time."""
    rows = [_CsvRow(id=1, name='alice')]
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
    rows = [_CsvRow(id=1, name='alice')]
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
