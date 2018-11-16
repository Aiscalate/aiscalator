#!/usr/bin/env bash

TRY_LOOP="20"

AIRFLOW__CORE__EXECUTOR=SequentialExecutor
export AIRFLOW_HOME=/usr/local/airflow
export AISCALATOR_HOME=/home/user/.aiscalator/

mkdir -p /usr/local/airflow/workspace

for line in "$@"
do
    python -c """
import os
src = '${line}'.split(':')[0]
link = '${line}'.split(':')[1]
print('From ' + os.getcwd() + ' linking ' + link + ' -> ' + src)
os.symlink(src, link)
    """
done

# Install custom python package if requirements.txt is present
if [ -e "/requirements.txt" ]; then
    $(which pip) install --user -r /requirements.txt
fi

airflow initdb
# With the "Local" executor it should all run in one container.
airflow scheduler &
airflow webserver &

exec jupyter-lab
