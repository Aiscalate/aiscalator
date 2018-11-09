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
CLI module for Airflow related commands.
"""
import logging
import click

from aiscalator import __version__
from aiscalator.core.config import AiscalatorConfig
from aiscalator.airflow import command


@click.group()
@click.version_option(version=__version__)
def airflow():
    """Author workflow DAGs and run tasks on schedule."""
    pass


@airflow.command()
def setup():
    """Setup interactively the Airflow home folder and configurations."""
    click.echo(command.airflow_setup(AiscalatorConfig()))


@airflow.command()
def start():
    """Start docker images to bring airflow services up."""
    click.echo(command.airflow_up(AiscalatorConfig()))
    click.echo("""
Airflow: http://localhost:8080
Flower: http://localhost:5555
               """)


@airflow.command()
def stop():
    """Stop docker images to bring airflow services down."""
    click.echo(command.airflow_down(AiscalatorConfig()))


@airflow.command()
@click.option("-s", "--service", default="webserver",
              help='Run subcommand in docker service (default webserver)',
              metavar='<service>')
@click.argument('subcommand', nargs=-1, required=True)
def run(service, subcommand):
    """Run sub-command in a running docker service."""
    if not subcommand:
        subcommand = None
    click.echo(command.airflow_cmd(AiscalatorConfig(),
                                   service=service, cmd=subcommand))

# TODO CLI to  scale celery workers
# docker-compose -f docker-compose-CeleryExecutor.yml scale worker=5


@airflow.command()
def new():
    """Create a new DAG job"""
    # TODO to implement
    logging.error("Not implemented yet")


@airflow.command()
def edit():
    """Edit DAG job"""
    # TODO to implement
    logging.error("Not implemented yet")


@airflow.command()
def push():
    """Push a job into the DAGS folder to schedule in Airflow."""
    # TODO to implement
    logging.error("Not implemented yet")
