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
import os
from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.utils import subprocess_run


def docker_compose(conf: AiscalatorConfig):
    """
    Prepare a docker-compose command

    Parameters
    ----------
    conf : AiscalatorConfig
       Configuration object for the application
    Returns
    -------
    List
        The array of commands to start a docker-compose
        with the proper parameters
    """
    dockerfile = conf.find_user_config_file(
        "config/docker-compose-CeleryExecutor.yml"
    )
    commands = ["docker-compose"]
    for env in conf.user_env_file():
        if os.path.isfile(env):
            commands += ["--env-file", env]
    commands += ["-f", dockerfile]
    return commands


def airflow_setup(_: AiscalatorConfig):
    """
    Setup the airflow configuration files and environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    # docker build --build-arg DOCKER_GID=`getent group docker |
    # cut -d ':' -f 3` --rm -t aiscalator/airflow .
    # TODO : to implement
    logging.error("Not implemented yet")


def airflow_up(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    commands = docker_compose(conf) + ["up", "-d"]
    subprocess_run(commands, no_redirect=True)


def airflow_down(conf: AiscalatorConfig):
    """
    Stop an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    commands = docker_compose(conf) + ["down"]
    subprocess_run(commands, no_redirect=True)


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
    commands = docker_compose(conf) + [
        "run", "--rm", service,
    ]
    if cmd is not None:
        commands += cmd
    else:
        commands += ["airflow"]
    subprocess_run(commands, no_redirect=True)
