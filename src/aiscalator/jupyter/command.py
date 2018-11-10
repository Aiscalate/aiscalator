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
Implementations of commands for Jupyter
"""
import webbrowser
from logging import debug
from logging import info
from os import makedirs
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isfile
from os.path import join
from time import sleep

from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.config import convert_to_format
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer
from aiscalator.core.utils import copy_replace
from aiscalator.core.utils import data_file
from aiscalator.core.utils import subprocess_run
from aiscalator.jupyter.docker_image import build


def prepare_docker_env(step: AiscalatorConfig, program):
    """
    Assembles the list of commands to execute a docker run call

    When calling "docker run ...", this function also adds a set of
    additional parameters to mount the proper volumes and expose the
    correct environment for the call in the docker image mapped to the
    host directories. This is done so only some specific data and code
    folders are accessible within the docker image.

    Parameters
    ----------
    step : AiscalatorConfig
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
    # TODO: refactor using https://github.com/docker/docker-py ?
    commands = [
        "docker", "run", "--name", step.container_name(), "--rm",
        # TODO improve port publishing
        "-p", "10000:8888",
        "-p", "4040:4040"
    ]
    for env in step.user_env_file():
        if isfile(env):
            commands += ["--env-file", env]
    commands += prepare_docker_image_env(step)
    code_path = step.file_path('task.code_path')
    commands += [
        "--mount", "type=bind,source=" + dirname(code_path) +
        ",target=/home/jovyan/work/notebook/",
    ]
    commands += prepare_task_env(step)
    if step.has_step_field("task.execution_dir_path"):
        makedirs(step.file_path('task.execution_dir_path'), exist_ok=True)
        commands += [
            "--mount", "type=bind,source=" +
            step.file_path('task.execution_dir_path') +
            ",target=/home/jovyan/work/notebook_run/"
        ]
    commands += program
    debug("Running...: " + " ".join(commands))
    return commands


def prepare_docker_image_env(step: AiscalatorConfig):
    """
    Assemble the list of volumes to mount specific to
    building the docker image

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    list
        list of commands to bind those volumes
    """
    commands = []
    if step.step_config_path() is not None:
        commands += [
            "--mount", "type=bind,source=" + abspath(step.step_config_path()) +
            ",target=/home/jovyan/work/" + basename(step.step_config_path()),
        ]
    if step.has_step_field("docker_image.apt_package_path"):
        apt_packages = step.file_path('docker_image.apt_package_path')
        if apt_packages and isfile(apt_packages):
            commands += [
                "--mount", "type=bind,source=" + apt_packages +
                ",target=/home/jovyan/work/apt_packages.txt",
            ]
    if step.has_step_field("docker_image.requirements_path"):
        requirements = step.file_path('docker_image.requirements_path')
        if requirements and isfile(requirements):
            commands += [
                "--mount", "type=bind,source=" + requirements +
                ",target=/home/jovyan/work/requirements.txt",
            ]
    if step.has_step_field("docker_image.lab_extension_path"):
        lab_extensions = step.file_path('docker_image.lab_extension_path')
        if lab_extensions and isfile(lab_extensions):
            commands += [
                "--mount", "type=bind,source=" + lab_extensions +
                ",target=/home/jovyan/work/lab_extensions.txt",
            ]
    return commands


def prepare_task_env(step: AiscalatorConfig):
    """
    Assemble the list of volumes to mount specific to
    the task execution

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    list
        list of commands to bind those volumes
    """
    commands = []
    if step.root_dir():
        commands += mount_path(step, "task.modules_src_path",
                               "/home/jovyan/work/modules/")
        commands += mount_path(step, "task.input_data_path",
                               "/home/jovyan/work/data/input/",
                               readonly=True)
        commands += mount_path(step, "task.output_data_path",
                               "/home/jovyan/work/data/output/",
                               make_dirs=True)
    return commands


def mount_path(step: AiscalatorConfig, field, target_path,
               readonly=False, make_dirs=False):
    """
    Returu commands to mount path from list field into the
    docker image when running.

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for the step
    field : str
        the field in the configuration step that contains the path
    target_path : str
        where to mount them inside the container
    readonly : bool
        flag to mount the path as read-only
    make_dirs : bool
        flag to create the folder on the host before mounting if
        it doesn't exists.

    Returns
    -------
    list
        commands to mount all the paths from the field

    """
    commands = []
    if step.has_step_field(field):
        for value in step.step_field(field):
            # TODO handle URL
            for i in value:
                if make_dirs:
                    makedirs(abspath(step.root_dir() + i), exist_ok=True)
                if exists(step.root_dir() + i):
                    commands += [
                        "--mount",
                        "type=bind,source=" +
                        abspath(step.root_dir() + i) +
                        ",target=" + target_path + value[i] +
                        (",readonly" if readonly else "")
                    ]
    return commands


def jupyter_run(step: AiscalatorConfig, prepare_only=False):
    """
    Executes the step in browserless mode using papermill

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for the step
    prepare_only : bool
        Indicates if papermill should replace the parameters of the
        notebook only or it should execute all the cells too

    Returns
    -------
    string
        the path to the output notebook resulting from the execution
        of this step
    """
    step.validate_config()
    docker_image = build(step)
    notebook = ("/home/jovyan/work/notebook/" +
                basename(step.file_path('task.code_path')))
    notebook_output = step.notebook_output_path(notebook)
    parameters = step.extract_parameters()
    commands = prepare_docker_env(step, [
        docker_image, "start.sh",
        # TODO: check step type, if jupyter then papermill
        "papermill",
        notebook, notebook_output
    ])
    if prepare_only:
        commands.append("--prepare-only")
    commands += parameters
    logger = LogRegexAnalyzer()
    # TODO output log in its own execution log file
    subprocess_run(commands, log_function=logger.grep_logs)
    # TODO handle notebook_output execution history and latest successful run
    return notebook_output


def jupyter_edit(step: AiscalatorConfig):
    """
    Starts a Jupyter Lab environment configured to edit the focused step

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    string
        Url of the running jupyter lab
    """
    step.validate_config()
    docker_image = build(step)
    # TODO: shutdown other jupyter lab still running
    notebook = basename(step.step_field('task.code_path'))
    if step.extract_parameters():
        jupyter_run(step, prepare_only=True)
    commands = prepare_docker_env(step, [
        docker_image, "start.sh",
        'jupyter', 'lab'
    ])
    logger = LogRegexAnalyzer(b'http://.*:8888/.token=([a-zA-Z0-9]+)\n')
    subprocess_run(commands, log_function=logger.grep_logs, wait=False)
    for i in range(5):
        sleep(2)
        if logger.artifact():
            break
        info("docker run does not seem to be up yet... retrying ("
             + str(i) + "/5)")
    if logger.artifact():
        # TODO handle url better (not always localhost?)
        url = ("http://localhost:10000/lab/tree/work/notebook/" +
               notebook + "?token=" +
               logger.artifact())
        info(url + " is up and running.")
        # TODO --no-browser option
        webbrowser.open(url)
        return url
    return ""


def jupyter_new(name, path, output_format="hocon"):
    """
    Starts a Jupyter Lab environment configured to edit a brand new step

    Parameters
    ----------
    name : str
        name of the new step
    path : str
        path to where the new step files should be created
    output_format : str
        the format of the new configuration file to produce
    Returns
    -------
    string
        Url of the running jupyter lab
    """
    step_file = join(path, name, name) + '.conf'
    makedirs(dirname(step_file), exist_ok=True)
    copy_replace(data_file("../config/template/step.conf"), step_file,
                 pattern="Untitled", replace_value=name)
    if output_format != 'hocon':
        file = join(path, name, name) + '.' + output_format
        step_file = convert_to_format(step_file, output=file,
                                      output_format=output_format)

    notebook_file = join(path, name, 'notebook', name) + '.ipynb'
    makedirs(dirname(notebook_file), exist_ok=True)
    copy_replace(data_file("../config/template/notebook.json"), notebook_file)

    open(join(path, name, "apt_packages.txt"), 'a').close()
    open(join(path, name, "requirements.txt"), 'a').close()
    open(join(path, name, "lab_extensions.txt"), 'a').close()
    jupyter_edit(AiscalatorConfig(step_config=step_file,
                                  steps_selection=[name]))
