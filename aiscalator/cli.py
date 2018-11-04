# -*- coding: utf-8 -*-
"""
Command Line Interface of the AIscalator tool.

Using the python click package (https://click.palletsprojects.com/en/7.x/),
this module defines all the entry points to the application.

"""
import sys
import click

from aiscalator import __version__
from aiscalator.airflow import cli as airflow_cli
from aiscalator.jupyter import cli as jupyter_cli


@click.group()
@click.version_option(version=__version__)
def main():
    """ Command Line Interface to Aiscalate your data pipelines """
    pass


@main.command()
def version():
    """Show the version and exit."""
    click.echo(sys.argv[0] + ', version ' + __version__)


main.add_command(airflow_cli.airflow)
main.add_command(jupyter_cli.jupyter)

# TODO - pull run docker pull to download all images that might be needed

# TODO - startproject command like cookiecutter to easily start a new
# TODO pipeline/step

# TODO - store config file path globally with an alias
# TODO and use those shorter alias for easier commands
# TODO - list steps/pipelines/data/etc


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
