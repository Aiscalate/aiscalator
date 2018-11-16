# -*- coding: utf-8 -*-
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

# %% [markdown]
# ## Recap
# Alright, so we have a pretty basic DAG. At this point your code should look something like this:

# %%
"""
Code that goes along with the Airflow located at:
http://airflow.readthedocs.org/en/latest/tutorial.html
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

dag = DAG(
    'tutorial', default_args=default_args, schedule_interval=timedelta(1))

# t1, t2 and t3 are examples of tasks created by instantiating operators
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

t2 = BashOperator(
    task_id='sleep',
    bash_command='sleep 5',
    retries=3,
    dag=dag)

templated_command = """
    {% for i in range(5) %}
        echo "{{ ds }}"
        echo "{{ macros.ds_add(ds, 7)}}"
        echo "{{ params.my_param }}"
    {% endfor %}
"""

t3 = BashOperator(
    task_id='templated',
    bash_command=templated_command,
    params={'my_param': 'Parameter I passed in'},
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t1)

# %% [markdown]
# # Testing
# Running the Script
# Time to run some tests. First let’s make sure that the pipeline parses. Let’s assume we’re saving the code from the previous step in tutorial.py in the DAGs folder referenced in your airflow.cfg. The default location for your DAGs is ~/airflow/dags.

# %%
%%sh
python ~/dags/tutorial.py

# %% [markdown]
# If the script does not raise an exception it means that you haven’t done anything horribly wrong, and that your Airflow environment is somewhat sound.
#
# Command Line Metadata Validation
# Let’s run a few commands to validate this script further.

# %%
%%sh
# print the list of active DAGs
airflow list_dags

# prints the list of tasks the "tutorial" dag_id
airflow list_tasks tutorial

# prints the hierarchy of tasks in the tutorial DAG
airflow list_tasks tutorial --tree

# %% [markdown]
# ## Testing
# Let’s test by running the actual task instances on a specific date. The date specified in this context is an execution_date, which simulates the scheduler running your task or dag at a specific date + time:
#
#

# %%
%%sh
# command layout: command subcommand dag_id task_id date

# testing print_date
airflow test tutorial print_date 2015-06-01

# testing sleep
airflow test tutorial sleep 2015-06-01

# %% [markdown]
# Now remember what we did with templating earlier? See how this template gets rendered and executed by running this command:

# %%
%%sh
# testing templated
airflow test tutorial templated 2015-06-01

# %% [markdown]
# This should result in displaying a verbose log of events and ultimately running your bash command and printing the result.
#
# Note that the airflow test command runs task instances locally, outputs their log to stdout (on screen), doesn’t bother with dependencies, and doesn’t communicate state (running, success, failed, …) to the database. It simply allows testing a single task instance.
#
# ## Backfill
# Everything looks like it’s running fine so let’s run a backfill. backfill will respect your dependencies, emit logs into files and talk to the database to record status. If you do have a webserver up, you’ll be able to track the progress. airflow webserver will start a web server if you are interested in tracking the progress visually as your backfill progresses.
#
# Note that if you use depends_on_past=True, individual task instances will depend on the success of the preceding task instance, except for the start_date specified itself, for which this dependency is disregarded.
#
# The date range in this context is a start_date and optionally an end_date, which are used to populate the run schedule with task instances from this dag.

# %%
%%sh
# optional, start a web server in debug mode in the background
# airflow webserver --debug &

# start your backfill on a date range
airflow backfill tutorial -s 2015-06-01 -e 2015-06-07

# %% [markdown]
# ## What’s Next?
# That’s it, you’ve written, tested and backfilled your very first Airflow pipeline. Merging your code into a code repository that has a master scheduler running against it should get it to get triggered and run every day.
#
# Here’s a few things you might want to do next:
#
# Take an in-depth tour of the UI - click all the things!
#
# Keep reading the docs! Especially the sections on:
#
# Command line interface
# Operators
# Macros
# Write your first pipeline!

# %%
%%sh
airflow list_dags


# %%



