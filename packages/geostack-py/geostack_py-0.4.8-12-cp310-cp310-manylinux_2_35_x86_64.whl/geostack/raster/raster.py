# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import re
import os.path as pth
import ctypes
import json
from collections import OrderedDict
import numbers
import warnings
from math import ceil
from typing import Union, List, Dict, Tuple, Optional
from functools import singledispatch, update_wrapper
from itertools import filterfalse, product
import numpy as np
from .. import core
from ._cy_raster import (_RasterBaseList_d, _RasterBaseList_f,
    equalSpatialMetrics_f, equalSpatialMetrics_d)
from ._cy_raster import (_cyRaster_d, _cyRaster_f, _cyRaster_d_i,
    _cyRaster_f_i, _cyRaster_d_byt, _cyRaster_f_byt)
from ._cy_raster import _cyRasterBase_d, _cyRasterBase_f
from ._cy_raster import _RasterPtrList_d, _RasterPtrList_f
from ._cy_raster import _RasterDimensions_d, _RasterDimensions_f
from ._cy_raster import _Dimensions_f, _Dimensions_d
from ._cy_raster import _TileDimensions_f, _TileDimensions_d
from ._cy_raster import (DataFileHandler_f, DataFileHandler_d,
                         DataFileHandler_d_i, DataFileHandler_f_i,
                         DataFileHandler_d_byt, DataFileHandler_f_byt)
from ._cy_raster import TileSpecifications
from ._cy_raster import (getNullValue_dbl, getNullValue_flt, getNullValue_uint32,
                         getNullValue_int64, getNullValue_int32, getNullValue_uint64,
                         getNullValue_uint8, getNullValue_str)
from ._cy_raster import (sortColumns_d, sortColumns_f,
                         sortColumns_d_i, sortColumns_f_i,
                         sortColumns_d_byt, sortColumns_f_byt)
from ..vector import vector, _cy_vector
from ..runner import runner
from ..core import str2bytes
from ..utils import is_remote_uri, is_file_on_disk
from ..readers.rasterReaders import NC_Handler, GDAL_Handler, DataHandler
from ..readers.rasterReaders import XR_Handler, RIO_Handler
from ..readers import GRIB_Handler
from ..dataset.supported_libs import HAS_GDAL, HAS_NCDF, HAS_PYDAP, HAS_XARRAY # type: ignore
from ..dataset.supported_libs import HAS_RASTERIO, HAS_PYGRIB # type: ignore
from . import _base
from pathlib import PurePath

try:
    from functools import singledispatchmethod
except ImportError:
    def singledispatchmethod(func):
        """Reference: https://stackoverflow.com/a/24602374
        """
        dispatcher = singledispatch(func)
        def wrapper(*args, **kw):
            return dispatcher.dispatch(args[1].__class__)(*args, **kw)
        wrapper.register = dispatcher.register
        update_wrapper(wrapper, func)
        return wrapper

if HAS_PYDAP:
    from ..readers.ncutils import Pydap2NC

if HAS_GDAL:
    from osgeo import gdal

if HAS_RASTERIO:
    import rasterio as rio

if HAS_XARRAY:
    import xarray as xr

if HAS_NCDF:
    import netCDF4 as nc

if HAS_PYGRIB:
    import pygrib

__all__ = ["Raster", "equalSpatialMetrics", "RasterDimensions",
           "Dimensions", "TileDimensions", "TileSpecifications",
           "RasterFile", "RasterBaseList", "RasterPtrList",
           "getNullValue", "sortColumns", "RasterBase"]


def parse_slice(value):
    """
    Parses a `slice()` from string, like `start:stop:step`.

    reference: https://stackoverflow.com/a/54421070
    """
    if value:
        parts = value.split(':')
        if len(parts) == 1:
            # slice(stop)
            parts = [None, parts[0]]
        # else: slice(start, stop[, step])
    else:
        # slice()
        parts = []
    return slice(*[int(p) if p else None for p in parts])


def getNullValue(dtype: np.dtype) -> numbers.Real:
    """get the null value for a given data type.

    Parameters
    ----------
    dtype : np.dtype
        a numpy data type

    Returns
    -------
    numbers.Real
        internal null value for a given data type
    """
    out = np.nan
    if dtype in [np.float32, float]:
        out = getNullValue_flt()
    elif dtype in [np.float64, getattr(np, 'float_', 'float64')]:
        out = getNullValue_dbl()
    elif dtype == np.uint32:
        out = getNullValue_uint32()
    elif dtype == np.uint8:
        out = getNullValue_uint8()
    elif dtype == np.uint64:
        out = getNullValue_uint64()
    elif dtype in [np.int32, int]:
        out = getNullValue_int32()
    elif dtype in [np.int_, np.int64]:
        out = getNullValue_int64()
    elif dtype in [str, bytes]:
        out = getNullValue_str()
    return out


class TileDimensions:
    def __init__(self: "TileDimensions", dtype: np.dtype=core.REAL):
        self._dtype: np.dtype = None
        self._handle = None

    @classmethod
    def copy(cls, other: "TileDimensions") -> "TileDimensions":
        """copy a tile dimensions object into a new instance of `TileDimensions`.

        This method is used to copy a cython TileDimensions object into a python
        TileDimensions object.

        Parameters
        ----------
        other : TileDimensions,_TileDimensions_d,_TileDimensions_f
            an instance of TileDimensions to copy into a TileDimensions object

        Returns
        -------
        TileDimensions
            an instance of TileDimensions python object.

        Raises
        ------
        TypeError
            Input argument should be an instance of TileDimensions
        RuntimeError
            Input tile dimensions is not yet initialized
        """
        if not isinstance(other, (cls, _TileDimensions_d, _TileDimensions_f)):
            raise TypeError("Input argument should be an instance of TileDimensions")
        if isinstance(other, cls):
            if other._handle is not None:
                out = cls.copy(other._handle)
            else:
                raise RuntimeError("Input tile dimensions is not yet initialized")
        elif isinstance(other, _TileDimensions_d):
            out = cls(dtype=np.float64)
            out._handle = _TileDimensions_d.copy(other)
        elif isinstance(other, _TileDimensions_f):
            out = cls(dtype=np.float32)
            out._handle = _TileDimensions_f.copy(other)
        return out

    def to_dict(self) -> Dict:
        """return a tile dimensions object as a dictionary.

        Returns
        -------
        Dict
            a dictionary with the dimensions of a raster tile

        Raises
        ------
        RuntimeError
            `TileDimensions` is not yet initialized
        """
        if self._handle is not None:
            return self._handle.to_dict()
        else:
            raise RuntimeError("TileDimensions is not yet initialized")

    @property
    def grid(self) -> Tuple[np.ndarray]:
        if self.ny == 1:
            grid_x = np.arange(self.ox+0.5*self.hx,
                               self.ex+0.5*self.hx, self.hx)
            return grid_x
        elif self.ny > 1:
            grid_x = np.arange(self.ox+0.5*self.hx,
                               self.ex+0.5*self.hx, self.hx)
            grid_y = np.arange(self.oy+0.5*self.hy,
                               self.ey+0.5*self.hy, self.hy)
            return grid_x, grid_y
        elif self.nz > 1:
            grid_x = np.arange(self.ox+0.5*self.hx,
                               self.ex+0.5*self.hx, self.hx)
            grid_y = np.arange(self.oy+0.5*self.hy,
                               self.ey+0.5*self.hy, self.hy)
            grid_z = np.arange(self.oz+0.5*self.hz,
                               self.ez+0.5*self.hz, self.hz)
            return grid_x, grid_y, grid_z

    def __getattr__(self, other: str) -> numbers.Real:
        if self._handle is None:
            raise RuntimeError("TileDimensions is not yet initialized")
        if other in ['nx', 'ny', 'nz', 'hx', 'hy', 'hz', 'ox', 'oy',
                     'mx', 'my', 'ex', 'ey', 'ez']:
            return getattr(getattr(self, "_handle"), other)
        else:
            raise AttributeError("%s is not a recognized attribute" % other)

    def __str__(self) -> str:
        dim_dict = self.to_dict()
        dim_string = '\n'.join([f"    {item:6s}:  {dim_dict[item]}" for item in dim_dict])
        return dim_string

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__


class Dimensions:
    def __init__(self: "Dimensions", dtype: np.dtype=core.REAL):
        if dtype is not None:
            if dtype != core.REAL and dtype != np.float64:
                raise ValueError("dtype should be either np.float32 or np.float64")
        self._dtype: np.dtype = dtype
        self._handle = None

    @classmethod
    def copy(cls, other: "Dimensions") -> "Dimensions":
        if not isinstance(other, (cls, _Dimensions_d, _Dimensions_f)):
            raise TypeError("Input argument should be an instance of Dimensions")
        if isinstance(other, cls):
            if other._handle is not None:
                out = cls.copy(other._handle)
            else:
                raise RuntimeError("Input dimensions is not yet initialized")
        elif isinstance(other, _Dimensions_d):
            out = cls(dtype=np.float64)
            out._handle = _Dimensions_d.copy(other)
        elif isinstance(other, _Dimensions_f):
            out = cls(dtype=np.float32)
            out._handle = _Dimensions_f.copy(other)
        return out

    @classmethod
    def from_dict(cls, other: Dict, dtype: np.dtype=core.REAL) -> "Dimensions":
        """instantiate a Dimensions object from a dictionary

        Parameters
        ----------
        other : Dict
            a dictionary with parameters for instantiating Dimensions
        dtype : np.dtype, optional
            data type of Dimensions object, by default np.float32

        Returns
        -------
        Dimensions
            an instance of Dimensions object

        Raises
        ------
        TypeError
            Input argument should be a dictionary
        KeyError
            argument not present in the input dictionary
        """
        if not isinstance(other, (dict, OrderedDict)):
            raise TypeError("Input argument should be a dictionary")
        missing_args = ""
        for item in ['nx', 'ny', 'nz', 'hx', 'hy', 'hz', 'ox', 'oy', 'mx', 'my']:
            if item not in other:
                missing_args += "%s," % item
        if len(missing_args) > 0:
            raise KeyError("%s not present in the input dictionary" % missing_args[:-1])

        if dtype == np.float32:
            out = cls.copy(_Dimensions_f.from_dict(other))
        elif dtype == np.float64:
            out = cls.copy(_Dimensions_d.from_dict(other))
        return out

    def to_dict(self) -> Dict:
        if self._handle is not None:
            return self._handle.to_dict()
        else:
            raise RuntimeError("Dimensions is not yet initialized")

    @property
    def grid(self) -> Tuple[np.ndarray]:
        if self.ny == 1:
            grid_x = np.arange(self.ox+0.5*self.hx,
                               self.ex+0.5*self.hx, self.hx, dtype=self._dtype)
            return grid_x
        elif self.ny > 1:
            grid_x = np.arange(self.ox+0.5*self.hx, self.ex+0.5*self.hx,
                               self.hx, dtype=self._dtype)
            grid_y = np.arange(self.oy+0.5*self.hy, self.ey+0.5*self.hy,
                               self.hy, dtype=self._dtype)
            return grid_x, grid_y
        elif self.nz > 1:
            grid_x = np.arange(self.ox+0.5*self.hx, self.ex+0.5*self.hx,
                               self.hx, dtype=self._dtype)
            grid_y = np.arange(self.oy+0.5*self.hy, self.ey+0.5*self.hy,
                               self.hy, dtype=self._dtype)
            grid_z = np.arange(self.oz+0.5*self.hz, self.ez+0.5*self.hz,
                               self.hz, dtype=self._dtype)
            return grid_x, grid_y, grid_z

    def __eq__(self, other: "Dimensions") -> bool:
        assert isinstance(other, Dimensions)
        return self._handle == other._handle

    def __ne__(self, other: "Dimensions") -> bool:
        assert isinstance(other, Dimensions)
        return self._handle != other._handle

    def __getattr__(self, other: str) -> numbers.Real:
        if self._handle is None:
            raise RuntimeError("Dimensions is not yet initialized")
        if other in ['nx', 'ny', 'nz', 'hx', 'hy', 'hz', 'ox', 'oy', 'mx', 'my']:
            return getattr(getattr(self, "_handle"), other)
        else:
            raise AttributeError("%s is not a recognized attribute" % other)

    def __str__(self) -> str:
        dim_dict = self.to_dict()
        dim_string = '\n'.join([f"    {item:6s}:  {dim_dict[item]}" for item in dim_dict])
        return dim_string

    def __repr__(self):
        return "<class 'geostack.raster.%s'>\n%s" % (self.__class__.__name__, str(self))


class RasterDimensions:
    def __init__(self: "RasterDimensions", dtype: np.dtype=core.REAL):
        self._dtype: np.dtype = None
        self._handle = None
        if dtype is not None:
            if dtype in [np.float64, ctypes.c_double]:
                self._handle = _RasterDimensions_d()
                self._dtype = np.float64
            elif dtype in [float, np.float32, ctypes.c_float]:
                self._handle = _RasterDimensions_f()
                self._dtype = np.float32
            else:
                raise TypeError("dtype should be np.float32 or np.float64")

    @classmethod
    def copy(cls, other: "RasterDimensions") -> "RasterDimensions":
        if isinstance(other, (cls, _RasterDimensions_d,
                              _RasterDimensions_f)):
            if isinstance(other, cls):
                if other._handle is not None:
                    out = cls.copy(other._handle)
                else:
                    raise RuntimeError("Input instance of RasterDimensions is not initialized")
            else:
                out = cls(dtype=None)
                if isinstance(other, _RasterDimensions_d):
                    out._dtype = np.float64
                    out._handle = other
                elif isinstance(other, _RasterDimensions_f):
                    out._dtype = np.float32
                    out._handle = other
            return out
        else:
            raise TypeError("copy argument should be an instance of RasterDimensions")

    @classmethod
    def from_dict(cls, other: Dict, dtype: np.dtype = core.REAL) -> "RasterDimensions":
        if not isinstance(other, (dict, OrderedDict)):
            raise TypeError("Input argument should be a dictionary")
        missing_args = ""
        for item in ['dim', 'ex', 'ey', 'ez', 'tx', 'ty']:
            if item not in other:
                missing_args += f"{item},"
            if len(missing_args) > 0:
                raise KeyError(f"{missing_args[:-1]} not present in the input dictionary")

        if not isinstance(other['dim'], (dict, OrderedDict)):
            raise TypeError("value of 'dim' key in the input dictionary should be a dictionary")

        missing_args = ""
        for item in ['nx', 'ny', 'nz', 'hx', 'hy', 'hz', 'ox', 'oy', 'mx', 'my']:
            if item not in other['dim']:
                missing_args += f"{item},"
        if len(missing_args) > 0:
            raise KeyError(f"{missing_args[:-1]} not present in the 'dim' key in the input dictionary")

        out = cls(dtype=None)
        if dtype == np.float32:
            out._dtype = np.float32
            out._handle = _RasterDimensions_f(other)
        elif dtype == np.float64:
            out._dtype = np.float64
            out._handle = _RasterDimensions_d(other)
        return out

    def to_dict(self) -> Dict:
        if self._handle is not None:
            return self._handle.to_dict()
        else:
            raise RuntimeError("RasterDimensions is not yet initialized")

    @property
    def grid(self) -> Tuple[np.ndarray]:
        if self.ny == 1:
            grid_x = np.arange(self.ox, self.ex, self.hx)
            return grid_x
        elif self.ny > 1:
            grid_x = np.arange(self.ox, self.ex, self.hx)
            grid_y = np.arange(self.oy, self.ey, self.hy)
            return grid_x, grid_y
        elif self.nz > 1:
            grid_x = np.arange(self.ox, self.ex, self.hx)
            grid_y = np.arange(self.oy, self.ey, self.hy)
            grid_z = np.arange(self.oz, self.ez, self.hz)
            return grid_x, grid_y, grid_z

    def __getattr__(self, other: str) -> numbers.Real:
        if self._handle is None:
            raise RuntimeError("RasterDimensions is not yet initialized")
        if other in ['nx', 'ny', 'nz', 'hx', 'hy', 'hz', 'ox', 'oy', 'oz',
                     'mx', 'my', 'ex', 'ey', 'ez', 'tx', 'ty']:
            return getattr(getattr(self, "_handle"), other)
        else:
            raise AttributeError(f"{other} is not a recognized attribute")

    def __eq__(self, other: "RasterDimensions") -> bool:
        assert isinstance(other, RasterDimensions)
        return self._handle == other._handle

    def __ne__(self, other: "RasterDimensions") -> bool:
        assert isinstance(other, RasterDimensions)
        return self._handle != other._handle

    def __str__(self) -> str:
        raster_dims = self.to_dict()
        dim_dict = raster_dims.pop("dim")
        raster_string = "RasterDimensions:\n"
        raster_string += '\n'.join([f"    {item:6s}:  {raster_dims[item]}" for item in raster_dims])
        raster_string += "\n" + '\n'.join([f"    {item:6s}:  {dim_dict[item]}" for item in dim_dict])
        return raster_string

    def __repr__(self):
        return "<class 'geostack.raster.%s'>\n%s" % (self.__class__.__name__, str(self))


class RasterBase(_base._RasterBase):
    def __init__(self, other):
        self._handle = None

        if not isinstance(other, (_cyRasterBase_d, _cyRasterBase_f)):
            raise TypeError("object is not of valid type")

        if isinstance(other, _cyRasterBase_d):
            self._handle = other
            self._dtype = np.float64
        elif isinstance(other, _cyRasterBase_f):
            self._handle = other
            self._dtype = np.float32

        self.data_type = self.getDataTypeString()
        self.base_type = self._dtype

    def hasData(self) -> bool:
        """Check if raster object has data.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : bool
            Return true if raster object has data else false.
        """
        return self._handle.hasData()

    def getDataTypeString(self) -> np.dtype:
        """get raster datatype as string

        Returns
        -------
        numpy.dtype
            raster data type as numpy dtype object
        """
        assert self._handle is not None
        dtype = self._handle.getDataTypeString().replace("_t", "")
        if dtype == "float":
            dtype = f"{dtype}32"
        return np.dtype(dtype)

    def write(self, fileName: str,
              jsonConfig: Optional[Union[Dict, str]] = None) -> None:
        """Write raster data to a output file.

        Parameters
        ----------
        fileName : str
            Path of the file to write raster data.
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the output file.

        Returns
        -------
        Nil
        """
        if jsonConfig is None:
            _json_config = core.str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = core.str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = core.str2bytes(json.dumps(jsonConfig))

        self._handle.write(fileName, _json_config)

    @property
    def dtype(self) -> np.dtype:
        """get raster data type.

        Returns
        -------
        np.dtype
            raster data type as numpy datatype object
        """
        return self.getDataTypeString()

    def getDimensions(self) -> "RasterDimensions":
        """Get dimensions of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : RasterDimensions object
            Return dimensions of the raster object.
        """
        return self.getRasterDimensions()

    def getRasterDimensions(self) -> "RasterDimensions":
        """Get raster dimensions of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : RasterDimensions object
            An instance of RasterDimensions containing dimensions of the Raster object.
        """
        return RasterDimensions.copy(self._handle.getRasterDimensions())

    def getBounds(self) -> "vector.BoundingBox":
        """Get bounding box of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : BoundingBox object
            Return bounding box of the raster object.
        """
        return vector.BoundingBox.from_bbox(self._handle.getBounds())

    def setProjectionParameters(self, other: Union["core.ProjectionParameters", str]) -> None:
        """Set projection parameters for the raster.

        Parameters
        ----------
        other : ProjectionParameters | str
            An instance of projection parameters obtained from a wkt or proj4.

        Returns
        -------
        Nil
        """
        if isinstance(other, str):
            self._handle.setProjectionParameters_str(other)
        else:
            self._handle.setProjectionParameters(other._handle)

    def getProjectionParameters(self) -> "core.ProjectionParameters":
        """Get projection parameters from the raster.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : ProjectionParameters
            Returns Raster projection parameters as an instance of ProjectionParameters
        """
        out = core.ProjectionParameters.from_proj_param(
            self._handle.getProjectionParameters())
        return out

    @property
    def data(self) -> np.ndarray:
        """Get data from RasterBase.

        This is a convenience function to extract data from RasterBase
        by copying it to a Raster object using runScript.

        Returns
        -------
        np.ndarray
            raster data as ndarray
        """
        r_data = runner.runScript(f'output = {self.name}', [self])
        assert r_data.shape == self.shape
        return r_data.data

    @property
    def bounds(self):
        return self.getBounds()

    @property
    def dimensions(self) -> "RasterDimensions":
        return self.getDimensions()

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__


class Raster(_base._RasterBase):
    """Raster wrapper class for cython wrapper of c++ Raster class.
    """
    def __init__(self: "Raster", *args, **kwargs):

        if len(args) > 0:
            _inp_args = self._parse_args(args)
        if kwargs:
            _inp_args = self._parse_kwargs(kwargs)

        if not len(args) > 0 and not kwargs:
            _inp_args = ["", core.REAL, core.REAL]

        super().__init__(*_inp_args[1:])
        _name = _inp_args[0]

        if not core.is_valid_name(_name):
            raise ValueError(f"'{_name}' is not valid for a Raster")

        # create an object map
        obj_map = {
            (np.float32, np.float32): _cyRaster_f,
            (np.float32, np.uint32): _cyRaster_f_i,
            (np.float32, np.uint8): _cyRaster_f_byt,
            (np.float64, np.float64): _cyRaster_d,
            (np.float64, np.uint32): _cyRaster_d_i,
            (np.float64, np.uint8): _cyRaster_d_byt
        }

        # get and instantiate the cython object
        try:
            self._handle = obj_map[(self.base_type, self.data_type)](
                                   core.str2bytes(_name))
        except Exception as e:
            if isinstance(e, KeyError):
                raise RuntimeError(f"Combination of base_type: {self.base_type} and "+
                                   f"data_type: {self.data_type} is not valid")
            else:
                raise e

    def _parse_args(self, args):
        # set default values
        out = ["", core.REAL, core.REAL]

        if len(args) > 3:
            raise RuntimeError("Only three Parameters at most should be provided")
        for i, arg in enumerate(args, 0):
            if i == 0:
                if isinstance(arg, str):
                    out[i] = arg
                else:
                    raise ValueError("first argument, name of Raster should be string type")
            elif i == 1:
                if arg in [np.float64, ctypes.c_double]:
                    out[i] = np.float64
                elif arg != np.float32:
                    raise ValueError("Second argument, base type should be np.float32/np.float64")
            elif i == 2:
                if arg in [ctypes.c_double, np.float64]:
                    out[i] = np.float64
                elif arg in [np.uint32, np.int32, np.int]:
                    out[i] = np.uint32
                elif arg in [np.uint8]:
                    out[i] = arg
                elif arg != np.float32:
                    raise ValueError("Third argument, data type should be np.uint32/np.float32/np.float64")
            else:
                raise TypeError("Unable to understand provided argument")
        return out

    def _parse_kwargs(self, kwargs):
        # set default values
        out = ["", core.REAL, core.REAL]

        if len(kwargs) > 3:
            raise RuntimeError("Only three keyword Parameters at most should be provided")
        for arg in kwargs:
            if arg == "name":
                if isinstance(kwargs[arg], str):
                    out[0] = kwargs[arg]
                else:
                    raise TypeError("Incorrect type for 'name' keyword argument")
            elif arg == "base_type":
                if kwargs[arg] in [np.float64, ctypes.c_double]:
                    out[1] = np.float64
                elif kwargs[arg] != np.float32:
                    raise ValueError("base_type can be np.float32/np.float64")
            elif arg == "data_type":
                if kwargs[arg] in [ctypes.c_double, np.float64]:
                    out[2] = np.float64
                elif kwargs[arg] in [np.int32, np.uint32]:
                    out[2] = np.uint32
                elif kwargs[arg] in [np.uint8]:
                    out[2] = kwargs[arg]
                elif kwargs[arg] != np.float32:
                    ValueError("data_type can be of type np.float32, np.float64, np.uint32")
            else:
                raise TypeError("Unable to understand provided argument")
        return out

    @property
    def data(self) -> np.ndarray:
        return self.get_full_data()

    @data.setter
    def data(self, inpData: np.ndarray):
        self.set_full_data(inpData)

    def set_full_data(self, inpData: np.ndarray):
        # Check raster
        if not hasattr(self, "raster_dim"):
            self.raster_dim = self.getDimensions()

        if not isinstance(inpData, np.ndarray):
            raise TypeError("Input argument should be a numpy array")

        assert self._handle is not None, "Raster is not instantiated"

        # Check data
        if inpData.ndim > 3:
            raise NotImplementedError("Only handling of upto 3D arrays have been added")

        if inpData.shape != self.shape:
            raise ValueError("Shape mismatch between Raster dimensions and input data")

        # Set data
        numTiles: int = self.dimensions.tx * self.dimensions.ty
        for idx in range(numTiles):
            tj, ti = divmod(idx, self.dimensions.tx)
            idx_s, idx_e, jdx_s, jdx_e = self.get_tile_idx_bounds(idx)
            if self.ndim == _base.RasterKind.Raster1D:
                if np.ma.isMaskedArray(inpData):
                    self.readData(inpData[idx_s:idx_e].filled(
                        fill_value=self.nullValue).astype(self.data_type), ti=ti, tj=tj)
                else:
                    self.readData(inpData[idx_s:idx_e].astype(self.data_type), ti=ti, tj=tj)
            elif self.ndim == _base.RasterKind.Raster2D:
                if np.ma.isMaskedArray(inpData):
                    self.readData(inpData[jdx_s:jdx_e,idx_s:idx_e].filled(
                        fill_value=self.nullValue).astype(self.data_type),
                                  ti=ti, tj=tj)
                else:
                    self.readData(inpData[jdx_s:jdx_e,idx_s:idx_e].astype(self.data_type),
                                  ti=ti, tj=tj)
            elif self.ndim == _base.RasterKind.Raster3D:
                if np.ma.isMaskedArray(inpData):
                    self.readData(inpData[:, jdx_s:jdx_e,idx_s:idx_e].filled(
                        fill_value=self.nullValue).astype(self.data_type),
                                  ti=ti, tj=tj)
                else:
                    self.readData(inpData[:, jdx_s:jdx_e,idx_s:idx_e].astype(self.data_type),
                                  ti=ti, tj=tj)

    def __copy__(self):
        return Raster.copy(f"{self.name}_copy", self, deep=False)

    def __deepcopy__(self, memo):
        return self.deepcopy(f"{self.name}_copy")

    def deepcopy(self, name: str = "out") -> "Raster":
        """Return a deep copy of the raster object

        Parameters
        ----------
        name : str, optional
            name of the output raster, by default "out"

        Returns
        -------
        Raster
            A raster object after deep copy
        """
        return Raster.copy(name, self, deep=True)

    @classmethod
    def copy(cls, name: Optional[str], other: "Raster", deep: bool=False) -> "Raster":
        """Create a copy of raster from input raster.

        Parameters
        ----------
        name : str
            Name of the output raster.
        other : Raster
            Input raster to be used for copying.

        Returns
        -------
        out : Raster
            Output copy of raster object

        Examples
        --------
        >>> import numpy as np
        >>> testRasterA = Raster("testRasterA", np.float32)
        >>> testRasterA.init(nx = 5, ny = 5, hx = 1.0, hy = 1.0)
        >>> testRasterC = Raster.copy("testRasterC", testRasterA)
        """
        # get the name for the raster
        raster_name: str = name
        if raster_name is None:
            try:
                raster_name = other.name
            except AttributeError:
                if hasattr(other, 'getProperty_str'):
                    raster_name = other.getProperty_str('name')
                elif hasattr(other, 'getProperty'):
                    raster_name = other.getProperty('name')

        if deep:
            if raster_name is None:
                raise ValueError(f"`name` cannot be None, please specify a name for copy")
            out = Raster(name=raster_name,
                         base_type=other.base_type,
                         data_type=other.data_type)
            out.init_with_dims(other.dimensions)
            out.setProjectionParameters(other.getProjectionParameters())
            runner.runScript(f"{out.name} = {other.name};", [out, other],
                             output_type=other.data_type)
        else:
            if isinstance(other, cls):
                out = cls(name=raster_name)
                if out.base_type == np.float32:
                    if out.data_type == out.base_type:
                        out._handle = other._handle
                    else:
                        out._handle = other._handle
                elif out.base_type == np.float64:
                    if out.data_type == out.base_type:
                        out._handle = other._handle
                    else:
                        out._handle = other._handle
                out.name = raster_name
            else:
                # create an data_type mape map
                type_map = {
                    ("f",): dict(base_type=np.float32, data_type=np.float32),
                    ("f", "i"): dict(base_type=np.float32, data_type=np.uint32),
                    ("f", "byt"): dict(base_type=np.float32, data_type=np.uint8),
                    ("d",): dict(base_type=np.float64, data_type=np.float64),
                    ("d", "i"): dict(base_type=np.float64, data_type=np.uint32),
                    ("d", "byt"): dict(base_type=np.float64, data_type=np.uint8)
                }

                # get the base type and data type string, when they are different
                obj_parsed = re.search("_cyRaster_(?P<base_type>.*)_(?P<data_type>.*)",
                                       type(other).__name__)
                if obj_parsed is None:
                    # get the base type string when both base and data are of same type
                    obj_parsed = re.search("_cyRaster_(?P<base_type>.*)",
                                           type(other).__name__)
                if obj_parsed is None:
                    raise RuntimeError("Unable to get the base_type and data type")

                # get the data and base type for the object and instantiate it
                try:
                    out = cls(**type_map[obj_parsed.groups()])
                except Exception as e:
                    if isinstance(e, KeyError):
                        raise RuntimeError(f"object {other} is not valid")
                    else:
                        raise e
                out._handle = other
                out.name = raster_name
        return out

    def init_with_bbox(self: "Raster", bbox: "vector.BoundingBox", hx: numbers.Real,
                       hy: numbers.Real = 0.0, hz: numbers.Real = 0.0):
        """instantiate a Raster object from a BoundingBox object

        Parameters
        ----------
        bbox : vector.BoundingBox
            an instance of BoundingBox object
        hx : numbers.Real
            resolution in x-direction
        hy : numbers.Real, optional
            resolution in y-direction, by default 0.0
        hz : numbers.Real, optional
            resolution in z-direction, by default 0.0

        Raises
        ------
        TypeError
            resolution should be a real number
        TypeError
            input bounding box should be an instance of BoundingBox
        """
        if not isinstance(hx, numbers.Real):
            raise TypeError("resolution should be a real number")
        if not isinstance(bbox, (vector.BoundingBox,
                                 _cy_vector._BoundingBox_d,
                                 _cy_vector._BoundingBox_f)):
            raise TypeError("input bounding box should be an instance of BoundingBox")

        assert self._handle is not None, "Raster is not instantiated"

        if isinstance(bbox, vector.BoundingBox):
            assert self.base_type == bbox._dtype, "datatype mismatch"
            self._handle.init(bbox._handle, hx=hx, hy=hy, hz=hz)
        else:
            if isinstance(bbox, _cy_vector._BoundingBox_d):
                assert self.base_type == np.float64, "datatype mismatch"
            elif isinstance(bbox, _cy_vector._BoundingBox_f):
                assert self.base_type == np.float32, "datatype mismatch"
            self._handle.init(bbox, hx=hx, hy=hy, hz=hz)

    initWithBoundingBox = init_with_bbox

    def init_with_dims(self: "Raster", dims: "RasterDimensions"):
        """instantiate a Raster object with a given RasterDimensions object.

        Parameters
        ----------
        dims : RasterDimensions
            an instance of Raster dimensions object

        Raises
        ------
        TypeError
            input raster dimensions should be an instance of RasterDimensions
        """
        if not isinstance(dims, (RasterDimensions,
                                 _RasterDimensions_d,
                                 _RasterDimensions_f)):
            raise TypeError("input raster dimensions should be an instance of RasterDimensions")
        assert self._handle is not None, "Raster is not instantiated"
        if isinstance(dims, RasterDimensions):
            assert self.base_type == dims._dtype, "datatype mismatch"
            self._handle.init(dims._handle)
        else:
            if isinstance(dims, _RasterDimensions_d):
                assert self.base_type == np.float64, "datatype mismatch"
            elif isinstance(dims, _RasterDimensions_f):
                assert self.base_type == np.float32, "datatype mismatch"
            self._handle.init(dims)

    initWithDimensions = init_with_dims

    def init(self: "Raster", nx: numbers.Integral, hx: numbers.Real,
             ny: Optional[numbers.Integral] = None, nz: Optional[numbers.Integral] = None,
             hy: Optional[numbers.Real] = None, hz: Optional[numbers.Real] = None,
             ox: numbers.Real = 0.0, oy: numbers.Real = 0.0,
             oz: numbers.Real = 0.0, **kwargs):
        """initialize an instantiated Raster object.

        Parameters
        ----------
        nx : numbers.Integral
            raster size in x-direction
        hx : numbers.Real
            cell size in x-direction
        ny : Optional[numbers.Integral], optional
            raster size in y-direction, by default None
        nz : Optional[numbers.Integral], optional
            raster size in x-direction, by default None
        hy : Optional[numbers.Real], optional
            cell size in y-direction, by default None
        hz : Optional[numbers.Real], optional
            cell size in z-direction, by default None
        ox : numbers.Real, optional
            x-coordinate of origin, by default 0.0
        oy : numbers.Real, optional
            y-coordinate of origin, by default 0.0
        oz : numbers.Real, optional
            z-coordinate of origin, by default 0.0

        Raises
        ------
        AssertionError
            Raster is not instantiated
        ValueError
            for 2d array, hy cannot be None
        ValueError
            for 3d array, hy and hz cannot be None

        Examples
        --------
        >>> # for 1D raster
        >>> testA = Raster(name="testA")
        >>> testA.init(10, 1.0)

        >>> # for 2D raster
        >>> testA = Raster(name="testA")
        >>> testA.init(10.0, 1.0, ny=10, hy=1.0)

        >>> # for 3D raster
        >>> testA = Raster(name="testA")
        >>> testA.init(10.0, 1.0, ny=10, hy=1.0, nz=2, hz=1.0)
        """
        assert self._handle is not None, "Raster is not instantiated"
        if (ny is None or ny == 0) and (nz is None or nz == 0):
            self._handle.init1D(nx, hx, ox)
        elif ny > 0 and (nz is None or nz == 0):
            if hy is not None:
                self._handle.init2D(nx, ny, hx, hy, ox, oy)
            else:
                raise ValueError("for 2d array, hy cannot be None")
        elif ny > 0 and nz > 0:
            if hy is not None and hz is not None:
                self._handle.init3D(nx, ny, nz, hx, hy, hz, ox, oy, oz)
            else:
                raise ValueError("for 3d array, hy and hz cannot be None")

    @classmethod
    def init_with_raster(cls, name: str, other: "Raster",
                         dims: Union[List, Tuple] = ["x", "y", "z"],
                         data_type: Optional[np.dtype] = None,
                         **kwargs) -> "Raster":
        """create a Raster object from a source Raster object.

        This function can be useful in simplifying workflow creation, where
        a source `Raster` can be used to create a new `Raster` object. This method
        comes in handy as it can set the name, assign `data_type`, set the
        `RasterDimensions` and the `ProjectionParameters`. It can also be useful
        in creating a 2D `Raster` object with same horizontal grid, usually done when
        building spatial masks.

        Parameters
        ----------
        name : str
            name of the output Raster object
        other : Raster
            source Raster object
        dims : Union[List, Tuple], optional
            list of dimensions to use from source Raster object, by default ["x", "y", "z"]
        data_type: np.dtype, optional
            data type for the output Raster, by default None

        Returns
        -------
        Raster
            an output Raster object with specified dimensionality

        Examples
        --------
        >>> # create Projection Parameters object
        >>> epsg_4326 = ProjectionParameters.from_proj4("+proj=longlat +datum=WGS84 +no_defs")

        >>> # create source Raster
        >>> testA = Raster(name="testA")
        >>> testA.init(nx=10, hx=1.0, ny=10, hy=1.0, nz=10, hz=1.0)
        >>> testA.setProjectionParameters(epsg_4326)

        >>> # create a 2D raster with uint32 datatype
        >>> testB = Raster.init_with_raster(name="testB", other=testA,
                                            dims=['x', 'y'],
                                            data_type=np.uint32)

        >>> # create a 2D raster
        >>> testB = Raster.init_with_raster(name="testB", other=testA,
                                            dims=['x', 'y'])

        >>> # create a 3D raster with user-defined number of levels
        >>> testC = Raster.init_with_raster(name="testC", other=testA,
                                            dims=['x', 'y', 'z'], nz=5)
        """
        dim_kwargs = {"x": ["nx", "hx", "ox"],
                      "y": ["ny", "hy", "oy"],
                      "z": ["nz", "hz", "oz"]}

        if data_type is None:
            data_type = other.data_type

        out = cls(name=name, base_type=other.base_type,
                  data_type=data_type)
        source_dims = other.dimensions

        raster_dims = {}

        for dim in dims:
            for arg in dim_kwargs[dim]:
                raster_dims[arg] = kwargs.get(arg, getattr(source_dims, arg))

        out.init(**raster_dims)
        out.setProjectionParameters(other.getProjectionParameters())
        return out

    def setCellValue(self, c: numbers.Real, i: numbers.Integral,
                     j: numbers.Integral = 0, k: numbers.Integral = 0):
        """Set a value to a cell in the raster object.

        Parameters
        ----------
        c : int/float
            The value to be assigned to a the cells in the raster object.
        i : int
            Cell index along x-axis
        j : int (optional)
            Cell index along y-axis.
        k : int (optional)
            Cell index along z-axis

        Returns
        -------
        Nil
        """
        assert self._handle is not None, "Raster is not instantiated"
        if isinstance(c, numbers.Real):
            return self._handle.setCellValue(c, i, j=j, k=k)
        else:
            raise TypeError("%s is not supported" % type(c).__name__)

    def setAllCellValues(self, c: numbers.Real):
        """Set a constant value for all the cells in the raster object.

        Parameters
        ----------
        c : int/float
            A constant value to be assigned to all the cells in the raster object.

        Returns
        -------
        Nil
        """
        assert self._handle is not None, "Raster is not instantiated"
        if isinstance(c, numbers.Real):
            return self._handle.setAllCellValues(c)
        else:
            raise TypeError("%s is not supported" % type(c).__name__)

    def __pad_data_array(self, inparray: np.ndarray,
                         nz: Optional[numbers.Integral] = None) -> np.ndarray:

        # Check data
        assert self._handle is not None, "Raster is not instantiated"

        # Pad data
        nx = ny = TileSpecifications().tileSize
        if self.ndim == _base.RasterKind.Raster1D:
            _buf = np.full((nx,), self.nullValue,)
            _buf[:inparray.size] = inparray[:]
            _buf = _buf.reshape((nx,))
        elif self.ndim == _base.RasterKind.Raster2D:
            _buf = np.full((ny, nx,), self.nullValue)
            inp_ny, inp_nx = inparray.shape
            _buf[:inp_ny, :inp_nx] = inparray
        elif self.ndim == _base.RasterKind.Raster3D:
            if nz is None:
                raise ValueError("nz should not be None for 3D array")
            _buf = np.full((nz, ny, nx,), self.nullValue)
            inp_nz, inp_ny, inp_nx = inparray.shape
            _buf[:inp_nz, :inp_ny, :inp_nx] = inparray

        return _buf.astype(self.data_type)

    def readData(self, inp, ti: numbers.Integral = 0, tj: numbers.Integral = 0):
        """Set tile data for the raster object.

        Parameters
        ---------
        ti : int
            Tile index in x-direction.
        tj : int
            Tile index in y-direction.

        Returns
        ------
        Nil

        Examples
        --------
        >>> import numpy as np
        >>> testRasterA = Raster(name="testRasterA", base_type=np.float32,
        ... data_type=np.float32)
        >>> testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> testRasterA.readData(np.arange(25).reshape((5,5)), ti=0, tj=0)
        """
        if isinstance(inp, np.ndarray):
            # Check data
            assert inp.dtype == self.data_type, "datatype mismatch"
            assert self._handle is not None, "Raster is not instantiated"

            # Set data
            assert inp.ndim <= 3, "Up to three dimensions are currently supported"
            if inp.ndim == 1:
                assert self.ndim == _base.RasterKind.Raster1D, "Raster object is not 1D"
                _buf = self.__pad_data_array(inp)
                self._handle.set1D(_buf, ti=ti, tj=tj)
            elif inp.ndim == 2:
                assert self.ndim == _base.RasterKind.Raster2D, "Raster object is not 2D"
                _buf = self.__pad_data_array(inp)
                self._handle.set2D(_buf, ti=ti, tj=tj)
            elif inp.ndim == 3:
                assert self.ndim == _base.RasterKind.Raster3D, "Raster object is not 3D"
                _buf = self.__pad_data_array(inp, nz=self.dimensions.nz)
                self._handle.set3D(_buf, ti=ti, tj=tj)
        else:
            raise TypeError("input can only be numpy array")

    def writeData(self, ti: numbers.Integral = 0,
                  tj: numbers.Integral = 0) -> np.ndarray:
        """Get tile data from the raster object.

        Parameters
        ----------
        ti : int
            Tile index in x-direction.
        tj : int
            Tile index in y-direction.

        Returns
        -------
        out : np.ndarray
            Tile data from the Raster object.

        Examples
        --------
        >>> import numpy as np
        >>> testRasterA = Raster(name="testRasterA", base_type=np.float32,
        ... data_type=np.float32)
        >>> testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> testRasterA.setAllCellValues(2.0)
        >>> testRasterA.writeData()
        """
        assert self._handle is not None, "Raster is not instantiated"
        num_tiles = self.dimensions.tx * self.dimensions.ty
        if ti < 0 or tj < 0:
            raise ValueError("Tile index should be a positive whole number")
        tile_idx = ti + self.dimensions.tx * tj
        if tile_idx >= num_tiles:
            raise ValueError("Requested tile is out of bounds")
        return self._handle.getData(ti, tj)

    def read(self, fileName: str, jsonConfig: Union[Dict, str]=None):
        """Read a file into the raster object.

        Parameters
        ----------
        fileName : str
            Path of the file to be read into the Raster object.
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the input file.

        Returns
        -------
        Nil
        """
        if jsonConfig is None:
            _json_config = core.str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = core.str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = core.str2bytes(json.dumps(jsonConfig))

        if not pth.exists(fileName):
            raise FileNotFoundError("file %s doesnt exist, check path" % fileName)

        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        if isinstance(fileName, (str, bytes)):
            self._handle.read(core.str2bytes(fileName), _json_config)

        raster_out = Raster.copy(self.name, self)
        self._handle = raster_out._handle
        self.data_type = raster_out.data_type
        self.base_type = raster_out.base_type

    @staticmethod
    def zeros_like(name: str, other: 'Raster') -> 'Raster':
        """create a Raster filled with zeros

        Parameters
        ----------
        name : str
            name of the output raster
        other : Raster
            source Raster used to create a zero Raster

        Returns
        -------
        Raster
            output raster with zeros
        """
        out = Raster.full_like(name=name, fill_value=0, other=other)
        return out

    @staticmethod
    def empty_like(name: str, other: 'Raster') -> 'Raster':
        """create an empty raster from a source Raster

        Parameters
        ----------
        name : str
            name of the output Raster
        other : Raster
            source Raster used to create an empty Raster

        Returns
        -------
        Raster
            output raster filled with noData
        """
        out = Raster(name=name, data_type=other.data_type,
                     base_type=other.base_type)
        out.init_with_dims(other.dimensions)
        out.setProjectionParameters(other.getProjectionParameters())
        return out

    @staticmethod
    def full_like(name: str, fill_value: numbers.Real,
                  other: 'Raster') -> 'Raster':
        """create an filled raster with a `fill_value` from a source Raster

        Parameters
        ----------
        name : str
            name of the output Raster
        fill_value: numbers.Real
            value used to fill Raster
        other : Raster
            source Raster used to create an empty Raster

        Returns
        -------
        Raster
            output raster filled with `fill_value`
        """
        out = Raster.empty_like(name=name, other=other)
        out.setAllCellValues(fill_value)
        return out

    @property
    def bounds(self):
        return self.getBounds()

    @property
    def dimensions(self) -> "RasterDimensions":
        return self.getDimensions()

    @property
    def reduceVal(self) -> Union[float, int]:
        return self._handle.reduceVal()

    def deleteRasterData(self):
        self._handle.deleteRasterData()

    def get_raster_base(self):
        out = RasterBase(self._handle.get_raster_base())
        return out

    def __setitem__(self, prop: Union[slice, Tuple],
                    value: Union[int, float, np.ndarray]):

        def handle_none(s, r): return r if s is None or s == -1 else s

        def nearest_offset(inp, x): return ((inp // x) + 1) * x

        if isinstance(prop, (slice, int)):
            prop = [prop,]

        if all(map(lambda item: not isinstance(item, slice), prop)):
            self.setCellValue(value, *prop)
        elif any(map(lambda s: s is Ellipsis, prop)):
            raise NotImplementedError("Unable to handle ellipsis")
        else:
            # remove the z-tile index from the slice
            tile_idx = self._slice_to_tiles(prop)
            if self.ndim == len(prop) == 3:
                zdim_offset = self.ndim - 3
                z_slice = prop[zdim_offset]
            if len(tile_idx) == 3:
                tile_idx = tile_idx[-2:]

            data_size = {(0, 0): {"x_size": 0, "y_size": 0}}

            for tile_idx_tpl in product(*tile_idx):
                if self.ndim > 1:
                    (ti, tj) = tile_idx_tpl
                    idx = tj + ti * self.dimensions.tx
                    idx_s, idx_e, jdx_s, jdx_e = self.get_tile_idx_bounds(idx)
                else:
                    (ti,) = tile_idx_tpl
                    idx = ti
                    idx_s, idx_e, _, _ = self.get_tile_idx_bounds(idx)

                num_tiles = self.dimensions.tx * self.dimensions.ty
                if idx > num_tiles or idx < 0:
                    raise ValueError("Request tile number of out of bounds")

                tj, ti = divmod(idx, self.dimensions.tx)

                # for 1D raster, force tj to 0
                if self.ndim == 1:
                    tj = 0

                # get tile data
                tile_data = self.get_tile(idx)

                # parse input slice
                if self.ndim >= 1:
                    xdim_offset = self.ndim - 1
                    if isinstance(prop[xdim_offset], slice):
                        x_slice = slice(
                            min(max(handle_none(prop[xdim_offset].start, idx_s), idx_s), idx_e),
                            min(handle_none(prop[xdim_offset].stop, idx_e), idx_e),
                            handle_none(prop[xdim_offset].step, 1)
                        )

                        # remove idx offset (use tile index)
                        x_slice = slice(x_slice.start - (idx_s * ti),
                                        x_slice.stop - (idx_s * ti),
                                        x_slice.step)

                        # get the size of the array to be copied
                        x_size = ceil((x_slice.stop - x_slice.start) / x_slice.step)

                        if ti > 0 and x_slice.step > 1:
                            # for strides greater than 1, need to offset to a closest number
                            # use tile x-index to get correct starting point
                            start_offset = nearest_offset((idx_s * ti), x_slice.step) - (idx_s * ti)
                            x_slice = slice(start_offset, x_slice.stop, x_slice.step)
                    else:
                        x_slice = prop[xdim_offset]
                        x_size = 1
                if self.ndim >= 2:
                    ydim_offset = self.ndim - 2
                    if isinstance(prop[ydim_offset], slice):
                        y_slice = slice(
                            min(max(handle_none(prop[ydim_offset].start, jdx_s), jdx_s), jdx_e),
                            min(handle_none(prop[ydim_offset].stop, jdx_e), jdx_e),
                            handle_none(prop[ydim_offset].step, 1)
                        )
                        # remove idx offset
                        y_slice = slice(y_slice.start - (jdx_s * tj),
                                        y_slice.stop - (jdx_s * tj),
                                        y_slice.step)
                        # get the size of the array to be copied
                        y_size = ceil((y_slice.stop - y_slice.start) / y_slice.step)
                        if tj > 0 and y_slice.step > 1:
                            # for strides greater than 1, need to offset to a closest number
                            start_offset = nearest_offset((jdx_s * tj), y_slice.step) - (jdx_s * tj)
                            y_slice = slice(start_offset, y_slice.stop, y_slice.step)
                    else:
                        y_slice = prop[ydim_offset]
                        y_size = 1

                # update tile data
                if self.ndim == 1:
                    x_offset = sum([data_size[(_ti, 0)]['x_size']
                                    for _ti in range(ti-1, -1, -1)
                                    if (_ti, 0) in data_size])
                    tile_data[x_slice] = value[x_offset : x_offset + x_size]
                    # add the x-size of data copied to the data_size
                    data_size[(ti, tj)] = {"x_size": x_size, "y_size": 0}
                elif self.ndim == 2:
                    # compute the offset in x-direction
                    x_offset = sum([data_size[(_ti, 0)]['x_size']
                                    for _ti in range(ti-1, -1, -1)
                                    if (_ti, 0) in data_size])
                    # compute the offset in y-direction
                    y_offset = sum([data_size[(0, _tj)]['y_size']
                                    for _tj in range(tj-1, -1, -1)
                                    if (0, _tj) in data_size])

                    if x_size == 1:
                        _value = value[y_offset : y_offset + y_size]
                    elif y_size == 1:
                        _value = value[x_offset : x_offset + x_size]
                    else:
                        _value = value[y_offset : y_offset + y_size,
                                       x_offset : x_offset + x_size]

                    tile_data[y_slice, x_slice] = _value
                    # add the x-size and y-size of data copied to the data_size
                    data_size[(ti, tj)] = {"x_size": x_size, "y_size": y_size}

                elif self.ndim == 3:
                    # compute the offset in x-direction
                    x_offset = sum([data_size[(_ti, 0)]['x_size']
                                    for _ti in range(ti-1, -1, -1)
                                    if (_ti, 0) in data_size])
                    # compute the offset in y-direction
                    y_offset = sum([data_size[(0, _tj)]['y_size']
                                    for _tj in range(tj-1, -1, -1)
                                    if (0, _tj) in data_size])

                    if x_size == 1:
                        _value = value[:, y_offset : y_offset + y_size]
                    elif y_size == 1:
                        _value = value[:, x_offset : x_offset + x_size]
                    else:
                        _value = value[:, y_offset : y_offset + y_size,
                                       x_offset : x_offset + x_size]


                    tile_data[z_slice, y_slice, x_slice] = _value
                    # add the x-size and y-size of data copied to the data_size
                    data_size[(ti, tj)] = {"x_size": x_size, "y_size": y_size}

                #set tile data
                if self.ndim == 1:
                    self._handle.set1D(tile_data, ti=ti, tj=tj)
                elif self.ndim == 2:
                    self._handle.set2D(tile_data, ti=ti, tj=tj)
                elif self.ndim == 3:
                    self._handle.set3D(tile_data, ti=ti, tj=tj)

    def __setstate__(self, ds: Dict) -> None:
        # instantiate raster
        self.__init__(data_type = ds.get("data_type"),
                      base_type = ds.get("base_type"))

        # initialise with dimensions
        self.init(**ds['dimensions']['dim'])

        # set properties
        for prop in ds['properties']:
            self.setProperty(prop, ds['properties'].get(prop))

        # set variables
        if 'variables' in ds:
            for var in ds['variables']:
                self.setVariableData(var, ds["variables"].get(var))

        # proj params
        proj_params = core.ProjectionParameters.from_dict(ds['projection_params'])
        self.setProjectionParameters(proj_params)

        # set raster data
        self.data = ds['data']

    def __getstate__(self) -> Dict:
        output = {
            "data_type": self.data_type,
            "base_type": self.base_type,
            "dimensions": self.getDimensions().to_dict(),
            "properties": dict(map(lambda item: (item,self.getProperty(item)),
                                   self.getPropertyNames()))
        }

        # extract variables
        if self.hasVariables():
            output['variables'] = {}
            for item in self.getVariableNames():
                output[item] = self.getVariableData(item)

        # extract projection parameters
        output['projection_params'] = self.getProjectionParameters().to_dict()

        # extract raster data
        output['data'] = self.data

        return output

    def __repr__(self):
        return "<class 'geostack.raster.%s'>\n%s" % (self.__class__.__name__, str(self))


class RasterPtrList(_base._Raster_list):
    """A container analogous to python list object.

    RasterPtrList object is a list of shared pointers of a number of Raster objects.
    The RasterPtrList object is used internally by the geostack c++ library to
    hold shared ptr to a number of rasters in a c++ vector.
    """
    def __init__(self: "RasterPtrList", *args, dtype: np.dtype=core.REAL):
        if dtype is not None:
            if dtype in [np.float64, ctypes.c_double]:
                super().__init__(np.float64, handle=_RasterPtrList_d())
            elif dtype in [float, np.float32, ctypes.c_float]:
                super().__init__(np.float32, handle=_RasterPtrList_f())
            else:
                raise TypeError("dtype should be np.float32 or np.float64")
        if args:
            if dtype is None:
                raise ValueError("dtype must be given when instantiating from iterable")
            if len(args) > 1:
                raise ValueError("Only one argument should be provided")
            if not isinstance(args[0], (list, tuple)):
                raise ValueError("Input argument should be a list or tuple")
            else:
                self._from_iterable(args[0])

    @singledispatchmethod
    def from_object(self, arg: "RasterPtrList"):
        raise NotImplementedError(f"Cannot cast {type(arg)} into RasterPtrList")

    @from_object.register(tuple)
    def _(self, arg: Tuple[Union['Raster', 'RasterFile']]) -> None:
        """Instantiate RasterPtrList from tuple of Raster/ RasterFile.

        Parameters
        ----------
        arg : tuple
            A tuple of Raster or RasterFile object.

        Returns
        -------
        Nil
        """
        self._from_tuple(arg)

    @from_object.register(list)
    def _(self, arg: List[Union['Raster', 'RasterFile']]) -> None:
        """Instantiate RasterPtrList from list of Raster/ RasterFile.

        Parameters
        ----------
        arg : List[Union[Raster, RasterFile]]
            A list of Raster or RasterFile objects.

        Returns
        -------
        Nil
        """
        self._from_list(arg)

    @property
    def size(self: "RasterPtrList") -> numbers.Integral:
        """Get size of the RasterPtrList.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : int
            Length of the RasterPtrList.
        """
        return self._size

    def append(self: "RasterPtrList", arg: Union['Raster', 'RasterFile']) -> None:
        """Append a Raster/RasterFile object to RasterPtrList.

        Parameters
        ----------
        arg : Raster/ RasterFile object.
            A Raster/ RasterFile object to append to RasterPtrList.

        Returns
        -------
        Nil
        """
        self._append(arg)

    def add_data_handler(self: "RasterPtrList", arg: 'RasterFile') -> None:
        """Add a RasterFile object to the RasterPtrList.

        Parameters
        ----------
        arg : RasterFile object
            A RasterFile object to be added to RasterPtrList.

        Returns
        -------
        Nil
        """
        self._add_data_handler(arg)

    def add_raster(self: "RasterPtrList", arg: 'Raster') -> None:
        """Add a Raster object to the RasterPtrList.

        Parameters
        ----------
        arg : Raster object
            A Raster object to be added to RasterPtrList.

        Returns
        -------
        Nil
        """
        self._add_raster(arg)

    def get_raster(self, index: int = 0) -> 'RasterBase':
        if index < 0 or index > self.size:
            raise IndexError("Index is not valid")
        out = RasterBase(self._handle.get_raster_from_vec(index))
        return out

    def __getitem__(self, other: int):
        if isinstance(other, numbers.Integral):
            return self.get_raster(other)
        else:
            raise TypeError("input argument should an integer")

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__


class RasterBaseList(_base._Raster_list):
    """A container analogous to python list object.

    RasterBaseList object is a list of reference wrapper around a Raster object.
    The RasterBaseList object is used internally by the geostack c++ library to
    hold references to a number of raster in a c++ vector.
    """
    def __init__(self: "RasterBaseList", *args, dtype: np.dtype=core.REAL):
        if dtype is not None:
            if dtype in [np.float64, ctypes.c_double]:
                super().__init__(np.float64, handle=_RasterBaseList_d())
            elif dtype in [float, np.float32, ctypes.c_float]:
                super().__init__(np.float32, handle=_RasterBaseList_f())
            else:
                raise TypeError("dtype should be np.float32 or np.float64")
        if args:
            if dtype is None:
                raise ValueError("dtype must be given when instantiating from iterable")
            if len(args) > 1:
                raise ValueError("Only one argument should be provided")
            if not isinstance(args[0], (list, tuple)):
                raise ValueError("Input argument should be a list or tuple")
            else:
                self._from_iterable(args[0])

    @singledispatchmethod
    def from_object(self, arg) -> None:
        raise NotImplementedError(f"Cannot cast {type(arg)} into RasterBaseList")

    @from_object.register(tuple)
    def _(self, arg: Tuple) -> None:
        """Instantiate RasterBaseList from tuple of Raster/ RasterFile.

        Parameters
        ---------
        arg : tuple
            A tuple of Raster or RasterFile object.

        Returns
        -------
        Nil
        """
        self._from_tuple(arg)

    @from_object.register(list)
    def _(self, arg: List) -> None:
        """Instantiate RasterBaseList from list of Raster/ RasterFile.

        Parameters
        ---------
        arg : list
            A list of Raster or RasterFile objects.

        Returns
        -------
        Nil
        """
        self._from_list(arg)

    @property
    def size(self) -> numbers.Integral:
        """Get size of the RasterBaseList.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : int
            Length of the RasterBaseList.
        """
        return self._size

    def append(self: "RasterBaseList", args: Union['Raster', 'RasterFile', 'RasterBase']) -> None:
        """Append a Raster/RasterFile object to RasterBaseList.

        Parameters
        ---------
        arg1 : Raster/ RasterFile object.
            A Raster/ RasterFile object to append to RasterBaseList.

        Returns
        -------
        Nil
        """
        self._append(args)

    def add_data_handler(self: "RasterBaseList", args: "RasterFile") -> None:
        """Add a RasterFile object to the RasterBaseList.

        Parameters
        ---------
        arg1 : RasterFile object
            A RasterFile object to be added to RasterBaseList.

        Returns
        -------
        Nil
        """
        self._add_data_handler(args)

    def add_raster(self: "RasterBaseList", args: "Raster") -> None:
        """Add a Raster object to the RasterbaseList.

        Parameters
        ----------
        arg1 : Raster object
            A Raster object to be added to RasterBaseList.

        Returns
        -------
        Nil
        """
        self._add_raster(args)

    def get_raster(self, index: int = 0) -> 'RasterBase':
        if index < 0 or index > self.size:
            raise IndexError("Index is not valid")
        out = RasterBase(self._handle.get_raster_from_vec(index))
        return out

    def __getitem__(self, other: int):
        if isinstance(other, numbers.Integral):
            self.get_raster(other)
        else:
            raise TypeError("input argument should an integer")

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__


class RasterFile(_base._RasterBase):
    """Data file reader with file input through Python libraries.

    Parameters
    ----------
    base_type : numpy.dtype
        base type for Raster object
    data_type : numpy.dtype
        data type for Raster object
    variable_map : Union[dict, str], Optional
        a dictionary with raster name to variable mapping or name of variable in the data file
    name : str, Optional
        name of the raster
    file_handler : DataHandler object
        User defined file reader/ writer object e.g. NC_Handler, GDAL_Handler
    file_path : Union[str, gdal.Dataset, nc.Dataset]
        Path of the file to be read or an instance of opened file using IO libraries.

    Attributes
    ----------
    base_type : numpy.dtype
        base type used for the Raster object
    data_type : numpy.dtype
        data type used for the Raster object
    _handle : _DataFileHandler_f/ _DataFileHandler_d object
        An instance of the RasterFile cython object

    Methods
    -------
    getTime()
        Get time based on current time index in the input file.
    getTimeIndex(time_idx)
        Get current time index in the input file.
    getTimeFromIndex(time_idx)
        Get time in the input file based on index.
    getIndexFromTime(time)
        Get index in the input file based on time.
    setTimeIndex(time_idx)
        Update time or raster band index in the input file.
    read(thredds=bool)
        Read file and initialised raster using dimensions from the input file.
    write(fileName, jsonConfig)
        Write file to path 'fileName' and set configuration given in 'jsonConfig'.
    setFileInputHandler()
        Set file input handler in the raster object.
    setFileOutputHandler()
        Set file output handler in the raster object.
    getProperty(prop)
        Get the value of property 'prop' from the raster object.
    hasProperty(prop)
        Check whether property 'prop' is defined for the raster object.
    setProperty(prop, propValue, propType=(str/float,int))
        Set a value of property 'prop' to a value 'propValue' and data type 'propType'.
    getRasterDimensions()
        Get dimensions for the raster object.
    getData(ti, tj, tidx)
        Get raster data for tile index (ti, tj) and time index 'tidx'. Here time index is the third
        dimension like raster band, vertical levels, time.

    Examples
    --------
    >>> filepath = "http://dapds00.nci.org.au/thredds/dodsC/zv2/agcd/v1/tmax/mean/r005/01month/agcd_v1_tmax_mean_r005_monthly_2020.nc"

    >>> # Using 'name' as variable identifier
    >>> obj = RasterFile(name="tmax", filePath=filepath, backend='netcdf')
    >>> obj.read(thredds=True)
    >>> obj.shape
    (691, 886)

    >>> # Specify variable name using 'variable_map'
    >>> obj = RasterFile(name="tasmax", variable_map="tmax", filePath=filepath, backend='netcdf')
    >>> obj.read(thredds=True)
    >>> obj.shape
    (691, 886)

    >>> # Specify a dictionary to map variable to raster using 'variable_map'
    >>> obj = RasterFile(name="tasmax", variable_map={"tasmax":"tmax"}, filePath=filepath, backend='netcdf')
    >>> obj.read(thredds=True)
    >>> obj.shape
    (6691, 886)

    >>> # Specify a dictionary to map variable to raster using 'variable_map'
    >>> obj = RasterFile(variable_map={"tasmax":"tmax"}, filePath=filepath, backend='netcdf')
    >>> obj.read(thredds=True)
    >>> obj.shape
    (6691, 886)
    """
    def __init__(self: "RasterFile", filePath: str=None, backend: str=None,
                 file_handler=None, base_type: np.dtype=core.REAL,
                 data_type: np.dtype=core.REAL, name: str=None, **kwargs):

        if name is None:
            _var_name = str2bytes('')
        else:
            _var_name = str2bytes(name)

        _supported_backends = {'xarray': XR_Handler,
                               "netcdf": NC_Handler,
                               "rasterio": RIO_Handler,
                               "gdal": GDAL_Handler,
                               "grib": GRIB_Handler}

        if file_handler is None and backend is None:
            raise ValueError("value of file_handler and backend cannot be None")
        if file_handler is not None and backend is not None:
            raise ValueError("Only file_handler or backend should be specified")

        if backend is not None:
            if isinstance(backend, str):
                if backend in _supported_backends:
                    _file_handler = _supported_backends[backend]
                else:
                    raise ValueError(f"{backend} is not recognised")
            else:
                raise TypeError("Value of backend should be of string type")
        elif file_handler is not None:
            _file_handler = file_handler

        if not issubclass(_file_handler, DataHandler):
            raise TypeError("file_handler should be an instance of DataHandler")

        if filePath is None:
            file_path = ''
        else:
            if isinstance(filePath, PurePath):
                filePath = str(filePath)
            file_path = filePath

        # keyword argument for instantiating data file handler
        self.obj_kwargs = {}

        if issubclass(_file_handler, GDAL_Handler) and HAS_GDAL:
            if not isinstance(file_path, gdal.Dataset):
                if not isinstance(file_path, str):
                    raise TypeError("file_path should be a string")
        elif issubclass(_file_handler, GRIB_Handler) and HAS_PYGRIB:
            if 'variable_map' not in kwargs:
                if 'grib_mapper' in kwargs:
                    warnings.warn("grib_mapper is deprecated, use variable_map", DeprecationWarning)
                else:
                    raise ValueError("variable map required for grib backend")
            # process keyword argument for grib backend
            for item in kwargs:
                if item in ["user", "passwd", "acct"]:
                    self.obj_kwargs[item] = kwargs.get(item)
            self.obj_kwargs['variable_map'] = kwargs.get("variable_map",
                                                    kwargs.get("grib_mapper"))
            if not isinstance(file_path, pygrib.open):
                if not isinstance(file_path, str):
                    raise TypeError("file_path should be a string")
        elif issubclass(_file_handler, RIO_Handler) and HAS_RASTERIO:
            if not isinstance(file_path, rio.DatasetReader):
                if not isinstance(file_path, (str, list)):
                    raise TypeError("file_path should be a string")
        elif issubclass(_file_handler, XR_Handler) and HAS_XARRAY:
            if 'variable_map' not in kwargs:
                warnings.warn("variable_map should be specified")
            self.obj_kwargs["variable_map"] = kwargs.get("variable_map",
                                            {f"{_var_name.decode()}":_var_name.decode()})
            if self.obj_kwargs["variable_map"] is None:
                self.obj_kwargs["variable_map"] = {f"{_var_name.decode()}":_var_name.decode()}
            if isinstance(self.obj_kwargs["variable_map"], str):
                self.obj_kwargs["variable_map"] = {f"{_var_name.decode()}":self.obj_kwargs["variable_map"]}
            if not isinstance(file_path, (xr.Dataset, xr.DataArray)):
                if not isinstance(file_path, (str, list)):
                    raise TypeError("file_path should be a string or list of string")
        elif issubclass(_file_handler, NC_Handler) and HAS_NCDF:
            if 'variable_map' not in kwargs:
                warnings.warn("variable_map should be specified")
            self.obj_kwargs["variable_map"] = kwargs.get("variable_map",
                                            {f"{_var_name.decode()}":_var_name.decode()})
            if self.obj_kwargs["variable_map"] is None:
                self.obj_kwargs["variable_map"] = {f"{_var_name.decode()}":_var_name.decode()}
            if isinstance(self.obj_kwargs["variable_map"], str):
                self.obj_kwargs["variable_map"] = {f"{_var_name.decode()}":self.obj_kwargs["variable_map"]}
            if not isinstance(file_path, (nc.Dataset, nc.MFDataset)):
                if HAS_PYDAP:
                    if not isinstance(file_path, Pydap2NC):
                        if not isinstance(file_path, (str, list)):
                            raise TypeError("file_path should be a string")
                else:
                    if not isinstance(file_path, (str, list)):
                        raise TypeError("file_path should be a string or list of string")
        else:
            if not isinstance(file_path, str):
                raise TypeError("file_path should be a string")

        if isinstance(filePath, str):
            if not len(filePath) > 0:
                raise ValueError(f"file {filePath} is not valid")
            else:
                if not is_file_on_disk(filePath):
                    raise FileNotFoundError(f'File {filePath} is not valid')
        elif isinstance(filePath, list):
            if any(map(lambda item: not len(item) > 0, filePath)):
                raise ValueError(f"file name {item} is not valid")

            not_found_files = list(filterfalse(is_file_on_disk, filePath))
            if len(not_found_files) > 0:
                raise FileNotFoundError(f'Files {not_found_files} are not valid')

        # arguments for instantiating data file handler
        self.obj_args = [_var_name, _file_handler, file_path]

        if not core.is_valid_name(_var_name):
            raise ValueError(f"'{_var_name}' is not a valid Raster name")

        # create an object map for DataFileHandler
        obj_map = {
            (np.float32, np.float32): DataFileHandler_f,
            (np.float32, np.uint32): DataFileHandler_f_i,
            (np.float32, np.uint8): DataFileHandler_f_byt,
            (np.float64, np.float64): DataFileHandler_d,
            (np.float64, np.uint32): DataFileHandler_d_i,
            (np.float64, np.uint8): DataFileHandler_d_byt,
        }

        super().__init__(base_type, data_type)
        try:
            self._handle = obj_map[(base_type, data_type)](*self.obj_args, **self.obj_kwargs)
        except Exception as e:
            if isinstance(e, KeyError):
                raise RuntimeError(f"Combination of base_type: {base_type},: "+
                                   f" data_type: {data_type} is not valid")
            else:
                raise e

        self._backend = backend
        self._readConfig = {}

    def __copy__(self):
        raise NotImplementedError()

    def __deepcopy__(self, memo):
        raise NotImplementedError()

    def getTime(self) -> numbers.Real:
        """Get time based on current time index in the input file.

        Parameters
        ----------
        Nil

        Returns
        -------
        time : double
            Time associated with time index.
        """

        assert self._handle is not None, "RasterFile is not instantiated"

        return self._handle.get_time()

    def getTimeIndex(self) -> numbers.Integral:
        """Get current time index in the input file.

        Parameters
        ----------
        Nil

        Returns
        -------
        time_idx : int
            Current time index.
        """

        assert self._handle is not None, "RasterFile is not instantiated"

        return self._handle.get_time_index()

    def getMaximumTimeIndex(self) -> numbers.Integral:
        """Get maximum time index in the input file.

        Parameters
        ----------
        Nil

        Returns
        -------
        max_idx : int
            Maximum time index.
        """

        assert self._handle is not None, "RasterFile is not instantiated"

        return self._handle.get_max_time_index()

    def getTimeFromIndex(self, time_idx: numbers.Integral) -> np.double:
        """Get time in the input file based on index.

        Parameters
        ----------
        time_idx : int
            Time index or raster band count.

        Returns
        -------
        time : double
            Time associated with time index.
        """

        assert self._handle is not None, "RasterFile is not instantiated"

        return self._handle.time_from_index(time_idx)

    def getIndexFromTime(self, time: numbers.Real) -> numbers.Integral:
        """Get index in the input file based on time.

        Parameters
        ----------
        time : double
            Epoch time value.

        Returns
        -------
        time_idx : int
            Time index associated time.
        """

        assert self._handle is not None, "RasterFile is not instantiated"

        return self._handle.index_from_time(time)

    def deleteRasterData(self):
        # Get handle
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")

        # Clear all raster data
        self._custom_getattr(cy_obj).deleteRasterData()

    def setTimeIndex(self, time_idx: numbers.Integral):
        """Update time index in the input file.

        Parameters
        ----------
        time_idx : int
            Time index or raster band count.

        Returns
        -------
        Nil
        """

        # Check index
        if not isinstance(time_idx, numbers.Integral):
            raise TypeError("time_idx should be of type int")

        # Update time
        self._handle.update_time(time_idx)
        self.deleteRasterData()

    def update_variable_map(self, varname: Union[Dict, str]):
        """update variable map, which maps file variable to raster name

        Parameters
        ----------
        varname : Union[str, Dict]
            name of the variable in the file or the grib file map
        """
        self._handle.update_variable_map(varname)

    def read(self,
             thredds: bool=False,
             use_pydap: bool=False,
             read_projection: bool=True,
             layers: Optional[Union[List, numbers.Integral]] = None,
             dims: Optional[Tuple] = None,
             jsonConfig: Optional[Union[Dict, str]]=None):
        """Read input file and initialise Raster object.

        Parameters
        ----------
        thredds: bool, Optional
            check to read file hosted on thredds
        use_pydap: bool, Optional
            check to use pydap to read file over opendap
        read_projection: bool, Optional
            check whether to read projection from file or not
        layers: Union[List, numbers.Integral], Optional
            Indices for reading three dimensional raster data
        jsonConfig = Union[Dict, str], Optional
            a config parameter to read netcdf variable

        Returns
        -------
        Nil
        """
        assert self._handle is not None, "RasterFile is not instantiated"

        # Set to index 1 by default for gdal and rasterio
        if self._backend in ["gdal", "rasterio"]:
            self._handle.update_time(1)
            default_layers = -1
        else:
            default_layers = 0

        if jsonConfig is not None:
            assert isinstance(jsonConfig, (dict, str)), "jsonConfig should be a dict or str"
            if isinstance(jsonConfig, str):
                jsonConfig = json.loads(jsonConfig)
            _layers = jsonConfig.get("layers", layers)
            if isinstance(_layers, str):
                _layers = parse_slice(_layers[1:-1])
            _dims = jsonConfig.get("dims", dims)
            _variable = jsonConfig.get("variable", "")
            if _variable != "":
                self.update_variable_map(_variable)
        else:
            _layers = layers
            _dims = dims

        _layers = default_layers if _layers is None else _layers

        # create a read config
        self._readConfig = {
            "thredds": thredds,
            "use_pydap": use_pydap,
            "read_projection": read_projection,
            "layers": _layers,
            "dims": _dims
        }

        # Read data
        self._handle.read(thredds=thredds,
                          use_pydap=use_pydap,
                          read_projection=read_projection,
                          layers=_layers, dims=_dims)
        self.setFileInputHandler()

        # set const flag for files
        if self._backend in ['netcdf', 'xarray']:
            _file_name = ""
            if isinstance(self._handle._file_name, str):
                _file_name = self._handle._file_name
            elif isinstance(self._handle._file_name, object):
                if hasattr(self._handle._file_name, "filepath"):
                    _file_name = getattr(self._handle._file_name, "filepath")()
                elif any(map(lambda s: hasattr(self._handle._file_name, s),
                             ["_file_obj", "encoding"])):
                    try:
                        _file_name = self._handle._file_name._file_obj._filename
                    except AttributeError:
                        try:
                            _file_name = self._handle._file_name.encoding['source']
                        except Exception as e:
                            _file_name = ""
            if thredds:
                # set const to False for remote files
                self.setConst(False)
            elif len(_file_name) > 0 and is_remote_uri(_file_name):
                self.setConst(False)
            else:
                self.setConst(True)
        elif self._backend in ['gdal', 'rasterio']:
            # set const to False for remote files
            if self._handle is not None and self._handle._file_name is not None:
                if isinstance(self._handle._file_name, str):
                    if len(self._handle._file_name) > 0 and is_remote_uri(self._handle._file_name):
                        self.setConst(False)
                elif hasattr(self._handle._file_name, "GetFileList"):
                    self.setConst(False)
            else:
                self.setConst(True)
        else:
            self.setConst(True)

    @property
    def data_vars(self) -> List[str]:
        return self.get_data_variables()

    def get_data_variables(self) -> List[str]:
        return self._handle.get_data_variables()

    @property
    def file_info(self):
        return self.get_file_info()

    def get_file_info(self) -> Dict:
        """get the information about the file contents.

        Example
        -------
        >>> from geostack.raster import RasterFile
        >>> filein = RasterFile(name='test', filePath='test.nc', backend='netcdf')
        >>> filein.get_file_info()
        {"filename": "", "dimensions": [], "variables" : []}

        Returns
        -------
        Dict
            a dictionary with file contents
        """
        return self._handle.get_file_info()

    @property
    def invert_y(self) -> bool:
        return self._handle.class_obj.invert_y

    @invert_y.setter
    def invert_y(self, other: bool):
        self._handle.class_obj.invert_y = other

    def setFileInputHandler(self):
        """Set File input handler for the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        Nil
        """
        assert self._handle is not None, "RasterFile is not instantiated"
        if  not self._has_input_handler:
            self._handle.setFileInputHandler()
            self._has_input_handler = True

    def setFileOutputHandler(self):
        """Set File output handler for the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        Nil
        """
        assert self._handle is not None, "RasterFile is not instantiated"
        self._handle.setFileOutputHandler()

    @property
    def dimensions(self) -> "RasterDimensions":
        return self.getRasterDimensions()

    def _custom_getattr(self, attr: str):
        if len(attr.split('.')) > 0:
            _attr_list = attr.split(".")
            for i, item in enumerate(_attr_list, 0):
                if i == 0:
                    ret = getattr(self, item)
                else:
                    ret = getattr(ret, item)
        else:
            ret = getattr(self, attr)
        return ret

    def hasProperty(self, prop: str) -> bool:
        """Check if a property is defined for the raster object.

        Parameters
        ----------
        prop : str
            Name of the property.

        Returns
        -------
        out : bool
            True if property is defined else False.

        Examples
        --------
        >>> import numpy as np
        >>> from geostack.readers import GDAL_Handler
        >>> testRasterA = RasterFile(file_handler=GDAL_Handler,
        ...                               file_path="test.tif",
        ...                               data_type=np.float32,
        ...                               base_type=np.float32)
        >>> testRasterA.setProperty("name", "testRasterA", prop_type=str)
        >>> testRasterA.hasProperty("name")
        True
        """
        if not isinstance(prop, str):
            raise TypeError("property name 'prop' should be of string type")
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")
        _prop = core.str2bytes(prop)
        return self._custom_getattr(cy_obj).hasProperty(_prop)

    def getProperty(self, prop: str, prop_type: Optional[type]=None):
        """Get the value of a property from the Raster object.

        Parameters
        ----------
        prop : str
            Name of the property.
        prop_type: type, default is None
            data type used to cast property value

        Returns
        -------
        out : str/float/int
            Value of the property from the Raster object.

        Examples
        --------
        >>> import numpy as np
        >>> from geostack.readers import GDAL_Handler
        >>> testRasterA = RasterFile(file_handler=GDAL_Handler,
        ...                               file_path="test.tif",
        ...                               data_type=np.float32,
        ...                               base_type=np.float32)
        >>> testRasterA.setProperty("name", "testRasterA", prop_type=str)
        >>> testRasterA.hasProperty("name")
        True
        >>> testRasterA.getProperty("name", prop_type=str)
        testRasterA
        """
        if not isinstance(prop, (str, bytes)):
            raise TypeError("property name 'prop' should be of string type")

        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")

        if prop_type is None:
            _prop_type = self.getPropertyType(prop).__name__
        else:
            _prop_type = prop_type.__name__

        # create a mapping for methods
        method_map = {"int": self._custom_getattr(cy_obj).getProperty_int,
                      "str": self._custom_getattr(cy_obj).getProperty_str}
        if self.base_type == np.float64:
            method_map['float64'] = self._custom_getattr(cy_obj).getProperty_dbl
        elif self.base_type == np.float32:
            method_map['float'] = self._custom_getattr(cy_obj).getProperty_flt

        method = method_map.get(_prop_type)
        if method is None:
            raise TypeError("value of prop_type is not of acceptable type")

        if self.hasProperty(prop):
            _prop = core.str2bytes(prop)
            out = method(_prop)
            return out
        else:
            raise KeyError("Property %s is not attached to the object" % prop)

    def setProperty(self, prop: Union[str,bytes],
                    value: Union[str, int, float, np.float64],
                    prop_type: Optional[type]=None):
        """Set a value of property 'prop' to a value 'propValue' and data type 'propType'.

        Parameters
        ----------
        prop : Union[str, bytes] type
            Name of the property to be defined for the raster object.
        value : Union[str, int, float, np.float64] type
            Value of the property for the raster object.
        prop_type : type, default is None
            data type of the property defined for the raster object.

        Returns
        -------
        Nil

        Examples
        -------
        >>> import numpy as np
        >>> from geostack.readers import GDAL_Handler
        >>> testRasterA = RasterFile(file_handler=GDAL_Handler,
        ...                          file_path="test.tif",
        ...                          data_type=np.float32,
        ...                          base_type=np.float32)
        >>> testRasterA.setProperty("name", "testRasterA", prop_type=str)
        >>> testRasterA.hasProperty("name")
        True
        """
        if not isinstance(prop, (str, bytes)):
            raise TypeError("property name 'prop' should be of string type")

        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("RasterFile and underlying Raster has not been created")

        _prop = core.str2bytes(prop)

        if prop_type is not None:
            _prop_type = prop_type.__name__
        else:
            _prop_type = "str"

        # create a mapping for methods
        method_map = {"int": self._custom_getattr(cy_obj).setProperty_int,
                      "str": self._custom_getattr(cy_obj).setProperty_str}
        if self.base_type == np.float64:
            method_map['float64'] = self._custom_getattr(cy_obj).setProperty_dbl
        elif self.base_type == np.float32:
            method_map['float'] = self._custom_getattr(cy_obj).setProperty_flt

        if _prop in ['name', b'name']:
            if not core.is_valid_name(value):
                raise ValueError(f"'{value}' is not a value Raster name")

        method = method_map.get(_prop_type)
        if method is None:
            raise TypeError("value of prop_type is not of acceptable type")
        if _prop_type == "str":
            method(_prop, core.str2bytes(f"{value}"))
        else:
            method(_prop, prop_type(value))

    @property
    def bounds(self) -> "vector.BoundingBox":
        return self.getBounds()

    def getData(self,
                ti: numbers.Integral = 0,
                tj: numbers.Integral = 0) -> np.ndarray:
        """Get raster data for tile index (ti, tj) and time index 'tidx'.

        Parameters
        ----------
        ti : int
            Tile index in x-direction.
        tj : int
            Tile index in y-direction.

        Returns
        -------
        out : numpy.ndarray
            Tile data from the Raster object.
        """
        assert self._handle is not None, "RasterFile has not be initialized"
        if not isinstance(ti, numbers.Integral):
            raise TypeError("ti should on integer type")
        if not isinstance(tj, numbers.Integral):
            raise TypeError("tj should on integer type")

        if self._has_input_handler:
            return self._handle.getData(ti, tj)
        else:
            raise RuntimeError("FileInputHandler is not yet set!!!")

    @property
    def data(self) -> np.ndarray:
        return self.get_full_data()

    def getProperties(self) -> Dict:
        """Get all the properties of an object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out: dict
            A dictionary containing properties and values of the properties.

        Examples
        --------
        >>> testRasterA = Raster(name="testRasterA")
        >>> testRasterA.getProperties()
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")

        _properties = self._custom_getattr(cy_obj).getProperties()
        return _properties

    def getPropertyType(self, propName: Union[str, bytes]) -> type:
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")
        _prop_type = self._custom_getattr(cy_obj).getPropertyType(core.str2bytes(propName))
        return core.PropertyType.to_pytype(_prop_type)

    @property
    def reduceVal(self) -> numbers.Real:
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
            if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                cy_obj = "_handle.cy_raster_obj"
        else:
            raise AttributeError("Raster or Vector has not been created")
        out = self._custom_getattr(cy_obj).reduceVal()
        return out

    def close(self):
        if hasattr(self, '_handle'):
            self._handle.class_obj.close()

    def __del__(self, *args, **kwargs):
        self.close()

    def __setstate__(self, ds: Dict) -> None:
        # instantiate raster
        self.__init__(data_type=ds.get("data_type"),
                      base_type=ds.get("base_type"),
                      **ds.get('kwargs'))

        # initialise with dimensions
        self.read(**ds.get('readConfig'))

        # set properties
        for prop in ds['properties']:
            self.setProperty(prop, ds['properties'].get(prop))

        # set variables
        if 'variables' in ds:
            for var in ds['variables']:
                self.setVariableData(var, ds["variables"].get(var))

        # proj params
        proj_params = core.ProjectionParameters.from_dict(ds['projection_params'])
        self.setProjectionParameters(proj_params)

        self.setTimeIndex(ds.get('timeIndex', 0))

    def __getstate__(self) -> Dict:
        output = {
            "data_type": self.data_type,
            "base_type": self.base_type,
            "dimensions": self.getDimensions().to_dict(),
            "properties": dict(map(lambda item: (item, self.getProperty(item)),
                                   self.getPropertyNames()))
        }

        # extract variables
        if self.hasVariables():
            output['variables'] = {}
            for item in self.getVariableNames():
                output[item] = self.getVariableData(item)

        # extract projection parameters
        output['projection_params'] = self.getProjectionParameters().to_dict()

        output['timeIndex'] = self.getTimeIndex()

        output['kwargs'] = self.obj_kwargs
        output['kwargs']['name'] = self.obj_args[0]
        output['kwargs']['filePath'] = self.obj_args[2]
        output['kwargs']['backend'] = self._backend

        output['readConfig'] = self._readConfig

        return output

    def __exit__(self):
        self.close()

    def __repr__(self):
        return "<class 'geostack.raster.%s'>\n%s" % (self.__class__.__name__, str(self))


def equalSpatialMetrics(this: "Dimensions", other: "Dimensions") -> bool:
    '''Check alignment of input Dimensions

    Parameters
    ----------
    this: Dimensions
        an instance of Dimensions class
    other: Dimensions
        an instance of Dimensions class

    Returns
    -------
    out : bool
        True if equal, False otherwise

    Examples
    --------
    >>> dimA = {'hx': 0.02999,
    ...         'hy': 0.02999,
    ...         'hz': 1.0,
    ...         'mx': 491,
    ...         'my': 723,
    ...         'nx': 491,
    ...         'ny': 723,
    ...         'nz': 1,
    ...         'ox': 142.16879,
    ...         'oy': -28.69602,
    ...         'oz': 0.0}
    >>> dimB = {'hx': 0.02999,
    ...         'hy': 0.02999,
    ...         'hz': 1.0,
    ...         'mx': 491,
    ...         'my': 723,
    ...         'nx': 491,
    ...         'ny': 723,
    ...         'nz': 1,
    ...         'ox': 142.16879,
    ...         'oy': -28.69602,
    ...         'oz': 0.0}
    >>> testDimensionsA = Dimensions.from_dict(dimA, dtype=np.float32)
    >>> testDimensionsB = Dimensions.from_dict(dimB, dtype=np.float32)
    >>> out = equalSpatialMetrics(testDimensionsA, testDimensionsB)
    True
    '''
    if isinstance(this, Dimensions) and isinstance(other, Dimensions):
        assert this._dtype == other._dtype, "datatype mismatch"
        if this._dtype == np.float32:
            out = equalSpatialMetrics_f(this._handle, other._handle)
        elif this._dtype == np.float64:
            out = equalSpatialMetrics_d(this._handle, other._handle)
    elif isinstance(this, _Dimensions_f) and isinstance(other, _Dimensions_f):
        out = equalSpatialMetrics_f(this, other)
    elif isinstance(this, _Dimensions_d) and isinstance(other, _Dimensions_d):
        out = equalSpatialMetrics_d(this, other)
    else:
        raise TypeError("Input Parameters should be instance of Dimensions")
    return out


def sortColumns(inp_raster: Union["Raster", "RasterFile"],
                name: Optional[str]=None, inplace: bool=False) -> "Raster":
    """sort 3d raster along the layer axis.

    Parameters
    ----------
    inp_raster : Raster/RasterFile
        input raster object
    name: str, Optional
        name of the raster when sorting is not inplace, default "sorted"
    inplace: bool, Optional
        if True, sort input raster inplace, else return a new Raster object with sorted values

    Raises
    ------
    TypeError
        input raster should be an instance of Raster/ RasterFile object

    Examples
    --------
    >>> import numpy as np
    >>> from geostack.raster import Raster
    >>> testA = Raster(name="testA")
    >>> testA.init(64, 1.0, ny=64, hy=1.0, nz=10, hz=1.0)

    >>> # assign data
    >>> random_data = np.random.random(testA.shape)
    >>> testA.data = random_data

    >>> # sort data in place
    >>> sortColumns(testA, inplace=True)
    >>> np.allclose(np.sort(random_data, axis=0), testA)
    True

    >>> # sort a copy of raster, and return sorted copy
    >>> testA.data = random_data
    >>> out = sortColumns(testA, inplace=False)
    >>> np.allclose(np.sort(random_data, axis=0), out)
    True
    """
    # create a method for (base_type, data_type) tuple
    method_map = {
        (np.float32, np.float32): sortColumns_f,
        (np.float64, np.float64): sortColumns_d,
        (np.float32, np.uint32): sortColumns_f_i,
        (np.float64, np.uint32): sortColumns_d_i,
        (np.float32, np.uint8): sortColumns_f_byt,
        (np.float64, np.uint8): sortColumns_d_byt
    }

    if isinstance(inp_raster, (Raster, RasterFile)):
        sort_method = method_map[(inp_raster.base_type, inp_raster.data_type)]
    else:
        raise TypeError("inp_raster should be an instance of Raster/ RastercFile")

    if inp_raster.ndim != 3:
        raise TypeError("input_raster should be a 3-dimensional raster")

    if inplace:
        sort_method(inp_raster._handle)
    else:
        if name is None:
            name = 'sorted'

        out_raster = inp_raster.deepcopy(name=name)
        sort_method(out_raster._handle)

        if name is None:
            out_raster.name = inp_raster.name
        return out_raster
