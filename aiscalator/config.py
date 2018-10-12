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
    """Look for configuration files at multiple locations
    depending on how the application was installed"""
    for loc in [
        os.environ.get(env_key, ''),
        "resources",
        os.path.expanduser("~") + '.aiscalator/',
        os.getenv('VIRTUAL_ENV', '') + '/etc/aiscalator/'
    ]:
        try:
            path = os.path.join(loc, filename)
            with open(path, 'rt') as f:
                setup(f)
            return path
        except IOError:
            pass
    return None


def setup_logging(file):
    """Setup logging configuration
    """
    os.makedirs('/tmp/aiscalator/log', exist_ok=True)
    conf = safe_load(file.read())
    config.dictConfig(conf)


def setup_app_config(file):
    """Setup application configuration"""
    pass


class AiscalatorConfig(object):

    def __init__(self, config_path, notebook=None):
        self.config_path = config_path
        self.rootDir = os.path.dirname(config_path)
        if not self.rootDir.endswith("/"):
            self.rootDir += "/"
        log_level = os.getenv('AISCALATOR_LOG_LEVEL', None)
        path = find_global_config_file(
            "config/logging.yaml",
            setup_logging,
            'AISCALATOR_LOG_FILE'
        )
        if path is None:
            logging.basicConfig(level=logging.INFO)
        if log_level is not None:
            logging.root.setLevel(log_level)
        msg = ("Starting " + os.path.basename(__name__) +
               " version " + __version__ + " on " +
               "_".join(uname()).replace(" ", "_"))
        logging.debug(msg)
        find_global_config_file(
            "config/config.json",
            setup_app_config,
            "AISCALATOR_CONFIG"
        )
        # TODO: different formats, merge multiple files etc
        try:
            j = json.loads(config_path)
        except json.decoder.JSONDecodeError:
            try:
                with open(config_path, "r") as f:
                    j = json.load(f)
            except Exception as err2:
                logging.error("Invalid configuration file")
                raise err2
        logging.debug("Configuration file = " +
                      json.dumps(j, indent=4))
        self.conf = j
        self.step = None
        if notebook is not None:
            self.focus_step(notebook)
            if self.step is None:
                raise ValueError("Unknown step " + notebook)

    def focus_step(self, notebook):
        step = find(self.conf['step'], notebook)
        if step is not None:
            self.step = step
        elif notebook == "_":
            self.step = self.conf['step'][0]

    def step_field(self, field):
        if self.has_step_field(field):
            return self.step[field]
        else:
            return None

    def has_step_field(self, field):
            if self.step is None:
                return False
            else:
                return field in self.step

    def file_path(self, string):
        # TODO if string is url/git repo, download file locally first
        return os.path.abspath(self.rootDir + self.step_field(string))

    def container_name(self):
        return (
            self.step_field("type") +
            "_" +
            self.step_field("name")
        )

    def extract_parameters(self):
        result = []
        if self.has_step_field("parameters"):
            for p in self.step_field("parameters"):
                for k in p:
                    result += ["-p", k, p[k]]
        return result

    def notebook_output_path(self, notebook):
        return ("/home/jovyan/work/notebook_run/" +
                os.path.basename(notebook).replace(".ipynb", "") + "_" +
                self.timestamp_now() +
                # TODO params to string
                # TODO self.gconf.user()
                ".ipynb")

    def timestamp_now(self):
        d = datetime.utcnow().replace(tzinfo=timezone("UTC"))
        # TODO use config from self.gconf.get_timezone()
        pst = timezone('Europe/Paris')
        return d.astimezone(pst).strftime("%Y%m%d%H%M%S%f")

    def generate_global_config(self):
        # TODO when gconf file is not found, generate a new one from a template
        pass

