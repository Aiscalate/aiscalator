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


def test_cli_jupyter():
    """Test the CLI on Jupyter sub-commands."""
    runner = CliRunner()
    print()
    with runner.isolated_filesystem():
        # test = ['jupyter', "new", "test", "--name", "test_name"]
        test = ['jupyter']
        msg = "Testing CLI with: " + " ".join(test) + " => "
        print(msg)
        result = runner.invoke(cli.main, test)

        assert result.exit_code == 0
