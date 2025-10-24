from datetime import datetime, timedelta

import numpy as np
from scipy import stats
from utide import solve, reconstruct

from uhslc_station_tools.utils import datenum


def calwts(Tc, S):
    """
     This routine computes a set of convolution-type filter weights
     using the procedure described in Bloomfield's book. The half
     amplitude point of the filter is Tc and the total span of the
     filter is S. The span, S, must be odd or a fatal error occurs.
    Parameters:
    -----------
    Tc: The period where the filter will have 50%
        amplitude response. The units must be in
        terms of the time step. For example, using
        Tc=10 with an hourly time step gives half
        amplitude response at a period of 10 hours.
        However, if the time step is 5 days, then
        using Tc=10 puts the 50% point at 50 days.

    S:  The total span of the filter in units of
        time step (see above under Tc). N.B., this
        includes the central weights and BOTH sides
        of the filter. This number is therefore
        odd for a proper filter.

    Returns:
    --------
     wts -  The computed weights. This is a vector
            of length S that has been normalized to
            unit sum.
    --------------------------------------------------------------------
    NOTES  :  1. The routine CALRSP can be used to check the response
              function in frequency space for the filter.


    HISTORY:  1. Original version written 15 March 1989 by Gary Mitchum.
    """

    # Check that the span of the filter is odd. Stop if not.
    if S % 2 == 0:
        print('Number of filter weights is not odd. Execution terminated.')
        raise
    s = int((S - 1) / 2)
    t = np.arange(1, s + 1, 1)

    wt = np.sin(2 * np.pi * t / Tc) * np.sin(2 * np.pi * t / S) / (4 * np.pi ** 2 * t ** 2 / (Tc * S))

    facnrm = 1 + 2 * sum(wt)
    wts = np.append(np.flip(wt, 0), np.append(1, wt)) / facnrm

    return wts


def smooth_gap1(u, wt, ngap=0.8):
    """
    Convolve with ``wt`` while tolerating gaps in ``u``.

    ``NaN`` values in ``u`` are treated as gaps. Convolution is normalized by a
    convolved validity mask; outputs where the effective data fraction is below
    ``ngap`` (relative to ``sum(wt)``) are set to ``NaN``.

    Args:
        u: 1-D array-like input signal containing ``NaN`` gaps.
        wt: 1-D array of convolution filter weights.
        ngap: Minimum valid-weight fraction (0-1) required to keep a value.

    Returns:
        1-D ``numpy.ndarray`` of filtered values, same length as ``u``.
    """

    # Zero out gaps.
    k = np.argwhere(np.isnan(u))

    u[k] = 0

    # Add zeros to front and end of time series.
    n = len(u)
    nwt = len(wt)
    nwt2 = int(np.floor(nwt / 2))
    uu = np.append(np.full(nwt2, 0), np.append(u, np.full(nwt2, 0)))

    # Apply convolution.
    ua = np.convolve(uu, wt, 'same')

    # Binary vector, 1 if data, 0 no data.
    xx = np.full(len(uu), 1)
    xx[uu == 0] = 0
    nu = np.convolve(xx, wt, 'same')

    # NaN out data if nu < .8
    ua = np.divide(ua, nu, out=np.full_like(ua, np.nan), where=(nu != 0) & (~np.isnan(nu)))
    kn = np.argwhere(nu / sum(wt) < ngap)
    ua[kn] = np.nan

    # Trim off wts at beginning and end of time series.
    ua = ua[nwt2:nwt2 + n]

    return ua


def matlab2datetime(matlab_datenum):
    """
    Convert a MATLAB datenum to a Python ``datetime``.

    Args:
        matlab_datenum: Floating MATLAB serial date number (days since
            0000-01-00 with an offset of 366 days vs. Python ordinal).

    Returns:
        ``datetime.datetime`` corresponding to ``matlab_datenum``.
    """

    day = datetime.fromordinal(int(matlab_datenum))
    dayfrac = timedelta(days=matlab_datenum % 1) - timedelta(days=366)

    return day + dayfrac + +timedelta(microseconds=3)


def hr_calwts_filt(tin, xin):
    """
    Uses calwts.m to compute
    filter weights for Bloomfield's convolution filter.  Assumes constant sample period
    for input time series (i.e., no discontinuities).

    Parameters:
    -----------
    tin: A time vector as an array same length as xin
    xin: An array of date points at tin

    Returns:
    --------

    [tout, xout]: An array of timeseries centered on hour
    """

    # filter cutoff period = 90 minutes
    # filter length = 180 minutes

    # filter performance
    # 99.43% power at 6 hour period
    # 89.22% power at 3 hour period
    # 59.8% power at 2 hour period
    # 0.21% power at 1 hour period

    # Compute weights depending on sample period.
    dt = np.nanmedian(np.diff(tin)) * 24 * 60
    Tc = round(90 / dt)
    S = round(180 / dt)

    # Ensure odd length filter.
    if S % 2 == 0:
        S += 1

    # Filter weights.
    wts = calwts(Tc, S)

    # Input sample period.
    dt = np.nanmedian(np.diff(tin))
    t = np.arange(tin[0], tin[-1], dt)

    # Find gaps > 16 minutes.
    k = np.where(np.diff(tin) > 16.0 / 60 / 24)[0]
    if len(k) == 0:
        print("ZERO - No large gaps found, interpolating whole series")
        x = np.interp(t, tin, xin)
        # Correct interpolated values that are exact matches in tin.
        tin_arr = np.asarray(tin)
        idx = np.searchsorted(t, tin_arr)
        valid_idx = idx < len(t)
        idx_valid = idx[valid_idx]
        tin_valid = tin_arr[valid_idx]
        is_close = np.isclose(t[idx_valid], tin_valid, atol=1e-8)
        valid = np.zeros_like(idx, dtype=bool)
        valid[valid_idx] = is_close
        # Fix: Only override where interpolated and raw values differ.
        same = idx[valid]
        same = same[same < len(xin)]
        if same.size:
            diff_mask = xin[same] != x[same]
            x[same[diff_mask]] = xin[same[diff_mask]]
    else:
        x = np.full(len(t), np.nan)
        for jj in range(len(k) + 1):
            if jj == 0:
                j1 = 0
                j2 = k[jj]
            elif jj == len(k):
                j1 = k[jj - 1]
                j2 = len(tin) - 1
            else:
                j1 = k[jj - 1]
                j2 = k[jj]
            kk = np.where(np.logical_and(t >= tin[j1], t <= tin[j2]))[0]
            if len(kk) > 1:
                x[kk] = np.interp(t[kk], tin[j1:j2 + 1], xin[j1:j2 + 1])

    # Convolution allowing for gaps.
    xs = smooth_gap1(x, wts, .8)

    yr_ar = []
    mon_ar = []
    day_ar = []
    hr_ar = []

    # Convert the Matlab epoch to Python datetime.
    for d in t:
        _date = datetime.fromordinal(int(d)) + timedelta(days=d % 1) - timedelta(days=366)
        yr_ar.append(_date.year)
        mon_ar.append(_date.month)
        day_ar.append(_date.day)
        hr_ar.append(_date.hour)

    yr = np.asarray(yr_ar)
    mon = np.asarray(mon_ar)
    day = np.asarray(day_ar)
    hr = np.asarray(hr_ar)

    # Get first hour.
    t1 = datenum(datetime(yr[0], mon[0], day[0], hr[0], 0, 0))
    if t1 < t[0]:
        t1 = datenum(datetime(yr[0], mon[0], day[0], hr[0], 0, 0) + timedelta(hours=1))

    # Total number of hours.
    nhrs = int(np.floor((t[-1] - t1) * 24) + 1)

    tout = []

    for j in range(nhrs):
        tout.append(datenum(datetime(yr[0], mon[0], day[0], hr[0], 0, 0) + timedelta(hours=j)))

    tout = np.asarray(tout)

    if tout[-1] > t[-1]:
        tout = tout[0:-1]

    xout = np.interp(tout, t, xs)

    return [tout, xout]


def var_flag(arg):
    '''
    Returns an int based on channel code supplied
    '''
    c = -1
    if arg == 'enc':
        c = 0
    elif arg == 'enb':
        c = 1
    elif arg == 'adr':
        c = 2
    elif arg == 'sdr':
        c = 3
    elif arg == 'prs':
        c = 4
    elif arg == 'rad':
        c = 5
    elif arg == 'ra2':
        c = 6
    elif arg == 'ecs':
        c = 7
    elif arg == 'ec2':
        c = 8
    elif arg == 'bub':
        c = 9
    elif arg == 'en0':
        c = 10
    elif arg == 'pwi':
        c = 11
    elif arg == 'pwl':
        c = 12
    elif arg == 'bwl':
        c = 13
    elif arg == 'pr2':
        c = 14
    elif arg == 'ana':
        c = 15
    elif arg == 'prb':
        c = 16
    elif arg == 'hou':
        c = 17

    return c


def channel_merge(hr_data, chan_params):
    '''
    Takes hourly data calculated by hr_process and fills in the gaps using
    the successive channels based on the hierarchy defined in chan_params

    Parameters:
    -----------
    hr_data: hourly data for all channels for a particular station, calculated
    with hr_process function

    chan_params: An array of dictionaries, in which each key is the channel name
    and the value is an integer (0,1, or 2), representing is the adjustment flag
    (see below). E.g.: [{'rad': 0}, {'prs': 0}]

    The elements in the array need to be ordered by the channel importance (e.g
    primary channel, secondary, and so on).

    Adjustment flag 0: no adjustment,
    Adjustment flag 1: adjust means,
    Adjustment flag 2: adjust means and linear trend

    Returns:
    --------
    A time series of merged hourly data for a particular station along with the
    channel mask for each particular data point so that the data can be backtracked
    to the channel (sensor) it came from.
    '''

    datac = {}

    for i, var in enumerate(chan_params):
        # 1) Get time and data of the primary channel and output the primary channel,
        # name, and station number.

        ch_name = list(chan_params[i].keys())[0]
        flagpar = list(chan_params[i].values())[0]

        # TODO: Sometimes there won't be any data for the primary channel.
        # For example station 113 in 2018.
        # Need to fall down to the next channel on the list and use it as a
        # primary.
        if i == 0:
            tc = hr_data[ch_name]["time"].flatten()
            xc = hr_data[ch_name]["sealevel"].flatten()
            c = np.full(len(tc), 1) * var_flag(ch_name)
            datac["var"] = ch_name
        # 2) Go through successive channels.
        else:
            if ch_name in hr_data:
                print("CHANNEL NAME", ch_name)
                tn = hr_data[ch_name]["time"].flatten()
                xn = hr_data[ch_name]["sealevel"].flatten()

                ts = min(tn[0], tc[0])
                te = max(tn[-1], tc[-1])
                # 2.1) Adjust start end end date by comparing it to previous channel.
                if ts != tc[0] or te != tc[-1]:
                    tt = []
                    print('NON PRIMARY channel has a time vector different than the primary')
                    nhr = int(np.floor((te - ts) * 24) + 1)
                    _date = datetime.fromordinal(int(ts)) + timedelta(days=ts % 1) - timedelta(days=366)
                    yr = _date.year
                    mon = _date.month
                    day = _date.day
                    hr = _date.hour
                    # tt can be a vector in Matlab so tt should be an array and it will be length of
                    # 0 to nhr (in matlab it is to nhr-1).
                    for n in range(nhr):
                        tt.append(datenum(datetime(yr, mon, day, hr, 0, 0) + timedelta(hours=n)))
                    tt = np.asarray(tt).flatten()
                    xx = np.full(len(tt), np.nan)
                    cc = np.full(len(tt), np.nan)
                    k = np.where(np.logical_and(tt >= tc[0], tt <= tc[-1]))[0]
                    xx[k] = xc
                    tt[k] = tc
                    cc[k] = c
                    xc = xx
                    tc = tt
                    c = cc
                # 2.2) Adjust start end end date by comparing it to previous channel
                # and adjust the data.
                if ts != tn[0] or te != tn[-1]:
                    tt = []
                    print('NON PRIMARY channel has a time vector different than the other NON primary')
                    nhr = int(np.floor((te - ts) * 24) + 1)
                    _date = datetime.fromordinal(int(ts)) + timedelta(days=ts % 1) - timedelta(days=366)
                    yr = _date.year
                    mon = _date.month
                    day = _date.day
                    hr = _date.hour
                    # tt can be a vector in Matlab so tt should be an array and it will be length of
                    # 0 to nhr (in matlab it is to nhr-1)
                    for n in range(nhr):
                        tt.append(datenum(datetime(yr, mon, day, hr, 0, 0) + timedelta(hours=n)))
                    tt = np.asarray(tt).flatten()
                    xx = np.full(len(tt), np.nan)
                    if tt[-1] >= tn[-1]:
                        k = np.where(np.logical_and(tt >= tn[0], tt <= tn[-1]))[0]
                        xx[k] = xn
                        tt[k] = tn
                        print("alpha")
                    else:
                        k = np.where(tt >= tn[0])[0]
                        tmp = np.where(tn > tt[-1])[0]
                        tmp = len(tmp)
                        xx[k] = xn[:len(xn) - tmp]
                        tt[k] = tn[:len(tn) - tmp]
                        print("beta")
                    xn = xx
                    tn = tt
                # 2.3) Find values where input is nan but output is not.
                if len(xc) == len(xn):
                    kk = np.where(np.logical_and(np.isnan(xc), ~np.isnan(xn)))[0]
                    print("gamma")
                else:
                    if len(xn) > len(xc):
                        kk = np.where(np.logical_and(np.isnan(xc), ~np.isnan(xn[:len(xc)])))[0]
                        print("delta")
                    else:
                        kk = np.where(np.logical_and(np.isnan(xc[:len(xn)]), ~np.isnan(xn)))[0]
                        print("etha")

                # 2.4) Find the gaps and their size.
                gaps = []
                if len(kk) > 0:
                    dk = np.diff(kk)
                    nk = np.where(dk > 1)[0]
                    gaps = np.ndarray(shape=(len(nk) + 1, 2), dtype=object)
                    if (len(nk) == 0):
                        gaps[0, 0] = kk[0]
                        gaps[0, 1] = kk[-1]
                    else:
                        for jnk in range(len(nk)):
                            if jnk == 0:
                                gaps[jnk, 0] = kk[0]
                                gaps[jnk, 1] = kk[nk[jnk]]
                            else:
                                gaps[jnk, 0] = kk[nk[jnk - 1] + 1]
                                gaps[jnk, 1] = kk[nk[jnk]]
                        gaps[len(nk), 0] = kk[nk[len(nk) - 1] + 1]
                        gaps[len(nk), 1] = kk[-1]
                        # print("gaps[len(nk),0]", gaps[len(nk),0])
                        # print("gaps[len(nk),1]", gaps[len(nk),1])
                        # print("kk[nk[len(nk)-1]+1]", kk[nk[len(nk)-1]+1])
                        # print("kk[-1]", kk[-1])
                        # print("len nk",len(nk))
                    ngap = np.size(gaps[:, 1])

                    for jgap in range(ngap):
                        j1 = gaps[jgap, 0] - 24 * 7
                        j2 = gaps[jgap, 1] + 24 * 7
                        if j1 < 0:
                            j1 = 0
                        if j2 > len(xc) - 1:
                            # print("THIS CASE")
                            j2 = len(xc) - 1
                        if gaps[jgap, 1] == gaps[jgap, 0]:
                            samp_num = 1
                        elif gaps[jgap, 1] - gaps[jgap, 0] == 1:
                            samp_num = 2
                        else:
                            samp_num = gaps[jgap, 1] + 1 - gaps[jgap, 0]
                        jj = np.linspace(gaps[jgap, 0], gaps[jgap, 1], samp_num, dtype=int)

                        if j2 == j1:
                            samp_num = 1
                        elif j2 - j1 == 1:
                            samp_num = 2
                        else:
                            samp_num = j2 + 1 - j1

                        j1_to_j2 = np.linspace(j1, j2, samp_num, dtype=int)
                        # return
                        # 2.5) interpolate based on the flagpar
                        if flagpar == 2:

                            tti = tc[j1_to_j2]
                            yyi = xc[j1_to_j2] - xn[j1_to_j2]
                            mask = ~np.isnan(tti) & ~np.isnan(yyi)
                            b = stats.linregress(tti[mask], yyi[mask])
                            comb = np.ndarray(shape=(len(jj), 2), dtype=float)
                            comb[:, 0] = tc[jj]
                            comb[:, 1] = np.full(len(jj), 1)
                            xc[jj] = xn[jj] + np.matmul(comb, np.array([b.slope, b.intercept]))
                        elif flagpar == 1:
                            b = np.nanmean(xc[j1_to_j2] - xn[j1_to_j2])
                            if np.isnan(b):
                                b = 0
                            # print("jj start", jj[0])
                            # print("jj end", jj[-1])
                            # print("nanmean", np.nanmean(xn[jj]))
                            # print("jj", jj)
                            # print("len jj", len(jj))
                            xc[jj] = xn[jj] + b
                        elif flagpar == 0:
                            xc[jj] = xn[jj]

                        c[jj] = np.full(len(jj), 1) * var_flag(ch_name)

    # 3) Find remaining nan data points and asign nan values to channel mask at
    # those points.
    k = np.where(np.isnan(xc))[0]
    c[k] = -1

    # 4) Create an object of time, sealevel, channel mask.
    datac["time"] = tc
    datac["sealevel"] = xc
    datac["channel"] = c
    datac["ch_priority"] = chan_params

    # 5) Return the object (will contain the above plus prim channel and station num).
    return datac


def hr_process(_data, yr1, yr2):
    """
    Parameters:
    -----------
    _data: a dictionary of sealevel data for a station split by channel name (created using upload(path) method).
    yr1,yr2: Integers, representing years between which to limit data

    Returns:
    --------

    dictionary: hourly averages for each channel and tide

    """

    hr_data = {}
    for key in _data.keys():
        times = _data[key]['time']
        sealevels = _data[key]['sealevel']
        if len(times) < 2:
            print(f"Skipping {key} - not enough data")
            continue
        if np.all(np.diff(times) == 0):
            print(f"Skipping {key} - time vector not changing")
            continue

        # Compute hourly average.
        try:
            [th, xh] = hr_calwts_filt(times, sealevels)
        except ValueError as e:
            print(f"Skipping {key} due to filter error: {e}")
            continue

        # Limit data between yr1 and yr2.
        ky = np.argwhere(np.logical_and(th >= datenum(yr1), th < datenum(yr2)))
        if len(ky) == 0:
            continue

        th = th[ky]
        xh = xh[ky]

        # Interpolate predicted tide to hourly time stamp from 15min.
        hr_data[key] = {'time': th, 'sealevel': xh, 'station': _data[key]['station']}

    return hr_data


def day_119filt(_data, _lat):
    """
    Daily 119-hour low-pass filter centered on local noon.

    Builds a 119-hour (5-day) window with half-amplitude at 60 hours, removes
    predicted tide via UTide harmonic analysis, then computes a daily value at
    approximately noon using a gap-aware convolution and channel-weighted mask.

    Args:
        _data: Dict with keys ``time`` (MATLAB datenum), ``sealevel`` (array),
            and ``channel`` (source flags) for a merged series (e.g., from
            :func:`channel_merge`).
        _lat: Station latitude in decimal degrees (for UTide nodal corrections).

    Returns:
        Dict with keys:
        * ``time``: 1-D array of daily times (noon samples).
        * ``residual``: Full-resolution residual series (observed - tide).
        * ``sealevel``: Daily filtered values at noon (``NaN`` if insufficient data).
        * ``channel``: Daily channel mask (weighted/rounded integer codes).
    """

    data_day = {}
    Tc = 60  # filter cutoff period = 60 hr (2.5 days)
    S = 119  # filter length = 119 hr (~5 days, must be odd)

    wts = np.asarray(calwts(Tc, S))
    t = _data["time"]
    x = _data["sealevel"]

    # 1) Find tide prediction
    # 2) Calculate residual
    # 3) Center data on noon

    coef = solve(_data["time"].flatten(), _data["sealevel"].flatten(), lat=_lat, nodal=False, epoch="matlab", white=True)
    coef.slope = 0
    coef.mean = 0
    coef.A[np.where(coef.aux.frq < 1 / 30)] = 0
    tide = reconstruct(_data["time"].flatten(), coef, epoch="matlab")

    # Residual.
    xr = x - tide["h"]

    hr_ar = []

    _date = [matlab2datetime(float(tval)) for tval in _data["time"]]
    for d in _date:
        hr_ar.append(d.hour)
    hr = np.asarray(hr_ar)
    k = np.where(hr == 12)[0]
    ks = k - 59
    ke = k + 59

    kk = np.where(ks < 1)[0]
    ks[kk] = 0

    kk = np.where(ke > len(x))[0]
    ke[kk] = len(x) - 1

    nday = len(k)
    tout = t[k]
    xout = np.full(nday, np.nan)
    cout = xout.copy()

    for j in range(nday):
        xx = np.full(119, np.nan)
        ww = np.full(119, np.nan)
        cc = np.full(119, np.nan)

        slice_len = ke[j] - ks[j] + 1
        expected_len = 119
        start_index = 59 - (k[j] - ks[j])

        # Skip if the index would go out of bounds in the 119-length window.
        if start_index < 0 or (start_index + slice_len) > expected_len:
            print(f"WARNING: In day_119filt, skipping window at index {j}")
            print(f"         Reason: out-of-bounds filter index (start: {start_index}, length: {slice_len})")
            continue

        # Prepare slices.
        xr_slice = xr[ks[j]:ke[j] + 1]
        wts_slice = wts[start_index:start_index + slice_len]
        chan_slice = _data["channel"][ks[j]:ke[j] + 1]

        # Check if all slices match.
        if (len(xr_slice) == slice_len and
            len(wts_slice) == slice_len and
            len(chan_slice) == slice_len):

            xx[start_index:start_index + slice_len] = xr_slice
            ww[start_index:start_index + slice_len] = wts_slice
            cc[start_index:start_index + slice_len] = chan_slice
        else:
            print(f"WARNING: In day_119filt, skipping window at index {j} due to slice mismatch")
            continue

        kg = np.where(~np.isnan(xx))[0]
        xout[j] = zero_division(sum(xx[kg] * ww[kg]), sum(ww[kg]))
        cout[j] = np.round(zero_division(sum(cc[kg] * ww[kg]), sum(ww[kg])))

        kb = np.where(np.isnan(xx))[0]

        if len(kb) > 0:
            if sum(abs(ww[kb])) > 0.25:
                xout[j] = np.nan
                cout[j] = np.nan

    data_day["time"] = tout
    data_day["residual"] = xr
    data_day["sealevel"] = xout
    data_day["channel"] = cout

    return data_day


def is_number(s):
    """
    Return ``True`` if ``s`` can be converted to ``float``.

    Args:
        s: Any object.

    Returns:
        ``True`` if ``float(s)`` succeeds, else ``False``.
    """

    try:
        float(s)
        return True
    except ValueError:
        return False


def zero_division(n, d):
    """
    Safe division with ``NaN`` on zero denominator.

    Args:
        n: Numerator (scalar or array-like).
        d: Denominator (scalar or array-like).

    Returns:
        ``n / d`` where ``d != 0``; otherwise ``numpy.nan``.
    """

    return n / d if d else np.nan
