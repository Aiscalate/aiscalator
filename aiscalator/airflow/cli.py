"""
CLI module for Airflow related commands.
"""
import click
from aiscalator import __version__
from aiscalator.core.config import AiscalatorConfig
from aiscalator.airflow import airflow_command


@click.group()
@click.version_option(version=__version__)
def airflow():
    """Author workflow DAGs and run tasks on schedule."""
    pass


@airflow.command()
def setup():
    """Setup interactively the Airflow home folder and configurations."""
    click.echo(airflow_command.airflow_setup(AiscalatorConfig()))


@airflow.command()
def start():
    """Start docker images to bring airflow services up."""
    click.echo(airflow_command.airflow_up(AiscalatorConfig()))
    click.echo("""
Airflow: http://localhost:8080
Flower: http://localhost:5555
               """)


@airflow.command()
def stop():
    """Stop docker images to bring airflow services down."""
    click.echo(airflow_command.airflow_down(AiscalatorConfig()))


@airflow.command()
@click.option("-s", "--service", default="webserver",
              help='Run subcommand in docker service (default webserver)',
              metavar='<service>')
@click.argument('subcommand', nargs=-1, required=True)
def run(service, subcommand):
    """Run sub-command in a running docker service."""
    if len(subcommand) == 0:
        subcommand = None
    click.echo(airflow_command.airflow_cmd(AiscalatorConfig(),
                                           service=service, cmd=subcommand))

# TODO CLI to  scale celery workers
# docker-compose -f docker-compose-CeleryExecutor.yml scale worker=5
