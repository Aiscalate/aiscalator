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

# %% [markdown]
# # A papermill example: Fitting a model
#

# %% [markdown]
# ### Specify default parameters
#
# This is a "parameters" cell, which defines default

# %% {"tags": ["parameters"]}
# Our default parameters
# This cell has a "parameters" tag, means that it defines the parameters for use in the notebook
start_date = "2001-08-05"
stop_date = "2016-01-01"

# %% [markdown]
# ## Set up our packages and create the data
#
# We'll run `plt.ioff()` so that we don't get double plots in the notebook

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import papermill as pm
plt.ioff()
np.random.seed(1337)

# %%
# Generate some fake data by date
dates = pd.date_range("2010-01-01", "2020-01-01")
data = pd.DataFrame(np.random.randn(len(dates)), index=dates, columns=['mydata'])
data = data.rolling(100).mean()  # Smooth it so it looks purdy

# %% [markdown]
# ## Choose a subset of data to highlight
#
# Here we use the **start_date** and **stop_date** parameters, which are defined above by default, but can
# be overwritten at runtime by papermill.

# %%
data_highlight = data.loc[start_date: stop_date]

# %% [markdown]
# We use the `pm.record()` function to keep track of how many records were included in the
# highlighted section. This lets us inspect this value after running the notebook with papermill.
#
# We also include a ValueError if we've got a but in the start/stop times, which will be captured
# and displayed by papermill if it's triggered.

# %%
num_records = len(data_highlight)
pm.record('num_records', num_records)
if num_records == 0:
    raise ValueError("I have no data to highlight! Check that your dates are correct!")

# %% [markdown]
# ## Make our plot
#
# Below we'll generate a matplotlib figure with our highlighted dates. By calling `pm.display()`, papermill
# will store the figure to the key that we've specified (`highlight_dates_fig`). This will let us inspect the
# output later on.

# %%
fig, ax = plt.subplots()
ax.plot(data.index, data['mydata'], c='k', alpha=.5)
ax.plot(data_highlight.index, data_highlight['mydata'], c='r', lw=3)
ax.set(title="Start: {}\nStop: {}".format(start_date, stop_date))
pm.display('highlight_dates_fig', fig)

# %%



