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
from os.path import dirname
from os.path import isfile
from os.path import join
from tempfile import TemporaryDirectory

from aiscalator.core.config import AiscalatorConfig
from aiscalator.core.utils import copy_replace
from aiscalator.core.utils import subprocess_run


def docker_compose(conf: AiscalatorConfig,
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
    conf.validate_config()
    dockerfile = conf.find_user_config_file(
        "config/docker-compose-CeleryExecutor.yml"
    )
    commands = ["docker-compose"]
    # Prepare a temp folder to run the command from
    with TemporaryDirectory(prefix="aiscalator_") as tmp:
        with open(join(tmp, ".env"), mode="w") as env_file:
            # concatenate all the env files into one
            for env in conf.user_env_file():
                if isfile(env):
                    with open(env, mode="r") as file:
                        for line in file:
                            env_file.write(line)
        copy_replace(join(tmp, ".env"),
                     join(dirname(dockerfile), ".env"))
    commands += ["-f", dockerfile] + extra_commands
    subprocess_run(commands, no_redirect=True)


def airflow_setup(conf: AiscalatorConfig):
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
    conf.validate_config()
    logging.error("Not implemented yet")


def airflow_up(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    docker_compose(conf, ["up", "-d"])


def airflow_down(conf: AiscalatorConfig):
    """
    Stop an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    docker_compose(conf, ["down"])


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
    docker_compose(conf, commands)
