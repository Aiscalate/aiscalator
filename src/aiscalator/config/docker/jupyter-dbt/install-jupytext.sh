#!/usr/bin/env bash
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

# This script relies on the use of https://github.com/mwouts/jupytext

# Generate jupyter notebook config file
JUPYTER_NOTEBOOK_CONFIG="${HOME}/.jupyter/jupyter_notebook_config.py"

if [ -e  "${JUPYTER_NOTEBOOK_CONFIG}" ]; then
    echo "Editing file ${JUPYTER_NOTEBOOK_CONFIG}"
else
    echo jupyter notebook --generate-config
    jupyter notebook --generate-config
fi

grep  -q "jupytext.TextFileContentsManager" ${JUPYTER_NOTEBOOK_CONFIG}
if [ $? -ne 0 ]; then
    echo "Adding Jupytext support to Jupyter Notebooks"
    echo 'c.NotebookApp.contents_manager_class = "jupytext.TextFileContentsManager"' >> ${JUPYTER_NOTEBOOK_CONFIG}
    echo 'c.ContentsManager.default_jupytext_formats = "ipynb,auto"' >> ${JUPYTER_NOTEBOOK_CONFIG}
    echo 'c.ContentsManager.preferred_jupytext_formats_save = "auto:percent"' >> ${JUPYTER_NOTEBOOK_CONFIG}
fi
