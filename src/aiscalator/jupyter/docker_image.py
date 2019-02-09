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
import logging
from os import chdir
from os import getcwd
from os import listdir
from os.path import isdir
from os.path import isfile
from os.path import join
from shutil import copy
from tempfile import TemporaryDirectory

from aiscalator.core import utils
from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.log_regex_analyzer import LogRegexAnalyzer


def build(conf: AiscalatorConfig):
    """
    Builds the docker image following the parameters specified in the
    focused step's configuration file

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for this step

    Returns
    -------
    string
        the docker artifact name of the image built
    """
    input_docker_src = conf.step_field("docker_image.input_docker_src")
    # TODO check if input_docker_src refers to an existing docker image
    # in which case, if no customization is needed, no need to build
    cwd = getcwd()
    result = None
    try:
        # Prepare a temp folder to build docker image
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            _prepare_build_dir(conf, tmp, input_docker_src)
            chdir(tmp)
            result = _run_build(conf)
    finally:
        chdir(cwd)
    return result


def _prepare_build_dir(conf, dst, input_docker_src):
    """
    Copies all necessary files for building docker images in a tmp folder,
    substituting some specific macros accordingly to handle customized
    images such as:
    - add-apt-repository
    - apt-install packages
    - pip install packages
    - jupyter lab extensions

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for this step
    dst : str
        temporary folder where to prepare the files
    input_docker_src : str
        name of the dockerfile package to use

    """
    input_docker_dir = utils.data_file("../config/docker/" + input_docker_src)

    if conf.app_config_has("jupyter.dockerfile_src"):
        # dockerfile is redefined in application configuration
        dockerfile_src = conf.app_config()["jupyter.dockerfile_src"]
        input_docker_dir = _find_docker_src(input_docker_src, dockerfile_src)

    if isdir(input_docker_dir):
        dockerfile = input_docker_dir + "/Dockerfile"
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            stg = "jupyter.docker_image"
            allow = (conf.app_config_has(stg + ".allow_apt_repository") and
                     conf.app_config()[stg + ".allow_apt_repository"])
            if allow:
                dockerfile = _include_apt_repo(conf, dockerfile,
                                               join(tmp, "apt_repository"))
            allow = (conf.app_config_has(stg + ".allow_apt_packages") and
                     conf.app_config()[stg + ".allow_apt_packages"])
            if allow:
                dockerfile = _include_apt_package(conf, dockerfile,
                                                  join(tmp, "apt_package"))
            allow = (conf.app_config_has(stg + ".allow_requirements") and
                     conf.app_config()[stg + ".allow_requirements"])
            if allow:
                dockerfile = _include_requirements(conf, dockerfile,
                                                   join(tmp, "requirements"),
                                                   dst)
            allow = (conf.app_config_has(stg +
                                         ".allow_lab_extensions") and
                     conf.app_config()[stg + ".allow_lab_extensions"])
            if allow:
                dockerfile = _include_lab_extensions(conf, dockerfile,
                                                     join(tmp,
                                                          "lab_extension"))
            copy(dockerfile, dst + '/Dockerfile')
        # copy the other files other than Dockerfile
        for file in listdir(input_docker_dir):
            if file != "Dockerfile":
                copy(join(input_docker_dir, file), join(dst, file))


def _find_docker_src(input_docker_src, dirs):
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
    return utils.data_file("../config/docker/" + input_docker_src)


def _include_apt_repo(conf: AiscalatorConfig, dockerfile, tmp):
    """
    Include add-apt-repository packages into the dockerfile

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for this step
    dockerfile : str
        path to the dockerfile to modify
    tmp : str
        path to the temporary dockerfile output

    Returns
    -------
        path to the resulting dockerfile
    """
    if conf.has_step_field("docker_image.apt_repository_path"):
        content = conf.step_file_path("docker_image.apt_repository_path")
        value = utils.format_file_content(content, prefix=" ", suffix="\\\n")
        if value:
            value = ("RUN apt-get update \\\n" +
                     " && apt-get install -yqq \\\n" +
                     "      software-properties-common \\\n" +
                     " && apt-add-repository \\\n" + value +
                     " && apt-get update")
            utils.copy_replace(dockerfile, tmp,
                               pattern="# apt_repository.txt #",
                               replace_value=value)
            return tmp
    return dockerfile


def _include_apt_package(conf: AiscalatorConfig, dockerfile, tmp):
    """
    Include apt-install packages into the dockerfile

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for this step
    dockerfile : str
        path to the dockerfile to modify
    tmp : str
        path to the temporary dockerfile output

    Returns
    -------
        path to the resulting dockerfile
    """
    if conf.has_step_field("docker_image.apt_package_path"):
        content = conf.step_file_path("docker_image.apt_package_path")
        value = utils.format_file_content(content, prefix=" ", suffix="\\\n")
        if value:
            value = ("RUN apt-get update && apt-get install -yqq \\\n" +
                     value +
                     """    && apt-get purge --auto-remove -yqq $buildDeps \\
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
            utils.copy_replace(dockerfile, tmp,
                               pattern="# apt_packages.txt #",
                               replace_value=value)
            return tmp
    return dockerfile


def _include_requirements(conf: AiscalatorConfig, dockerfile, tmp, dst):
    """
        Include pip install packages into the dockerfile

        Parameters
        ----------
        conf : AiscalatorConfig
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
    if conf.has_step_field("docker_image.requirements_path"):
        content = conf.step_file_path("docker_image.requirements_path")
        copy(content, join(dst, 'requirements.txt'))
        utils.copy_replace(dockerfile, tmp,
                           pattern="# requirements.txt #",
                           replace_value="""
    COPY requirements.txt requirements.txt
    RUN pip install -r requirements.txt
    RUN rm requirements.txt""")
        return tmp
    return dockerfile


def _include_lab_extensions(conf: AiscalatorConfig, dockerfile, tmp):
    """
        Include jupyter lab extensions packages into the dockerfile

        Parameters
        ----------
        conf : AiscalatorConfig
            Configuration object for this step
        dockerfile : str
            path to the dockerfile to modify
        tmp : str
            path to the temporary dockerfile output

        Returns
        -------
            path to the resulting dockerfile
        """
    if conf.has_step_field("docker_image.lab_extension_path"):
        content = conf.step_file_path("docker_image.lab_extension_path")
        prefix = "&& jupyter labextension install "
        value = utils.format_file_content(content,
                                          prefix=prefix, suffix=" \\\n")
        if value:
            value = "RUN echo 'Installing Jupyter Extensions' \\\n" + value
            utils.copy_replace(dockerfile, tmp,
                               pattern="# lab_extensions.txt #",
                               replace_value=value)
            return tmp
    return dockerfile


def _run_build(conf: AiscalatorConfig):
    """
    Run the docker build command to produce the image and tag it.

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for this step

    Returns
    -------
    str
        the docker image ID that was built
    """
    logger = logging.getLogger(__name__)
    commands = ["docker", "build", "--rm"]
    output_docker_name = None
    if conf.has_step_field("docker_image.output_docker_name"):
        output_docker_name = conf.step_field("docker_image.output_docker_name")
        commands += ["-t", output_docker_name + ":latest"]
    commands += ["."]
    log = LogRegexAnalyzer(b'Successfully built ([a-zA-Z0-9]+)\n')
    logger.info("Running...: %s", " ".join(commands))
    utils.subprocess_run(commands, log_function=log.grep_logs)
    result = log.artifact()
    test = (
        result and
        output_docker_name is not None and
        conf.has_step_field("docker_image.output_docker_tag")
    )
    if test:
        commands = ["docker", "tag"]
        output_docker_tag = conf.step_field("docker_image.output_docker_tag")
        commands += [result, output_docker_name + ":" + output_docker_tag]
        # TODO implement docker tag output_docker_tag_commit_hash
        logger.info("Running...: %s", " ".join(commands))
        utils.subprocess_run(commands)
    return result
