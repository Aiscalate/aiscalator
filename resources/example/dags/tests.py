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
# print the list of active DAGs
airflow list_dags

# %%
%%sh
# prints the list of tasks the "tutorial" dag_id
airflow list_tasks papermill_example

# prints the hierarchy of tasks in the tutorial DAG
airflow list_tasks papermill_example --tree

# %%
%%sh 
airflow test papermill_example pwd_task 2015-06-01

# %%
%%sh 
airflow test papermill_example papermill_run 2015-06-01


# %%
%%sh 
airflow backfill papermill_example -s 2015-06-01 -e 2015-06-03

# %%



