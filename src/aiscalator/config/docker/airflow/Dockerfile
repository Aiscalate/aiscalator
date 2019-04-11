# AUTHOR: Christophe Duong <chris@aiscalate.com>
# DESCRIPTION: Airflow container tuned for AIscalator
# BUILD: docker build --build-arg DOCKER_GID=`getent group docker | cut -d ':' -f 3` --rm -t aiscalator/airflow .
# SOURCE: https://github.com/aiscalate/aiscalator

FROM puckel/docker-airflow:1.10.2
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

ARG AIRFLOW_HOME=/usr/local/airflow
ARG DOCKER_GID
ARG DOCKER_GROUP
# Reuse host GID for docker group in container
USER root
RUN groupadd -r -g ${DOCKER_GID} ${DOCKER_GROUP} || true

ENV HOME ${AIRFLOW_HOME}

# https://docs.docker.com/install/linux/docker-ce/debian/
RUN apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
     apt-transport-https \
     ca-certificates \
     gnupg2 \
     software-properties-common \
     build-essential \
     git \
     netcat \
     python-dev \
     unzip \
     nano \
     wget \
     less \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY req_docker.txt req_docker.txt

RUN curl -fsSL "https://download.docker.com/linux/debian/gpg" | apt-key add - \
    && add-apt-repository \
        "deb [arch=amd64] \
        https://download.docker.com/linux/debian \
        $(lsb_release -cs) \
        stable" \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
        docker-ce \
    && pip install -r req_docker.txt \
    && apt-get purge --auto-remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        "/var/lib/apt/lists/" \
        "/tmp/" \
        "/var/tmp/" \
        "/usr/share/man" \
        "/usr/share/doc" \
        "/usr/share/doc-base" \
    && mkdir -p \
        "/var/lib/apt/lists/" \
        "/tmp/" \
        "${AIRFLOW_HOME}/.jupyter" \
        "${AIRFLOW_HOME}/dags" \
        "/var/tmp/"

# optional additional apt_repository.txt:
# apt_repository.txt #

# optional additional apt_packages.txt:
# apt_packages.txt #

# optional additional requirements.txt:
# requirements.txt #

# optional additional lab_extensions.txt:
# lab_extensions.txt #

COPY config/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg
COPY jupyter_notebook_config.txt ${AIRFLOW_HOME}/.jupyter/jupyter_notebook_config.py
COPY start-jupyter.sh /start-jupyter.sh
RUN chown -R airflow: ${AIRFLOW_HOME}
RUN usermod -a -G ${DOCKER_GROUP} airflow

EXPOSE 8080 5555 8793 8888

USER airflow

WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["/entrypoint.sh"]
# set default arg for entrypoint
CMD ["webserver"]
