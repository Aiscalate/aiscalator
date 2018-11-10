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
Handles configurations files for the application
"""
from datetime import datetime
from platform import uname
import logging
from logging import config
import os
from urllib.error import HTTPError, URLError
import uuid
from tempfile import TemporaryDirectory

import pyhocon
from pytz import timezone
from yaml import safe_load

from aiscalator import __version__
from aiscalator.core.utils import data_file, copy_replace


def setup_logging():
    """ Setup the logging configuration of the application """
    log_level = os.getenv('AISCALATOR_LOG_LEVEL', None)
    with open(data_file("../config/logging.yaml"), 'rt') as file:
        path = load_logging_conf(file)
    if not path:
        logging.basicConfig(level=logging.INFO)
    if log_level:
        logging.root.setLevel(log_level)
    msg = ("Starting " + os.path.basename(__name__) +
           " version " + __version__ + " on " +
           "_".join(uname()).replace(" ", "_"))
    logging.debug(msg)


def load_logging_conf(file):
    """Reads and loads the logging configuration file"""
    if file:
        os.makedirs('/tmp/aiscalator/log', exist_ok=True)
        conf = safe_load(file.read())
        config.dictConfig(conf)
        return file
    return None


def generate_global_config() -> str:
    """Generate a standard configuration file for the application in the
    user's home folder ~/.aiscalator/config/aiscalator.conf from the
    template file in aiscalator/config/template/aiscalator.conf
    """
    dst = os.path.join(os.path.expanduser("~"),
                       ".aiscalator/config/aiscalator.conf")
    now = '"' + str(datetime
                    .utcnow()
                    .replace(tzinfo=timezone("UTC"))) + '"'
    with TemporaryDirectory() as tmp:
        copy_replace(data_file("../config/template/aiscalator.conf"),
                     os.path.join(tmp, "aiscalator.conf"),
                     pattern="testUserID",
                     replace_value=generate_user_id())
        copy_replace(os.path.join(tmp, "aiscalator.conf"),
                     dst,
                     pattern="generation_date",
                     replace_value=now)
    return dst


def generate_user_id() -> str:
    """
    Returns
    -------
    str
        Returns a string identifying this user when the
        setup was run first
    """
    return 'u' + str((uuid.getnode()))


class AiscalatorConfig:
    """
    A configuration object for the Aiscalator application.

    This object stores:
        - global configuration for the whole application
        - configuration for a particular context specified in a step
          configuration file.
        - In this case, we might even focus on a particular step.

    ...

    Attributes
    ----------
    _user_config_override : str
        path to the specified user config
    _app_conf
        global configuration object for the application
    _step_config : str
        path to the step configuration (or plain configuration as string)
    _focused_steps : list
        list of selected steps
    _step_it : int
        index of the step being processed
    _step
        configuration object for the currently processed step
    """
    def __init__(self,
                 user_config_override=None,
                 step_config=None,
                 steps_selection=None):
        """
        Parameters
            ----------
            user_config_override : str
                path of the user configuration folder to override
                the default one
            step_config : str
                path to the step configuration file (or plain configuration
                string)
            steps_selection : List
                list of names of steps from the configuration file to focus on
        """
        self._user_config_override = user_config_override
        self._app_conf = self.setup_app_config()
        setup_logging()
        self._step_config = step_config
        all_steps = parse_step_config(step_config)
        self._focused_steps = select_steps(all_steps, steps_selection)
        self._step_it = 0
        self._step = self.next_step()

    def setup_app_config(self):
        """
        Setup global application configuration.
        If not found in the default location, this method will generate
        a brand new one.

        """
        try:
            file = self.find_user_config_file("config/aiscalator.conf")
            conf = pyhocon.ConfigFactory.parse_file(file)
        except FileNotFoundError:
            conf = pyhocon.ConfigFactory.parse_file(generate_global_config())
        return conf

    def find_user_config_file(self, filename) -> str:
        """
        Looks for configuration files in the user configuration folder

        Parameters
        ----------
        filename : str
            file to search for

        Returns
        -------
        str
            path to the filename in the user configuration folder

        """
        # TODO check user_config_folder override in environment
        if self._user_config_override:
            return os.path.join(self._user_config_override, filename)
        # TODO url user config?
        return os.path.join(os.path.expanduser("~"), '.aiscalator', filename)

    def next_step(self):
        """
        Iterates to the next configuration step from the list
        of selected steps

        Returns
        -------
            the next configuration object

        """
        result = None
        i = self._step_it
        if i < len(self._focused_steps):
            self._step_it += 1
            result = self._focused_steps[i]
        self._step = result
        return result

    def user_env_file(self) -> list:
        """
        Find a list of env files to pass to docker containers

        Returns
        -------
        List
            env files

        """
        # TODO look if env file has been defined in the focused step
        # TODO look in user config if env file has been redefined
        return [self.find_user_config_file("config/.env")]

    def notebook_output_path(self, notebook) -> str:
        """Generates the name of the output notebook"""
        return ("/home/jovyan/work/notebook_run/" +
                os.path.basename(notebook).replace(".ipynb", "") + "_" +
                self.timestamp_now() +
                self.user_id() +
                ".ipynb")

    def timestamp_now(self) -> str:
        """
         Depending on how the timezone is configured, returns the
         timestamp for this instant.

        """
        date_now = datetime.utcnow().replace(tzinfo=timezone("UTC"))
        if self._app_conf["aiscalator"]:
            pst = timezone(self.app_config().timezone)
        else:
            pst = timezone('Europe/Paris')
        return date_now.astimezone(pst).strftime("%Y%m%d%H%M%S")

    def app_config(self):
        """
        Returns
        -------
        str
            the configuration object for the aiscalator application
        """
        return self._app_conf["aiscalator"]

    def user_id(self) -> str:
        """
        Returns
        -------
        str
            the user id stored when the application was first setup
        """
        return self.app_config()["user.id"]

    def app_config_has(self, field) -> bool:
        """
        Tests if the applicatin config has a configuration
        value for the field.

        """
        if not self.app_config():
            return False
        return field in self.app_config()

    def step_field(self, field):
        """
        Returns the value associated with the field for the currently
        focused step.

        """
        if self.has_step_field(field):
            return self._step[1][field]
        return None

    def has_step_field(self, field) -> bool:
        """
        Tests if the currently focused step has a configuration
        value for the field.

        """
        if not self._step:
            return False
        return field in self._step[1]

    def step_config_path(self):
        """
        Returns
        -------
        str
            Returns the path to the step configuration file.
            If it was an URL, it will return the path to the temporary
            downloaded version of it.
            If it was a plain string, then returns None

        """
        if os.path.exists(self._step_config):
            if pyhocon.ConfigFactory.parse_file(self._step_config):
                return os.path.abspath(self._step_config)
        # TODO if string is url/git repo, download file locally first
        return None

    def step_name(self):
        """
        Returns the name of the currently focused step
        """
        if not self._step:
            return None
        return self._step[0]

    def root_dir(self):
        """
        Returns
        -------
        str
            Returns the path to the folder containing the step
            configuration file
        """
        path = self.step_config_path()
        if path:
            root_dir = os.path.dirname(path)
            if not root_dir.endswith("/"):
                root_dir += "/"
            return root_dir
        return None

    def file_path(self, string):
        """
        Returns absolute path of a file from a field of the currently
        focused step.

        """
        if not self.has_step_field(string):
            return None
        # TODO handle url
        root_dir = self.root_dir()
        if root_dir:
            return os.path.abspath(os.path.join(root_dir,
                                                self.step_field(string)))
        return os.path.abspath(self.step_field(string))

    def container_name(self) -> str:
        """Return the docker container name to execute this step"""
        return (
            self.step_field("task.type") +
            "_" +
            self.step_name()
        )

    def extract_parameters(self) -> list:
        """Returns a list of docker parameters"""
        result = []
        if self.has_step_field("task.parameters"):
            for param in self.step_field("task.parameters"):
                for key in param:
                    result += ["-p", key, param[key]]
        return result

    def validate_config(self):
        """
        Check if all the fields in the reference config are
        defined in focused steps too. Otherwise
        raise an Exception (either pyhocon.ConfigMissingException
        or pyhocon.ConfigWrongTypeException)

        """
        reference = data_file("../config/template/minimum_aiscalator.conf")
        ref = pyhocon.ConfigFactory.parse_file(reference)
        msg = "In Global Application Configuration file "
        validate_configs(self._app_conf, ref, msg,
                         missing_exception=True,
                         type_mismatch_exception=True)
        reference = data_file("../config/template/aiscalator.conf")
        ref = pyhocon.ConfigFactory.parse_file(reference)
        msg = "In Global Application Configuration file "
        validate_configs(self._app_conf, ref, msg,
                         missing_exception=False,
                         type_mismatch_exception=True)
        reference = data_file("../config/template/minimum_step.conf")
        ref = pyhocon.ConfigFactory.parse_file(reference)
        for step_name, step in self._focused_steps:
            msg = "in step named " + step_name
            validate_configs(step,
                             ref["steps"]["Untitled"],
                             msg,
                             missing_exception=True,
                             type_mismatch_exception=True)
        reference = data_file("../config/template/step.conf")
        ref = pyhocon.ConfigFactory.parse_file(reference)
        for step_name, step in self._focused_steps:
            msg = "in step named " + step_name
            validate_configs(step,
                             ref["steps"]["Untitled"],
                             msg,
                             missing_exception=False,
                             type_mismatch_exception=True)


def validate_configs(test, reference, path,
                     missing_exception=True,
                     type_mismatch_exception=True):
    """
    Recursively check two configs if they match

    Parameters
    ----------
    test
        configuration object to test
    reference
        reference configuration object
    path : str
        this accumulates the recursive path for details in Exceptions
    missing_exception : bool
        when a missing field is found, raise xception?
    type_mismatch_exception : bool
        when a field has type mismatch, raise xception?

    """
    # TODO instead of exceptions, build a log of "compilation" errors...
    for key in reference.keys():
        if key not in test.keys():
            msg = (path + ": Missing definition of " + key)
            if missing_exception:
                raise pyhocon.ConfigMissingException(
                    message="Exception " + msg
                )
            else:
                logging.warning("Warning %s", msg)
        elif not isinstance(test[key], type(reference[key])):
            msg = (path + ": Type mismatch of " + key + " found type " +
                   str(type(test[key])) + " instead of " +
                   str(type(reference[key])))
            if type_mismatch_exception:
                raise pyhocon.ConfigWrongTypeException(
                    message="Exception " + msg
                )
            else:
                logging.warning("Warning %s", msg)
        elif (isinstance(test[key], pyhocon.config_tree.ConfigTree) and
              isinstance(reference[key], pyhocon.config_tree.ConfigTree)):
            # test recursively
            validate_configs(test[key], reference[key],
                             ".".join([path, key]),
                             missing_exception,
                             type_mismatch_exception)
        elif (isinstance(test[key], list) and
              isinstance(reference[key], list)):
            # iterate through both collections
            for i in test[key]:
                for j in reference[key]:
                    validate_configs(i, j, ".".join([path, key]),
                                     missing_exception,
                                     type_mismatch_exception)


def parse_step_config(step_config):
    """
    Interpret the step_config to produce a step configuration
    object. It could be provided as:
    - a path to a local file
    - a url to a remote file
    - the plain configuration stored as string

    Returns
    -------
    Step configuration object

    """
    if not step_config:
        return None
    if os.path.exists(step_config):
        conf = pyhocon.ConfigFactory.parse_file(step_config)
    else:
        try:
            conf = pyhocon.ConfigFactory.parse_URL(step_config)
        except (HTTPError, URLError):
            conf = pyhocon.ConfigFactory.parse_string(step_config)
    return conf


def select_steps(step_conf, steps_selection: list) -> list:
    """
    Extract the list of step objects corresponding to
    the list of names provided.

    Parameters
    ----------
    step_conf
        step configuration object
    steps_selection : list
        list of names of step to extract
    Returns
    -------
    list
        list of tuples of (step_name, step) of selected
        configuration objects
    """
    result = []
    tasks = []
    if step_conf:
        tasks = find_tasks(step_conf["steps"])
        if steps_selection:
            for target_step in steps_selection:
                for step_name, step in tasks:
                    if step_name == target_step:
                        result += [(step_name, step)]
        else:
            result = [tasks[0]]
    if steps_selection and not result:
        msg = (" ".join(steps_selection) +
               " was not found in step configurations.\n ")
        if tasks:
            msg += ("Available tasks are: " +
                    " ".join([task_name for task_name, tasks in tasks]))
        raise pyhocon.ConfigMissingException(msg)
    return result


def find_tasks(tree: pyhocon.ConfigTree, path=""):
    """
    Find all Tasks objects in the Configuration object and report
    their paths.

    Parameters
    ----------
    tree : pyhocon.ConfigTree
        Configuration object
    path : str
        path that was traversed to get to this tree

    Returns
    -------
    list
        list of names of Configuration objects containing a
        definition of a section 'task'
    """
    result = []
    if path:
        next_path = path + "."
    else:
        next_path = ""
    for key in tree.keys():
        if key == 'task':
            result += [(path, tree)]
        else:
            if isinstance(tree[key], pyhocon.config_tree.ConfigTree):
                value = find_tasks(tree[key], path=next_path + key)
                if value:
                    result += value
    return result


def convert_to_format(file: str, output: str, output_format: str):
    """
    Converts a HOCON file to another format

    Parameters
    ----------
    file : str
        hocon file to convert
    output : str
        output file to produce
    output_format : str
        format of the output file

    Returns
    -------
    str
        the output file
    """
    (pyhocon
     .converter
     .HOCONConverter
     .convert_from_file(file, output_file=output,
                        output_format=output_format))
    os.remove(file)
    return output
