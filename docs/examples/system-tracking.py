"""
Detect if a System is Tracking
==============================

Identifying if a system is tracking or fixed tilt
"""

# %%
# It is valuable to identify if a system is fixed tilt or tracking for
# future analysis. This example shows how to use
# :py:func:`pvanalytics.system.is_tracking_envelope` to determine if a
# system is tracking or not by fitting data to a maximum power or
# irradiance envelope, and fitting this envelope to quadratic and
# quartic curves. The r^2 output from these fits is used to determine
# if the system fits a tracking or fixed-tilt profile.

import pvanalytics
from pvanalytics.system import is_tracking_envelope
from pvanalytics.features.clipping import geometric
from pvanalytics.features.daytime import power_or_irradiance
import pandas as pd
import pathlib

# %%
# First, we import the AC power data stream that we are going to check the
# mounting configuration for. This particular data stream is associated with
# a fixed-tilt system.

pvanalytics_dir = pathlib.Path(pvanalytics.__file__).parent
ac_power_file = pvanalytics_dir / 'data' / \
    'serf_east_AC_power_system_estimate.csv'
data = pd.read_csv(ac_power_file, index_col=0, parse_dates=True)
data = data.sort_index()
time_series = data['ac_power']
time_series = time_series.asfreq('15T')

# %%
# Run the clipping and the daytime filters on the time series.
# Both of these masks will be used as inputs to the
# :py:func:`pvanalytics.system.is_tracking_envelope` function.

# Generate the daylight mask for the AC power time series
daytime_mask = power_or_irradiance(time_series)

# Generate the clipping mask for the time series
clipping_mask = geometric(time_series)

# %%
# Now, we use :py:func:`pvanalytics.system.is_tracking_envelope` to
# identify if the data stream is associated with a tracking system.

predicted_mounting_config = is_tracking_envelope(time_series,
                                                 daytime_mask,
                                                 clipping_mask)

print("Estimated mounting configuration: " + predicted_mounting_config.name)