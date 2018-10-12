from logging import info, debug
from os import chdir, getcwd, makedirs
from os.path import basename, dirname, abspath
from re import search
from shutil import copy
from tempfile import TemporaryDirectory
from time import sleep
import webbrowser

from .utils import copy_replace, subprocess_run
from .config import find_global_config_file, AiscalatorConfig


class DockerLogAnalyzer(object):

    def __init__(self, pattern=None):
        self.artifact = "latest"
        self.pattern = pattern

# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    def log_docker_build(self, pipe):
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            # TODO improve logging in its own subprocess log file?
            info(line)
            if self.pattern is not None:
                m = search(self.pattern, line)
                if m:
                    self.artifact = m.group(1).decode("utf-8")


def docker_build(step: AiscalatorConfig):
    # Retrieve configuration parameters
    dockerfilename = step.step_field('dockerfile')
    if dockerfilename is None:
        dockerfilename = "spark_template.conf"
    dockerfile = find_global_config_file("docker/" + dockerfilename)
    docker_image_name = step.step_field('dockerImageName')
    requirements = step.file_path('requirementsPath')
    cwd = getcwd()
    try:
        # Prepare a temp folder to build docker image
        with TemporaryDirectory(prefix="aiscalator_") as tmp:
            # copy the dockerfile
            if requirements is not None:
                copy_replace(dockerfile, tmp + '/Dockerfile',
                             '#requirements.txt#', """
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm requirements.txt"""
                             )
                copy(requirements, tmp + '/requirements.txt')
            else:
                copy(dockerfile, tmp + '/Dockerfile')
            chdir(tmp)
            debug("Running...: docker build --rm -t " +
                  docker_image_name + " .")
            logger = DockerLogAnalyzer(b'Successfully built (\w+)\n')
            subprocess_run([
                "docker", "build", "--rm", "-t", docker_image_name, "."
            ], log_function=logger.log_docker_build)
            result = logger.artifact
    finally:
        chdir(cwd)
    return result


def prepare_docker_run_notebook(step: AiscalatorConfig, program):
    commands = [
        "docker", "run", "--name", step.container_name(), "--rm",
        "-p", "10000:8888",
     ]
    # TODO improve port publishing
    filename = (step.file_path('path'))
    commands += [
        "--mount", "type=bind,source=" + dirname(filename) +
        ",target=/home/jovyan/work/notebook/",
        "--mount", "type=bind,source=" + abspath(step.config_path) +
                   ",target=/home/jovyan/work/" + basename(step.config_path),
    ]
    requirements = step.file_path('requirementsPath')
    if requirements is not None:
        commands += [
            "--mount", "type=bind,source=" + requirements +
                       ",target=/home/jovyan/work/requirements.txt",
        ]
    for v in step.step_field("modulesPath"):
        # TODO support readonly flag in config & bind vs tmpfs types
        for i in v:
            # TODO check if v[i] is relative path?
            commands += [
                "--mount", "type=bind,source=" + abspath(step.rootDir + i) +
                ",target=/home/jovyan/work/modules/" + v[i]
            ]
    for v in step.step_field("inputPath"):
        for i in v:
            # TODO check if v[i] is relative path?
            commands += [
                "--mount", "type=bind,source=" + abspath(step.rootDir + i) +
                ",target=/home/jovyan/work/data/input/" + v[i] +
                ",readonly"
            ]
    for v in step.step_field("outputPath"):
        for i in v:
            # TODO check if v[i] is relative path?
            makedirs(abspath(step.rootDir + i), exist_ok=True)
            commands += [
                "--mount", "type=bind,source=" + abspath(step.rootDir + i) +
                ",target=/home/jovyan/work/data/output/" + v[i]
            ]
    # TODO if filename does not exist, generate one
    commands += program
    debug("Running...: " + " ".join(commands))
    return commands


def docker_run_papermill(step: AiscalatorConfig, prepare_only=False):
    docker_image = docker_build(step)
    notebook = ("/home/jovyan/work/notebook/" +
                basename(step.file_path('path')))
    notebook_output = step.notebook_output_path(notebook)
    parameters = step.extract_parameters()
    makedirs(step.file_path('executionDirPath'), exist_ok=True)
    commands = prepare_docker_run_notebook(step, [
            "--mount", "type=bind,source=" +
                       step.file_path('executionDirPath') +
            ",target=/home/jovyan/work/notebook_run/",
            docker_image, "start.sh",
            # TODO: check step type, if jupyter then papermill
            "papermill", notebook, notebook_output
    ])
    if prepare_only:
        commands.append("--prepare-only")
    commands += parameters
    logger = DockerLogAnalyzer()
    # TODO output log in its own execution log file
    subprocess_run(commands, log_function=logger.log_docker_build)
    # TODO handle notebook_output execution history and latest successful run
    return notebook_output


def docker_run_lab(step: AiscalatorConfig):
    docker_image = docker_build(step)
    # TODO: shutdown other jupyter lab still running
    notebook = basename(step.step_field('path'))
    if len(step.extract_parameters()) > 0:
        docker_run_papermill(step, prepare_only=True)
    makedirs(step.file_path('executionDirPath'), exist_ok=True)
    commands = [
        "--mount",
        "type=bind,source=" + step.file_path('executionDirPath') +
        ",target=/home/jovyan/work/notebook_run/",
    ]
    commands = prepare_docker_run_notebook(step, commands + [
        docker_image, "start.sh", 'jupyter', 'lab'
    ])
    logger = DockerLogAnalyzer(b'http://.*:8888/\?token=(\w+)\n')
    subprocess_run(commands, log_function=logger.log_docker_build, wait=False)
    for i in range(5):
        sleep(2)
        if logger.artifact != "latest":
            break
        info("docker run does not seem to be up yet... retrying ("
             + str(i) + "/5)")
    if logger.artifact != "latest":
        # TODO handle url better (not always localhost)
        url = ("http://localhost:10000/lab/tree/work/notebook/" +
               notebook + "?token=" +
               logger.artifact)
        info(url + " is up and running.")
        # TODO --no-browser option
        webbrowser.open(url)
        return url
    else:
        return ""
