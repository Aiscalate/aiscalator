#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""
import os
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

ROOT_DIR = os.getenv('VIRTUAL_ENV', '')
if len(ROOT_DIR) == 0:
    ROOT_DIR = os.getenv('HOME') + '/.aiscalator/'
else:
    ROOT_DIR += '/etc/aiscalator/'
data_files = [
    (ROOT_DIR + 'config',
     ['resources/config/logging.yaml']),
    (ROOT_DIR + 'config/docker/jupyter-spark/',
     ['resources/config/docker/jupyter-spark/Dockerfile']),
    (ROOT_DIR + 'config/docker/airflow/',
     ['resources/config/docker/airflow/Dockerfile']),
    (ROOT_DIR + 'config/docker/airflow/config',
     ['resources/config/docker/airflow/config/airflow.cfg']),
    (ROOT_DIR + 'config/docker/airflow/config',
     ['resources/config/docker/airflow/config/docker-compose-CeleryExecutor.yml']),
    (ROOT_DIR + 'config/docker/airflow/config',
     ['resources/config/docker/airflow/config/docker-compose-LocalExecutor.yml']),
]

requirements = [
    'Click>=6.0',
    'pytz>=2018.5',
    'PyYAML>=3.13'
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Christophe Duong",
    author_email='chris@aiscalate.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Aiscalate Command Line Tool",
    entry_points={
        'console_scripts': [
            'aiscalator=aiscalator.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='aiscalator',
    name='aiscalator',
    packages=find_packages(),
    data_files=data_files,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/Aiscalate/aiscalator',
    version='0.0.2',
    zip_safe=False,
)
