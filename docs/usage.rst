=====
Usage
=====

The project is still in Alpha version, there is still a lot of work to be done.
At the moment, you can install using two methods

1) Install from PyPI::

    pip install aiscalator

2) or Download latest version directly from git and install::

    git clone https://github.com/Aiscalate/aiscalator.git
    cd aiscalator/
    make install

After cloning the project, you can start testing the following commands at the moment::

    aiscalator jupyter new examples
    ls -l examples/
    aiscalator jupyter edit resources/example/example.conf
    aiscalator jupyter run resources/example/example.conf
    aiscalator airflow start
