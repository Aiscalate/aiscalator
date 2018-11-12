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
import logging
from re import search


class LogRegexAnalyzer():
    """
    A regular expression analyzer object to parse logs and extract
    values from patterns in the logs.
    ...

    Attributes
    ----------
    _artifact : str
        Value of the pattern found in the logs
    _pattern : bytes
        Regular expression to search for in the logs
    """

    def __init__(self, pattern=None, log_level=logging.DEBUG):
        """
        Parameters
        ----------
        pattern : pattern
            Regular expression to search for in the logs
        """
        self._artifact = None
        self._pattern = pattern
        self._log_level = log_level

# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    def grep_logs(self, pipe):
        """
        Reads the logs and extract values defined by the pattern

        Parameters
        ----------
        pipe
            Stream of logs to analyze
        """
        logger = logging.getLogger(__name__)
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            logger.log(self._log_level, b'\n' + line)
            if self._pattern is not None:
                match = search(self._pattern, line)
                if match:
                    self._artifact = match.group(1).decode("utf-8")

    def artifact(self):
        """ Returns the artifact extracted from the logs."""
        return self._artifact
