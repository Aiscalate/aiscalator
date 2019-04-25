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
Implementations of commands for Airflow
"""
import logging
import re
from grp import getgrgid
from os import listdir
from os import makedirs
from os import remove
from os import stat
from os import symlink
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isfile
from os.path import islink
from os.path import join
from os.path import realpath
from tempfile import TemporaryDirectory

from aiscalator.core import utils
from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer


def _docker_compose(conf: AiscalatorConfig,
                    extra_commands: list):
    """
    Run the docker-compose command

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application
    extra_commands : list
        list of sub-commands to run in docker-compose

    """
    logger = logging.getLogger(__name__)
    conf.validate_config()
    dockerfile = join(conf.app_config_home(), "config",
                      conf.airflow_docker_compose_file())
    commands = ["docker-compose"]
    # Prepare a temp folder to run the command from
    with TemporaryDirectory(prefix="aiscalator_") as tmp:
        with open(join(tmp, ".env"), mode="w") as env_file:
            # concatenate all the env files into one
            for env in conf.user_env_file(conf.dag_field("definition.env")):
                if isfile(env):
                    with open(env, mode="r") as file:
                        for line in file:
                            env_file.write(line)
        utils.copy_replace(join(tmp, ".env"),
                           join(dirname(dockerfile), ".env"))
    commands += ["-f", dockerfile] + extra_commands
    logger.info("Running...: %s", " ".join(commands))
    utils.subprocess_run(commands, no_redirect=True)


def airflow_setup(conf: AiscalatorConfig,
                  config_home: str,
                  workspace: list,
                  append: bool = True):
    """
    Setup the airflow configuration files and environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application
    config_home : str
        path to the configuration home directory
    workspace : list
        List of path to directories to mount as volumes
        to airflow workers to use as workspaces
    append : bool
        flag to tell if workspace should be appended to
        the list in the config or replace it.

    """
    logger = logging.getLogger(__name__)
    conf.validate_config()
    if config_home:
        makedirs(config_home, exist_ok=True)
        conf.redefine_app_config_home(config_home)
    ws_path = "airflow.setup.workspace_paths"
    if conf.app_config_has(ws_path):
        if append:
            workspace += conf.app_config()[ws_path]
    conf.redefine_airflow_workspaces(workspace)
    image = 'latest'
    if _docker_compose_grep(conf):
        image = _airflow_docker_build(conf)
        if not image:
            raise Exception("Failed to build docker image")
    src = utils.data_file("../config/docker/airflow/config/")
    dst = join(conf.app_config_home(), "config")
    logger.info("Generating a new configuration folder for aiscalator:\n\t%s",
                dst)
    makedirs(dst, exist_ok=True)
    makedirs(join(conf.app_config_home(), "dags"), exist_ok=True)
    makedirs(join(conf.app_config_home(), "pgdata"), exist_ok=True)
    makedirs(join(conf.app_config_home(), "workspace"), exist_ok=True)
    pattern = [
        r"(\s+)# - workspace #",
        "aiscalator/airflow:latest",
    ]
    workspace = []
    for line in conf.app_config()[ws_path]:
        host_src, container_dst = _split_workspace_string(conf, line)
        # bind the same path from host in the container (after creating a
        # symbolic link at container_dst path)
        workspace += [r"\1- " + host_src + ':' + host_src]
    workspace += [r"\1# - workspace #"]
    value = [
        "\n".join(workspace),
        "aiscalator/airflow:" + image,
    ]
    for file in listdir(src):
        utils.copy_replace(join(src, file),
                           join(dst, file),
                           pattern=pattern,
                           replace_value=value)


def airflow_up(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    if _docker_compose_grep(conf):
        if not _airflow_docker_build(conf):
            raise Exception("Failed to build docker image")
    _docker_compose(conf, ["up", "-d"])


def _docker_compose_grep(conf: AiscalatorConfig):
    """
    Checks if the docker-compose file is using the
    aiscalator/airflow docker image. In which case,
    we need to make sure that image is properly built
    and available.

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    Returns
    -------
    bool
        Returns if aiscalator/airflow docker image is
        needed and should be built.
    """
    docker_compose_file = join(conf.app_config_home(), "config",
                               conf.airflow_docker_compose_file())
    pattern = re.compile(r"\s+image:\s+aiscalator/airflow")
    try:
        with open(docker_compose_file, "r") as file:
            for line in file:
                if re.match(pattern, line):
                    # docker compose needs the image
                    return True
    except FileNotFoundError:
        # no docker compose, default will need the image
        return True
    return False


def _airflow_docker_build(conf: AiscalatorConfig):
    """ Build the aiscalator/airflow image and return its ID."""
    logger = logging.getLogger(__name__)
    # TODO get airflow dockerfile from conf?
    conf.app_config_home()
    dockerfile_dir = utils.data_file("../config/docker/airflow")
    # TODO customize dockerfile with apt_packages, requirements etc
    docker_gid, docker_group = _find_docker_gid_group()
    commands = [
        "docker", "build",
        "--build-arg", "DOCKER_GID=" + str(docker_gid),
        "--build-arg", "DOCKER_GROUP=" + str(docker_group),
        "--rm", "-t", "aiscalator/airflow:latest",
        dockerfile_dir
    ]
    log = LogRegexAnalyzer(b'Successfully built ([a-zA-Z0-9]+)\n')
    logger.info("Running...: %s", " ".join(commands))
    utils.subprocess_run(commands, log_function=log.grep_logs)
    result = log.artifact()
    if result:
        # tag the image built with the sha256 of the dockerfile
        tag = utils.sha256(join(dockerfile_dir, 'Dockerfile'))[:12]
        commands = [
            "docker", "tag", result, "aiscalator/airflow:" + tag
        ]
        logger.info("Running...: %s", " ".join(commands))
        utils.subprocess_run(commands)
        return tag
    return None


def _find_docker_gid_group():
    """Returns the group ID and name owning the /var/run/docker.sock file"""
    stat_info = stat('/var/run/docker.sock')
    if stat_info:
        gid = stat_info.st_gid
        return gid, getgrgid(gid)[0]
    return None, None


def airflow_down(conf: AiscalatorConfig):
    """
    Stop an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    _docker_compose(conf, ["down"])


def airflow_cmd(conf: AiscalatorConfig, service="webserver", cmd=None):
    """
    Execute an airflow subcommand

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application
    service : string
        service name of the container where to run the command
    cmd : list
        subcommands to run
    """
    commands = [
        "run", "--rm", service,
    ]
    if cmd is not None:
        commands += cmd
    else:
        commands += ["airflow"]
    _docker_compose(conf, commands)


def airflow_edit(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    logger = logging.getLogger(__name__)
    conf.validate_config()
    docker_image = _airflow_docker_build(conf)
    if docker_image:
        # TODO: shutdown other jupyter lab still running
        port = 10001
        notebook = basename(conf.dag_field('definition.code_path'))
        notebook, notebook_py = utils.notebook_file(notebook)
        commands = _prepare_docker_env(conf, [
            "aiscalator/airflow:" + docker_image, "bash",
            "/start-jupyter.sh",
            "/usr/local/airflow/work/" + notebook_py +
            ":/usr/local/airflow/dags/" + notebook_py
        ], port)
        return utils.wait_for_jupyter_lab(commands, logger, notebook,
                                          port, "work")
    raise Exception("Failed to build docker image")


def _prepare_docker_env(conf: AiscalatorConfig, program, port):
    """
    Assembles the list of commands to execute a docker run call

    When calling "docker run ...", this function also adds a set of
    additional parameters to mount the proper volumes and expose the
    correct environment for the call in the docker image.

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the step
    program : List
        the rest of the commands to execute as part of
        the docker run call

    Returns
    -------
    List
        The full Array of Strings representing the commands to execute
        in the docker run call
    """
    logger = logging.getLogger(__name__)
    commands = [
        "docker", "run", "--name", conf.dag_container_name() + "_edit",
        "--rm",
        # TODO improve port publishing
        "-p", str(port) + ":8888",
        "-p", "18080:8080",
    ]
    for env in conf.user_env_file(conf.dag_field("definition.env")):
        if isfile(env):
            commands += ["--env-file", env]
    commands += [
        "--mount", "type=bind,source=/var/run/docker.sock,"
                   "target=/var/run/docker.sock",
    ]
    code_path = conf.dag_file_path('definition.code_path')
    notebook, _ = utils.notebook_file(code_path)
    utils.check_notebook_dir(logger, notebook)
    commands += [
        "--mount", "type=bind,source=" + dirname(notebook) +
        ",target=/usr/local/airflow/work/",
    ]
    if conf.config_path() is not None:
        commands += [
            "--mount",
            "type=bind,source=" + abspath(conf.config_path()) +
            ",target="
            "/usr/local/airflow/" + basename(conf.config_path()),
        ]
    workspace = []
    ws_path = "airflow.setup.workspace_paths"
    if conf.app_config_has(ws_path):
        ws_home = join(conf.app_config_home(),
                       "workspace")
        makedirs(ws_home, exist_ok=True)
        for folder in conf.app_config()[ws_path]:
            src, dst = _split_workspace_string(conf, folder)
            # bind the same path from host in the container (after creating
            # a symbolic link at dst path)
            workspace += [src + ":" + src]
            commands += [
                "--mount", "type=bind,source=" + src +
                ",target=" + src
            ]
        commands += [
            "--mount", "type=bind,source=" + ws_home +
            ",target=/usr/local/airflow/workspace/"
        ]
    commands += program + workspace
    return commands


def _split_workspace_string(conf: AiscalatorConfig, workspace):
    """
    Interprets the workspace string and split into src and dst
    paths:
    - The src is a path on the host machine.
    - The dst is a path on the container.
    In case, the workspace string doesn't specify both paths
    separated by a ':', this function will automatically mount it
    in the $app_config_home_directory/work/ folder creating a
    symbolic link with the same basename as the workspace.

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the step
    workspace : str
        the workspace string to interpret
    Returns
    -------
    (str, str)
        A tuple with both src and dst paths
    """
    logger = logging.getLogger(__name__)
    root_dir = conf.app_config_home()
    if workspace.strip():
        if ':' in workspace:
            src = abspath(workspace.split(':')[0])
            if not src.startswith('/'):
                src = abspath(join(root_dir, src))
            dst = workspace.split(':')[1]
            if not dst.startswith('/'):
                dst = abspath(join(root_dir, dst))
        else:
            src = abspath(workspace)
            if not src.startswith('/'):
                src = abspath(join(root_dir, src))
            # in the workspace special folder, we'll create the same named
            # folder (basename) that is actually a link back to the one
            # we want to include in our workspace.
            dst = join("workspace", basename(workspace.strip('/')))
            link = join(root_dir, dst)
            if realpath(src) != realpath(link):
                if exists(link) and islink(link):
                    logger.warning("Removing an existing symbolic"
                                   " link %s -> %s",
                                   link, realpath(link))
                    remove(link)
                if not exists(link):
                    logger.info("Creating a symbolic link %s -> %s", link, src)
                    symlink(src, link)
            dst = "/usr/local/airflow/" + dst
        return src, dst
    return None, None


def airflow_push(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    # TODO to implement
    logging.error("Not implemented yet %s", conf.app_config_home())
