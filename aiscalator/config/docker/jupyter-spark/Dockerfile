# AUTHOR: Christophe Duong <chris@aiscalate.com>
# DESCRIPTION: Jupyter container tuned for AIscalator
# BUILD: docker build --rm -t aiscalator/jupyter-spark .
# SOURCE: https://github.com/aiscalate/aiscalator

# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-all-spark-notebook
FROM jupyter/all-spark-notebook:50d1eb9ec2d8
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

COPY install-jupytext.sh /home/jovyan/install-jupytext.sh

RUN pip install pip==18.1 \
    && pip install papermill==0.15.1 \
    && pip install flake8==3.6.0 \
    && pip install jupytext==0.8.4 \
    && jupyter labextension install "@jupyterlab/celltags" \
    && bash "/home/jovyan/install-jupytext.sh" \
    && rm "/home/jovyan/install-jupytext.sh"

# optional additional apt_packages.txt:
#apt_packages.txt#

# optional additional requirements.txt:
#requirements.txt#

# optional additional lab_extensions.txt:
#lab_extensions.txt#

RUN mkdir -p "/home/jovyan/work/notebook_run/" \
    && mkdir -p "/home/jovyan/work/modules/"
ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/work/modules/"
