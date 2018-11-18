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
"""
API module of the AIscalator tool.

This module presents the entrypoint to use from a python script.
It is intended to be used like this, usually from an airflow DAG
scripts defining an AIscalator task::

    from aiscalator import api

    api.jupyter_run("path/to/config.conf", "step_name")

"""
from aiscalator.core.config import AiscalatorConfig
from aiscalator.jupyter import command


def jupyter_run(config, notebook=None,
                prepare_only=False,
                param=None,
                param_raw=None):
    """
    Executes the step in browserless mode using papermill

    Parameters
    ----------
    config : str
        path to the configuration file
    notebook : str
        name of node to run, if None, then run the first one
    parameters : list
        List of parameters and their values
    prepare_only : bool
        Indicates if papermill should replace the parameters of the
        notebook only or it should execute all the cells too

    Returns
    -------
    string
        the path to the output notebook resulting from the execution
        of this step
    """
    # TODO implements parameters passing
    if notebook:
        app_config = AiscalatorConfig(config=config,
                                      step_selection=notebook)
    else:
        app_config = AiscalatorConfig(config=config)
    return command.jupyter_run(app_config, prepare_only=prepare_only,
                               param=param, param_raw=param_raw)
