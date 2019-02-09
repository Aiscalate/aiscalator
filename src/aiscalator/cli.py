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
Command Line Interface of the AIscalator tool.

Using the python click package (https://click.palletsprojects.com/en/7.x/),
this module defines all the entry points to the application.

"""
import logging
import sys

import click

from aiscalator import __version__
from aiscalator.airflow import cli as airflow_cli
from aiscalator.jupyter import cli as jupyter_cli


@click.group()
@click.version_option(version=__version__)
def main():
    """ Command Line Interface to Aiscalate your data pipelines """


@main.command()
@click.version_option(version=__version__)
def version():
    """Show the version and exit."""
    click.echo(sys.argv[0] + ', version ' + __version__)


@main.command()
@click.version_option(version=__version__)
def setup():
    """Setup the configuration of AIscalator applications"""
    # TODO to implement
    logging.error("Not implemented yet")


@main.command()
@click.version_option(version=__version__)
def cookiecutter():
    """Generates a cookiecutter project to AIscalate"""
    # TODO to implement
    logging.error("Not implemented yet")


main.add_command(airflow_cli.airflow)
main.add_command(jupyter_cli.jupyter)

# TODO - pull run docker pull to download all images that might be needed

# TODO - startproject command like cookiecutter to easily start a new
# TODO pipeline/step

# TODO - store config file path globally with an alias
# TODO and use those shorter alias for easier commands
# TODO - list steps/pipelines/data/etc

# docker rmi $(docker images --quiet --filter "dangling=true")
# docker kill $(docker ps -q)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
