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
from os.path import expanduser
from os.path import join

import click

from aiscalator import __version__
from aiscalator.airflow import command
from aiscalator.core.config import AiscalatorConfig


@click.group()
@click.version_option(version=__version__)
def airflow():
    """Author workflow DAGs and run tasks on schedule."""


@airflow.command()
@click.version_option(version=__version__)
@click.option('-d', '--config-home', 'config_home',
              default=join(expanduser("~"), '.aiscalator'),
              help="Redefine the location of the application home directory.")
@click.option('--append/--replace', 'append', default=False)
@click.argument('workspace', nargs=-1, required=True,
                type=click.Path())
def setup(config_home, append, workspace):
    """Setup interactively the Airflow home folder and configurations."""
    click.echo(command.airflow_setup(AiscalatorConfig(),
                                     config_home, workspace,
                                     append=append))


@airflow.command()
@click.version_option(version=__version__)
def update():
    """
    Checks and tries to update the current docker image
    to run airflow to a newer version.

    Initiates a docker pull of the latest images we are depending on
    and build the next aiscalator images from there.
    Before replacing the version tags in the Dockerfile, we make sure
    to do a maximum in the background while still having a working
    image in the meantime.

    """
    # TODO to implement
    logging.error("Not implemented yet")


@airflow.command()
@click.version_option(version=__version__)
def start():
    """Start docker images to bring airflow services up."""
    click.echo(command.airflow_up(AiscalatorConfig()))
    click.echo("""
Airflow: http://localhost:8080
Flower: http://localhost:5555
               """)


@airflow.command()
@click.version_option(version=__version__)
def stop():
    """Stop docker images to bring airflow services down."""
    click.echo(command.airflow_down(AiscalatorConfig()))


@airflow.command()
@click.option("-s", "--service", default="webserver",
              help='Run subcommand in docker service (default webserver)',
              metavar='<service>')
@click.argument('subcommand', nargs=-1, required=True)
@click.version_option(version=__version__)
def run(service, subcommand):
    """Run sub-command in a running docker service."""
    if not subcommand:
        subcommand = None
    click.echo(command.airflow_cmd(AiscalatorConfig(),
                                   service=service, cmd=subcommand))

# TODO CLI to  scale celery workers
# docker-compose -f docker-compose-CeleryExecutor.yml scale worker=5


@airflow.command()
@click.option('--name', prompt='What is the name of your dag?',
              help="Name of the new dag to create",
              metavar='<DAG>')
@click.option('-f', '--format', 'output_format',
              help="format of the configuration file (default is hocon)",
              type=click.Choice(['json', 'hocon']),
              default='hocon')
@click.argument('path', type=click.Path())
@click.version_option(version=__version__)
def new(name, output_format, path):
    """Create a new DAG job"""
    # TODO to implement
    logging.error("Not implemented yet %s %s %s",
                  name, output_format, path)


@airflow.command()
@click.argument('conf', type=click.Path(exists=True))
@click.argument('notebook', nargs=-1)
@click.version_option(version=__version__)
def edit(conf, notebook):
    """Edit DAG job"""
    if len(notebook) < 2:
        notebook = notebook[0] if notebook else None
        app_config = AiscalatorConfig(config=conf,
                                      dag_selection=notebook)
        click.echo(command.airflow_edit(app_config))
    else:
        raise click.BadArgumentUsage("Expecting one or less notebook names")


@airflow.command()
@click.argument('conf', type=click.Path(exists=True))
@click.argument('notebook', nargs=-1)
@click.version_option(version=__version__)
def push(conf, notebook):
    """Push a job into the DAGS folder to schedule in Airflow."""
    if notebook:
        for note in notebook:
            app_config = AiscalatorConfig(config=conf,
                                          dag_selection=note)
            click.echo(command.airflow_push(app_config))
    else:
        app_config = AiscalatorConfig(config=conf)
        click.echo(command.airflow_push(app_config))
