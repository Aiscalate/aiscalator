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
#     version: 3.6.6
# ---

# %% {"tags": ["parameters"]}
# Our default parameters
# This cell has a "parameters" tag, means that it defines the parameters for use in the notebook
run_date = '2018-11-18'
source_id = 'sensor1'
nb_days = 7

# %%
import statsmodels.api as sm
import matplotlib.pyplot as plt
from datetime import datetime, timedelta 
import os
import pandas as pd

from pylab import rcParams
import papermill as pm

# %%
data_dir = "../data/input/step1" 
data = None
run_datetime = datetime.strptime(run_date, '%Y-%m-%d')
for i in range(nb_days):    
    deltatime = run_datetime - timedelta(i)
    month_partition = deltatime.strftime("%Y-%m")
    delta = datetime.strftime(deltatime, '%Y-%m-%d')    
    file = os.path.join(data_dir, month_partition, delta + "-" + source_id + ".csv")
    if os.path.exists(file):
        print("Loading " + file)
        new = pd.read_csv(file)
        if data is not None:
            data = pd.concat([data, new])
        else:
            data = new

# %%
data['date'] = data['date'].apply(lambda x : datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
print(data['date'].describe())
data.describe()

# %%
data = data.sort_values('date').set_index('date', drop=True)
data = data.asfreq(freq="5min")
data.head(5)

# %%
pred = sm.load("../data/input/step2/prediction_model_" + run_date + "-" + source_id)

# %%
pred_ci = pred.conf_int()
rcParams['figure.figsize'] = 18, 8
fig, ax = plt.subplots()
ax.plot(data[data.index > (run_datetime - timedelta(3))]['mydata'], label='observed')
ax.plot(pred.predicted_mean, label='One-step ahead Forecast', alpha=.7)
ax.fill_between(pred_ci.index,
                pred_ci.iloc[:, 0],
                pred_ci.iloc[:, 1], color='k', alpha=.2)
ax.set_xlabel('Date')
ax.set_ylabel('mydata')
ax.set(title='Results on {}'.format(run_date))
fig.legend()

# %%



