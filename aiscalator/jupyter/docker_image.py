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
Module responsible to build docker images for jupyter subcommands
"""
from logging import debug
from os import chdir, getcwd, listdir
from os.path import isfile, join, isdir
from shlex import quote

from shutil import copy
from tempfile import TemporaryDirectory

from aiscalator.core.utils import copy_replace, subprocess_run, data_file
from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer


def build(step: AiscalatorConfig):
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
    input_docker_src = step.step_field("docker_image.input_docker_src")
    # TODO check if input_docker_src refers to an existing docker image
    # in which case, if no customization is needed, no need to build
    cwd = getcwd()
    try:
        # Prepare a temp folder to build docker image
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            prepare_build_dir(step, tmp, input_docker_src)
            chdir(tmp)
            result = run_build(step)
    finally:
        chdir(cwd)
    return result


def prepare_build_dir(step, dst, input_docker_src):
    """
    Copies all necessary files for building docker images in a tmp folder,
    substituting some specific macros accordingly to handle customized
    images such as:
    - apt-install packages
    - pip install packages
    - jupyter lab extensions

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for this step
    dst : str
        temporary folder where to prepare the files
    input_docker_src : str
        name of the dockerfile package to use

    """
    input_docker_dir = data_file("../config/docker/" + input_docker_src)

    if step.app_config_has("jupyter.dockerfile_src"):
        # dockerfile is redefined in application configuration
        dockerfile_src = step.app_config()["jupyter.dockerfile_src"]
        input_docker_dir = find_docker_src(input_docker_src, dockerfile_src)

    if isdir(input_docker_dir):
        dockerfile = input_docker_dir + "/Dockerfile"
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            # TODO check app_config to see if we allow the following:
            dockerfile = include_apt_package(step, dockerfile,
                                             join(tmp, "apt_package"))
            dockerfile = include_requirements(step, dockerfile,
                                              join(tmp, "requirements"),
                                              dst)
            dockerfile = include_lab_extensions(step, dockerfile,
                                                join(tmp, "lab_extension"))
            copy(dockerfile, dst + '/Dockerfile')
        for file in listdir(input_docker_dir):
            if file != "Dockerfile":
                copy(join(input_docker_dir, file), join(dst, file))


def find_docker_src(input_docker_src, dirs):
    """
    Finds a pre-configured dockerfile package or return the default one.

    Parameters
    ----------
    input_docker_src : str
        name of the dockerfile package to use
    dirs : list
        list of directories to check

    Returns
    -------
    str
        path to the corresponding dockerfile package
    """
    for src in dirs:
        if isfile(join(src, input_docker_src, "Dockerfile")):
            return src
    return data_file("../config/docker/" + input_docker_src)


def include_apt_package(step: AiscalatorConfig, dockerfile, tmp):
    """
    Include apt-install packages into the dockerfile

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for this step
    dockerfile : str
        path to the dockerfile to modify
    tmp : str
        path to the temporary dockerfile output

    Returns
    -------
        path to the resulting dockerfile
    """
    if step.has_step_field("docker_image.apt_package_path"):
        content = step.file_path("docker_image.apt_package_path")
        value = format_file_content(content, suffix="\\\n")
        if value:
            value = ("RUN apt-get install -yqq \\\n" + value + """
    && apt-get purge --auto-remove -yqq $buildDeps \\
    && apt-get autoremove -yqq --purge \\
    && apt-get clean \\
    && rm -rf \\
        /var/lib/apt/lists/* \\
        /tmp/* \\
        /var/tmp/* \\
        /usr/share/man \\
        /usr/share/doc \\
        /usr/share/doc-base
        """)
            copy_replace(dockerfile, tmp,
                         pattern="#apt_packages.txt#",
                         replace_value=value)
            return tmp
    return dockerfile


def include_requirements(step: AiscalatorConfig, dockerfile, tmp, dst):
    """
        Include pip install packages into the dockerfile

        Parameters
        ----------
        step : AiscalatorConfig
            Configuration object for this step
        dockerfile : str
            path to the dockerfile to modify
        tmp : str
            path to the temporary dockerfile output
        dst : str
            path to the final temporary directory

        Returns
        -------
            path to the resulting dockerfile
        """
    if step.has_step_field("docker_image.requirements_path"):
        content = step.file_path("docker_image.requirements_path")
        copy(content, join(dst, 'requirements.txt'))
        copy_replace(dockerfile, tmp,
                     pattern="#requirements.txt#",
                     replace_value="""
    COPY requirements.txt requirements.txt
    RUN pip install -r requirements.txt
    RUN rm requirements.txt""")
        return tmp
    return dockerfile


def include_lab_extensions(step: AiscalatorConfig, dockerfile, tmp):
    """
        Include jupyter lab extensions packages into the dockerfile

        Parameters
        ----------
        step : AiscalatorConfig
            Configuration object for this step
        dockerfile : str
            path to the dockerfile to modify
        tmp : str
            path to the temporary dockerfile output

        Returns
        -------
            path to the resulting dockerfile
        """
    if step.has_step_field("docker_image.lab_extension_path"):
        content = step.file_path("docker_image.lab_extension_path")
        prefix = "&& jupyter labextension install "
        value = format_file_content(content,
                                    prefix=prefix, suffix=" \\\n")
        if value:
            value = "RUN echo 'Installing Jupyter Extensions' \\\n" + value
            copy_replace(dockerfile, tmp,
                         pattern="#lab_extensions.txt#",
                         replace_value=value)
            return tmp
    return dockerfile


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
            result += prefix + quote(line) + suffix
    return result


def run_build(step: AiscalatorConfig):
    """
    Run the docker build command to produce the image and tag it.

    Parameters
    ----------
    step : AiscalatorConfig
        Configuration object for this step

    Returns
    -------
    str
        the docker image ID that was built
    """
    commands = ["docker", "build", "--rm"]
    output_docker_name = None
    if step.has_step_field("docker_image.output_docker_name"):
        output_docker_name = step.step_field("docker_image.output_docker_name")
        commands += ["-t", output_docker_name + ":latest"]
    commands += ["."]
    debug("Running...: " + " ".join(commands))
    logger = LogRegexAnalyzer(b'Successfully built ([a-zA-Z0-9]+)\n')
    subprocess_run(commands, log_function=logger.grep_logs)
    result = logger.artifact()
    test = (
        result and
        output_docker_name is not None and
        step.has_step_field("docker_image.output_docker_tag")
    )
    if test:
        commands = ["docker", "tag"]
        output_docker_tag = step.step_field("docker_image.output_docker_tag")
        commands += [result, output_docker_name + ":" + output_docker_tag]
        # TODO implement docker tag output_docker_tag_commit_hash
        debug("Running...: " + " ".join(commands))
        subprocess_run(commands)
    return result
