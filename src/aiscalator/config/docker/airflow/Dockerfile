# AUTHOR: Christophe Duong <chris@aiscalate.com>
# DESCRIPTION: Airflow container tuned for AIscalator
# BUILD: docker build --build-arg DOCKER_GID=`getent group docker | cut -d ':' -f 3` --rm -t aiscalator/airflow .
# SOURCE: https://github.com/aiscalate/aiscalator

FROM puckel/docker-airflow:1.10.0-5
LABEL maintainer="Christophe Duong <chris@aiscalate.com>"

ARG AIRFLOW_HOME=/usr/local/airflow
ARG DOCKER_GID
# Reuse host GID for docker group in container
USER root
RUN groupadd -r -g ${DOCKER_GID} docker

# https://docs.docker.com/install/linux/docker-ce/debian/
RUN apt-get update -yqq \
    #&& apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
     apt-transport-https \
     ca-certificates \
     gnupg2 \
     software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://download.docker.com/linux/debian/gpg" | apt-key add - \
    && add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable" \
    && apt-get update -yqq \
    #&& apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        docker-ce \
    && pip install aiscalator==0.1.0 \
    && apt-get purge --auto-remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        "/var/lib/apt/lists/" \
        "/tmp/" \
        "/var/tmp/" \
        "/usr/share/man" \
        "/usr/share/doc" \
        "/usr/share/doc-base"
    && mkdir -p \
        "/var/lib/apt/lists/" \
        "/tmp/" \
        "/var/tmp/

COPY config/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg

RUN chown -R airflow: ${AIRFLOW_HOME}
RUN usermod -a -G docker airflow

EXPOSE 8080 5555 8793

USER airflow
WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["/entrypoint.sh"]
# set default arg for entrypoint
CMD ["webserver"]
