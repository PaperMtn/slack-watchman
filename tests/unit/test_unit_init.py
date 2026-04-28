from unittest.mock import patch

import pytest

from slack_watchman import main


def test_main_handles_exception_before_init_logger(capfd, monkeypatch):
    """An exception raised before init_logger executes is surfaced cleanly.

    Previously, OUTPUT_LOGGER was set to '' at the top of main() and only
    replaced with a real logger after argparse + metadata lookup. Any
    exception raised in between fell into the top-level `except Exception`
    handler, which then called ''.log(...) and raised AttributeError —
    masking the original error and producing a confusing traceback.
    """
    monkeypatch.setattr('sys.argv', ['slack-watchman'])

    with patch('slack_watchman.metadata') as mock_metadata:
        mock_metadata.metadata.side_effect = RuntimeError('package metadata broken')
        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1

    output = capfd.readouterr().err + capfd.readouterr().out
    # The handler must not have crashed with AttributeError on the placeholder.
    assert "'str' object has no attribute 'log'" not in output
    assert "'NoneType' object has no attribute 'log'" not in output


def test_main_handles_timeout_before_init_logger(capfd, monkeypatch):
    """TimeoutError before init_logger should not crash the handler either."""
    monkeypatch.setattr('sys.argv', ['slack-watchman'])

    with patch('slack_watchman.metadata') as mock_metadata:
        mock_metadata.metadata.side_effect = TimeoutError('upstream slow')
        # TimeoutError handler does not call sys.exit, so main() returns normally.
        main()

    output = capfd.readouterr().err + capfd.readouterr().out
    assert "'str' object has no attribute 'log'" not in output
    assert "'NoneType' object has no attribute 'log'" not in output
