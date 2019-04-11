# AUTHOR: Christophe Duong <chris@aiscalate.com>
# DESCRIPTION: Jupyter container tuned for AIscalator
# BUILD: docker build --rm -t aiscalator/jupyter-spark .
# SOURCE: https://github.com/aiscalate/aiscalator

# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-all-spark-notebook
FROM jupyter/minimal-notebook:4cdbc9cdb7d1
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

COPY install-jupytext.sh /home/jovyan/install-jupytext.sh

COPY req_docker.txt req_docker.txt

RUN pip install -r req_docker.txt \
    && python -m bash_kernel.install \
    && jupyter labextension install "@jupyterlab/celltags" \
    && bash "/home/jovyan/install-jupytext.sh" \
    && rm "/home/jovyan/install-jupytext.sh"

USER root
# optional additional apt_repository.txt:
# apt_repository.txt #

# optional additional apt_packages.txt:
# apt_packages.txt #
USER jovyan

# optional additional requirements.txt:
# requirements.txt #

# optional additional lab_extensions.txt:
# lab_extensions.txt #

COPY start-papermill.sh /home/jovyan/start-papermill.sh

RUN mkdir -p "/home/jovyan/work/notebook_run/" \
    && mkdir -p "/home/jovyan/work/modules/"
ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/work/modules/"
