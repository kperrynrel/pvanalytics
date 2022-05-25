"""Tests for data shift quality control functions."""
import pandas as pd
import pytest
from pvanalytics.quality import data_shifts as dt
from ..conftest import DATA_DIR
import ruptures

test_file_1 = DATA_DIR / "pvlib_data_shift.csv"

@pytest.fixture
def generate_time_series():
    # Pull down the saved PVLib dataframe and process it
    df = pd.read_csv(test_file_1)
    signal_no_index = df['value']
    df.index = pd.to_datetime(df['timestamp'])
    signal_datetime_index = df['value']
    changepoint_date = df[df['label'] == 1].index[0]
    df_weekly_resample = df.resample('W').median()['value']
    return (signal_no_index, signal_datetime_index,
            df_weekly_resample, changepoint_date)


def requires_ruptures(test):
    """Skip `test` if ruptures is not installed."""
    try:
        import ruptures  # noqa: F401
        has_ruptures = True
    except ImportError:
        has_ruptures = False
    return pytest.mark.skipif(
        not has_ruptures, reason="requires ruptures")(test)


@requires_ruptures
def test_detect_data_shifts(generate_daily_time_series):
    """
    Unit test that data shifts are correctly identified in the simulated time
    series.
    """
    signal_no_index, signal_datetime_index, df_weekly_resample, \
        changepoint_date = generate_daily_time_series
    # Test that an error is thrown when a Pandas series with no datetime
    # index is passed
    pytest.raises(TypeError, dt.detect_data_shifts, signal_no_index)
    # Test that an error is thrown when an incorrect ruptures method is passed
    pytest.raises(TypeError, dt.detect_data_shifts, signal_datetime_index,
                  True, False, "Pelt")
    # Test that an error is thrown when weekly data is passed
    pytest.raises(ValueError, dt.detect_data_shifts, df_weekly_resample)
    # Test that an error is thrown when an incorrect string is passed as the
    # cost variable
    pytest.raises(ValueError, dt.detect_data_shifts, signal_datetime_index,
                  True, False, ruptures.Binseg, "none")
    # Test that a data shift is successfully detected within 5 days of
    # inserted changepoint
    shift_index = dt.detect_data_shifts(time_series=signal_datetime_index)
    shift_index_dates = list(shift_index[shift_index].index)
    # Test that the column name is handled if a series with no name is passed
    signal_unnamed = signal_datetime_index.rename(None)
    shift_index_unnamed = dt.detect_data_shifts(signal_unnamed)
    shift_index_unnamed_dates = list(
        shift_index_unnamed[shift_index_unnamed].index)
    # Run model with manually entered parameters
    shift_index_param = dt.detect_data_shifts(signal_datetime_index, True,
                                              False, ruptures.BottomUp, "rbf")
    shift_index_param_dates = list(
        shift_index_param[shift_index_param].index)
    assert (abs((changepoint_date - shift_index_dates[0]).days) <= 5)
    assert (abs((changepoint_date - shift_index_unnamed_dates[0]).days) <= 5)
    assert (abs((changepoint_date - shift_index_param_dates[0]).days) <= 5)
    assert (len(shift_index_param.index) == len(signal_datetime_index.index))


def test_filter_data_shifts(generate_daily_time_series):
    """
    Unit test that the longest interval between data shifts is selected for
    the simulated daily time series data set.
    """
    signal_no_index, signal_datetime_index, df_weekly_resample, \
        changepoint_date = generate_daily_time_series
    # Run the time series where there are no changepoints
    interval_dict_short = dt.get_longest_shift_segment_dates(
        time_series=signal_datetime_index[:100])
    # Run the time series where there is a changepoint
    interval_dict = dt.get_longest_shift_segment_dates(
        time_series=signal_datetime_index)
    assert (interval_dict['start_date'] == pd.to_datetime('2015-11-06')) & \
        (interval_dict['end_date'] == pd.to_datetime('2020-12-24'))
    assert (interval_dict_short['start_date'] ==
            signal_datetime_index.index.min()+pd.DateOffset(days=7)) & \
        (interval_dict_short['end_date'] ==
         signal_datetime_index[:100].index.max()-pd.DateOffset(days=7))
