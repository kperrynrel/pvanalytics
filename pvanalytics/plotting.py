"""
Plotting functions for visualizing QA issues.
"""

import pandas as pd
from matplotlib import pyplot as plt
from scipy import stats
import plotly.express as px
#Import plotly for viewing in the browser
import plotly.io as pio
import numpy as np
#pio.renderers.default = "browser"

def generate_time_shift_heat_map(time_series):
    """
    This function creates a heat map of a time series, which shows if there are
    time shifts due to daylight savings time or sensor drift.
    """
    plt.figure()
    # #Remove anything more than 3 standard deviations from the mean (outliers)
    # #OR use IQR calculation to remove outliers (Q1 - 5*IQR) or (Q3 - 5*IQR)
    # mean = np.mean(dataframe[signal_column], axis=0)
    # std = np.std(dataframe[ signal_column], axis=0)
    # Q1 = np.quantile(dataframe[dataframe[ signal_column]>0][ signal_column], 0.25)
    # Q3 = np.quantile(dataframe[dataframe[ signal_column]>0][ signal_column], 0.75)
    # IQR = Q3 - Q1
    # #Outlier cleaning statement--set outliers to 0
    # dataframe.loc[(abs(mean - dataframe[ signal_column]) > (5*std)) |
    #               (dataframe[ signal_column] <= 0) |
    #               (dataframe[ signal_column] >= (Q3 + 5*IQR))] = np.nan
    #dataframe[signal_column] = dataframe[signal_column].fillna(0)
    #Get time of day from the associated datetime column
    time_of_day = time_series.index.dt.hour + time_series.index.dt.minute/60
    # #Pivot the dataframe 
    # dataframe_pivoted = dataframe.pivot_table(index='time_of_day', 
    #                      columns=time_series.index, 
    #                      values=time_series)
    plt.pcolormesh(time_series.columns, time_series.index, time_series)
    plt.ylabel('Time of day [0-24]')
    plt.xlabel('Date')
    plt.xticks(rotation=60)
    plt.colorbar()
    plt.tight_layout()
    return


def plot_missing_system_data(time_series_dataframe):
    """
    Identify and visualize missing data periods for a system containing
    multiple data streams. 
    """
    pass


def plot_clearsky_sensor_irradiance_comparison(time_series):
    """
    This function examines a sensor-based irradiance data stream, and 
    compares it to its associated clearsky irradiance, based on the associated
    tilt and azimuth. This function is designed to 
    """
    pass

def visualize_data_shifts(time_series):
    """
    Visualize data shifts for a time series.
    """
    pass


def plot_filter(time_series, mask):
    """
    Plot a time series with a particular mask overlay. 
    """
    pass