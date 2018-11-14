.. highlight:: shell

============
Installation
============


Stable release
--------------

To install aiscalator, run this command in your terminal:

.. code-block:: console

    $ pip install aiscalator

This is the preferred method to install aiscalator, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io/en/stable/
.. _Python installation guide: https://docs.python-guide.org/starting/installation/



From sources
------------

The sources for aiscalator can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/aiscalate/aiscalator

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/aiscalate/aiscalator/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ make install


.. _Github repo: https://github.com/aiscalate/aiscalator
.. _tarball: https://github.com/aiscalate/aiscalator/tarball/master



Development environment on Mac OS
---------------------------------

First, Install docker: https://docs.docker.com/docker-for-mac/install/

Then, we need to have a proper python environment installed:
We would recommend using Homebrew_ to install pyenv_. Best practices
would also to be using virtualenv and virtualenvwrapper.


.. _Homebrew: https://brew.sh/
.. _pyenv: https://github.com/pyenv/pyenv

.. code-block:: console

    brew install python

    # to successfully run all tests with tox, make sure to have
    # each version of python installed
    brew install pyenv
    brew install pyenv-virtualenv
    brew install pyenv-virtualenvwrapper

    # Follow their documentations to add the proper environment variables to your
    # startup scripts (~/,bash_profile etc)

    pyenv install 3.4.9 3.5.6 3.6.7 3.7.1 pypy3.5-6.0.0

    # in case pyenv runs into errors when running tox because it
    # cannot find python3.X (even though python3.X.Y is installed):
    git clone git://github.com/concordusapps/pyenv-implict.git ~/.pyenv/plugins/pyenv-implict


    pip install -r requirements_dev.txt

    # run all tests
    tox
