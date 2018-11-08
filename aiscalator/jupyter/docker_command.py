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
from logging import info, debug
from os import chdir, getcwd, makedirs, listdir
from os.path import basename, dirname, abspath, isfile, join
from shutil import copy
from tempfile import TemporaryDirectory
from time import sleep
import webbrowser

from aiscalator.core.utils import copy_replace, subprocess_run, data_file
from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer


def docker_build(step: AiscalatorConfig):
    """
    Builds the docker image following the parameters specified in the
    focused step's configuration file

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for this step

    Returns
    -------
    string
        the docker artifact name of the image built
    """
    # Retrieve configuration parameters
    # TODO check validity of dockerfilename (choice are jupyter-spark)
    dockerfilename = step.step_field('dockerfile')
    if dockerfilename is None:
        dockerfilename = "jupyter-spark"
    dockerfiledir = data_file("../config/docker/" + dockerfilename)
    docker_image_name = step.step_field('dockerImageName')
    requirements = step.file_path('requirementsPath')
    cwd = getcwd()
    try:
        # Prepare a temp folder to build docker image
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            # copy the dockerfile
            if requirements is not None and isfile(requirements):
                copy_replace(dockerfiledir + "/Dockerfile",
                             tmp + '/Dockerfile',
                             '#requirements.txt#', """
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm requirements.txt"""
                             )
                copy(requirements, tmp + '/requirements.txt')
            else:
                copy(dockerfiledir + "/Dockerfile", tmp + '/Dockerfile')
            for file in listdir(dockerfiledir):
                if file != "Dockerfile":
                    copy(join(dockerfiledir, file), join(tmp, file))
            chdir(tmp)
            debug("Running...: docker build --rm -t " +
                  docker_image_name + " .")
            logger = LogRegexAnalyzer(b'Successfully built ([a-zA-Z0-9]+)\n')
            subprocess_run([
                "docker", "build", "--rm", "-t", docker_image_name, "."
            ], log_function=logger.grep_logs)
            result = logger.artifact
    finally:
        chdir(cwd)
    return result


def prepare_docker_run_notebook(step: AiscalatorConfig, program):
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
    commands = [
        "docker", "run", "--name", step.container_name(), "--rm",
        "-p", "10000:8888",
        "-p", "4040:4040"
    ]
    for env in step.user_env_file():
        if isfile(env):
            commands += ["--env-file", env]
    # TODO improve port publishing
    filename = (step.file_path('path'))
    commands += [
        "--mount", "type=bind,source=" + dirname(filename) +
        ",target=/home/jovyan/work/notebook/",
        "--mount", "type=bind,source=" + abspath(step.config_path) +
        ",target=/home/jovyan/work/" + basename(step.config_path),
    ]
    requirements = step.file_path('requirementsPath')
    if requirements is not None and isfile(requirements):
        commands += [
            "--mount", "type=bind,source=" + requirements +
            ",target=/home/jovyan/work/requirements.txt",
        ]
    for value in step.step_field("modulesPath"):
        # TODO support readonly flag in config & bind vs tmpfs types
        for i in value:
            # TODO check if v[i] is relative path?
            commands += [
                "--mount", "type=bind,source=" + abspath(step.root_dir + i) +
                ",target=/home/jovyan/work/modules/" + value[i]
            ]
    for value in step.step_field("inputPath"):
        for i in value:
            # TODO check if v[i] is relative path?
            commands += [
                "--mount", "type=bind,source=" + abspath(step.root_dir + i) +
                ",target=/home/jovyan/work/data/input/" + value[i] +
                ",readonly"
            ]
    for value in step.step_field("outputPath"):
        for i in value:
            # TODO check if v[i] is relative path?
            makedirs(abspath(step.root_dir + i), exist_ok=True)
            commands += [
                "--mount", "type=bind,source=" + abspath(step.root_dir + i) +
                ",target=/home/jovyan/work/data/output/" + value[i]
            ]
    # TODO if filename does not exist, generate one
    commands += program
    debug("Running...: " + " ".join(commands))
    return commands


def docker_run_papermill(step: AiscalatorConfig, prepare_only=False):
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
    docker_image = docker_build(step)
    notebook = ("/home/jovyan/work/notebook/" +
                basename(step.file_path('path')))
    notebook_output = step.notebook_output_path(notebook)
    parameters = step.extract_parameters()
    makedirs(step.file_path('executionDirPath'), exist_ok=True)
    commands = prepare_docker_run_notebook(step, [
        "--mount", "type=bind,source=" +
        step.file_path('executionDirPath') +
        ",target=/home/jovyan/work/notebook_run/",
        docker_image, "start.sh",
        # TODO: check step type, if jupyter then papermill
        "papermill", notebook, notebook_output
    ])
    if prepare_only:
        commands.append("--prepare-only")
    commands += parameters
    logger = LogRegexAnalyzer()
    # TODO output log in its own execution log file
    subprocess_run(commands, log_function=logger.grep_logs)
    # TODO handle notebook_output execution history and latest successful run
    return notebook_output


def docker_run_lab(step: AiscalatorConfig):
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
    docker_image = docker_build(step)
    # TODO: shutdown other jupyter lab still running
    notebook = basename(step.step_field('path'))
    if step.extract_parameters():
        docker_run_papermill(step, prepare_only=True)
    makedirs(step.file_path('executionDirPath'), exist_ok=True)
    commands = [
        "--mount",
        "type=bind,source=" + step.file_path('executionDirPath') +
        ",target=/home/jovyan/work/notebook_run/",
    ]
    commands = prepare_docker_run_notebook(step, commands + [
        docker_image, "start.sh", 'jupyter', 'lab'
    ])
    logger = LogRegexAnalyzer(b'http://.*:8888/.token=([a-zA-Z0-9]+)\n')
    subprocess_run(commands, log_function=logger.grep_logs, wait=False)
    for i in range(5):
        sleep(2)
        if logger.artifact != "latest":
            break
        info("docker run does not seem to be up yet... retrying ("
             + str(i) + "/5)")
    if logger.artifact != "latest":
        # TODO handle url better (not always localhost?)
        url = ("http://localhost:10000/lab/tree/work/notebook/" +
               notebook + "?token=" +
               logger.artifact)
        info(url + " is up and running.")
        # TODO --no-browser option
        webbrowser.open(url)
        return url
    return ""


def docker_new(name, path):
    """
    Starts a Jupyter Lab environment configured to edit a brand new step

    Parameters
    ----------
    name : string
        name of the new step
    path : path
        path to where the new step files should be created

    Returns
    -------
    string
        Url of the running jupyter lab
    """
    step_file = join(path, name, name) + '.json'
    makedirs(dirname(step_file), exist_ok=True)
    copy_replace(data_file("../config/template/step.json"), step_file,
                 pattern="Untitled", replace_value=name)

    notebook_file = join(path, name, 'notebook', name) + '.ipynb'
    makedirs(dirname(notebook_file), exist_ok=True)
    copy_replace(data_file("../config/template/notebook.json"), notebook_file)

    open(join(path, name, "requirements.txt"), 'a').close()
    docker_run_lab(AiscalatorConfig(step_file, [name]))
