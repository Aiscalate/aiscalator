# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-all-spark-notebook
FROM jupyter/all-spark-notebook:latest
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

COPY install-jupytext.sh /home/jovyan/install-jupytext.sh

RUN pip install --upgrade pip \
    && pip install papermill \
    && pip install flake8 \
    && pip install jupytext \
    && jupyter labextension install @jupyterlab/celltags \
    && bash /home/jovyan/install-jupytext.sh

# optional additional requirements.txt:
#requirements.txt#

ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/work/modules/"
