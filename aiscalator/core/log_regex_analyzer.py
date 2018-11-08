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
"""
Class to parse output logs from subprocess and catch particular expressions
"""
from logging import info
from re import search


class LogRegexAnalyzer():
    """
    A regular expression analyzer object to parse logs and extract
    values from patterns in the logs.
    ...

    Attributes
    ----------
    artifact : string
        Value of the pattern found in the logs
    pattern : bytes
        Regular expression to search for in the logs
    """

    def __init__(self, pattern=None):
        """
        Parameters
        ----------
        pattern : string
            Regular expression to search for in the logs
        """
        self.artifact = "latest"
        self.pattern = pattern

# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    def grep_logs(self, pipe):
        """
        Reads the logs and extract values defined by the pattern

        Parameters
        ----------
        pipe
            Stream of logs to analyze
        """
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            # TODO improve logging in its own subprocess log file?
            info(line)
            if self.pattern is not None:
                match = search(self.pattern, line)
                if match:
                    self.artifact = match.group(1).decode("utf-8")
