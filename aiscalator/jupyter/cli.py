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
CLI module for Jupyter related commands.
"""
import click
import logging

from aiscalator import __version__
from aiscalator.core.config import AiscalatorConfig
from aiscalator.jupyter import docker_command


@click.group()
@click.version_option(version=__version__)
def jupyter():
    """Notebook environment to explore and handle data."""
    pass


@jupyter.command()
def setup():
    """Setup the docker image to run notebooks."""
    # TODO: ask questions and generates json + ipynb files
    # TODO: afterward edit the newly created step
    logging.error("Not implemented yet")
    pass


@jupyter.command()
def new():
    """Create a new notebook file with a new aiscalate config."""
    # TODO: ask questions and generates json + ipynb files
    # TODO: afterward edit the newly created step
    logging.error("Not implemented yet")
    pass


@jupyter.command()
@click.argument('conf')
@click.argument('notebook', nargs=-1)
# TODO add parameters override from CLI
def edit(conf, notebook):
    """Edit the notebook from an aiscalate config with JupyterLab."""
    click.echo(docker_command.docker_run_lab(AiscalatorConfig(conf, notebook)))


@jupyter.command()
@click.argument('conf')
@click.argument('notebook', nargs=-1)
# TODO add parameters override from CLI
def run(conf, notebook):
    """Run the notebook from an aiscalate config without GUI."""
    # TODO run multiple notebooks
    # we have to stage notebooks with same dockerfile together,
    # merge their requirements so that groups of notebooks can be
    # run together in the same container sequentially
    click.echo(docker_command.docker_run_papermill(
        AiscalatorConfig(conf, notebook))
    )
