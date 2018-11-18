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
# # Airflow Tutorial
#
# ## It’s a DAG definition file
# One thing to wrap your head around (it may not be very intuitive for everyone at first) is that this Airflow Python script is really just a configuration file specifying the DAG’s structure as code. The actual tasks defined here will run in a different context from the context of this script. Different tasks run on different workers at different points in time, which means that this script cannot be used to cross communicate between tasks. Note that for this purpose we have a more advanced feature called XCom.
#
# People sometimes think of the DAG definition file as a place where they can do some actual data processing - that is not the case at all! The script’s purpose is to define a DAG object. It needs to evaluate quickly (seconds, not minutes) since the scheduler will execute it periodically to reflect the changes if any.
#
# ## Importing Modules
# An Airflow pipeline is just a Python script that happens to define an Airflow DAG object. Let’s start by importing the libraries we will need.

# %%
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# %% [markdown]
# ## Default Arguments
# We’re about to create a DAG and some tasks, and we have the choice to explicitly pass a set of arguments to each task’s constructor (which would become redundant), or (better!) we can define a dictionary of default parameters that we can use when creating tasks.

# %%
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

# %% [markdown]
# For more information about the BaseOperator’s parameters and what they do, refer to the airflow.models.BaseOperator documentation.
#
# Also, note that you could easily define different sets of arguments that would serve different purposes. An example of that would be to have different settings between a production and development environment.
#
# ## Instantiate a DAG
# We’ll need a DAG object to nest our tasks into. Here we pass a string that defines the dag_id, which serves as a unique identifier for your DAG. We also pass the default argument dictionary that we just defined and define a schedule_interval of 1 day for the DAG.
#

# %%
dag = DAG('tutorial', default_args=default_args)

# %% [markdown]
# ## Tasks
# Tasks are generated when instantiating operator objects. An object instantiated from an operator is called a constructor. The first argument task_id acts as a unique identifier for the task.

# %%
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

# %% [markdown]
# Notice how we pass a mix of operator specific arguments (bash_command) and an argument common to all operators (retries) inherited from BaseOperator to the operator’s constructor. This is simpler than passing every argument for every constructor call. Also, notice that in the second task we override the retries parameter with 3.
#
# The precedence rules for a task are as follows:
#
# 1. Explicitly passed arguments
# 2. Values that exist in the default_args dictionary
# 3. The operator’s default value, if one exists
#
# A task must include or inherit the arguments task_id and owner, otherwise Airflow will raise an exception.
#
# ## Templating with Jinja
# Airflow leverages the power of Jinja Templating and provides the pipeline author with a set of built-in parameters and macros. Airflow also provides hooks for the pipeline author to define their own parameters, macros and templates.
#
# This tutorial barely scratches the surface of what you can do with templating in Airflow, but the goal of this section is to let you know this feature exists, get you familiar with double curly brackets, and point to the most common template variable: {{ ds }} (today’s “date stamp”).
#
#

# %%
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

# %% [markdown]
# Notice that the templated_command contains code logic in {% %} blocks, references parameters like {{ ds }}, calls a function as in {{ macros.ds_add(ds, 7)}}, and references a user-defined parameter in {{ params.my_param }}.
#
# The params hook in BaseOperator allows you to pass a dictionary of parameters and/or objects to your templates. Please take the time to understand how the parameter my_param makes it through to the template.
#
# Files can also be passed to the bash_command argument, like bash_command='templated_command.sh', where the file location is relative to the directory containing the pipeline file (tutorial.py in this case). This may be desirable for many reasons, like separating your script’s logic and pipeline code, allowing for proper code highlighting in files composed in different languages, and general flexibility in structuring pipelines. It is also possible to define your template_searchpath as pointing to any folder locations in the DAG constructor call.
#
# Using that same DAG constructor call, it is possible to define user_defined_macros which allow you to specify your own variables. For example, passing dict(foo='bar') to this argument allows you to use {{ foo }} in your templates. Moreover, specifying user_defined_filters allow you to register you own filters. For example, passing dict(hello=lambda name: 'Hello %s' % name) to this argument allows you to use {{ 'world' | hello }} in your templates. For more information regarding custom filters have a look at the Jinja Documentation
#
# For more information on the variables and macros that can be referenced in templates, make sure to read through the Macros section
#
# ## Setting up Dependencies
# We have two simple tasks that do not depend on each other. Here’s a few ways you can define dependencies between them:

# %%
t2.set_upstream(t1)

# This means that t2 will depend on t1
# running successfully to run
# It is equivalent to
# t1.set_downstream(t2)

t3.set_upstream(t1)

# all of this is equivalent to
# dag.set_dependency('print_date', 'sleep')
# dag.set_dependency('print_date', 'templated')

# %% [markdown]
# Note that when executing your script, Airflow will raise exceptions when it finds cycles in your DAG or when a dependency is referenced more than once.
#
# Airflow UI is [here](http://localhost:18080). Next: [Testing](./Testing.ipynb)

# %%



