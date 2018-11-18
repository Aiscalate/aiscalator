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
nb_days = 32

# %%
import numpy as np
import pandas as pd
import papermill as pm
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import statsmodels.api as sm
from pylab import rcParams
import itertools

# turn off interactive plotting to avoid double plotting
plt.ioff()

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

# %% [markdown]
# https://towardsdatascience.com/an-end-to-end-project-on-time-series-analysis-and-forecasting-with-python-4835e6bf050b
#
#
# https://www.statsmodels.org/dev/generated/statsmodels.tsa.seasonal.seasonal_decompose.html

# %%
rcParams['figure.figsize'] = 18, 8
decomposition = sm.tsa.seasonal_decompose(data['mydata'], model='additive', freq=288)
fig = decomposition.plot()


# %%
p = d = q = range(0, 2)
pdq = list(itertools.product(p, d, q))
seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]

print('Examples of parameter combinations for Seasonal ARIMA...')
print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[1]))
print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[2]))
print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[3]))
print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[4]))

# %%
scores = {
    "AIC" : [],
    "param" : [],
    "param_seasonal" : []
}
for param in pdq:
    for param_seasonal in seasonal_pdq:
        try:
            mod = sm.tsa.statespace.SARIMAX(
                data['mydata'],
                order=param,
                seasonal_order=param_seasonal,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            results = mod.fit()
            scores['AIC'].append(results.aic)
            scores['param'].append(param)
            scores['param_seasonal'].append(param_seasonal)
            print('ARIMA{}x{}12 - AIC:{}'.format(param, param_seasonal, results.aic))
        except:
            continue
scores = pd.DataFrame.from_dict(scores)
scores.sort_values('AIC').head(5)

# %%
best = scores.sort_values('AIC').head(1).values[0]
mod = sm.tsa.statespace.SARIMAX(data['mydata'],
                                order=best[1],
                                seasonal_order=best[2],
                                enforce_stationarity=True,
                                enforce_invertibility=False)
results = mod.fit()
print(results.summary().tables[1])

# %%
results.plot_diagnostics(figsize=(16, 8))
plt.show()

# %%
pred = results.get_prediction(start=(run_datetime - timedelta(1)), dynamic=False)
pred_ci = pred.conf_int()

fig, ax = plt.subplots()
ax.plot(data[data.index > (run_datetime - timedelta(3))]['mydata'], label='observed')
ax.plot(pred.predicted_mean, label='One-step ahead Forecast', alpha=.7)
ax.fill_between(pred_ci.index,
                pred_ci.iloc[:, 0],
                pred_ci.iloc[:, 1], color='k', alpha=.2)
ax.set_xlabel('Date')
ax.set_ylabel('mydata')
ax.set(title='Results of ARIMA{}x{}12 - AIC:{} on {}'.format(best[1], best[2], round(best[0]), run_date))
fig.legend()
pm.display('arima_results_fig', fig)

# %%
pred.save("../data/output/step2/prediction_model_" + run_date + "-" + source_id)

# %%



