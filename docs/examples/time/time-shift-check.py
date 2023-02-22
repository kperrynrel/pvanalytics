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
plt.title(data_stream)
plt.show()
plt.close('all')


# %%
# We run '' to estimate the time shifts in the series. 
time_shift_series = time_shift_estimation(midday_diff_series)