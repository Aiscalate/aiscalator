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
run_date = "2018-04-28"
source_id = 'sensor1'

# %%
import pandas as pd
import numpy as np
import papermill as pm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import time
import os
plt.ioff()

# %%
run_datetime = datetime.strptime(run_date, '%Y-%m-%d')
ts = pd.date_range("00:00", "23:59", freq="5min")
td = ts - timedelta((datetime.now() - run_datetime).days)
data = pd.DataFrame(np.random.randn(len(td)), columns=['mydata'])
data = data.rolling(70, min_periods=1, center=True).mean()  # Smooth it so it looks purdy
data['date'] = td
data['hour'] = data['date'].apply(lambda x: datetime.strftime(x, "%H"))

# %%
print(data['date'].describe())
data.describe()

# %%
data = data.sort_values('date').set_index('date', drop=True)
data.head(5)

# %%
fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
plt.gcf().autofmt_xdate()
ax.plot(data.index, data['mydata'], c='k', alpha=.5)
ax.set(title="Activity for the day of {}".format(run_date))
pm.display('activity_day_fig', fig)

# %%
month_partition = run_datetime.strftime("%Y-%m")
output_file = "../data/output/step1/" + month_partition + "/" + run_date + '-' + source_id + '.csv'
print(output_file)

# %%
os.makedirs(os.path.dirname(output_file), exist_ok=True)
data.to_csv(output_file)


