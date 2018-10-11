# -*- coding: utf-8 -*-

"""Console script for aiscalator."""
import sys
import click
import json

from .edit_command import edit_command
from .run_command import run_command


@click.group()
def main():
    """
    Command Line Interface to Aiscalate your data pipelines
    """
    pass


def parse_config(conf):
    try:
        j = json.loads(conf)
    except json.decoder.JSONDecodeError as err1:
        try:
            with open(conf, "r") as f:
                j = json.load(f)
        except Exception as err2:
            print("Invalid configuration file", file=sys.stderr)
            raise err2
    print("Configuration file:", file=sys.stderr)
    print(json.dumps(j, indent=4), file=sys.stderr)
    return j


@main.command()
@click.argument('conf')
@click.argument('notebook')
def edit(conf, notebook):
    "Open an environment to edit notebook's code (in Jupyter Lab)"
    click.echo(edit_command(parse_config(conf), notebook))


@main.command()
@click.argument('conf')
@click.argument('notebook')
def run(conf, notebook):
    "Run notebook's code without GUI (through Papermill)"
    click.echo(run_command(parse_config(conf), notebook))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
