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
import logging
import os.path
from os import makedirs

from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.config import convert_to_format
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer
from aiscalator.core.utils import copy_replace
from aiscalator.core.utils import data_file
from aiscalator.core.utils import subprocess_run
from aiscalator.core.utils import wait_for_jupyter_lab
from aiscalator.jupyter.docker_image import build


def _prepare_docker_env(conf: AiscalatorConfig, program):
    """
    Assembles the list of commands to execute a docker run call

    When calling "docker run ...", this function also adds a set of
    additional parameters to mount the proper volumes and expose the
    correct environment for the call in the docker image mapped to the
    host directories. This is done so only some specific data and code
    folders are accessible within the docker image.

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
    # TODO: refactor using https://github.com/docker/docker-py ?
    commands = [
        "docker", "run", "--name", conf.step_container_name(), "--rm",
        # TODO improve port publishing
        "-p", "10000:8888",
        "-p", "4040:4040"
    ]
    for env in conf.user_env_file():
        if os.path.isfile(env):
            commands += ["--env-file", env]
    commands += _prepare_docker_image_env(conf)
    code_path = conf.step_file_path('task.code_path')
    commands += [
        "--mount", "type=bind,source=" + os.path.dirname(code_path) +
        ",target=/home/jovyan/work/notebook/",
    ]
    commands += _prepare_task_env(conf)
    if conf.has_step_field("task.execution_dir_path"):
        makedirs(conf.step_file_path('task.execution_dir_path'), exist_ok=True)
        commands += [
            "--mount", "type=bind,source=" +
            conf.step_file_path('task.execution_dir_path') +
            ",target=/home/jovyan/work/notebook_run/"
        ]
    commands += program
    return commands


def _prepare_docker_image_env(conf: AiscalatorConfig):
    """
    Assemble the list of volumes to mount specific to
    building the docker image

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    list
        list of commands to bind those volumes
    """
    commands = []
    if conf.config_path() is not None:
        commands += [
            "--mount",
            "type=bind,source=" + os.path.realpath(conf.config_path()) +
            ",target="
            "/home/jovyan/work/" + os.path.basename(conf.config_path()),
        ]
    if conf.has_step_field("docker_image.apt_package_path"):
        apt_packages = conf.step_file_path('docker_image.apt_package_path')
        if apt_packages and os.path.isfile(apt_packages):
            commands += [
                "--mount", "type=bind,source=" + apt_packages +
                ",target=/home/jovyan/work/apt_packages.txt",
            ]
    if conf.has_step_field("docker_image.requirements_path"):
        requirements = conf.step_file_path('docker_image.requirements_path')
        if requirements and os.path.isfile(requirements):
            commands += [
                "--mount", "type=bind,source=" + requirements +
                ",target=/home/jovyan/work/requirements.txt",
            ]
    if conf.has_step_field("docker_image.lab_extension_path"):
        lab_extensions = conf.step_file_path('docker_image.lab_extension_path')
        if lab_extensions and os.path.isfile(lab_extensions):
            commands += [
                "--mount", "type=bind,source=" + lab_extensions +
                ",target=/home/jovyan/work/lab_extensions.txt",
            ]
    return commands


def _prepare_task_env(conf: AiscalatorConfig):
    """
    Assemble the list of volumes to mount specific to
    the task execution

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    list
        list of commands to bind those volumes
    """
    commands = []
    if conf.root_dir():
        commands += _mount_path(conf, "task.modules_src_path",
                                "/home/jovyan/work/modules/")
        commands += _mount_path(conf, "task.input_data_path",
                                "/home/jovyan/work/data/input/",
                                readonly=True)
        commands += _mount_path(conf, "task.output_data_path",
                                "/home/jovyan/work/data/output/",
                                make_dirs=True)
    return commands


def _mount_path(conf: AiscalatorConfig, field, target_path,
                readonly=False, make_dirs=False):
    """
    Returu commands to mount path from list field into the
    docker image when running.

    Parameters
    ----------
    conf : AiscalatorConfig
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
    if conf.has_step_field(field):
        for value in conf.step_field(field):
            # TODO handle URL
            for i in value:
                if make_dirs:
                    makedirs(os.path.realpath(conf.root_dir() + i),
                             exist_ok=True)
                if os.path.exists(conf.root_dir() + i):
                    commands += [
                        "--mount",
                        "type=bind,source=" +
                        os.path.realpath(conf.root_dir() + i) +
                        ",target=" + target_path + value[i] +
                        (",readonly" if readonly else "")
                    ]
    return commands


def jupyter_run(conf: AiscalatorConfig, prepare_only=False):
    """
    Executes the step in browserless mode using papermill

    Parameters
    ----------
    conf : AiscalatorConfig
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
    logger = logging.getLogger(__name__)
    conf.validate_config()
    docker_image = build(conf)
    if not docker_image:
        raise Exception("Failed to build docker image")
    notebook = ("/home/jovyan/work/notebook/" +
                os.path.basename(conf.step_file_path('task.code_path')))
    notebook_output = conf.step_notebook_output_path(notebook)
    parameters = conf.step_extract_parameters()
    commands = _prepare_docker_env(conf, [
        docker_image, "start.sh",
        # TODO: check step type, if jupyter then papermill
        "papermill",
        notebook, notebook_output
    ])
    if prepare_only:
        commands.append("--prepare-only")
    commands += parameters
    log = LogRegexAnalyzer()
    logger.info("Running...: %s", " ".join(commands))
    subprocess_run(commands, log_function=log.grep_logs)
    # TODO handle notebook_output execution history and latest successful run
    return notebook_output


def jupyter_edit(conf: AiscalatorConfig):
    """
    Starts a Jupyter Lab environment configured to edit the focused step

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the step

    Returns
    -------
    string
        Url of the running jupyter lab
    """
    logger = logging.getLogger(__name__)
    conf.validate_config()
    docker_image = build(conf)
    if docker_image:
        # TODO: shutdown other jupyter lab still running
        notebook = os.path.basename(conf.step_field('task.code_path'))
        if conf.step_extract_parameters():
            jupyter_run(conf, prepare_only=True)
        commands = _prepare_docker_env(conf, [
            docker_image, "start.sh",
            'jupyter', 'lab'
        ])
        return wait_for_jupyter_lab(commands, logger, notebook,
                                    10000, "work/notebook")
    raise Exception("Failed to build docker image")


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
    step_file = os.path.join(path, name, name) + '.conf'
    makedirs(os.path.dirname(step_file), exist_ok=True)
    copy_replace(data_file("../config/template/step.conf"), step_file,
                 pattern="Untitled", replace_value=name)
    if output_format != 'hocon':
        file = os.path.join(path, name, name) + '.' + output_format
        step_file = convert_to_format(step_file, output=file,
                                      output_format=output_format)

    notebook_file = os.path.join(path, name, 'notebook', name) + '.ipynb'
    makedirs(os.path.dirname(notebook_file), exist_ok=True)
    copy_replace(data_file("../config/template/notebook.json"), notebook_file)

    open(os.path.join(path, name, "apt_packages.txt"), 'a').close()
    open(os.path.join(path, name, "requirements.txt"), 'a').close()
    open(os.path.join(path, name, "lab_extensions.txt"), 'a').close()
    jupyter_edit(AiscalatorConfig(config=step_file,
                                  step_selection=name))
