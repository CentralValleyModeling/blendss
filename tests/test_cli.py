import logging
from unittest import mock

import pytest
from pytest import LogCaptureFixture

import blendss

LOGGER = logging.getLogger()  # Library currently uses the root logger


def test_cli_import():
    assert hasattr(blendss, "cli")
    cli = blendss.cli.cli
    assert callable(cli)


@mock.patch("blendss.cli.blend")
def test_cli_minimum_args(
    mock_blend: mock.AsyncMock,
    caplog: LogCaptureFixture,
):
    mock_blend.return_value = None
    args = ["-m", "./tests/assets/test.toml", "--fv", "calsim3"]
    with mock.patch("sys.argv", args):
        blendss.cli.cli()
    for record in caplog.records:
        assert record.levelno <= logging.INFO


@mock.patch("blendss.blend.generate_new_paths")
@mock.patch("blendss.blend.resolve_wildcards")
def test_cli_error_name_collision(
    mock_wildcard: mock.AsyncMock,
    mock_gen: mock.AsyncMock,
):
    mock_wildcard.return_value = {0, 1, 2, 3}
    mock_gen.return_value = {0, 1, 2}  # smaller return
    args = ["-m", "./tests/assets/test.toml", "--fv", "calsim3"]
    with mock.patch("sys.argv", args):
        with pytest.raises(ValueError):
            blendss.cli.cli()


@mock.patch("blendss.blend.pdss.copy_multiple_rts")
@mock.patch("blendss.blend.generate_new_paths")
@mock.patch("blendss.blend.resolve_wildcards")
def test_cli_warns_name_collision(
    mock_wildcard: mock.AsyncMock,
    mock_gen: mock.AsyncMock,
    mock_copy: mock.AsyncMock,
    caplog: LogCaptureFixture,
):
    mock_wildcard.return_value = {0, 1, 2, 3}
    mock_gen.return_value = {0, 1, 2, 3}  # same every time
    mock_copy.return_value = None
    args = ["-m", "./tests/assets/test.toml", "--fv", "calsim3"]
    with mock.patch("sys.argv", args):
        blendss.cli.cli()
    assert LOGGER.isEnabledFor(logging.INFO)
    assert len(caplog.records) > 0
    warnings = 0
    for record in caplog.records:
        if record.levelno == logging.WARNING:
            warnings += 1
    assert warnings > 0
