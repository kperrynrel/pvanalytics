"""
Time Shift Detection
====================

Identifying time shifts in AC power or irradiance data using the PVAnalytics
time module.
"""

# %%
# Identifying and correcting time shifts from AC power/energy and irradiance
# time series data aids in future analysis, including degradation analysis.
# These time shifts frequently occur as a result of time-zone mislabeling,
# where the time series may erroneously have daylight savings time (DST), be
# represented in the wrong timezone, or have random time shifts due to
# operator error. In this example, we show how to use
# :py:func:`pvanalytics.features.` to estimate time shifts
# in data, and :py:func:`pvanalytics.features.` to correct
# these time shifts, so the data is correctly presented in the original time
# zone.

from pvanalytics.features import daytime
from pvanalytics.quality.outliers import zscore
from pvanalytics.quality import gaps
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import pvanalytics
import pvlib


def get_sunrise_sunset_timestamps(time_series, daytime_mask):
    """
    Get the timestamp for sunrise/sunset for the time series.
    
    Parameters 
    ----------
    time_series: Pandas datetime series of measured data (can be irradiance,
                                                          power, or energy)
    daytime_mask: Pandas series of boolean masks for day/night periods.
        Same datetime index as time_series object.
    
    Returns
    ---------
    sunrise_series: Pandas series of the sunrise 
        datetimes for each day in the time series.
    sunset_series: Pandas series of the sunset
        datetimes for each day in the time series.
    midday_series: Pandas series of the midway 
        point datetimes (halfway between sunrise and sunset) for each day in 
        the time series.
    """
    day_night_changes = daytime_mask.groupby(
        daytime_mask.index.date).apply(lambda x: x.ne(x.shift().ffill()))
    #Get the first 'day' mask for each day in the series; proxy for sunrise
    sunrise_series = pd.Series(daytime_mask[(daytime_mask) &
                                            (day_night_changes)].index)
    sunrise_series = pd.Series(sunrise_series.groupby(sunrise_series.dt.date).min(),
                              index= sunrise_series.dt.date).drop_duplicates()
    # Get the sunset value for each day; this is the first nighttime period
    # after sunrise  
    sunset_series = pd.Series(daytime_mask[~(daytime_mask) & (day_night_changes)].index)
    sunset_series = pd.Series(sunset_series.groupby(sunset_series.dt.date).max(),
                              index= sunset_series.dt.date).drop_duplicates()
    # Generate a 'midday' series, which is the midpoint between sunrise
    # and sunset for every day in the data set
    midday_series = sunrise_series + ((sunset_series - sunrise_series)/2)
    #Return the pandas series associated with the sunrise, sunset, and midday points
    return sunrise_series, sunset_series, midday_series 


# %%
# First, read in the XXX example, which has XXXX

pvanalytics_dir = pathlib.Path(pvanalytics.__file__).parent
time_shift_file = 'C:/Users/kperry/Documents/source/repos/time-shift-validation/data/generated_issues/1229_poa_irradiance_west_array_30min_partial_DST.csv'#pvanalytics_dir / 'data' / '1229_poa_irradiance_west_array_30min_partial_DST.csv'
df = pd.read_csv(time_shift_file, index_col=0, parse_dates=True)
time_series = df.iloc[:, 0]
ts_freq_minutes = 30
latitude = 28.0392
longitude = -81.95
time_series.plot()
plt.show()
plt.close('all')


# %%
# Before estimating time shifts in the time series, pre-process the data to
# remove frozen/stuck data periods, negative data, outliers, and days with less
# than 33% of data present, respectively. This data cleaning leads more
# accurate day/night masking and subsequent time shift estimations. 
# Remove frozen/stuck data periods
stale_data_mask = gaps.stale_values_diff(time_series)
time_series = time_series[~stale_data_mask]
time_series = time_series.asfreq(str(ts_freq_minutes) + 'T')
# Remove negative data
time_series = time_series[(time_series >= 0) | (time_series.isna())]
time_series = time_series.asfreq(str(ts_freq_minutes) + 'T')
# Remove any outliers via z-score filter
zscore_outlier_mask = zscore(time_series, zmax=2,
                             nan_policy='omit')
time_series = time_series[(~zscore_outlier_mask)]
time_series = time_series.asfreq(str(ts_freq_minutes) + 'T')
# Remove days where less than 33% of data is present
completeness = gaps.complete(time_series,
                            minimum_completeness=0.33)
time_series = time_series[completeness]
time_series = time_series.asfreq(str(ts_freq_minutes) + 'T')


# %%
# Now let's mask day-night periods for the processed time series. Specifically,
# we use day-night masking outputs to estimate the daily sunrise and sunset 
# times for the time series.
daytime_mask = daytime.power_or_irradiance(time_series,
                                           freq=str(ts_freq_minutes) + 'T',
                                           low_value_threshold=0.005)
#Generate the sunrise, sunset, and halfway pts for the data stream


sunrise_series, sunset_series, midday_series = get_sunrise_sunset_timestamps(time_series,
                                                                             daytime_mask)


# %%
# Using :py:func:`pvlib.solarposition.sun_rise_set_transit_spa`, get the
# modeled sunrise and sunset times based on the system's latitude-longitude
# coordinates and its labeled time zone.
modeled_sunrise_sunset_df = pvlib.solarposition.sun_rise_set_transit_spa(
    time_series.index,
    latitude, longitude)
modeled_sunrise_sunset_df.index = modeled_sunrise_sunset_df.index.date
modeled_sunrise_sunset_df = modeled_sunrise_sunset_df.drop_duplicates()
# Calculate the midday point between sunrise and sunset for each day
# in the modeled irradiance series
modeled_midday_series = modeled_sunrise_sunset_df['sunrise'] + \
                        (modeled_sunrise_sunset_df['sunset'] - \
                         modeled_sunrise_sunset_df['sunrise']) / 2


# %%
#Compare the data stream's daily halfway point to the modeled halfway point
midday_diff_series = (modeled_midday_series -
                      midday_series).dt.total_seconds() / 60

# Run a secondary z-score outlier filter to clean up the midday difference
# series
zscore_outlier_mask = zscore(midday_diff_series, zmax=3,
                             nan_policy='omit')
midday_diff_series = midday_diff_series[~zscore_outlier_mask]

# Visualize the midday difference series.
midday_diff_series.plot()
plt.show()
plt.close('all')


# %%
# We run '' to estimate the time shifts in the series. 
#time_shift_series = time_shift_estimation(midday_diff_series)