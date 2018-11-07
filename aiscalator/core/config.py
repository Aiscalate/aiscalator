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
from datetime import datetime
import json
import logging
from logging import config
import os
from pytz import timezone

from platform import uname
from yaml import safe_load
from aiscalator import __version__
from aiscalator.core.utils import find, data_file


def setup_logging():
    """ Setup the logging configuration of the application """
    log_level = os.getenv('AISCALATOR_LOG_LEVEL', None)

    with open(data_file("../config/logging.yaml"), 'rt') as f:
        path = load_logging_conf(f)
    if path is None:
        logging.basicConfig(level=logging.INFO)
    if log_level is not None:
        logging.root.setLevel(log_level)
    msg = ("Starting " + os.path.basename(__name__) +
           " version " + __version__ + " on " +
           "_".join(uname()).replace(" ", "_"))
    logging.debug(msg)


def load_logging_conf(file):
    """Reads and loads the logging configuration file"""
    if file is not None:
        os.makedirs('/tmp/aiscalator/log', exist_ok=True)
        conf = safe_load(file.read())
        config.dictConfig(conf)
        return file
    return None


def generate_global_config():
    """Generate a standard configuration file for the application in the
    user's home folder ~/.aiscalator/config/config.json
    """
    # TODO when gconf file is not found, generate a new one from a template
    return ""


class AiscalatorConfig(object):
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
    config_path : string
        path to the step configuration file
    rootDir : string
        path to the directory containing the configuration file
    conf : string
        step configuration after loading the file
    step : string
        step name the application is currently focusing on
    """
    def __init__(self, step_config_path=None, notebook=None):
        """
        Parameters
            ----------
            step_config_path : string
                path to the step configuration file
            notebook : List
                name of the step from the configuration file to focus on
        """
        self.config_path = step_config_path
        if step_config_path is None:
            self.rootDir = None
        else:
            self.rootDir = os.path.dirname(step_config_path)
            if not self.rootDir.endswith("/"):
                self.rootDir += "/"
        setup_logging()
        try:
            f = open(self.find_user_config_file("config/config.json"), "rt")
        except Exception:
            generate_global_config()
            f = open(data_file("../config/config.json"), "rt")
        self.setup_app_config(f)
        f.close()
        self.conf = self.setup_step_config()
        self.step = self.focus_step(notebook)

    def setup_app_config(self, file):
        """Setup application configuration"""
        print(file)
        # TODO: different formats, merge multiple files etc

    def setup_step_config(self):
        """Setup step configuration"""
        if self.config_path is None:
            return None
        try:
            j = json.loads(self.config_path)
        except json.decoder.JSONDecodeError:
            try:
                with open(self.config_path, "r") as f:
                    j = json.load(f)
            except Exception as err2:
                logging.error("Invalid configuration file")
                raise err2
        logging.debug("Configuration file = " + json.dumps(j, indent=4))
        return j

    def focus_step(self, notebook):
        """Find the notebook in the step configuration"""
        result = None
        if self.config_path is None:
            return None
        if notebook is None or len(notebook) == 0:
            result = self.conf['step'][0]
        else:
            step = find(self.conf['step'], notebook[0])
            if step is not None:
                result = step
            elif notebook == "_":
                result = self.conf['step'][0]
        if result is None:
            raise ValueError("Unknown step " + notebook[0])
        return result

    def find_user_config_file(self, filename):
        """
        Looks for configuration files in the user configuration folder

        Parameters
        ----------
        filename : string
            file to search for

        Returns
        -------
        string
            path to the filename in the user configuration folder
        """
        # TODO check user_config_folder override in environment
        # TODO check if user_config_folder has been redefined on command line
        return os.path.expanduser("~") + '/.aiscalator/' + filename

    def user_env_file(self):
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

    def notebook_output_path(self, notebook):
        """Generates the name of the output notebook"""
        return ("/home/jovyan/work/notebook_run/" +
                os.path.basename(notebook).replace(".ipynb", "") + "_" +
                self.timestamp_now() +
                # TODO params to string
                # TODO self.gconf.user()
                ".ipynb")

    def timestamp_now(self):
        """Depending on how the timezone is configured, returns the
         timestamp for now
        """
        d = datetime.utcnow().replace(tzinfo=timezone("UTC"))
        # TODO use config from self.gconf.get_timezone()
        pst = timezone('Europe/Paris')
        return d.astimezone(pst).strftime("%Y%m%d%H%M%S%f")

    def step_field(self, field):
        """Returns the value associated with the field for the focused step"""
        if self.has_step_field(field):
            return self.step[field]
        else:
            return None

    def has_step_field(self, field):
        """Tests if the focus step has a configuration value for the field"""
        if self.step is None:
            return False
        else:
            return field in self.step

    def file_path(self, string):
        """Returns absolute path of a file from a field of the focused step"""
        # TODO if string is url/git repo, download file locally first
        return os.path.abspath(self.rootDir + self.step_field(string))

    def container_name(self):
        """Return the docker container name to execute this step"""
        return (
            self.step_field("type") +
            "_" +
            self.step_field("name")
        )

    def extract_parameters(self):
        """Returns a list of docker parameters"""
        result = []
        if self.has_step_field("parameters"):
            for p in self.step_field("parameters"):
                for k in p:
                    result += ["-p", k, p[k]]
        return result
