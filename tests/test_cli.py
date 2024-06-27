import pytest

import blendss


def test_cli_import():
    assert hasattr(blendss, "cli")
    cli = blendss.cli
    assert callable(cli)
