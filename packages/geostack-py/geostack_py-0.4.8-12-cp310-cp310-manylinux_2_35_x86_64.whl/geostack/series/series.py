# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os.path as pth
import numbers
import numpy as np
try:
    import numpy.typing as npt
    ArrayLike = npt.ArrayLike
except ImportError:
    ArrayLike = np.ndarray
from datetime import datetime
from functools import partial
from typing import List, Dict, Union, Optional, Any
from fnmatch import fnmatch

from ._cy_series import (Series_dbl_flt,
                         Series_int_flt,
                         Series_dbl_dbl,
                         Series_int_dbl)  # noqa
from .. import gs_enums
from .. import raster
from .. import core
from ..dataset.supported_libs import import_or_skip

global HAS_PYTZ

pytz, HAS_PYTZ = import_or_skip('pytz')

__all__ = ["Series"]


def parse_date_string(inp_str: str, timezone=None,
                      dt_format: str = "%Y-%m-%dT%H:%M:%SZ") -> datetime:
    """parse a date string to datetime object

    Parameters
    ----------
    inp_str : str
        datetime string
    timezone : pytz.BaseTzInfo, optional
        time zone as a pytz object, by default None
    dt_format : str, optional
        string format for parsing datetime string, by default "%Y-%m-%dT%H:%M:%SZ"

    Returns
    -------
    datetime
        a datetime object from the datetime string

    Raises
    ------
    TypeError
        timezone should be an instance of pytz.BaseTzInfo
    """
    time_zone = None
    try:
        out_date = datetime.strptime(inp_str, dt_format)
    except ValueError:
        if fnmatch(inp_str, "*+??:??"):
            out_date = datetime.fromisoformat(inp_str)
        else:
            raise RuntimeError("Unable to parse datetime")

    if HAS_PYTZ:
        if timezone is None:
            time_zone = pytz.UTC
        else:
            if isinstance(timezone, pytz.BaseTzInfo):
                time_zone = timezone
            else:
                raise TypeError(
                    "timezone should be an instance of pytz.BaseTzInfo")

        out_date = out_date.replace(tzinfo=time_zone)
    return out_date


class Series:
    def __init__(self, *args, **kwargs):
        self.obj_types: Dict = {"index_type": np.int64,
                                "value_type": core.REAL}
        self.fileName = None

        if args:
            self._parse_args(args)
        if kwargs:
            self._parse_kwargs(kwargs)

        if self.obj_types['value_type'] == np.float32:
            if self.obj_types['index_type'] == np.int64:
                self._handle = Series_int_flt()
            else:
                self._handle = Series_dbl_flt()
        else:
            if self.obj_types['index_type'] == np.int64:
                self._handle = Series_int_dbl()
            else:
                self._handle = Series_dbl_dbl()

        if self.fileName is not None:
            self.from_file(self.fileName)

    def from_file(self, fileName: str) -> None:
        """initialise Series object with data from file

        Parameters
        ----------
        fileName : str
            path of series file
        """
        self._handle.from_file(fileName)

    @staticmethod
    def c_copy(other: Any) -> Series:
        """make shallow copy of Series object

        Parameters
        ----------
        other : Any
            an instance of Series object

        Returns
        -------
        Series
            ab object with a copy of Series object
        """
        dtype_map = {
            Series_dbl_dbl: (np.float64, np.float64),
            Series_dbl_flt: (np.float64, np.float32),
            Series_int_dbl: (np.int64, np.float64),
            Series_int_flt: (np.int64, np.float32),
        }

        if hasattr(other, '_handle'):
            out = Series(**other.obj_types)
            out._handle = other._handle
        elif type(other) in dtype_map:
            obj_types = dtype_map[type(other)]
            out = Series(*obj_types)
            out._handle = other

        return out

    def _parse_args(self, inpargs: List):
        for item in inpargs:
            if isinstance(item, str):
                self.fileName = item

        args = [item for item in filter(lambda s: not isinstance(s, str), inpargs)]

        arg_len = min(len(args), 2)
        for item, arg in zip(['index_type', 'value_type'], range(arg_len)):
            if item == "index_type":
                if args[arg] in [int, np.int32, np.int64]:
                    self.obj_types[item] = np.int64
                elif args[arg] in [float, np.float32, np.float64]:
                    self.obj_types[item] = np.float64
                else:
                    raise ValueError(f"{item} type can be only int64/float64")
            else:
                if args[arg] in [float, np.float32, np.float32]:
                    self.obj_types[item] = np.float32
                elif args[arg] in [np.float64]:
                    self.obj_types[item] = np.float64
                else:
                    raise ValueError(
                        f"{item} type can be only float32/float64")

    def _parse_kwargs(self, inpargs: Dict):
        for item in inpargs:
            if isinstance(inpargs[item], str):
                self.fileName = inpargs[item]

        kwargs = [(item, inpargs[item]) for item in
                  filter(lambda s: not isinstance(inpargs[s], str), inpargs)]
        kwargs = dict(kwargs)

        arg_len = min(len(kwargs), 2)
        for item in ['index_type', 'value_type']:
            if item == "index_type":
                if kwargs.get(item) in [int, np.int32, np.int64]:
                    self.obj_types[item] = np.int64
                elif kwargs.get(item) in [float, np.float32, np.float64]:
                    self.obj_types[item] = np.float64
                else:
                    raise ValueError("Index type can be only int64/float64")
            else:
                if kwargs.get(item, core.REAL) in [float, np.float32]:
                    self.obj_types[item] = np.float32
                elif kwargs.get(item, core.REAL) in [np.float64]:
                    self.obj_types[item] = np.float64
                else:
                    raise ValueError("Value type can be only float32/float64")

    @staticmethod
    def read_csv_file(filepath: str, **kwargs) -> "Series":
        """parse a csv file or csv data into a Series object.

        Parameters
        ----------
        filepath : str
            path of the csv file or csv data as string delimited by newline character

        Returns
        -------
        Series
            a series object
        """
        if kwargs.get("index_type"):
            x_type = kwargs.get("index_type")
            kwargs.pop('index_type')
        else:
            x_type = np.int64
        if kwargs.get('value_type'):
            y_type = kwargs.get("value_type")
            kwargs.pop('value_type')
        else:
            y_type = core.REAL
        out = Series(index_type=x_type, value_type=y_type)
        out.from_csvfile(filepath, **kwargs)
        return out

    def from_csvfile(self, other: str, index_col: int = 0,
                     usecols: Optional[List] = None, parse_date: bool = False,
                     dt_format: Optional[str] = None, time_factor: Optional[numbers.Real] = None,
                     timezone=None, **kwargs):
        """method to parse csv file or csv data string.

        Parameters
        ----------
        other : str
            path to a csv file or csv data as string
        index_col : int, optional
            column number to use as index, by default 0
        usecols : List, optional
            a list of column indices to use for parsing, by default None
        parse_date : bool, optional
            flag to parse date, by default False
        dt_format : str, optional
            a string representation of datetime format, by default None
        time_factor : numbers.Real, optional
            a factor to apply to the time index, by default None
        timezone : pytz.BaseTzInfo, optional
            time zone offset, by default None

        Raises
        ------
        TypeError
            input argument should be of str type
        FileNotFoundError
            file is not present
        AssertionError
            Series object only support two columns
        ValueError
            index column should be in usecols
        """
        if not isinstance(other, str):
            raise TypeError("input argument should be of str type")

        if '\n' not in other:
            if not pth.exists(other):
                raise FileNotFoundError(f"{other} is not present")

        if parse_date:
            if dt_format is None:
                datetime_format = "%Y-%m-%dT%H:%M:%SZ"
            else:
                datetime_format = dt_format

            if time_factor is None:
                _time_factor = 1.0
            else:
                _time_factor = time_factor

        if usecols is not None:
            assert len(usecols) == 2, "Series object only support two columns"
        else:
            usecols = [index_col, 1]

        if not kwargs.get("dtype"):
            if not parse_date:
                if self.index_type == np.int64:
                    x_type = 'i8'
                elif self.index_type == np.float64:
                    x_type = 'f8'
            else:
                x_type = "U25"
            if self.value_type == np.float32:
                y_type = 'f4'
            elif self.value_type == np.float64:
                y_type = 'f8'
            dtype = f'{x_type},{y_type}'
        else:
            dtype = kwargs.get('dtype')
            kwargs.pop('dtype')

        if kwargs.get('names') and isinstance(kwargs.get("names"), list):
            col_names = kwargs['names']
            kwargs.pop('names')
        else:
            if '\n' not in other:
                with open(other, 'r') as inp:
                    row = inp.readline()
            else:
                row = other.split('\n')[0]
            col_names = [row.split(',')[item] for item in usecols]

        if '\n' not in other:
            datainp = np.genfromtxt(other, dtype=dtype, usecols=usecols,
                                    names=col_names, delimiter=',', **kwargs)
        else:
            datainp = np.genfromtxt(filter(lambda s: len(s.strip()) > 0, other.split('\n')),
                                    dtype=dtype, usecols=usecols, delimiter=',',
                                    names=col_names, **kwargs)

        if kwargs.get('names'):
            var_names = kwargs.get('names')
        else:
            var_names = datainp.dtype.names

        if index_col not in usecols:
            raise ValueError("index column should be in usecols")
        for item in usecols:
            if item != index_col:
                var_col = item

        nx = len(datainp)

        if index_col < var_col:
            var_name = var_names[1]
            index_name = var_names[0]
        else:
            var_name = var_names[0]
            index_name = var_names[1]

        if parse_date:
            date_parser = partial(parse_date_string, timezone=timezone,
                                  dt_format=datetime_format)
            dt_stamp = [date_parser(item).timestamp()
                        for item in datainp[var_names[index_col]]]
            dt_stamp = np.array(
                dt_stamp, dtype=self.index_type) * _time_factor
        else:
            dt_stamp = datainp[index_name]
        self.add_values(dt_stamp, datainp[var_name])
        self.setName(var_name)

    def from_list(self, other: List,
                  isSorted: bool = False):
        """add data to series object from a list.

        Parameters
        ----------
        other : List
            a list with index and values
        isSorted: bool
            flag to sort data at ingestion
        """
        assert len(other[0]) == 2, "input argument should be list of list"
        self.from_ndarray(np.array(other))

    def from_ndarray(self, other: np.ndarray,
                     isSorted: bool = False):
        """add data to series object from a ndarray.

        Parameters
        ----------
        other : np.ndarray
            a ndarray with index and values
        isSorted: bool
            flag to sort data at ingestion
        """
        assert isinstance(
            other, np.ndarray), "input argument should be np.ndarray"
        if isinstance(other, np.recarray):
            self.from_recarray(other)
        else:
            assert other.shape[1] == 2, "np.ndarray should be (N,2) shape"
            self.add_values(other[:, 0].astype(self.index_type),
                            other[:, 1].astype(self.value_type),
                            isSorted=isSorted)

    def from_recarray(self, other: np.recarray,
                      isSorted: bool = False):
        """add data to series object from a np.recarray.

        Parameters
        ----------
        other : np.recarray
            a numpy record array with index and values
        isSorted: bool
            flag to sort data at ingestion
        """
        assert isinstance(
            other, np.recarray), "input argument should be np.recarray"
        assert len(other.dtype) == 2, "np.recarray should have two records"
        var_names = other.dtype.names
        index_name = var_names[0]
        var_name = var_names[1]
        self.setName(var_name)
        self.add_values(other[index_name].astype(self.index_type),
                        other[var_name].astype(self.value_type),
                        isSorted=isSorted)

    def add_value(self, x: Union[str, numbers.Real], y: numbers.Real,
                  isSorted: bool = False):
        """add a index and value to series object.

        Parameters
        ----------
        x : numbers.Real
            index for the value in series object
        y : numbers.Real
            value to add in the series object
        isSorted: bool
            flag to sort data at ingestion
        """
        assert self.index_type and self.value_type, "index/ value type not set"
        if isinstance(x, str):
            self._handle.add_string_value(core.str2bytes(x),
                                          self.value_type(y), isSorted=isSorted)
        else:
            self._handle.add_value(self.index_type(x),
                                   self.value_type(y), isSorted=isSorted)

    def add_values(self, x: np.ndarray, y: np.ndarray,
                   isSorted: bool = False):
        """add multiple values in a series object.

        Parameters
        ----------
        x : np.ndarray
            a numpy ndarray of indices
        y : np.ndarray
            a numpy ndarray of values
        isSorted: bool
            flag to sort data at ingestion
        """
        assert isinstance(x, np.ndarray) and isinstance(
            y, np.ndarray), "input should be np.ndarray"
        assert self.index_type and self.value_type, "index/ value type not set"
        self._handle.add_values(x.astype(self.index_type),
                                y.astype(self.value_type),
                                isSorted=isSorted)

    def setInterpolation(self, interp_type: Union[gs_enums.SeriesInterpolationType,
                                                  numbers.Integral]):
        """set interpolation scheme for a Series object.

        Parameters
        ----------
        interp_type : Union[gs_enums.SeriesInterpolationType, numbers.Integral]
            the interpolation scheme to use for the series object

        Raises
        ------
        TypeError
            series interpolation type should be int/ SeriesInterpolationType
        """
        if not isinstance(interp_type, (gs_enums.SeriesInterpolationType,
                                        numbers.Integral)):
            raise TypeError(
                "series interpolation type should be int/ SeriesInterpolationType")
        if isinstance(interp_type, numbers.Integral):
            self._handle.setInterpolation(interp_type)
        elif isinstance(interp_type, gs_enums.SeriesInterpolationType):
            self._handle.setInterpolation(interp_type.value)

    def setCapping(self, capping_type: Union[gs_enums.SeriesCappingType,
                                             numbers.Integral]):
        """set capping type for a Series object.

        Parameters
        ----------
        capping_type : Union[gs_enums.SeriesCappingType, numbers.Integral]
            the capping type to use for the series object
            - if Uncapped a non-data value will be returned if x is outside x-bounds
            - if Capped the limiting y-value will be returned if x is outside x-bounds

        Raises
        ------
        TypeError
            series capping type should be int/ SeriesCappingType
        """
        if not isinstance(capping_type, (gs_enums.SeriesCappingType,
                                         numbers.Integral)):
            raise TypeError(
                "series capping type should be int/ SeriesCappingType")
        if isinstance(capping_type, numbers.Integral):
            self._handle.setCapping(capping_type)
        elif isinstance(capping_type, gs_enums.SeriesCappingType):
            self._handle.setCapping(capping_type.value)

    def setName(self, other: Union[str, bytes]):
        """method to set name for a series object.

        Parameters
        ----------
        other : Union[str, bytes]
            name of the series object

        Raises
        ------
        TypeError
            name should be of str/bytes type
        """
        if isinstance(other, (str, bytes)):
            self._handle.setName(core.str2bytes(other))
        else:
            raise TypeError("name should be of str/ bytes type")

    def setBounds(self, lowerLimit: numbers.Real, upperLimit: numbers.Real):
        """method to set bounds for a series object.

        Parameters
        ----------
        lowerLimit : numbers.Real
            lower limit of the series bounds
        upperLimit : numbers.Real
            upper limit of the series bounds

        Raises
        ------
        RuntimeError
            value type is not set
        """
        if self.value_type:
            self._handle.setBounds(self.value_type(lowerLimit),
                                   self.value_type(upperLimit))
        else:
            raise RuntimeError("value type is not set")

    def get(self, x: Union[numbers.Real, ArrayLike]) -> Union[numbers.Real, ArrayLike]:
        """method to get value from a Series object.

        Parameters
        ----------
        x : Union[numbers.Real, npt.ArrayLike]
            index locations

        Returns
        -------
        Union[numbers.Real, npt.ArrayLike]
            values of a series object at a given index location

        Raises
        ------
        RuntimeError
            index type is not set
        """
        if self.index_type:
            if np.isscalar(x):
                out = self._handle(self.index_type(x))
            else:
                out = np.asanyarray(self._handle(x.astype(self.index_type)))
        else:
            raise RuntimeError("index type is not set")
        return out

    @classmethod
    def from_series(cls, other: "Series") -> "Series":
        """method to shallow copy a Series object.

        Parameters
        ----------
        other : Series
            an instance of python/ cython Series object

        Returns
        -------
        Series
            an instance of Series object with a copy of the input Series object

        Raises
        ------
        TypeError
            input object should be of Series type
        """
        if isinstance(other, cls):
            out = cls(**other.obj_type)
            out._handle.from_series(other._handle)
        else:
            obj_type = {Series_dbl_dbl: dict(index_type=np.float64,
                                             value_type=np.float64),
                        Series_int_dbl: dict(index_type=np.int64,
                                             value_type=np.float64),
                        Series_int_flt: dict(index_type=np.int64,
                                             value_type=np.float32),
                        Series_dbl_flt: dict(index_type=np.float64,
                                             value_type=np.float32)}
            if not obj_type.get(other):
                raise TypeError("input object should be of Series type")
            out = cls(**obj_type[other])
            out._handle.from_series(other)
        return out

    def getName(self) -> str:
        """method to get name of series object.

        Returns
        -------
        str
            name of the series object
        """
        return self._handle.getName()

    def clear(self):
        """clear the contents of Series object.
        """
        self._handle.clear()

    def get_xMax(self) -> numbers.Real:
        """get maximum of Series indices.

        Returns
        -------
        numbers.Real
            maximum index
        """
        return self._handle.get_xMax()

    def get_xMin(self) -> numbers.Real:
        """get minimum of Series indices.

        Returns
        -------
        numbers.Real
            minimum index
        """
        return self._handle.get_xMin()

    def get_yMax(self) -> numbers.Real:
        """get maximum of Series values.

        Returns
        -------
        numbers.Real
            maximum value
        """
        return self._handle.get_yMax()

    def get_yMin(self) -> numbers.Real:
        """get minimum of Series values.

        Returns
        -------
        numbers.Real
            minimum value
        """
        return self._handle.get_yMin()

    @property
    def isInitialised(self) -> bool:
        """method to check if Series object is initialized.

        Returns
        -------
        bool
            True if initialized, False otherwise
        """
        return self._handle.isInitialised()

    @property
    def isConstant(self) -> bool:
        """method to check if values in Series object are constant.

        Returns
        -------
        bool
            True if constant, False otherwise
        """
        return self._handle.isConstant()

    def inRange(self, x: numbers.Real) -> bool:
        """method to check if index is within the range of Series indices.

        Parameters
        ----------
        x : numbers.Real
            index location to check in the Series object

        Returns
        -------
        bool
            True if `x` is in range of Series indices, False otherwise

        Raises
        ------
        RuntimeError
            index type is not specified
        """
        if self.index_type:
            return self._handle.inRange(self.index_type(x))
        else:
            raise RuntimeError("index type is not specified")

    def update(self, isSorted: bool = False):
        """method to update Series object.
        """
        self._handle.update(isSorted=isSorted)

    def updateLimits(self):
        """method to update the limits of Series object.
        """
        self._handle.updateLimits()

    def getOrdinates(self, x: Optional[ArrayLike] = None) -> ArrayLike:
        """get values from the Series

        Returns
        -------
        npt.ArrayLike
            an array of values
        """
        if x is None:
            return np.asanyarray(self._handle.getOrdinates())
        else:
            return np.asanyarray(self._handle.get_values(self.index_type(x)))

    def getAbscissas(self) -> ArrayLike:
        """get ordinates from the Series

        Returns
        -------
        npt.ArrayLike
            an array of ordinates
        """
        return np.asanyarray(self._handle.getAbscissas())

    def resample(self, x: Union[numbers.Real, ArrayLike],
                 method: Union[str, int, 'gs_enums.SeriesInterpolationType'] = 0,
                 fill_value: Optional[Union[ArrayLike, numbers.Real]] = None,
                 left: Optional[numbers.Real] = None,
                 right: Optional[numbers.Real] = None) -> Union[numbers.Real, npt.ArrayLike]:
        """resample series for a given ordinates and interpolation method

        Parameters
        ----------
        x : Union[numbers.Real, npt.ArrayLike]
            single ordinate or an array of ordinates
        method : Union[str, int, gs_enums.SeriesInterpolationType]
            the interpolation scheme to use for the series object, default = 0
        fill_value : Optional[Union[npt.ArrayLike, numbers.Real]]
            - if float, return fill_value when x < index[0] or x > index[-1]
            - if two-element tuple, then first element is used when x < index[0] and
              second element is used when x > index[-1]
            default = None
        left : Optional[numbers.Real]
            value to return for x < index[0], default = None
        right : Optional[numbers.Real]
            value to return for x > index[-1], default = None

        Returns
        -------
        Union[numbers.Real, npt.ArrayLike]
            _description_
        """
        if isinstance(method, int):
            interp_method = gs_enums.SeriesInterpolationType(method)
        elif isinstance(method, str):
            interp_method = getattr(gs_enums.SeriesInterpolationType, method)
        elif isinstance(method, gs_enums.SeriesInterpolationType):
            interp_method = method

        # set interpolation method
        self.setInterpolation(interp_method)

        if interp_method == gs_enums.SeriesInterpolationType.BoundedLinear:
            if fill_value is not None:
                if len(fill_value) < 1 or np.isscalar(fill_value):
                    bounds = [fill_value] * 2
                elif len(fill_value) >= 2:
                    bounds = fill_value[:2]
                self.setBounds(*bounds)
            else:
                bounds = [raster.getNullValue(self.dtype),
                          raster.getNullValue(self.dtype)]
                if left is not None:
                    bounds[0] = left
                if right is not None:
                    bounds[1] = right
                self.setBounds(*bounds)

        # get values
        out = np.asanyarray(self._handle(self.index_type(x)))
        return out

    def getSize(self) -> np.uint32:
        return self._handle.getSize()

    @property
    def name(self) -> str:
        return self.getName()

    @name.setter
    def name(self, arg) -> None:
        self.setName(arg)

    @property
    def ndim(self) -> int:
        return 1

    @property
    def shape(self) -> int:
        return (self.getSize(), 2)

    @property
    def data(self) -> np.ndarray:
        return np.c_[self.getAbscissas(), self.getOrdinates()]

    @data.setter
    def data(self, *args) -> None:
        if isinstance(args[0], np.ndarray):
            # handle case when input array is 2d with x,y as columns
            assert isinstance(args[0], np.ndarray), "input args should be ndarray"
            assert args[0].ndim == 2, "input array should be 2 x N"
            inp_array = (args[0][:, 0], args[0][:, 1])
        elif isinstance(args[0], (list, tuple)):
            # handle case when input arrays are 1D with x, y as separate args
            inp_array = args[0][:2]
            assert len(inp_array[0]) == len(inp_array[1]), "input lengths should be same"

        self.clear()
        self.add_values(*inp_array)

    def isSorted(self) -> bool:
        return self._handle.isSorted()

    def mean(self) -> Union[float, np.float64]:
        return self._handle.mean()

    def sum(self) -> Union[float, np.float64]:
        return self._handle.total()

    @property
    def dtype(self) -> np.dtype:
        return self.obj_types.get("value_type")

    @property
    def index_type(self) -> np.dtype:
        return self.obj_types.get("index_type")

    @property
    def value_type(self) -> np.dtype:
        return self.obj_types.get("value_type")

    def __as_recarray__(self) -> np.ndarray:
        _name = self.name
        if _name == "":
            _name = "ordinate"
        return np.core.records.fromarrays(
            [self.getAbscissas(), self.getOrdinates()],
            dtype=np.dtype([('abscissa', self.index_type),
                            (_name, self.value_type)])
        )

    def __array__(self) -> np.ndarray:
        return self.data

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        inputs = tuple(x.data
                       if isinstance(x, Series) else x
                       for x in inputs)
        result = getattr(ufunc, method)(*inputs, **kwargs)
        return result

    def __getitem__(self, *args):
        return self.data.__getitem__(*args)

    def __len__(self) -> np.uint32:
        return self.getSize()

    def __call__(self, x: Union[numbers.Real, ArrayLike]) -> Union[numbers.Real, ArrayLike]:
        out = self._handle(self.index_type(x))
        if np.isscalar(out):
            return out
        else:
            return np.asanyarray(out)

    def __str__(self):
        x_col = "Index:   %s " % (self.index_type.__name__)
        x_col += f"{self.get_xMin()} ... {self.get_xMax()}\n"
        y_col = "Series variables:\n"
        y_col += "    %s (%s):   " % (self.getName(),
                                      self.value_type.__name__)
        y_col += f"{self.get_yMin()} ... {self.get_yMax()}"
        return x_col + y_col

    def getCapping(self) -> gs_enums.SeriesCappingType:
        return gs_enums.SeriesCappingType(self._handle.getCapping())

    def getInterpolation(self) -> gs_enums.SeriesInterpolationType:
        return gs_enums.SeriesInterpolationType(self._handle.getInterpolation())

    def __getstate__(self) -> Dict:
        _state = {
            "abscissa": self.getAbscissas(),
            "ordinate": self.getOrdinates(),
            "name": self.getName(),
            "index_type": self.index_type,
            "value_type": self.value_type,
            "capping": self.getCapping(),
            "interpolationType": self.getInterpolation()
        }
        return _state

    def __setstate__(self, ds) -> None:
        self.__init__(ds['index_type'], ds['value_type'])
        self.setName(ds['name'])
        self.add_values(ds['abscissa'], ds['ordinate'])
        self.setCapping(ds['capping'])
        self.setInterpolation(ds['interpolationType'])

    def __repr__(self):
        return "<class 'geostack.series.%s'>\n%s" % (self.__class__.__name__,
                                                     str(self))
