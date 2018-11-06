#!/usr/bin/env bash
# From https://github.com/mwouts/jupytext

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
