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
Various Utility functions
"""
from logging import info
import os
from threading import Thread
from subprocess import Popen, PIPE, STDOUT  # nosec


def data_file(path):
    """
    Utility function to find resources data file packaged along with code

    Parameters
    ----------
    path : path
        path to the resource file in the package

    Returns
    -------
        absolute path to the resource data file
    """
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)


def find(collection, item, field='name'):
    """
    Finds an element in a collection which has a field equal
    to particular item value

    Parameters
    ----------
    collection : Set
        Collection of objects
    item
        value of the item that we are looking for
    field : string
        Name of the field from the object to inspect

    Returns
    -------
    object
        Corresponding element that has a field matching item in
        the collection
    """
    for element in collection:
        if element[field] == item:
            return element
    return None


def copy_replace(src, dst, pattern='', replace_value=''):
    """
    Copies a file from src to dst replacing pattern by replace_value

    Parameters
    ----------
    src : string
        Path to the source filename to copy from
    dst : string
        Path to the output filename to copy to
    pattern : string
        Pattern to replace inside the src file
    replace_value
        Value to replace by in the dst file

    """
    if isinstance(src, str):
        file1 = open(src, 'r')
    else:
        file1 = src
    if isinstance(dst, str):
        file2 = open(dst, 'w')
    else:
        file2 = dst
    for line in file1:
        file2.write(line.replace(pattern, replace_value))
    if isinstance(src, str):
        file1.close()
    if isinstance(dst, str):
        file2.close()


def log_info(pipe):
    """ Default logging function """
    for line in iter(pipe.readline, b''):
        info(line)
    return True


class BackgroundThreadRunner():
    """
    Worker Thread to run logging output in the background

    ...

    Attributes
    ----------
    _process :
        Process object of the command running in the background
    _log_function : function(stream -> bool)
        callback function to log the output of the command
    _no_redirect : bool
        whether the subprocess STDOUT and STDERR should be redirected to logs
    _worker : Thread
        Thread object
    """
    def __init__(self, command, log_function, no_redirect=False):
        self._no_redirect = no_redirect
        if no_redirect:
            self._process = Popen(command)  # nosec
        else:
            self._process = Popen(command, stdout=PIPE, stderr=STDOUT)  # nosec
        self._log_function = log_function
        self._worker = Thread(name='worker', target=self.run)
        self._worker.start()

    def run(self):
        """
        Starts the Thread, process the output of the process.

        """
        if not self._no_redirect:
            self._log_function(self._process.stdout)

    def process(self):
        """Returns the process object."""
        return self._process


def subprocess_run(command, log_function=log_info,
                   no_redirect=False, wait=True):
    """
    Run command in a subprocess while redirecting output to log_function.

    The subprocess either runs synchroneoulsy or in the background depending on
    the wait parameter.

    Parameters
    ----------
    command : List
        Command to run in the subprocess
    log_function : function
        Callback function to log the output of the subprocess
    no_redirect : bool
        whether the subprocess STDOUT and STDERR should be redirected to logs
    wait : bool
        Whether the subprocess should be run synchroneously or in
        the background
    Returns
    -------
    int
        return code of the subprocess
    BackgroundThreadRunner
        the thread running in the background
    """
    if wait:
        if no_redirect:
            process = Popen(command, shell=False)  # nosec
        else:
            process = Popen(command,
                            stdout=PIPE,
                            stderr=STDOUT,
                            shell=False)  # nosec
            with process.stdout:
                log_function(process.stdout)
        return process.wait()
    else:
        return BackgroundThreadRunner(command, log_function, no_redirect)
