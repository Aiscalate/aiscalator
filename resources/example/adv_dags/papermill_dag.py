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
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# %%
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2018, 10, 25, 21, 15),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# %%
dag = DAG(
    'adv_papermill_example', 
    default_args=default_args,
    schedule_interval="@daily"
)

# %%
t1 = BashOperator(
    task_id='step1_ETL_data',
    bash_command="""
aiscalator jupyter run \
    /usr/local/airflow/workspace/example/example.conf \
    examples.advanced_papermill.step1 \
    -p run_date {{ ds }} 
""",
    dag=dag)

t2 = BashOperator(
    task_id='step2_model',
    bash_command="""
aiscalator jupyter run \
    /usr/local/airflow/workspace/example/example.conf \
    examples.advanced_papermill.step2 \
    -p run_date {{ ds }} 
""",
    dag=dag)

t3 = BashOperator(
    task_id='step3_report',
    bash_command="""
aiscalator jupyter run \
    /usr/local/airflow/workspace/example/example.conf \
    examples.advanced_papermill.step3 \
    -p run_date {{ ds }} 
""",
    dag=dag)

# %%
t3 << t2 << t1


# %%

