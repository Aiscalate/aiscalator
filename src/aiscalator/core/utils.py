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
import hashlib
import logging
import os
import re
import webbrowser
from pathlib import Path
from shlex import quote
from subprocess import PIPE  # nosec
from subprocess import STDOUT
from subprocess import Popen
from threading import Thread
from time import sleep

from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer


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


def copy_replace(src, dst, pattern=None, replace_value=None):
    """
    Copies a file from src to dst replacing pattern by replace_value

    Parameters
    ----------
    src : string
        Path to the source filename to copy from
    dst : string
        Path to the output filename to copy to
    pattern
        list of Patterns to replace inside the src file
    replace_value
        list of Values to replace by in the dst file

    """
    file1 = open(src, 'r') if isinstance(src, str) else src
    file2 = open(dst, 'w') if isinstance(dst, str) else dst
    pattern = (
        [pattern] if isinstance(pattern, str)
        else pattern
    )
    replace_value = (
        [replace_value] if isinstance(replace_value, str)
        else replace_value
    )
    if replace_value and pattern:
        if len(replace_value) != len(pattern):
            raise Exception("Invalid parameters: pattern and replace_value"
                            " have different sizes.")
        rules = [
            (re.compile(regex, re.IGNORECASE), value)
            for regex, value in zip(pattern, replace_value)
        ]
    else:
        rules = []
    for line in file1:
        if rules:
            for rule in rules:
                line = re.sub(rule[0], rule[1], line)
        file2.write(line)
    if isinstance(src, str):
        file1.close()
    if isinstance(dst, str):
        file2.close()


def log_info(pipe):
    """ Default logging function """
    logger = logging.getLogger(__name__)
    for line in iter(pipe.readline, b''):
        logger.debug(line)
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


def format_file_content(content, prefix="", suffix=""):
    """
    Reformat the content of a file line by line, adding prefix and suffix
    strings.

    Parameters
    ----------
    content : str
        path to the file to reformat its content
    prefix : str
        add to each line this prefix string
    suffix : str
        add to each line this suffix string
    Returns
    -------
    str
        Formatted content of the file
    """
    result = ""
    with open(content, "r") as file:
        for line in file:
            # TODO handle comments
            # TODO check validity of the line for extra security
            result += prefix + quote(line.replace('\n', '')) + suffix
    return result


def sha256(file: str):
    """
    Reads a file content and returns its sha256 hash.

    """
    sha = hashlib.sha256()
    with open(file, "rb") as content:
        for line in content:
            sha.update(line)
    return sha.hexdigest()


def wait_for_jupyter_lab(commands, logger, notebook, port, folder):
    """
    Starts jupyter lab and wait for it to start, returning the url it's
    running from.

    Parameters
    ----------
    commands: list
        List of commands to run to start the process
    logger : logging.Logger
        Logger object
    notebook : str
        path to the notebook
    port :
        port on which the jupyter lab is listening
    folder : str
        path in the container to reach the notebook

    Returns
    -------
    str
        url from which it is serving the jupyter lab
    """
    log = LogRegexAnalyzer(b'.*http://.*:8888/.token=([a-zA-Z0-9]+)(\r)?\n')
    logger.info("Running...: %s", " ".join(commands))
    subprocess_run(commands, log_function=log.grep_logs, wait=False)
    for i in range(5):
        sleep(2)
        if log.artifact():
            break
        msg = "docker run does not seem to be up yet..."
        msg += " retrying (%s/5)"
        logger.warning(msg, i)
    if log.artifact():
        # TODO handle url better (not always localhost?)
        url = ("http://localhost:" + str(port) +
               "/lab/tree/" + folder + "/" +
               notebook + "?token=" +
               log.artifact())
        logger.info("%s is up and running.", url)
        # TODO --no-browser option
        webbrowser.open(url)
        return url
    return ""


def check_notebook(logger, code_path, from_format="py:percent"):
    """
    Checks existence of notebook file and regenerates using
    jupytext from associated .py file if possible.
    Otherwise, create an empty notebook file.

    Parameters
    ----------
    code_path : str
        path to the notebook to check
    from_format : str
        jupytext format of the .py input file

    """
    notebook, notebook_py = notebook_file(code_path, from_format)
    # TODO: check if last modified date of notebook_py is behind notebook
    # then refresh it
    commands = [
        "jupytext", "--from", from_format, "--to", "notebook",
        notebook_py, "-o", notebook,
        "--set-formats", ".ipynb," + from_format
    ]
    if not os.path.exists(code_path):
        code_path_dir = os.path.dirname(code_path)
        if code_path_dir:
            os.makedirs(code_path_dir, exist_ok=True)
        copy_replace(data_file("../config/template/notebook.json"),
                     code_path,
                     pattern="__format__", replace_value=from_format)

        logger.info("Running...: %s", " ".join(commands))
        subprocess_run(commands)
    if os.path.isfile(notebook_py):
        commands += ["--sync"]
        logger.info("Running...: %s", " ".join(commands))
        subprocess_run(commands)
        # touch notebook.py so jupytext doesn't complain when
        # opening in the jupyter lab when the py is behind the
        # ipynb in modification time
        Path(notebook_py).touch()


def check_notebook_dir(logger, code_path, from_format="py:percent"):
    """
    Check a folder and generate all notebook files that might
    be required in that folder.

    Parameters
    ----------
    code_path : str
        path to a file in the folder
    from_format : str
        jupytext format of potential .py files

    """
    check_notebook(logger, code_path, from_format)
    code_path_dir = os.path.dirname(code_path)
    for file in os.listdir(code_path_dir):
        file = os.path.join(code_path_dir, file)
        notebook, notebook_py = notebook_file(file)
        if notebook != code_path and notebook_py != code_path:
            if (file.endswith(from_format.split(":")[0]) or
               file.endswith(".ipynb")):
                check_notebook(logger, notebook, from_format)


def notebook_file(code_path, from_format="py:percent"):
    """
    Parse a path to return both the ipynb and py versions of
    the file.

    Parameters
    ----------
    code_path : str
        path to a file
    from_format : str
        jupytext format of potential .py files

    Returns
    -------
    (str, str)
        tuple of 2 paths to ipynb and py files

    """
    if '.' in code_path:
        base_code_path = os.path.splitext(os.path.basename(code_path))[0]
        code_path_dir = os.path.dirname(code_path)
        code_path = os.path.join(code_path_dir, base_code_path)
    code_extension = from_format.split(":")[0]
    return code_path + '.ipynb', code_path + '.' + code_extension
