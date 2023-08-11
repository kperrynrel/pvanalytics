"""Tests for time-related quality control functions."""
from datetime import datetime
import pytz
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_series_equal
from pvanalytics.quality import time
from ..conftest import requires_ruptures


@pytest.fixture
def times():
    """One hour in Mountain Standard Time at 10 minute intervals.

    Notes
    -----
    Copyright (c) 2019 SolarArbiter. See the file
    LICENSES/SOLARFORECASTARBITER_LICENSE at the top level directory
    of this distribution and at `<https://github.com/pvlib/
    pvanalytics/blob/master/LICENSES/SOLARFORECASTARBITER_LICENSE>`_
    for more information.

    """
    MST = pytz.timezone('MST')
    return pd.date_range(start=datetime(2018, 6, 15, 12, 0, 0, tzinfo=MST),
                         end=datetime(2018, 6, 15, 13, 0, 0, tzinfo=MST),
                         freq='10T')


def test_timestamp_spacing_date_range(times):
    """An index generated by pd.date_range has the expected spacing."""
    assert_series_equal(
        time.spacing(times, times.freq),
        pd.Series(True, index=times)
    )


def test_timestamp_spacing_one_timestamp(times):
    """An index with only one timestamp has uniform spacing."""
    assert_series_equal(
        time.spacing(times[[0]], times.freq),
        pd.Series(True, index=[times[0]])
    )


def test_timestamp_spacing_one_missing(times):
    """The timestamp following a missing timestamp will be marked False."""
    assert_series_equal(
        time.spacing(times[[0, 2, 3]], times.freq),
        pd.Series([True, False, True], index=times[[0, 2, 3]])
    )


def test_timestamp_spacing_too_frequent(times):
    """Timestamps with too high frequency will be marked False."""
    assert_series_equal(
        time.spacing(times, '30min'),
        pd.Series([True] + [False] * (len(times) - 1), index=times)
    )


def _get_sunrise(location, tz):
    # Get sunrise times for 2020
    days = pd.date_range(
        start='1/1/2020',
        end='1/1/2021',
        freq='D',
        tz=tz
    )
    return location.get_sun_rise_set_transit(
        days, method='spa'
    ).sunrise


@pytest.mark.parametrize("tz, observes_dst", [('MST', False),
                                              ('America/Denver', True)])
def test_has_dst(tz, observes_dst, albuquerque):
    sunrise = _get_sunrise(albuquerque, tz)
    dst = time.has_dst(sunrise, 'America/Denver')
    expected = pd.Series(False, index=sunrise.index)
    expected.loc['2020-03-08'] = observes_dst
    expected.loc['2020-11-01'] = observes_dst
    assert_series_equal(
        expected,
        dst,
        check_names=False
    )


@pytest.mark.parametrize("tz, observes_dst", [('MST', False),
                                              ('America/Denver', True)])
def test_has_dst_input_series_not_localized(tz, observes_dst, albuquerque):
    sunrise = _get_sunrise(albuquerque, tz)
    sunrise = sunrise.tz_localize(None)
    expected = pd.Series(False, index=sunrise.index)
    expected.loc['2020-03-08'] = observes_dst
    expected.loc['2020-11-01'] = observes_dst
    dst = time.has_dst(sunrise, 'America/Denver')
    assert_series_equal(
        expected,
        dst
    )


@pytest.mark.parametrize("tz, observes_dst", [('MST', False),
                                              ('America/Denver', True)])
@pytest.mark.parametrize("freq", ['15T', '30T', 'H'])
def test_has_dst_rounded(tz, freq, observes_dst, albuquerque):
    sunrise = _get_sunrise(albuquerque, tz)
    # With rounding to 1-hour timestamps we need to reduce how many
    # days we look at.
    window = 7 if freq != 'H' else 1
    expected = pd.Series(False, index=sunrise.index)
    expected.loc['2020-03-08'] = observes_dst
    expected.loc['2020-11-01'] = observes_dst
    dst = time.has_dst(
        sunrise.dt.round(freq),
        'America/Denver',
        window=window
    )
    assert_series_equal(expected, dst, check_names=False)


def test_has_dst_missing_data(albuquerque):
    sunrise = _get_sunrise(albuquerque, 'America/Denver')
    sunrise.loc['3/5/2020':'3/10/2020'] = pd.NaT
    sunrise.loc['7/1/2020':'7/20/2020'] = pd.NaT
    # Doesn't raise since both sides still have some data
    expected = pd.Series(False, index=sunrise.index)
    expected['3/8/2020'] = True
    expected['11/1/2020'] = True
    assert_series_equal(
        time.has_dst(sunrise, 'America/Denver'),
        expected
    )
    missing_all_before = sunrise.copy()
    missing_all_after = sunrise.copy()
    missing_all_before.loc['3/1/2020':'3/5/2020'] = pd.NaT
    missing_all_after.loc['3/8/2020':'3/14/2020'] = pd.NaT
    missing_data_message = r'No data at .*\. ' \
                           r'Consider passing a larger `window`.'
    # Raises for missing data before transition date
    with pytest.raises(ValueError, match=missing_data_message):
        time.has_dst(missing_all_before, 'America/Denver')
    # Raises for missing data after transition date
    with pytest.raises(ValueError, match=missing_data_message):
        time.has_dst(missing_all_after, 'America/Denver')
    # Raises for missing data before and after the shift date
    sunrise.loc['3/1/2020':'3/7/2020'] = pd.NaT
    sunrise.loc['3/9/2020':'3/14/2020'] = pd.NaT
    with pytest.raises(ValueError, match=missing_data_message):
        time.has_dst(sunrise, 'America/Denver')
    with pytest.warns(UserWarning, match=missing_data_message):
        result = time.has_dst(sunrise, 'America/Denver', missing='warn')
    expected.loc['3/8/2020'] = False
    assert_series_equal(expected, result)
    sunrise.loc['3/1/2020':'3/14/2020'] = pd.NaT
    with pytest.warns(UserWarning, match=missing_data_message):
        result = time.has_dst(sunrise, 'America/Denver', missing='warn')
    assert_series_equal(expected, result)
    with pytest.raises(ValueError, match=missing_data_message):
        time.has_dst(sunrise, 'America/Denver')


def test_has_dst_gaps(albuquerque):
    sunrise = _get_sunrise(albuquerque, 'America/Denver')
    sunrise.loc['3/5/2020':'3/10/2020'] = pd.NaT
    sunrise.loc['7/1/2020':'7/20/2020'] = pd.NaT
    sunrise.dropna(inplace=True)
    expected = pd.Series(False, index=sunrise.index)
    expected['11/1/2020'] = True
    assert_series_equal(
        time.has_dst(sunrise, 'America/Denver'),
        expected
    )


def test_has_dst_no_dst_in_date_range(albuquerque):
    sunrise = _get_sunrise(albuquerque, 'America/Denver')
    july = sunrise['2020-07-01':'2020-07-31']
    february = sunrise['2020-02-01':'2020-03-05']
    expected_july = pd.Series(False, index=july.index)
    expected_march = pd.Series(False, index=february.index)
    assert_series_equal(
        expected_july,
        time.has_dst(july, 'America/Denver')
    )
    assert_series_equal(
        expected_march,
        time.has_dst(february, 'MST')
    )


@pytest.fixture(scope='module', params=['H', '15T', 'T'])
def midday(request, albuquerque):
    solar_position = albuquerque.get_solarposition(
        pd.date_range(
            start='1/1/2020', end='3/30/2020 23:59',
            tz='MST', freq=request.param
        )
    )
    mid_day = (solar_position['zenith'] < 87).groupby(
        solar_position.index.date
    ).apply(
        lambda day: (day[day].index.min()
                     + ((day[day].index.max() - day[day].index.min()) / 2))
    )
    mid_day = mid_day.dt.hour * 60 + mid_day.dt.minute
    mid_day.index = pd.DatetimeIndex(mid_day.index, tz='MST')
    return mid_day.astype(np.int64)


@requires_ruptures
def test_shift_ruptures_no_shift(midday):
    """Daytime mask with no time-shifts yields a series with 0s for
    shift amounts."""
    shift_mask, shift_amounts = time.shifts_ruptures(
        midday, midday
    )
    assert not shift_mask.any()
    assert_series_equal(
        shift_amounts,
        pd.Series(0, index=midday.index, dtype='int64'),
        check_names=False
    )


@requires_ruptures
def test_shift_ruptures_positive_shift(midday):
    """Every day shifted 1 hour later yields a series with shift
     of 60 for each day."""
    shifted = _shift_between(
        midday, 60,
        start='2020-01-01',
        end='2020-03-30'
    )
    expected_shift_mask = pd.Series(False, index=midday.index)
    expected_shift_mask['2020-01-01':'2020-03-30'] = True
    shift_mask, shift_amounts = time.shifts_ruptures(shifted, midday)
    assert_series_equal(shift_mask, expected_shift_mask, check_names=False)
    assert_series_equal(
        shift_amounts,
        pd.Series(60, index=shifted.index, dtype='int64'),
        check_names=False
    )


@requires_ruptures
def test_shift_ruptures_negative_shift(midday):
    shifted = _shift_between(
        midday, -60,
        start='2020-01-01',
        end='2020-03-30'
    )
    expected_shift_mask = pd.Series(False, index=midday.index)
    expected_shift_mask['2020-01-01':'2020-03-30'] = True
    shift_mask, shift_amounts = time.shifts_ruptures(shifted, midday)
    assert_series_equal(shift_mask, expected_shift_mask, check_names=False)
    assert_series_equal(
        shift_amounts,
        pd.Series(-60, index=shifted.index, dtype='int64'),
        check_names=False
    )


@requires_ruptures
def test_shift_ruptures_partial_shift(midday):
    shifted = _shift_between(
        midday, 60,
        start='2020-1-1', end='2020-2-1'
    )
    expected = pd.Series(60, index=midday.index)
    expected.loc['2020-2-2':] = 0
    expected_mask = expected != 0
    shift_mask, shift_amount = time.shifts_ruptures(shifted, midday)
    assert_series_equal(shift_mask, expected_mask, check_names=False)
    assert_series_equal(
        shift_amount,
        expected,
        check_names=False
    )


def _shift_between(series, shift, start, end):
    before = series[:start]
    during = series[start:end]
    after = series[end:]
    during = during + shift
    shifted = pd.concat([before, during, after])
    return shifted[~shifted.index.duplicated()]


@requires_ruptures
def test_shift_ruptures_period_min(midday):
    no_shifts = pd.Series(0, index=midday.index, dtype='int64')
    # period_min must be equal to length of series / 2 or less in order for
    # binary segmentation algoritm to work.
    shift_mask, shift_amount = time.shifts_ruptures(
        midday, midday,
        period_min=len(midday) / 2
    )
    assert not shift_mask.any()
    assert_series_equal(
        shift_amount,
        no_shifts,
        check_names=False
    )

    shifted = _shift_between(
        midday, 60,
        start='2020-01-01',
        end='2020-01-20'
    )
    shift_expected = pd.Series(0, index=shifted.index, dtype='int64')
    shift_expected.loc['2020-01-01':'2020-01-20'] = 60
    expected_mask = shift_expected != 0
    shift_mask, shift_amount = time.shifts_ruptures(
        midday, midday, period_min=30
    )
    assert not shift_mask.any()
    assert_series_equal(
        shift_amount,
        no_shifts,
        check_names=False
    )
    shift_mask, shift_amount = time.shifts_ruptures(
        shifted, midday, period_min=15
    )
    assert_series_equal(shift_mask, expected_mask, check_names=False)
    assert_series_equal(
        shift_amount,
        shift_expected,
        check_names=False
    )

    with pytest.raises(ValueError):
        time.shifts_ruptures(
            midday, midday,
            period_min=10000
        )


@requires_ruptures
def test_shifts_ruptures_shift_at_end(midday):
    shifted = _shift_between(
        midday, 60,
        start='2020-02-01',
        end='2020-03-30'
    )
    shift_expected = pd.Series(0, index=shifted.index, dtype='int64')
    shift_expected['2020-02-02':'2020-03-30'] = 60
    shift_mask, shift_amount = time.shifts_ruptures(shifted, midday)
    assert_series_equal(shift_mask, shift_expected != 0, check_names=False)
    assert_series_equal(
        shift_amount,
        shift_expected,
        check_names=False
    )


@requires_ruptures
def test_shifts_ruptures_shift_in_middle(midday):
    shifted = _shift_between(
        midday, 60,
        start='2020-01-25',
        end='2020-03-05'
    )
    shift_expected = pd.Series(0, index=shifted.index, dtype='int64')
    shift_expected['2020-01-26':'2020-03-05'] = 60
    shift_mask, shift_amount = time.shifts_ruptures(shifted, midday,
                                                    prediction_penalty=13)
    assert_series_equal(
        shift_mask,
        shift_expected != 0,
        check_names=False
    )
    assert_series_equal(
        shift_amount,
        shift_expected,
        check_names=False
    )


@requires_ruptures
def test_shift_ruptures_shift_min(midday):
    shifted = _shift_between(
        midday, 30,
        start='2020-01-01',
        end='2020-01-25',
    )
    shift_expected = pd.Series(0, index=shifted.index, dtype='int64')
    shift_expected.loc['2020-01-01':'2020-01-25'] = 30
    no_shift = pd.Series(0, index=shifted.index, dtype='int64')
    shift_mask, shift_amount = time.shifts_ruptures(
        shifted, midday,
        shift_min=60
    )
    assert not shift_mask.any()
    assert_series_equal(
        shift_amount,
        no_shift,
        check_names=False
    )
    shift_mask, shift_amount = time.shifts_ruptures(
        shifted, midday,
        shift_min=30
    )
    assert_series_equal(
        shift_mask,
        shift_expected != 0 if pd.infer_freq(shifted.index) != 'H' else False,
        check_names=False
    )
    assert_series_equal(
        shift_amount,
        shift_expected if pd.infer_freq(shifted.index) != 'H' else no_shift,
        check_names=False
    )


@requires_ruptures
def test_shifts_ruptures_tz_localized(midday):
    shift_mask, shift_amount = time.shifts_ruptures(
        midday.tz_localize(None),
        midday
    )
    assert not shift_mask.any()
    assert shift_mask.index.tz is None
    assert_series_equal(
        shift_amount,
        pd.Series(
            0, index=midday.index.tz_localize(None), dtype='int64'
        ),
        check_names=False
    )
    shift_mask, shift_amount = time.shifts_ruptures(
        midday,
        midday.tz_localize(None)
    )
    assert not shift_mask.any()
    assert shift_mask.index.tz == midday.index.tz
    assert_series_equal(
        shift_amount,
        pd.Series(
            0, index=midday.index, dtype='int64'
        ),
        check_names=False
    )
    shift_mask, shift_amount = time.shifts_ruptures(
        midday.tz_localize(None),
        midday.tz_localize(None)
    )
    assert not shift_mask.any()
    assert shift_mask.index.tz is None
    assert_series_equal(
        shift_amount,
        pd.Series(
            0, index=midday.index.tz_localize(None), dtype='int64'
        ),
        check_names=False
    )


@pytest.mark.parametrize("timezone, expected_dates",
                         [('America/Denver', ['2020-03-08', '2020-11-01']),
                          ('CET', ['2020-03-29', '2020-10-25']),
                          ('MST', [])])
def test_dst_dates(timezone, expected_dates):
    index = pd.date_range(
        start='2020-01-01',
        end='2020-12-31',
        freq='D',
        tz='America/Chicago'
    )
    dates = time.dst_dates(
        index,
        timezone
    )
    expected = pd.Series(False, index=index)
    for date in expected_dates:
        expected[date] = True
    assert_series_equal(dates, expected)
    # Test without timezone information.
    assert_series_equal(
        time.dst_dates(index.tz_localize(None), timezone),
        expected.tz_localize(None)
    )


def test_rounding():
    xs = pd.Series(
        [-10, 10, -16, 16, -28, 28, -30, 30, -8, 8, -7, 7, -3, 3, 0]
    )
    assert_series_equal(
        time._round_multiple(xs, 15),
        pd.Series([-15, 15, -15, 15, -30, 30, -30, 30, -15, 15, 0, 0, 0, 0, 0])
    )
    assert_series_equal(
        time._round_multiple(xs, 15, up_from=9),
        pd.Series([-15, 15, -15, 15, -30, 30, -30, 30, 0, 0, 0, 0, 0, 0, 0])
    )
    assert_series_equal(
        time._round_multiple(xs, 15, up_from=15),
        pd.Series([0, 0, -15, 15, -15, 15, -30, 30, 0, 0, 0, 0, 0, 0, 0])
    )
    assert_series_equal(
        time._round_multiple(xs, 30),
        pd.Series([0, 0, -30, 30, -30, 30, -30, 30, 0, 0, 0, 0, 0, 0, 0])
    )
