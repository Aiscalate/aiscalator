"""
Implementations of commands for Airflow
"""
import logging
from aiscalator.core.config import AiscalatorConfig, find_user_config_file
from aiscalator.core.utils import subprocess_run


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
    logging.error("Not implemented yet")
    pass


def airflow_up(conf: AiscalatorConfig):
    """
    Starts an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    dockerfile = find_user_config_file(
        "config/docker-compose-CeleryExecutor.yml"
    )
    commands = [
        "docker-compose", "-f",
        dockerfile,
        "up", "-d"
    ]
    subprocess_run(commands, no_redirect=True)


def airflow_down(conf: AiscalatorConfig):
    """
    Stop an airflow environment

    Parameters
    ----------
    conf : AiscalatorConfig
        Configuration object for the application

    """
    dockerfile = find_user_config_file(
        "config/docker-compose-CeleryExecutor.yml"
    )
    commands = [
        "docker-compose", "-f",
        dockerfile,
        "down"
    ]
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
    dockerfile = find_user_config_file(
        "config/docker-compose-CeleryExecutor.yml"
    )
    commands = [
        "docker-compose", "-f",
        dockerfile,
        "run", "--rm", service,
    ]
    if cmd is not None:
        commands += cmd
    else:
        commands += ["airflow"]
    subprocess_run(commands, no_redirect=True)
