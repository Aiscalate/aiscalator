=====
Usage
=====

First recommended but optional step is to make sure you have virtualenv installed
and create an environment to try out AIscalator.
(Note that you might need to install some prerequesite software for it to work)::

    mkvirtualenv aiscalate

The project is still in Alpha version, there is still a lot of work to be done.
At the moment, you can install using two methods

1) Install from PyPI::

    pip install aiscalator

2) or Download latest version directly from git and install::

    git clone https://github.com/Aiscalate/aiscalator.git
    cd aiscalator/
    make install

After cloning the project, you can start testing the following commands at the moment::

    aiscalator jupyter new src
    aiscalator jupyter edit resources/example/example.json
    aiscalator jupyter run resources/example/example.json
    aiscalator airflow start
