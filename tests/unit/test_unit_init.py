import time
from unittest.mock import patch

import pytest

from slack_watchman import _build_canvas_url, _compute_timeframe, main


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


@pytest.mark.parametrize("tm,delta", [('d', 86400), ('w', 604800), ('m', 2592000), ('a', 1576800000)])
def test_compute_timeframe_formats_in_utc(tm, delta):
    """The `after:` operator date is formatted in UTC, not the host's
    local timezone. Pre-fix the code used `time.localtime`, which made
    the result depend on `$TZ` and caused an off-by-one boundary skew
    between hosts and the workspace timezone."""
    # 2024-10-31 23:59:59 UTC: a timestamp that lands on a UTC date
    # boundary which most non-UTC TZs would round to a different day.
    now = 1730419199
    expected = time.strftime('%Y-%m-%d', time.gmtime(now - delta))
    assert _compute_timeframe(tm, now) == expected


@pytest.mark.parametrize(
    "workspace_url",
    [
        'https://example.slack.com/',
        'https://example.slack.com',
    ],
    ids=['with_trailing_slash', 'without_trailing_slash'],
)
def test_build_canvas_url_handles_trailing_slash_either_way(workspace_url):
    """`team.info` may or may not include a trailing slash on the
    workspace URL. Pre-fix the bare concat produced
    `https://example.slack.comcanvas/C123` when it didn't."""
    assert _build_canvas_url(workspace_url, 'C123') == \
        'https://example.slack.com/canvas/C123'


def test_compute_timeframe_does_not_call_localtime(monkeypatch):
    """If anyone reintroduces `time.localtime` here the off-by-one bug
    comes back. Trap localtime calls for the duration of the helper to
    catch that regression independently of the host's actual TZ."""
    calls = []
    real_localtime = time.localtime

    def trap(*args, **kwargs):
        calls.append(args)
        return real_localtime(*args, **kwargs)

    monkeypatch.setattr('slack_watchman.time.localtime', trap)
    _compute_timeframe('d', 1730419199)
    assert calls == []
