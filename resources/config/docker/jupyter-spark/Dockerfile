# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-all-spark-notebook
FROM jupyter/all-spark-notebook:latest
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

RUN pip install --upgrade pip \
    && pip install papermill \
    && pip install flake8

RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash

ENV NVM_DIR "${HOME}/.nvm"

RUN . $NVM_DIR/nvm.sh \
    && nvm install --lts \
    && jupyter labextension install @jupyterlab/celltags

# optional additional requirements.txt:
#requirements.txt#

ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/work/modules/"
