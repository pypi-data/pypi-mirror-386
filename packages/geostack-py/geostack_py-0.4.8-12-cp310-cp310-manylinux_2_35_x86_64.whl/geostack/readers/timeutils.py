# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import re
import sys
import numbers
from typing import Union, List, Any, Optional, Callable
from functools import partial
from datetime import datetime, timezone
import warnings
import numpy as np
from ..dataset import supported_libs
from . import ncutils

global HAS_CFTIME, HAS_PYTZ, HAS_CFUNITS

if supported_libs.HAS_NCDF:
    import netCDF4 as nc

if supported_libs.HAS_XARRAY:
    import xarray as xr

cftime, HAS_CFTIME = supported_libs.import_or_skip("cftime")
cfunits, HAS_CFUNITS = supported_libs.import_or_skip("cfunits")

if HAS_CFTIME:
    from cftime import date2num, date2index
    from cftime import Datetime360Day, DatetimeNoLeap

HAS_PYTZ, pytz = supported_libs.import_or_skip("pytz")

__all__ = ["RasterTime", "gribTime", "TimeArray", "regex"]

# reference: https://github.com/Unidata/MetPy/blob/main/src/metpy/xarray.py
regex = {
    "time": re.compile("\\bt\\b|(time|second|sec|minute|min|hour|hr|day|week|month|mon|year)[0-9]*"),
    "Z": re.compile(
        "(z|nav_lev|gdep|lv_|[o]*lev|bottom_top|sigma|h(ei)?ght|altitude|depth|"
        "isobaric|pres|isotherm)[a-z_]*[0-9]*"
    ),
    "Y": re.compile("y|j|nlat|nj"),
    "latitude": re.compile("y?(nav_lat|lat|gphi|north|south)[a-z0-9]*"),
    "X": re.compile("x|i|nlon|ni"),
    "longitude": re.compile("x?(nav_lon|lon|glam|east|west)[a-z0-9]*"),
}
regex["T"] = regex["time"]


def get_timestamp(inp_time,
                  tzinfo: Optional[timezone] = None) -> numbers.Real:
    """get epoch time for a time stamp.

    Parameters
    ----------
    inp_time : Union[datetime, cftime.datetime]
        input time stamp as date time object
    tzinfo : timezone/ pytz.BaseTzInfo object
        timezone information

    Returns
    -------
    numbers.Real
        epoch time for a given time stamp
    """
    out = None
    if HAS_CFTIME:
        if isinstance(inp_time, cftime.datetime):
            # if tzinfo is not None:
            #     _tz_info = tzinfo
            # else:
            #     _tz_info = timezone.utc
            out = date2num(inp_time, "seconds since 1970-01-01",
                           calendar=inp_time.calendar)
    if isinstance(inp_time, datetime):
        if inp_time.tzinfo is not None:
            out = inp_time.timestamp()
        else:
            # force naive datetime to utc
            _inp_time = inp_time.replace(tzinfo=timezone.utc)
            out = _inp_time.timestamp()
    elif isinstance(inp_time, np.datetime64):
        out = inp_time.astype('datetime64[s]').astype(int)
    assert out is not None, "input time should be datetime type"

    return out


def str_to_dt(tstamp: str,
              dt_format: Optional[str] = None,
              tzinfo: Optional[timezone] = None) -> datetime:
    """convert string time stamp to datetime object.

    Parameters
    ----------
    tstamp : str
        time stamp as string
    dt_format : str, optional
        str format to parse time stamp, by default None
    tzinfo : pytz.BaseTzInfo, optional
        time zone information as pytz object, by default None

    Returns
    -------
    datetime
        time stamp as datetime object

    Raises
    ------
    TypeError
        tzinfo should be an instance of pytz.BaseTzInfo
    """
    if dt_format is None:
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
    else:
        datetime_format = dt_format

    try:
        out_date = datetime.fromisoformat(tstamp)
    except ValueError:
        out_date = datetime.strptime(tstamp, datetime_format)

    if tzinfo is not None:
        out_date = out_date.replace(tzinfo=tzinfo)
    return out_date


def epoch_seconds_to_dt(tstamp: numbers.Real,
                        tzinfo: Optional[timezone] = None) -> datetime:
    """convert epoch seconds to datetime object.

    Parameters
    ----------
    tstamp : number.Real
        time in epoch seconds
    tzinfo : pytz.BaseTzInfo, Optional, default to None
        time zone as an instance of pytz.BaseTzInfo

    Returns
    -------
    datetime.datetime
        epoch seconds converted to datetime object
    """
    if tzinfo is None:
        if isinstance(tstamp, np.datetime64):
            time_stamp = datetime.fromtimestamp(tstamp.astype(
                'datetime64[s]').astype(int), timezone.utc)
        else:
            time_stamp = datetime.fromtimestamp(tstamp, timezone.utc)
    else:
        time_stamp = datetime.fromtimestamp(tstamp, tzinfo)
    return time_stamp


def dt_to_epoch_seconds(tstamp: Union[datetime, str],
                        dt_format: Optional[str] = None,
                        tzinfo: Optional[timezone] = None) -> numbers.Real:
    """convert datetime object to epoch seconds.

    Parameters
    ----------
    tstamp : Union[datetime, str]
        time stamp
    dt_format : str, optional
        str format to parse string time stamp, by default None

    Returns
    -------
    numbers.Real
        epoch seconds
    """
    if isinstance(tstamp, str):
        time_stamp = str_to_dt(tstamp, dt_format=dt_format,
                               tzinfo=tzinfo)
        return get_timestamp(time_stamp, tzinfo=tzinfo)
    else:
        return get_timestamp(tstamp, tzinfo=tzinfo)


@supported_libs.RequireLib("netcdf")
def get_index_bounds(nctime: Union[Any, np.ndarray],
                     start_time: Optional[Union[numbers.Real, str]] = None,
                     end_time: Optional[Union[numbers.Real, str]] = None,
                     dt_format: Optional[str] = None,
                     tzinfo: Optional[timezone] = None,
                     method: str = None):
    """get start and end index from the array of time stamps.

    Parameters
    ----------
    nctime : Union[nc.Variable, xr.DataArray, np.ndarray]
        an array of time stamps
    start_time : Union[numbers.Real, str]
        lower bound time stamp
    end_time : Union[numbers.Real, str]
        upper bound time stamp
    dt_format : str, optional
        str format to parse start and end date time, by default None
    method: str, Optional
        `before`, `after`, `nearest`, by default None
        The index selection method. before and after will return the index
        corresponding to the date just before or just after the given date
        if an exact match cannot be found. nearest will return the index that
        correspond to the closest date.

    Raises
    ------
    TypeError
        "ndarray nctime should be array of datetime object"
    """
    if HAS_CFTIME:
        dt_types = (datetime, cftime.datetime, numbers.Real)
    else:
        dt_types = (datetime, numbers.Real)

    if not isinstance(nctime, np.ndarray):
        check_time_array(nctime)

    if start_time is not None:
        # convert start time from str to datetime
        if isinstance(start_time, str):
            _start_time = str_to_dt(start_time, dt_format=dt_format,
                                    tzinfo=tzinfo)
        else:
            _start_time = epoch_seconds_to_dt(start_time, tzinfo=tzinfo)
    else:
        _start_time = num_to_dt(nctime, 0)

    if end_time is not None:
        # convert end time from str to datetime
        if isinstance(end_time, str):
            _end_time = str_to_dt(end_time, dt_format=dt_format,
                                  tzinfo=tzinfo)
        else:
            _end_time = epoch_seconds_to_dt(end_time, tzinfo=tzinfo)
    else:
        _end_time = num_to_dt(nctime, len(nctime) - 1)

    nt = nctime.shape[0]
    # convert start and end time to data type of nctime
    _start_time = conform_type(
        num_to_dt(nctime, 0), _start_time, tzinfo=tzinfo)
    _end_time = conform_type(num_to_dt(nctime, 0), _end_time, tzinfo=tzinfo)

    # check if start and end time are within nctime
    check_edges(nctime, _start_time, _end_time)

    if method is None:
        # if no method specified, set to `nearest`
        method = 'nearest'

    # get index for start time (nearest to desired start time instant)
    start_idx = get_index(nctime, _start_time, method=method)

    if method is None:
        # if no method specified, test whether time stamp is greater than start_idx
        if (_start_time > num_to_dt(nctime, start_idx)):
            # get index right of desired start time instant
            start_idx = get_index(nctime, _start_time, method='before')

    # get index for end time (nearest to desired end time instant)
    end_idx = get_index(nctime, _end_time, method=method)

    if method is None:
        # if no method specified, test whether time stamp is less than end_idx
        if (_end_time < num_to_dt(nctime, end_idx)):
            # get index right of desired end time instant
            end_idx = get_index(nctime, _end_time, method='after')
    return start_idx, end_idx


def get_index(nctime: Union[Any, np.ndarray],
              input_time: Union[numbers.Real, datetime],
              bounds: Optional[List] = None,
              method: Optional[str] = 'nearest',
              tzinfo: Optional[timezone] = None) -> numbers.Integral:
    """get start and end index from the array of time stamps.

    Parameters
    ----------
    nctime : Union[nc.Variable, xr.DataArray, np.ndarray]
        an array of time stamps
    input_time : Union[numbers.Real, datetime]
        time stamp to find index from array of time stamps
    bounds: list, Optional
        list of left and right bounds, by default None
    method: str, Optional
        `before`, `after`, `nearest`, by default 'nearest'
        The index selection method. before and after will return the index
        corresponding to the date just before or just after the given date
        if an exact match cannot be found. nearest will return the index that
        correspond to the closest date.

    Returns
    -------
    numbers.Integral
        index of time stamp
    """
    def _slow_method(nctime, time_instant, min_idx, max_idx,
                     from_right, method):
        # get end index
        if from_right:
            i = max_idx
            while i > (min_idx - 1):
                if num_to_dt(nctime, i) < time_instant:
                    break
                i -= 1
            time_idx = i + 1
        else:
            i = min_idx
            while i < max_idx:
                if num_to_dt(nctime, i) > time_instant:
                    break
                i += 1
            time_idx = i - 1

        return time_idx

    if not isinstance(nctime, np.ndarray):
        check_time_array(nctime)

    if bounds is None:
        nt = nctime.shape[0]
    else:
        nt = (bounds[1] - bounds[0]) + 1

    time_instant = conform_type(
        num_to_dt(nctime, 0), input_time, tzinfo=tzinfo)

    if bounds is None:
        min_idx = 0
        max_idx = nt - 1
    else:
        min_idx, max_idx = bounds

    # check closest end of end time
    from_right = (time_instant - num_to_dt(nctime, min_idx)
                  ) > (num_to_dt(nctime, max_idx) - time_instant)

    if not isinstance(nctime, np.ndarray):
        time_units = getattr(nctime, 'units', None)
        time_calendar = getattr(nctime, "calendar", None)
        if HAS_CFTIME:
            date2index_method = get_date2index_method(time_units,
                                                      calendar=time_calendar,
                                                      select=method)
            time_idx = date2index_method(time_instant, nctime)
        else:
            time_idx = _slow_method(nctime, time_instant, min_idx,
                                    max_idx, from_right, method)
    else:
        time_idx = _slow_method(nctime, time_instant, min_idx,
                                max_idx, from_right, method)

    if method == "before":
        if num_to_dt(nctime, time_idx) >= time_instant:
            time_idx -= 1
        time_idx = max(min_idx, time_idx)
    elif method == "after":
        if num_to_dt(nctime, time_idx) <= time_instant:
            time_idx += 1
        time_idx = min(max_idx, time_idx)
    return time_idx


@supported_libs.RequireLib("netcdf")
def check_time_array(nctime: Any) -> bool:
    """check if start and end time are within the array of time stamp

    Parameters
    ----------
    nctime : Union[nc.Variable, xr.DataArray]
        a netcdf variable or xarray.DataArray

    Returns
    -------
    bool

    Raises
    ------
    TypeError
        "nctime should be a netcdf variable or xr.DataArray"
    """

    if supported_libs.HAS_XARRAY:
        obj_types = (nc.Variable, xr.DataArray, TimeArray,
                     ncutils._ncVariable, nc._netCDF4._Variable)
    else:
        obj_types = (nc.Variable, TimeArray, ncutils._ncVariable,
                     nc._netCDF4._Variable)
    if not isinstance(nctime, obj_types):
        raise TypeError("nctime should be a netcdf variable or xr.DataArray")
    return True


def check_edges(nctime: Any,
                start_time: Union[datetime, numbers.Real] = None,
                end_time: Union[datetime, numbers.Real] = None,
                tzinfo: Optional[timezone] = None) -> bool:
    """check if start and end time are within the array of time stamp

    Parameters
    ----------
    nctime : Union[nc.Variable, xr.DataArray]
        a netcdf variable or xarray.DataArray
    start_time : Union[datetime, numbers.Real]
        start time stamp (lower bound)
    end_time : Union[datetime, numbers.Real]
        end time stamp (upper bound)

    Returns
    -------
    bool
        True if start and end time are within time stamp array

    Raises
    ------
    TypeError
        "nctime should be a netcdf variable or xr.DataArray"
    ValueError
        "start_time is not within input time stamps"
    ValueError
        "end_time is not within input time stamps"
    """
    if not isinstance(nctime, np.ndarray):
        check_time_array(nctime)

    if start_time is not None:
        if type(num_to_dt(nctime, 0)) != type(start_time):
            _start_time = conform_type(
                num_to_dt(nctime, 0), start_time, tzinfo=tzinfo)
        else:
            _start_time = start_time

        if _start_time < num_to_dt(nctime, 0) or _start_time > num_to_dt(nctime, len(nctime) - 1):
            raise ValueError("start_time is not within input time stamps")

    if end_time is not None:
        if type(num_to_dt(nctime, 0)) != type(end_time):
            _end_time = conform_type(num_to_dt(nctime, 0), end_time, tzinfo=tzinfo)
        else:
            _end_time = end_time

        if _end_time < num_to_dt(nctime, 0) or _end_time > num_to_dt(nctime, len(nctime) - 1):
            raise ValueError("end_time is not within input time stamps")

        if start_time is not None:
            if _start_time != _end_time:
                assert _end_time > _start_time, "end_time should be greater than start_time"

    return True


@supported_libs.RequireLib("netcdf")
def num_to_dt(nctime: Any,
              index: int) -> Union[Any, datetime]:
    """convert a time stamp from file to date time.

    Parameters
    ----------
    nctime : Union[nc.Variable, xr.DataArray, np.ndarray]
        a netcdf variable/ xarray.DataArray or numpy array of epoch times
    index : int
        index of time stamp to convert

    Returns
    -------
    Union[datetime, cftime.datetime]
        time stamp converted to datetime object
    """
    if hasattr(nctime, "units"):
        time_units = getattr(nctime, "units")
    elif hasattr(nctime, "attrs"):
        time_units = getattr(nctime, "attrs").get("units")

    if hasattr(nctime, "calendar"):
        time_calendar = getattr(nctime, "calendar")
    elif hasattr(nctime, "attrs"):
        time_calendar = getattr(nctime, "attrs").get(
            "calendar", "proleptic_gregorian")
    else:
        time_calendar = "proleptic_gregorian"

    num2date_method = get_num2date_method(time_units, calendar=time_calendar)

    if not isinstance(nctime, np.ndarray):
        check_time_array(nctime)
        _tstamp = nctime[index]
        try:
            tstamp = num2date_method(_tstamp)
        except Exception as e:
            if isinstance(_tstamp, np.datetime64):
                tstamp = datetime.fromisoformat(
                    _tstamp.astype('datetime64[s]').astype(str))
                try:
                    # try to get units and calendar from xarray encoding
                    units = getattr(nctime, "encoding").get("units")
                    calendar = getattr(nctime, "encoding").get("calendar")
                    tstamp = cftime.num2date(cftime.date2num([tstamp], units=units,
                                                             calendar=calendar), units=units,
                                             calendar=calendar)[0]
                except Exception as e:
                    pass
            else:
                raise RuntimeError(f"{e}")
    else:
        tstamp = nctime[index]
    return tstamp


def get_num2date_method(time_units: str, calendar: Optional[str] = None) -> Callable:
    numpy_unit_map = {'week': 'W', 'month': 'M', 'mon': 'M',
                      'day': 'D', 'year': 'Y', 'hour': 'h',
                      'minute': "m", 'min': "m", 'second': 's',
                      'sec': 's', 'millisecond': 'ms'}

    if time_units is None:
        unit_match = None
    else:
        unit_match = regex['time'].findall(time_units)

    if calendar is None:
        calendar = 'proleptic_gregorian'

    num2date = partial(nc.num2date, units=time_units, calendar=calendar)

    if unit_match is None:
        def num2date(s): return s
    elif isinstance(unit_match, list):
        if len(unit_match) > 0:
            r = re.compile(unit_match[0])
            if not any(filter(r.match, ['second', 'minute', 'hour', 'day'])):
                if calendar.lower() not in ['standard', 'proleptic_gregorian', 'gregorian']:
                    warnings.warn(
                        "Only standard/ proleptic gregorian calendar is supported", UserWarning)
                dt_string = ''.join(re.findall('[0-9\\-\\:T]\\w+', time_units))

                _dt_string = re.match("(?P<yyyy>\\d{4})-(?P<mm>\\d{2})-(?P<dd>\\" +
                                      "d{2})(?P<HH>\\d{2}):(?P<MM>\\d{2}):(?P<SS>\\d{2})",
                                      dt_string)

                if _dt_string is not None:
                    dt_string = (f"{_dt_string.group('yyyy')}-" +
                                 f"{_dt_string.group('mm')}-{_dt_string.group('dd')}")
                    dt_string += (f"T{_dt_string.group('HH')}:" +
                                  f"{_dt_string.group('MM')}:{_dt_string.group('SS')}")

                np_unit_match = numpy_unit_map[unit_match[0]]
                np_time_stamp = np.datetime64(dt_string, 's')

                dt_offset = np.timedelta64(np_time_stamp.astype(
                    f'datetime64[{np_unit_match}]').astype(int),
                    np_unit_match)

                # dt_offset = np.timedelta64(np.datetime64(
                #     dt_string).astype('datetime64').astype(int), 'D')

                def num2date(s):
                    out = np.array(s, dtype=f'datetime64[{np_unit_match}]') + dt_offset
                    if np_unit_match == 'W':
                        # this is a hack to get the offset right
                        # between numpy and netcdf library
                        out = out + np.timedelta64(1, 'D')

                    return out

    return num2date


def get_date2index_method(time_units: str, calendar: Optional[str] = None,
                          select: str = 'nearest') -> Callable:
    if time_units is None:
        unit_match = None
    else:
        unit_match = regex['time'].findall(time_units)

    if calendar is None:
        calendar = 'proleptic_gregorian'

    date2index_method = partial(date2index, calendar=calendar, select=select)

    if unit_match is None:
        dt_array = get_num2date_method(time_units, calendar=calendar)

        def date2index_method(s, dt): return int(
            np.argmin(np.abs(s - dt_array(dt[:]))))
    elif isinstance(unit_match, list):
        if len(unit_match) > 0:
            dt_array = get_num2date_method(time_units, calendar=calendar)

            def date2index_method(s, dt): return int(
                np.argmin(np.abs(s - dt_array(dt[:]))))

    return date2index_method


def conform_type(dst_time: Union[Any, numbers.Real, datetime],
                 src_time: Union[datetime, numbers.Real],
                 tzinfo: Optional[timezone] = None) -> Union[Any, datetime, numbers.Real]:
    """check and coerce datetime type.

    Parameters
    ----------
    dst_time : Union[datetime, cftime.datetime, numbers.Real]
        time stamp with a desired datetime type
    src_time : Union[datetime, numbers.Real]
        time stamp to be transformed

    Returns
    -------
    Union[datetime, cftime.datetime, numbers.Real]
        src date time after casting (when required)

    Raises
    ------
    TypeError
        "Unable to understand data type of dst_time"
    """
    out = None

    if isinstance(src_time, numbers.Real):
        _src_time = epoch_seconds_to_dt(src_time, tzinfo=tzinfo)
    elif isinstance(src_time, np.datetime64):
        # downgrade to seconds (from [ns])
        _src_time = np.datetime64(src_time, 's').astype(datetime)
    else:
        # when src_time is datetime object
        _src_time = src_time

    if isinstance(dst_time, datetime):
        out = _src_time
    elif isinstance(dst_time, np.datetime64):
        out = np.datetime64(_src_time).astype(dst_time.dtype)
    elif isinstance(dst_time, numbers.Real):
        out = get_timestamp(_src_time, tzinfo=tzinfo)

    if HAS_CFTIME:
        if isinstance(dst_time, cftime.datetime):
            dt_obj = type(dst_time)
            if issubclass(dt_obj, DatetimeNoLeap):
                if _src_time.day == 29 and _src_time.month == 2:
                    raise ValueError(
                        "Leap day not supported for no leap calendar")
            elif issubclass(dt_obj, Datetime360Day):
                if _src_time.day == 31:
                    raise ValueError(
                        "360day calendar doesn't support 31 day month")
            out = dt_obj(_src_time.year, _src_time.month,
                         _src_time.day, _src_time.hour,
                         _src_time.minute, _src_time.second)
        else:
            if out is None:
                raise TypeError("Unable to understand data type of dst_time")
    else:
        if out is None:
            raise TypeError("Unable to understand data type of dst_time")
    return out


class gribTime:
    def __init__(self, time_array: Union[List, np.ndarray], **kwargs):
        self.data = time_array
        self._units: str = kwargs.get(
            "units", "seconds since 1970-01-01 00:00:00")
        self._calendar: Optional[str] = "proleptic_gregorian"
        if not isinstance(time_array, np.ndarray):
            raise TypeError("input time array should be np.ndarray")

        if isinstance(time_array[0], datetime):
            self.data = np.array([item.replace(tzinfo=timezone.utc).timestamp()
                                  for item in self.data])

    @property
    def shape(self):
        return self.data.shape

    @property
    def units(self):
        return self._units

    @property
    def calendar(self):
        return self._calendar

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index: Union[slice, int, np.ndarray]):
        return self.data[index]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


class TimeArray:
    def __init__(self, nctime: Any):
        self._handle = nctime
        self._bounds = [0, len(nctime)]

        # create a list of valid objects and methods for each of the objects
        _valid_objects = []
        _valid_method = {}
        if supported_libs.HAS_XARRAY:
            _valid_objects.append(xr.DataArray)
            _valid_method[xr.DataArray] = lambda s: getattr(s, "values")
        if supported_libs.HAS_NCDF:
            _valid_objects += [nc.Variable, nc._netCDF4._Variable]
            for obj in [nc.Variable, nc._netCDF4._Variable]:
                _valid_method[obj] = lambda s: s
        if supported_libs.HAS_PYDAP:
            _valid_objects.append(ncutils._ncVariable)
            _valid_method[ncutils._ncVariable] = lambda s: s
        _valid_objects = tuple(_valid_objects)

        if isinstance(nctime, _valid_objects):
            method = list(
                filter(lambda s: isinstance(nctime, s), _valid_objects))
            if len(method) > 0:
                method = method[0]
            else:
                raise TypeError(f"Object type {type(nctime)} is not supported")
            self.data = _valid_method.get(method)(nctime)
        elif isinstance(nctime, np.ndarray):
            self._handle = self.data = gribTime(nctime[:])
        else:
            raise TypeError(
                "nctime should be a netcdf variable or xr.DataArray")

    @property
    def bounds(self) -> List:
        return self._bounds

    @bounds.setter
    def bounds(self, inp_bounds: List):
        self.update_bounds(inp_bounds)

    def update_bounds(self, bounds: List):
        self._bounds = bounds

    def __getattr__(self, arg: str):
        return getattr(self._handle, arg, None)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index: Union[slice, int, np.ndarray]):
        return self.data[index]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


class RasterTime:
    """Object to handle time variable from netcdf/ xarray datasets.
    """

    def __init__(self, nctime: Any, tzinfo: Optional[timezone] = None):
        self.left_bound = self.right_bound = None
        self.tzinfo = tzinfo

        if not isinstance(nctime, np.ndarray):
            check_time_array(nctime)
        self.time_variable = TimeArray(nctime)

    def get_bounds(self):
        return self.left_bound, self.right_bound

    def time_from_index(self, index: numbers.Integral) -> numbers.Real:
        """epoch time from index

        Parameters
        ----------
        index : numbers.Integral
            index for the time variable array

        Returns
        -------
        numbers.Real
            epoch time from the time variable array
        """
        # offset index by the left bound
        index = min(self.left_bound + index, self.right_bound)

        if isinstance(self.time_variable, np.ndarray):
            if isinstance(self.time_variable[0], numbers.Real):
                # return value when array contains numbers
                out = self.time_variable[index]
            else:
                # return epoch time when array contains datetime objects
                out = get_timestamp(
                    self.time_variable[index], tzinfo=self.tzinfo)
        else:
            # return epoch time when input is netcdf variable or xarray data array
            if check_time_array(self.time_variable):
                _time_stamp = num_to_dt(self.time_variable, index)
                out = get_timestamp(_time_stamp, tzinfo=self.tzinfo)
            else:
                raise TypeError("Can't understand datatype of time variable")
        return out

    def get_max_time_index(self) -> numbers.Integral:
        """return maximum index of time variable

        Parameters
        ----------
        Nil

        Returns
        -------
        int
            maximum time tindex
        """
        return len(self.time_variable) - 1

    def set_index_bounds(self, start_idx: Optional[numbers.Integral] = None,
                         end_idx: Optional[numbers.Integral] = None):
        """set index bounds of time variable for given start and end index

        Parameters
        ----------
        start_idx : numbers.Integral
            left index
        end_idx : numbers.Integral
            right index
        """
        if len(self.time_variable) > 0:
            if start_idx is None:
                start_idx = 0
            else:
                if start_idx < 0:
                    raise ValueError("Incorrect start index for time variable")

            if end_idx is None:
                end_idx = len(self.time_variable)-1
            else:
                if end_idx >= len(self.time_variable):
                    raise ValueError("Incorrect end index for time variable")

        self.left_bound = start_idx
        self.right_bound = end_idx

    def set_time_bounds(self, start_time: Optional[Union[numbers.Real, str]] = None,
                         end_time: Optional[Union[numbers.Real, str]] = None,
                         dt_format: Optional[str] = None,
                         method: str='nearest'):
        """set time bounds of time variable for start and end time

        Parameters
        ----------
        start_time : Union[numbers.Real, str]
            left bound time stamp
        end_time : Union[numbers.Real, str]
            right bound time stamp
        dt_format : str, optional
            str format to parse time stamp, by default None
        method: str, Optional
            `before`, `after`, `nearest`, by default 'nearest'
            The index selection method. before and after will return the index
            corresponding to the date just before or just after the given date
            if an exact match cannot be found. nearest will return the index that
            correspond to the closest date.

        Returns
        -------
        Nil
        """
        if len(self.time_variable) > 1:
            self.time_variable.bounds = list(get_index_bounds(self.time_variable, start_time,
                                                              end_time, dt_format=dt_format))
        self.left_bound = self.time_variable.bounds[0]
        self.right_bound = self.time_variable.bounds[1]

    def get_left_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        """get left index for a time stamp

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            time stamp to get left index from time variable array

        Returns
        -------
        numbers.Integral
            return left index from the time variable array
        """
        _time_stamp = conform_type(num_to_dt(self.time_variable, 0), timestamp)
        if len(self.time_variable) > 1:
            _time_idx = get_index(self.time_variable, _time_stamp,
                                  bounds=self.get_bounds(), method='before')
            _time_idx = max(self.left_bound, _time_idx)
        else:
            _time_idx = 0
        return _time_idx

    def get_right_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        """get right index for a time stamp

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            time stamp to get right index from time variable array

        Returns
        -------
        numbers.Integral
            return right index from the time variable array
        """
        _time_stamp = conform_type(num_to_dt(self.time_variable, 0), timestamp)
        if len(self.time_variable) > 1:
            _time_idx = get_index(self.time_variable, _time_stamp,
                                  bounds=self.get_bounds(), method='after')
            _time_idx = min(self.right_bound, _time_idx)
        else:
            _time_idx = 0
        return _time_idx

    def get_index(self, timestamp: Union[datetime, numbers.Real],
                  method: str = 'nearest') -> numbers.Integral:
        """get index for a time stamp

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            time stamp to get right index from time variable array
        method: str, Optional
            `before`, `after`, `nearest`, by default 'nearest'
            The index selection method. before and after will return the index
            corresponding to the date just before or just after the given date
            if an exact match cannot be found. nearest will return the index that
            correspond to the closest date.

        Returns
        -------
        numbers.Integral
            return closest index from the time variable array
        """
        _time_stamp = conform_type(num_to_dt(self.time_variable, 0), timestamp)
        if len(self.time_variable) > 1:
            _time_idx = get_index(self.time_variable, _time_stamp,
                                  bounds=self.get_bounds())
        else:
            _time_idx = 0
        return _time_idx

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


if __name__ == "__main__":
    # when converting epoch seconds to datetime, assumed to be UTC
    inp_epoch = 1381899600
    dt = epoch_seconds_to_dt(inp_epoch)
    epoch = dt_to_epoch_seconds(dt)
    assert inp_epoch == epoch

    # when the time zone information is UTC
    inp_str = "2011-11-04 00:05:23.283+00:00"
    dt = str_to_dt(inp_str)
    epoch = dt_to_epoch_seconds(dt)
    out_str = epoch_seconds_to_dt(epoch).isoformat()
    assert inp_str == out_str

    # when there is no time information
    inp_str = '2011-11-04'
    dt = str_to_dt(inp_str)
    epoch = dt_to_epoch_seconds(dt)
    out_str = epoch_seconds_to_dt(epoch).isoformat()
    assert inp_str == out_str[:len(inp_str)]

    # when there is a time offset, retaining timezone information
    inp_str = '2011-11-04T00:05:23+04:00'
    dt = str_to_dt(inp_str)
    epoch = dt_to_epoch_seconds(dt)
    out_str = epoch_seconds_to_dt(epoch, tzinfo=dt.tzinfo).isoformat()
    assert inp_str == out_str
