"""Functions for identifying if AC power streams are cumulative, and
correcting if so."""

import warnings

def energy_cumulative(energy_series, pct_increase_threshold = 95):
    r"""Test if an AC energy data stream is cumulative or not by differencing
    the time series, and determining if the derivative is continuously
    increasing.
    
    Parameters
    ----------
    energy_series: Series
    
    pct_increase_threshold: int

    Returns
    -------
    Boolean
        If energy stream is cumulative, True is returned. Otherwise False
        is returned.

    Notes
    -----
    Adapted from the NREL PV Fleets quality assurance (QA) routine. 
    """
    differenced_series = energy_series.diff()
    differenced_series = differenced_series.dropna()
    # If the time series is less than one day in length, or has fewer than
    # 10 readings, throw an error.
    if (len(differenced_series) < 10) | ():
        warnings.warn("The energy time series has a length of zero and "
                     "cannot be run.")
    else:
        # If over X percent of the data is increasing (set via the
        # pct_increase_threshold), then assume that the column is cumulative 
        differenced_series_positive_mask = (differenced_series >= -.5)
        pct_over_zero = differenced_series_positive_mask.value_counts(
            normalize=True) * 100
        if pct_over_zero[True] >= pct_increase_threshold:
            energy_series = energy_series.diff()
            return True
        else:
            return False

def correct_cumulative_energy(energy_series, pct_increase_threshold = 95):
    r"""Correct an energy time series if it is cumulative, so interval readings
    are returned.
    
    Parameters
    ----------
    energy_series: Series
    
    pct_increase_threshold: int

    Returns
    -------
    Series
        Time series of values with a datetime index, representing interval 
        (non-cumulative) data.

    Notes
    -----
    Adapted from the NREL PV Fleets quality assurance (QA) routine. 
    """
    # Test if the energy time series is cumulative
    cum_energy = energy_cumulative(energy_series,
                                   pct_increase_threshold)
    # If the energy series is cumulative, correct it
    if cum_energy:
        return energy_series.diff()
    #If series is not cumulative, return the original series
    else:
        return energy_series
        
