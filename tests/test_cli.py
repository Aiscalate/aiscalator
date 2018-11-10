#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Apache Software License 2.0
#
# Copyright (c) 2018, Christophe Duong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for `aiscalator` package."""

from click.testing import CliRunner

from aiscalator import cli


def test_cli_help_version():
    """Test the CLI --help and --version."""
    cli_tests = [
        [],
        ['--help'],
        ['--version'],
        ['version'],
        ['airflow'],
        ['airflow', '--help'],
        ['airflow', '--version'],
        ['airflow', "new", '--help'],
        ['airflow', "run", '--help'],
        ['airflow', "edit", '--help'],
        ['airflow', "setup", '--help'],
        ['airflow', "push", '--help'],
        ['airflow', "start", '--help'],
        ['airflow', "stop", '--help'],
        ['jupyter'],
        ['jupyter', '--help'],
        ['jupyter', '--version'],
        ['jupyter', "new", '--help'],
        ['jupyter', "run", '--help'],
        ['jupyter', "edit", '--help'],
        ['jupyter', "setup", '--help'],
        ['setup'],
        ['setup', '--help'],
        ['setup', '--version'],
        ['cookiecutter'],
        ['cookiecutter', '--help'],
        ['cookiecutter', '--version'],
    ]
    runner = CliRunner()
    print()
    for test in cli_tests:
        msg = "Testing CLI with: " + " ".join(test) + " => "
        result = runner.invoke(cli.main, test)
        print(msg + str(result.exit_code))
        assert result.exit_code == 0
