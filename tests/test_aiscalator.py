#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `aiscalator` package."""

from click.testing import CliRunner

from aiscalator import cli

# FIXME implements tests !!!


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
