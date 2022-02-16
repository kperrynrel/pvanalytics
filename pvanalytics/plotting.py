"""
Plotting functions for visualizing QA issues.
"""

from pvanalytics import outliers as out
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import numpy as np


def generate_time_shift_heat_map(time_series):
    """
    This function creates a heat map of a time series, which shows if there are
    time shifts due to daylight savings time or sensor drift.
    """
    plt.figure()
    #Remove anything more than 3 standard deviations from the mean (outliers)
    #OR use IQR calculation to remove outliers (Q1 - 5*IQR) or (Q3 - 5*IQR)
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
    tukey_mask = out.tukey(time_series, k=5)
    zscore_mask = out.zscore(time_series, zmax=5)
    zero_mask = (time_series <= 0)
    time_series[(tukey_mask) | (tukey_mask) | (zero_mask)] = np.nan
    time_series = time_series.fillna(0)
    #Get time of day from the associated datetime column
    time_of_day = time_series.index.dt.hour + time_series.index.dt.minute/60
    #Pivot the dataframe 
    dataframe_pivoted = dataframe.pivot_table(index='time_of_day', 
                          columns=time_series.index, 
                          values=time_series)
    
    fig = px.imshow(z)
    # Plot solar noon, sunrise + sunset lines for each day
    
    
    # If display_web_browser is set to True, the time series with mask
    # is rendered via the web browser.
    if display_web_browser is True:
        fig.show(renderer="browser")
    return fig    
    # plt.pcolormesh(time_series.columns, time_series.index, time_series)
    # plt.ylabel('Time of day [0-24]')
    # plt.xlabel('Date')
    # plt.xticks(rotation=60)
    # plt.colorbar()
    # plt.tight_layout()


def plot_missing_system_data(time_series_dataframe):
    """
    Identify and visualize missing data periods for a system containing
    multiple data streams. 
    """
    #Check for data holes
    time_series_dataframe = time_series_dataframe.notnull().resample('d').mean() > 0
    time_series_dataframe = time_series_dataframe[sorted(time_series_dataframe.columns)]
    plt.pcolormesh(time_series_dataframe.columns, 
                   time_series_dataframe.index, 
                   time_series_dataframe)
    plt.ylabel('date')
    plt.xlabel('standard_name')
    return plt


# def plot_clearsky_sensor_irradiance_comparison(time_series):
#     """
#     This function examines a sensor-based irradiance data stream, and 
#     compares it to its associated clearsky irradiance, based on the associated
#     tilt and azimuth. This function is designed to 
#     """
#     pass

def visualize_data_shifts(time_series, data_shift_dictionary):
    """
    Visualize data shifts for a time series.
    
    Parameters
    ----------

    Returns
    ---------    
    """
    pass


def plot_time_series_mask(signal, mask, display_web_browser=False):
    """
    This function allows the user to visualize masked data in
    a Plotly plot, after tweaking the function's different
    parameters. The plot of signal colored according to mask
    can be zoomed in on, for an in-depth look.
    This function exists for validating algorithms such as:
        -clipping.geometric() (clipping masking)
        -daytime.power_or_irradiance() (day/night masking)
    Function adapted from RdTools.plotting module.
    
    Parameters
    ----------
    signal : pandas.Series
        Index of the Pandas series is a Pandas datetime index. Usually
        this is PV power or energy, but other signals will work.
    mask : pandas.Series
        Pandas series of booleans, where included data periods
        are marked as True, and omitted-data periods occurs are
        marked as False. Should have the same detetime index as signal.
    display_web_browser : boolean, default False
        When set to True, the Plotly graph is displayed in the
        user's web browser.
    
    Returns
    ---------
    Interactive Plotly graph, with the masked time series for the filter.
    """
    # Get the names of the series and the datetime index
    column_name = signal.name
    if column_name is None:
        column_name = 'signal'
        signal = signal.rename(column_name)
    index_name = signal.index.name
    if index_name is None:
        index_name = 'datetime'
        signal = signal.rename_axis(index_name)
    # Visualize the time series, delineating periods by the mask
    # variable. Use plotly to visualize.
    df = pd.DataFrame(signal)
    # Add the mask as a column
    df['mask'] = mask
    df = df.reset_index()
    fig = px.scatter(df, x=index_name, y=column_name, color='mask',
                     color_discrete_map={
                         True: "blue",
                         False: "goldenrod"},
                     )
    # If display_web_browser is set to True, the time series with mask
    # is rendered via the web browser.
    if display_web_browser is True:
        fig.show(renderer="browser")
    return fig