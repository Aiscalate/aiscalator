from datetime import datetime
import json
import logging
from logging import config
import os
from pytz import timezone

from platform import uname
from yaml import safe_load
from . import __version__


from .utils import find


def find_global_config_file(filename, setup=(lambda x: x), env_key=""):
    """Looks for configuration files and run the setup function with it:

    This function will try to find the configuration filename at multiple
    locations:

        - From environment variable specified as env_key
        - From the development source tree: resources/
        - From user's home directory: ~/.aiscalator/
        - From virtual environment installation folder of data_files as
          specified in the setup.py

    Parameters
    ----------
    filename : string
        filename of the configuration file to find
    setup : function(x -> x)
        callback function to run with the valid configuration file found
    env_key : string
        environment variable name pointing to configuration file to load

    Returns
    -------
    string
        The path of the configuration that was found
    """
    for loc in [
        # from the environment variables
        os.environ.get(env_key, ''),
        # from the development folder
        "resources",
        # from user home
        os.path.expanduser("~") + '.aiscalator/',
        # from virtual environment install
        os.getenv('VIRTUAL_ENV', '') + '/etc/aiscalator/'
    ]:
        try:
            path = os.path.join(loc, filename)
            with open(path, 'rt') as f:
                setup(f)
            return path
        except IOError:
            pass
    setup(None)
    return None


def setup_logging():
    """ Setup the logging configuration of the application """
    log_level = os.getenv('AISCALATOR_LOG_LEVEL', None)
    path = find_global_config_file(
        "config/logging.yaml", load_logging_conf, 'AISCALATOR_LOG_FILE'
    )
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
    def __init__(self, config_path=None, notebook=None):
        """
        Parameters
            ----------
            config_path : string
                path to the step configuration file
            notebook : string
                name of the step from the configuration file to focus on
        """
        self.config_path = config_path
        if config_path is None:
            self.rootDir = None
        else:
            self.rootDir = os.path.dirname(config_path)
            if not self.rootDir.endswith("/"):
                self.rootDir += "/"
        setup_logging()
        find_global_config_file(
            "config/config.json", self.setup_app_config, "AISCALATOR_CONFIG"
        )
        self.conf = self.setup_step_config()
        self.step = self.focus_step(notebook)

    def setup_app_config(self, file):
        """Setup application configuration"""
        if file is None:
            file = generate_global_config()
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
        if notebook is None:
            result = self.conf['step'][0]
        else:
            step = find(self.conf['step'], notebook)
            if step is not None:
                result = step
            elif notebook == "_":
                result = self.conf['step'][0]
        if result is None:
            raise ValueError("Unknown step " + notebook)
        return result

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
