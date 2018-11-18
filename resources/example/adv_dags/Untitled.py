# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.1'
#       jupytext_version: 0.8.5
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.6.7
# ---

# %%
%%sh
pip install --upgrade "../workspace/dist/aiscalator-0.1.2-py3-none-any.whl" --user  --no-warn-script-location



# %%
%%sh
airflow list_dags

airflow list_tasks adv_papermill_example --tree

# %%
%%sh
airflow test adv_papermill_example generate_step1_data "2018-04-28"

# %%
%%sh
airflow backfill adv_papermill_example -s `date --date="10 days ago" +%Y-%m-%d` -e `date +%Y-%m-%d`

# %%


