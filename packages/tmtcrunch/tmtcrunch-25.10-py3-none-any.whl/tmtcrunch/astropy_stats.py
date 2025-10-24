# Licensed under a 3-clause BSD style license
"""
Several functions from astropy.stats in case astropy package is not installed.

https://www.astropy.org/
"""

import numpy as np

__all__ = [
    "median_absolute_deviation",
    "biweight_scale",
]


def median_absolute_deviation(data, axis=None, func=None, ignore_nan=False):
    """
    Calculate the median absolute deviation (MAD).

    The MAD is defined as ``median(abs(a - median(a)))``.

    Parameters
    ----------
    data : array-like
        Input array or object that can be converted to an array.
    axis : None, int, or tuple of int, optional
        The axis or axes along which the MADs are computed.  The default
        (`None`) is to compute the MAD of the flattened array.
    func : callable, optional
        The function used to compute the median. Defaults to `numpy.ma.median`
        for masked arrays, otherwise to `numpy.median`.
    ignore_nan : bool
        Ignore NaN values (treat them as if they are not in the array) when
        computing the median.  This will use `numpy.ma.median` if ``axis`` is
        specified, or `numpy.nanmedian` if ``axis==None`` and numpy's version
        is >1.10 because nanmedian is slightly faster in this case.

    Returns
    -------
    mad : float or `~numpy.ndarray`
        The median absolute deviation of the input array.  If ``axis``
        is `None` then a scalar will be returned, otherwise a
        `~numpy.ndarray` will be returned.
    """
    if func is None:
        # Check if the array has a mask and if so use np.ma.median
        # See https://github.com/numpy/numpy/issues/7330 why using np.ma.median
        # for normal arrays should not be done (summary: np.ma.median always
        # returns an masked array even if the result should be scalar). (#4658)
        if isinstance(data, np.ma.MaskedArray):
            is_masked = True
            func = np.ma.median
            if ignore_nan:
                data = np.ma.masked_where(np.isnan(data), data, copy=True)
        elif ignore_nan:
            is_masked = False
            func = np.nanmedian
        else:
            is_masked = False
            func = np.median  # drops units if result is NaN
    else:
        is_masked = None

    data = np.asanyarray(data)
    # np.nanmedian has `keepdims`, which is a good option if we're not allowing
    # user-passed functions here
    data_median = func(data, axis=axis)

    # broadcast the median array before subtraction
    if axis is not None:
        data_median = np.expand_dims(data_median, axis=axis)

    result = func(np.abs(data - data_median), axis=axis, overwrite_input=True)

    if axis is None and np.ma.isMaskedArray(result):
        # return scalar version
        result = result.item()
    elif np.ma.isMaskedArray(result) and not is_masked:
        # if the input array was not a masked array, we don't want to return a
        # masked array
        result = result.filled(fill_value=np.nan)

    return result


def _stat_functions(data, ignore_nan=False):
    if isinstance(data, np.ma.MaskedArray):
        median_func = np.ma.median
        sum_func = np.ma.sum
    elif ignore_nan:
        median_func = np.nanmedian
        sum_func = np.nansum
    else:
        median_func = np.median
        sum_func = np.sum

    return median_func, sum_func


def biweight_scale(
    data, c=9.0, M=None, axis=None, modify_sample_size=False, *, ignore_nan=False
):
    r"""
    Compute the biweight scale.

    The biweight scale is a robust statistic for determining the
    standard deviation of a distribution.  It is the square root of the
    `biweight midvariance
    <https://en.wikipedia.org/wiki/Robust_measures_of_scale#The_biweight_midvariance>`_.
    It is given by:

    .. math::

        \zeta_{biscl} = \sqrt{n} \ \frac{\sqrt{\sum_{|u_i| < 1} \
            (x_i - M)^2 (1 - u_i^2)^4}} {|(\sum_{|u_i| < 1} \
            (1 - u_i^2) (1 - 5u_i^2))|}

    where :math:`x` is the input data, :math:`M` is the sample median
    (or the input location) and :math:`u_i` is given by:

    .. math::

        u_{i} = \frac{(x_i - M)}{c * MAD}

    where :math:`c` is the tuning constant and :math:`MAD` is the
    `median absolute deviation
    <https://en.wikipedia.org/wiki/Median_absolute_deviation>`_.  The
    biweight midvariance tuning constant ``c`` is typically 9.0 (the
    default).

    If :math:`MAD` is zero, then zero will be returned.

    For the standard definition of biweight scale, :math:`n` is the
    total number of points in the array (or along the input ``axis``, if
    specified).  That definition is used if ``modify_sample_size`` is
    `False`, which is the default.

    However, if ``modify_sample_size = True``, then :math:`n` is the
    number of points for which :math:`|u_i| < 1` (i.e. the total number
    of non-rejected values), i.e.

    .. math::

        n = \sum_{|u_i| < 1} \ 1

    which results in a value closer to the true standard deviation for
    small sample sizes or for a large number of rejected values.

    Parameters
    ----------
    data : array-like
        Input array or object that can be converted to an array.
        ``data`` can be a `~numpy.ma.MaskedArray`.
    c : float, optional
        Tuning constant for the biweight estimator (default = 9.0).
    M : float or array-like, optional
        The location estimate.  If ``M`` is a scalar value, then its
        value will be used for the entire array (or along each ``axis``,
        if specified).  If ``M`` is an array, then its must be an array
        containing the location estimate along each ``axis`` of the
        input array.  If `None` (default), then the median of the input
        array will be used (or along each ``axis``, if specified).
    axis : None, int, or tuple of int, optional
        The axis or axes along which the biweight scales are computed.
        If `None` (default), then the biweight scale of the flattened
        input array will be computed.
    modify_sample_size : bool, optional
        If `False` (default), then the sample size used is the total
        number of elements in the array (or along the input ``axis``, if
        specified), which follows the standard definition of biweight
        scale.  If `True`, then the sample size is reduced to correct
        for any rejected values (i.e. the sample size used includes only
        the non-rejected values), which results in a value closer to the
        true standard deviation for small sample sizes or for a large
        number of rejected values.
    ignore_nan : bool, optional
        Whether to ignore NaN values in the input ``data``.

    Returns
    -------
    biweight_scale : float or `~numpy.ndarray`
        The biweight scale of the input data.  If ``axis`` is `None`
        then a scalar will be returned, otherwise a `~numpy.ndarray`
        will be returned.

    See Also
    --------
    biweight_midvariance, biweight_midcovariance, biweight_location, astropy.stats.mad_std, astropy.stats.median_absolute_deviation

    References
    ----------
    .. [1] Beers, Flynn, and Gebhardt (1990; AJ 100, 32) (https://ui.adsabs.harvard.edu/abs/1990AJ....100...32B)

    .. [2] https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/biwscale.htm

    """
    return np.sqrt(
        biweight_midvariance(
            data,
            c=c,
            M=M,
            axis=axis,
            modify_sample_size=modify_sample_size,
            ignore_nan=ignore_nan,
        )
    )


def biweight_midvariance(
    data, c=9.0, M=None, axis=None, modify_sample_size=False, *, ignore_nan=False
):
    r"""
    Compute the biweight midvariance.

    The biweight midvariance is a robust statistic for determining the
    variance of a distribution.  Its square root is a robust estimator
    of scale (i.e. standard deviation).  It is given by:

    .. math::

        \zeta_{bivar} = n \ \frac{\sum_{|u_i| < 1} \
            (x_i - M)^2 (1 - u_i^2)^4} {(\sum_{|u_i| < 1} \
            (1 - u_i^2) (1 - 5u_i^2))^2}

    where :math:`x` is the input data, :math:`M` is the sample median
    (or the input location) and :math:`u_i` is given by:

    .. math::

        u_{i} = \frac{(x_i - M)}{c * MAD}

    where :math:`c` is the tuning constant and :math:`MAD` is the
    `median absolute deviation
    <https://en.wikipedia.org/wiki/Median_absolute_deviation>`_.  The
    biweight midvariance tuning constant ``c`` is typically 9.0 (the
    default).

    If :math:`MAD` is zero, then zero will be returned.

    For the standard definition of `biweight midvariance
    <https://en.wikipedia.org/wiki/Robust_measures_of_scale#The_biweight_midvariance>`_,
    :math:`n` is the total number of points in the array (or along the
    input ``axis``, if specified).  That definition is used if
    ``modify_sample_size`` is `False`, which is the default.

    However, if ``modify_sample_size = True``, then :math:`n` is the
    number of points for which :math:`|u_i| < 1` (i.e. the total number
    of non-rejected values), i.e.

    .. math::

        n = \sum_{|u_i| < 1} \ 1

    which results in a value closer to the true variance for small
    sample sizes or for a large number of rejected values.

    Parameters
    ----------
    data : array-like
        Input array or object that can be converted to an array.
        ``data`` can be a `~numpy.ma.MaskedArray`.
    c : float, optional
        Tuning constant for the biweight estimator (default = 9.0).
    M : float or array-like, optional
        The location estimate.  If ``M`` is a scalar value, then its
        value will be used for the entire array (or along each ``axis``,
        if specified).  If ``M`` is an array, then its must be an array
        containing the location estimate along each ``axis`` of the
        input array.  If `None` (default), then the median of the input
        array will be used (or along each ``axis``, if specified).
    axis : None, int, or tuple of int, optional
        The axis or axes along which the biweight midvariances are
        computed.  If `None` (default), then the biweight midvariance of
        the flattened input array will be computed.
    modify_sample_size : bool, optional
        If `False` (default), then the sample size used is the total
        number of elements in the array (or along the input ``axis``, if
        specified), which follows the standard definition of biweight
        midvariance.  If `True`, then the sample size is reduced to
        correct for any rejected values (i.e. the sample size used
        includes only the non-rejected values), which results in a value
        closer to the true variance for small sample sizes or for a
        large number of rejected values.
    ignore_nan : bool, optional
        Whether to ignore NaN values in the input ``data``.

    Returns
    -------
    biweight_midvariance : float or `~numpy.ndarray`
        The biweight midvariance of the input data.  If ``axis`` is
        `None` then a scalar will be returned, otherwise a
        `~numpy.ndarray` will be returned.

    See Also
    --------
    biweight_midcovariance, biweight_midcorrelation, astropy.stats.mad_std, astropy.stats.median_absolute_deviation

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Robust_measures_of_scale#The_biweight_midvariance

    .. [2] Beers, Flynn, and Gebhardt (1990; AJ 100, 32) (https://ui.adsabs.harvard.edu/abs/1990AJ....100...32B)

    """
    median_func, sum_func = _stat_functions(data, ignore_nan=ignore_nan)

    if isinstance(data, np.ma.MaskedArray) and ignore_nan:
        data = np.ma.masked_where(np.isnan(data), data, copy=True)

    data = np.asanyarray(data).astype(np.float64)

    if M is None:
        M = median_func(data, axis=axis)
    if axis is not None:
        M = np.expand_dims(M, axis=axis)

    # set up the differences
    d = data - M

    # set up the weighting
    mad = median_absolute_deviation(data, axis=axis, ignore_nan=ignore_nan)

    if axis is None:
        # data is constant or mostly constant OR
        # data contains NaNs and ignore_nan=False
        if mad == 0.0 or np.isnan(mad):
            return mad**2  # variance units
    else:
        mad = np.expand_dims(mad, axis=axis)

    with np.errstate(divide="ignore", invalid="ignore"):
        u = d / (c * mad)

    # now remove the outlier points
    # ignore RuntimeWarnings for comparisons with NaN data values
    with np.errstate(invalid="ignore"):
        mask = np.abs(u) < 1
    if isinstance(mask, np.ma.MaskedArray):
        mask = mask.filled(fill_value=False)  # exclude masked data values

    u = u**2

    if modify_sample_size:
        n = sum_func(mask, axis=axis)
    else:
        # set good values to 1, bad values to 0
        include_mask = np.ones(data.shape)
        if isinstance(data, np.ma.MaskedArray):
            include_mask[data.mask] = 0
        if ignore_nan:
            include_mask[np.isnan(data)] = 0
        n = np.sum(include_mask, axis=axis)

    f1 = d * d * (1.0 - u) ** 4
    f1[~mask] = 0.0
    f1 = sum_func(f1, axis=axis)
    f2 = (1.0 - u) * (1.0 - 5.0 * u)
    f2[~mask] = 0.0
    f2 = np.abs(np.sum(f2, axis=axis)) ** 2

    # If mad == 0 along the specified ``axis`` in the input data, return
    # 0.0 along that axis.
    # Ignore RuntimeWarnings for divide by zero.
    with np.errstate(divide="ignore", invalid="ignore"):
        value = n * f1 / f2
        if np.isscalar(value):
            return value

        where_func = np.where
        if isinstance(data, np.ma.MaskedArray):
            where_func = np.ma.where  # return MaskedArray
        return where_func(mad.squeeze() == 0, 0.0, value)
