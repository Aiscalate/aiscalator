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
"""Tests for `jupyter.command` package."""

from aiscalator.core.config import AiscalatorConfig
from aiscalator.jupyter import command


def test_prepare_docker_image_env_extra_options():
    """Test the _prepare_docker_image_env."""
    options_list = command._prepare_docker_image_env(
        AiscalatorConfig("tests/jupyter/sample_pyhocon.conf")
    )
    'bridge' == options_list[-1]
    '--network' == options_list[-2]
