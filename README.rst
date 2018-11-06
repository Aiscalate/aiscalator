==========
AIscalator
==========


.. image:: https://img.shields.io/pypi/v/aiscalator.svg
        :target: https://pypi.python.org/pypi/aiscalator

.. image:: https://img.shields.io/travis/Aiscalate/aiscalator.svg
        :target: https://travis-ci.org/Aiscalate/aiscalator

.. image:: https://readthedocs.org/projects/aiscalator/badge/?version=latest
        :target: https://aiscalator.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://requires.io/github/Aiscalate/aiscalator/requirements.svg?branch=master
        :target: https://requires.io/github/Aiscalate/aiscalator/requirements/?branch=master
        :alt: Requirements Status


* Free software: Apache Software License 2.0
* Website: http://www.aiscalate.com
* Documentation: https://aiscalator.readthedocs.io.


Key Features
------------

Aiscalator is a toolbox to enable your team streamlining
processes from innovation to productization with:

* Jupyter workbench
    * Explore Data, Prototype Solutions
* Docker wrapper tools
    * Share Code, Deploy Reproducible Environments
* Airflow machinery
    * Schedule Tasks, Refine Products
* Data Science and Data Engineering best practices

.. image:: aiscalator_process.png
        :target: https://raw.githubusercontent.com/Aiscalate/aiscalator/master/resources/img/aiscalator_process.png
        :align: center

===========
Quick Start
===========

Installation
------------

Test if prerequisite softwares are installed:

.. code-block:: shell

    docker --version
    docker-compose --version
    pip --version

Install AIscalator tool:

.. code-block:: shell

    pip install aiscalator

Download docker image to run Jupyter:

.. code-block:: shell

    aiscalator jupyter setup

Download docker image to run Airflow:

.. code-block:: shell

    aiscalator airflow setup

Jupyter
-------

Create a new Jupyter notebook to work on, define corresponding aiscalator step:

.. code-block:: shell

    aiscalator jupyter new

Run the step without GUI:

.. code-block:: shell

    aiscalator jupyter run <aiscalator step>

Airflow
-------

Start Airflow services:

.. code-block:: shell

    aiscalator airflow start

Create a new AIscalator job, define the airflow DAG:

.. code-block:: shell

    aiscalator airflow new

Schedule AIscalator job:

.. code-block:: shell

    aiscalator airflow push <aiscalator DAG>
