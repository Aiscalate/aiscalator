#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Apache Software License 2.0
#
# Copyright (c) 2018, Christophe Duong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The setup script."""
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'pytz>=2018.5',
    'PyYAML>=3.13',
]

s = setup(
    author="Christophe Duong",
    author_email='chris@aiscalate.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    description="AIscalate your Jupyter Notebook Prototypes into Airflow Data Products",
    entry_points={
        'console_scripts': [
            'aiscalator=aiscalator.cli:main',
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    keywords='data science jupyter notebook prototype data engineering product airflow',
    name='aiscalator',
    packages=find_packages(),
    package_data={'config': ['*']},
    include_package_data=True,
    setup_requires=['pytest-runner'],
    test_suite='tests',
    tests_require=['pytest'],
    url='https://github.com/Aiscalate/aiscalator',
    version='0.1.0',
    zip_safe=False,
)
installation_path = s.command_obj['install'].install_lib
print("""

To install bash completion for aiscalator, add the following in your ~/.bashrc file:

    source """ + installation_path + "aiscalator-*/aiscalator/config/aiscalator-complete.sh\n\n")
