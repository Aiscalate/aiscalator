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
import os
import uuid
from datetime import datetime
from logging import DEBUG
from logging import Formatter
from logging import StreamHandler
from logging import getLogger
from logging.config import dictConfig
from platform import uname
from tempfile import mkstemp
from urllib.error import HTTPError
from urllib.error import URLError

import pyhocon
from pytz import timezone

from aiscalator import __version__
from aiscalator.core.utils import copy_replace
from aiscalator.core.utils import data_file


def _generate_global_config() -> str:
    """Generate a standard configuration file for the application in the
    user's home folder ~/.aiscalator/config/aiscalator.conf from the
    template file in aiscalator/config/template/aiscalator.conf
    """
    logger = getLogger(__name__)
    dst = os.path.join(os.path.expanduser("~"),
                       ".aiscalator/config/aiscalator.conf")
    logger.info("Generating a new configuration file for aiscalator:\n\t%s",
                dst)
    pattern = [
        "testUserID",
        "generation_date",
    ]
    replace_value = [
        generate_user_id(),
        '"' + str(datetime
                  .utcnow()
                  .replace(tzinfo=timezone("UTC"))) +
        '" // in UTC timezone',
    ]
    dst_dir = os.path.dirname(dst)
    if dst_dir:
        os.makedirs(dst_dir, exist_ok=True)
    copy_replace(data_file("../config/template/aiscalator.conf"),
                 dst, pattern=pattern, replace_value=replace_value)
    open(os.path.join(dst_dir, "apt_packages.txt"), 'a').close()
    open(os.path.join(dst_dir, "requirements.txt"), 'a').close()
    open(os.path.join(dst_dir, "lab_extensions.txt"), 'a').close()
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


def _app_config_file() -> str:
    """Return the path to the app configuration file."""
    if 'AISCALATOR_HOME' in os.environ:
        home = os.environ['AISCALATOR_HOME']
        file = os.path.join(home, "config", "aiscalator.conf")
        if os.path.exists(file):
            return file
    return os.path.join(os.path.expanduser("~"), '.aiscalator',
                        'config', 'aiscalator.conf')


# TODO refactor, splitting up the Global App Config part from
# Jupyter Config (step) and Airflow config (DAG) into 3 classes
# with separate APIs.
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
    _app_conf
        global configuration object for the application
    _config_path : str
        path to the configuration file (or plain configuration as string)
    _step_name : str
        name of the currently processed step
    _step
        configuration object for the currently processed step
    _dag_name : str
        name of the currently processed dag
    _dag
        configuration object for the currently processed dag
    """
    def __init__(self,
                 config=None,
                 step_selection=None,
                 dag_selection=None):
        """
        Parameters
            ----------
            config : str
                path to the step configuration file (or plain configuration
                string)
            step_selection : str
                Name of step from the configuration file to focus on
            dag_selection : str
                Name of dag from the configuration file to focus on
        """
        self._config_path = config
        self._app_conf = _setup_app_config()
        self._setup_logging()
        parsed_config = _parse_config(config)
        if parsed_config:
            step_sel = step_selection
            self._step_name, self._step = _select_config(parsed_config,
                                                         root_node='steps',
                                                         child_node='task',
                                                         selection=step_sel)
            self._dag_name, self._dag = _select_config(parsed_config,
                                                       root_node='dags',
                                                       child_node='definition',
                                                       selection=dag_selection)
        else:
            self._step_name = None
            self._step = None
            self._dag_name = None
            self._dag = None

    ###################################################
    # Global App Config methods                       #
    ###################################################

    def _setup_logging(self):
        """ Setup the logging configuration of the application """
        if self.app_config_has("logging"):
            log_config = self.app_config()["logging"]
            filename_list = [
                v['filename'] for k, v in
                _find_config_tree(log_config, "filename")
            ]
            # pre-create directory in advance for all loggers
            for file in filename_list:
                file_dir = os.path.dirname(file)
                if file_dir and not os.path.isdir(file_dir):
                    os.makedirs(file_dir, exist_ok=True)
            dictConfig(log_config)
        else:
            log = getLogger()
            handler = StreamHandler()
            formatter = Formatter(
                "%(asctime)s-%(threadName)s-%(name)s-%(levelname)s-%(message)s"
            )
            handler.setFormatter(formatter)
            log.addHandler(handler)
            log.setLevel(DEBUG)
        msg = ("Starting " + os.path.basename(__name__) +
               " version " + __version__ + " on " +
               "_".join(uname()).replace(" ", "_"))
        logger = getLogger(__name__)
        logger.debug(msg)

    def app_config_home(self) -> str:
        """Return the path to the app configuration folder."""
        if self.app_config_has("app_config_home_directory"):
            return self.app_config()["app_config_home_directory"]
        return os.path.join(os.path.expanduser("~"), '.aiscalator')

    def redefine_app_config_home(self, config_home):
        """
        Modify the configuration file to change the value of the
        application configuration home directory.

        Parameters
        ----------
        config_home : str
            path to the new configuration home

        Returns
        -------
        AiscalatorConfig
            the new configuration object
        """
        dst = _app_config_file()
        new_config = (
            pyhocon.ConfigFactory.parse_string(
                "aiscalator.app_config_home_directory = " + config_home
            )
        ).with_fallback(_app_config_file(), resolve=False)
        with open(dst, "w") as output:
            output.write(
                pyhocon.converter.HOCONConverter.to_hocon(new_config)
            )
        self._app_conf = new_config
        return new_config

    def redefine_airflow_workspaces(self, workspaces):
        """
        Modify the configuration file to change the value of the
        airflow workspaces

        Parameters
        ----------
        workspaces : list
            list of workspaces to bind to airflow

        Returns
        -------
        AiscalatorConfig
            the new configuration object
        """
        dst = _app_config_file()
        new_config = (
            pyhocon.ConfigFactory.parse_string(
                "aiscalator.airflow.setup.workspace_paths = [\n" +
                "\n".join([ws for ws in workspaces]) +
                "]"
            )
        ).with_fallback(_app_config_file(), resolve=False)
        with open(dst, "w") as output:
            output.write(
                pyhocon.converter.HOCONConverter.to_hocon(new_config)
            )
        self._app_conf = new_config
        return new_config

    def user_env_file(self, job=None) -> list:
        """
        Find a list of env files to pass to docker containers

        Parameters
        ----------
        job
            Optional step or dag config

        Returns
        -------
        List
            env files

        """
        logger = getLogger(__name__)
        result = []
        # Look if any env file or variables were defined in the step/dag
        if job:
            (_, env_filename) = mkstemp(prefix="aiscalator_", text=True)
            with open(env_filename, mode="w") as env_file:
                # concatenate all the env files and variables into one
                for env in job:
                    if isinstance(env, pyhocon.config_tree.ConfigTree):
                        for k in env.keys():
                            env_file.write(k + '=' + env.get(k) + '\n')
                    elif os.path.isfile(os.path.join(self.root_dir(), env)):
                        with open(os.path.join(self.root_dir(), env),
                                  mode="r") as file:
                            for line in file:
                                env_file.write(line)
                    else:
                        msg = ("Undefined env" + env +
                               ": expecting a dict of environment variables" +
                               " or path to environment configuration file.")
                        logger.warning("Warning %s", msg)
            result.append(env_filename)
        # TODO look in user config if env file has been redefined
        result.append(
            os.path.join(self.app_config_home(), "config", ".env")
        )
        return result

    def _timestamp_now(self) -> str:
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

    def config_path(self):
        """
        Returns
        -------
        str
            Returns the path to the step configuration file.
            If it was an URL, it will return the path to the temporary
            downloaded version of it.
            If it was a plain string, then returns None

        """
        if os.path.exists(self._config_path):
            if pyhocon.ConfigFactory.parse_file(self._config_path):
                return os.path.realpath(self._config_path)
        # TODO if string is url/git repo, download file locally first
        return None

    def root_dir(self):
        """
        Returns
        -------
        str
            Returns the path to the folder containing the
            configuration file
        """
        path = self.config_path()
        if path:
            root_dir = os.path.dirname(path)
            if not root_dir.endswith("/"):
                root_dir += "/"
            return root_dir
        return None

    def user_id(self) -> str:
        """
        Returns
        -------
        str
            the user id stored when the application was first setup
        """
        return self.app_config()["metadata.user.id"]

    def app_config_has(self, field) -> bool:
        """
        Tests if the applicatin config has a configuration
        value for the field.

        """
        if not self.app_config():
            return False
        return field in self.app_config()

    def airflow_docker_compose_file(self):
        """Return the configuration file to bring airflow services up."""
        if self.app_config_has("airflow.docker_compose_file"):
            return self.app_config()["airflow.docker_compose_file"]
        return None

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
        _validate_configs(self._app_conf, ref, msg,
                          missing_exception=True,
                          type_mismatch_exception=True)
        reference = data_file("../config/template/aiscalator.conf")
        ref = pyhocon.ConfigFactory.parse_file(reference)
        msg = "In Global Application Configuration file "
        _validate_configs(self._app_conf, ref, msg,
                          missing_exception=False,
                          type_mismatch_exception=True)
        if self._step_name:
            reference = data_file("../config/template/minimum_step.conf")
            ref = pyhocon.ConfigFactory.parse_file(reference)
            msg = "in step named " + self._step_name
            _validate_configs(self._step,
                              ref["steps"]["Untitled"],
                              msg,
                              missing_exception=True,
                              type_mismatch_exception=True)
            reference = data_file("../config/template/step.conf")
            ref = pyhocon.ConfigFactory.parse_file(reference)
            msg = "in step named " + self._step_name
            _validate_configs(self._step,
                              ref["steps"]["Untitled"],
                              msg,
                              missing_exception=False,
                              type_mismatch_exception=True)
        if self._dag_name:
            reference = data_file("../config/template/minimum_dag.conf")
            ref = pyhocon.ConfigFactory.parse_file(reference)
            msg = "in dag named " + self._dag_name
            _validate_configs(self._dag,
                              ref["dags"]["Untitled"],
                              msg,
                              missing_exception=True,
                              type_mismatch_exception=True)
            reference = data_file("../config/template/step.conf")
            ref = pyhocon.ConfigFactory.parse_file(reference)
            msg = "in dag named " + self._dag_name
            _validate_configs(self._dag,
                              ref["dags"]["Untitled"],
                              msg,
                              missing_exception=False,
                              type_mismatch_exception=True)

    ###################################################
    # Step methods                                    #
    ###################################################

    def step_notebook_output_path(self, notebook) -> str:
        """Generates the name of the output notebook"""
        return ("/home/jovyan/work/notebook_run/" +
                os.path.basename(notebook).replace(".ipynb", "") + "_" +
                self._timestamp_now() +
                self.user_id() +
                ".ipynb")

    def step_field(self, field):
        """
        Returns the value associated with the field for the currently
        focused step.

        """
        if self.has_step_field(field):
            return self._step[field]
        return None

    def has_step_field(self, field) -> bool:
        """
        Tests if the currently focused step has a configuration
        value for the field.

        """
        if not self._step:
            return False
        return field in self._step

    def step_name(self):
        """
        Returns the name of the currently focused step
        """
        return self._step_name

    def step_file_path(self, string):
        """
        Returns absolute path of a file from a field of the currently
        focused step.

        """
        if not self.has_step_field(string):
            return None
        # TODO handle url
        root_dir = self.root_dir()
        if root_dir:
            path = os.path.join(root_dir, self.step_field(string))
            return os.path.realpath(path)
        return os.path.realpath(self.step_field(string))

    def step_container_name(self) -> str:
        """Return the docker container name to execute this step"""
        return (
            self.step_field("task.type") +
            "_" +
            self.step_name().replace(".", "_")
        )

    def step_extract_parameters(self) -> list:
        """Returns a list of docker parameters"""
        result = []
        if self.has_step_field("task.parameters"):
            for param in self.step_field("task.parameters"):
                for key in param:
                    result += ["-p", key, param[key]]
        return result

    ###################################################
    # DAG methods                                     #
    ###################################################

    def dag_field(self, field):
        """
        Returns the value associated with the field for the currently
        focused dag.

        """
        if self.has_dag_field(field):
            return self._dag[field]
        return None

    def has_dag_field(self, field) -> bool:
        """
        Tests if the currently focused dag has a configuration
        value for the field.

        """
        if not self._dag:
            return False
        return field in self._dag

    def dag_name(self):
        """
        Returns the name of the currently focused dag
        """
        return self._dag_name

    def dag_file_path(self, string):
        """
        Returns absolute path of a file from a field of the currently
        focused dag.

        """
        if not self.has_dag_field(string):
            return None
        # TODO handle url
        root_dir = self.root_dir()
        if root_dir:
            path = os.path.join(root_dir, self.dag_field(string))
            return os.path.realpath(path)
        return os.path.realpath(self.dag_field(string))

    def dag_container_name(self) -> str:
        """Return the docker container name to execute this step"""
        return (
            "airflow_" +
            self.dag_name().replace(".", "_")
        )


def _setup_app_config():
    """
    Setup global application configuration.
    If not found in the default location, this method will generate
    a brand new one.

    """
    try:
        file = _app_config_file()
        conf = pyhocon.ConfigFactory.parse_file(file)
    except FileNotFoundError:
        conf = pyhocon.ConfigFactory.parse_file(_generate_global_config())
    # test if since_version is deprecated and regenerate a newer config
    return conf


def _validate_configs(test, reference, path,
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
    logger = getLogger(__name__)
    if isinstance(reference, pyhocon.config_tree.ConfigTree):
        for key in reference.keys():
            if key not in test.keys():
                msg = (path + ": Missing definition of " + key)
                if missing_exception:
                    raise pyhocon.ConfigMissingException(
                        message="Exception " + msg
                    )
                else:
                    logger.warning("Warning %s", msg)
            elif not isinstance(test[key], type(reference[key])):
                msg = (path + ": Type mismatch of " + key + " found type " +
                       str(type(test[key])) + " instead of " +
                       str(type(reference[key])))
                if type_mismatch_exception:
                    raise pyhocon.ConfigWrongTypeException(
                        message="Exception " + msg
                    )
                else:
                    logger.warning("Warning %s", msg)
            elif (isinstance(test[key], pyhocon.config_tree.ConfigTree) and
                  isinstance(reference[key], pyhocon.config_tree.ConfigTree)):
                # test recursively
                _validate_configs(test[key], reference[key],
                                  ".".join([path, key]),
                                  missing_exception,
                                  type_mismatch_exception)
            elif (isinstance(test[key], list) and
                  isinstance(reference[key], list)):
                # iterate through both collections
                for i in test[key]:
                    for j in reference[key]:
                        _validate_configs(i, j, ".".join([path, key]),
                                          missing_exception,
                                          type_mismatch_exception)


def _parse_config(step_config):
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


def _select_config(conf,
                   root_node: str, child_node: str,
                   selection: str):
    """
    Extract the list of step objects corresponding to
    the list of names provided.

    Parameters
    ----------
    conf
        step configuration object
    root_node : str
        node to start looking from
    child_node : str
        node that represents the leaves we are searching
        for. The path from root_node to child_node is compared
        with selection to check for a match.
    selection : str
        name of node to extract
    Returns
    -------
        tuple of (node_name, node) of selected
        configuration object
    """
    result = None
    candidates = []
    if conf and root_node in conf:
        candidates = _find_config_tree(conf[root_node], child_node)
        if selection:
            for name, candidate in candidates:
                if name == selection:
                    result = (name, candidate)
                    break
        else:
            result = candidates[0]
    if selection and not result:
        msg = (selection + "'s " + child_node +
               " was not found in " + root_node +
               " configurations.\n ")
        if candidates:
            msg += ("Available candidates are: " +
                    " ".join([name for name, _ in candidates]))
        raise pyhocon.ConfigMissingException(msg)
    return result


def _find_config_tree(tree: pyhocon.ConfigTree, target_node, path="") -> list:
    """
    Find all target_node objects in the Configuration object and report
    their paths.

    Parameters
    ----------
    tree : pyhocon.ConfigTree
        Configuration object
    target_node : str
        key of Config to find
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
        if key == target_node:
            result += [(path, tree)]
        else:
            if isinstance(tree[key], pyhocon.config_tree.ConfigTree):
                value = _find_config_tree(tree[key], target_node,
                                          path=next_path + key)
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
