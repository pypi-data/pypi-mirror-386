# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os
import os.path as pth
import sys
import numpy as np
import json
import warnings
import numbers
import logging
from abc import ABCMeta, abstractmethod
from typing import Union, Tuple, List, Dict, Any, Optional
from datetime import datetime
from collections import deque
from itertools import islice
from ..raster import raster
from .. import dataset
from ..dataset import supported_libs
from .. import utils
from .. import core
from ..core import solver
from .ncutils import Pydap2NC
from .timeutils import RasterTime, regex
from .tiffutils import (get_geotiff_tags, TIFFTAG_GEOTRANSMATRIX,
                        TIFFTAG_GEOPIXELSCALE, TIFFTAG_GEOTIEPOINTS)

global VERBOSITY
VERBOSITY_LEVEL = lambda : solver.Solver.get_verbose_level()

logger = logging.getLogger("geostack")

warnings.filterwarnings("ignore", category=UserWarning)

if supported_libs.HAS_GDAL:
    try:
        from osgeo import gdal, gdalconst, osr
        from osgeo import gdal_array
        os.environ['GDAL_CACHEMAX'] = "100"
        os.environ['VSI_CACHE'] = "OFF"
    except ImportError:
        warnings.warn(
            "gdal is not correctly installed, check your installation.", RuntimeWarning)
        supported_libs.HAS_GDAL = False

if supported_libs.HAS_NCDF:
    import netCDF4 as nc
    if supported_libs.HAS_PYDAP:
        from pydap.client import open_url

if supported_libs.HAS_XARRAY:
    import xarray as xr
    xr.set_options(file_cache_maxsize=1024, keep_attrs=True)

if supported_libs.HAS_RASTERIO:
    import rasterio as rio
    try:
        from rasterio.windows import Window
    except ImportError:
        warnings.warn(
            "rasterio is not correctly installed, check your installation.", RuntimeWarning)
        supported_libs.HAS_RASTERIO = False
    if supported_libs.HAS_RASTERIO and hasattr(rio, "_env"):
        rio._env.set_gdal_config("GDAL_CACHEMAX", 100)
        rio._env.set_gdal_config("VSI_CACHE", False, normalize=True)


__all__ = ["get_gdal_geotransform", "DataHandler", "GDAL_Handler",
           "NC_Handler", "XR_Handler", "RIO_Handler", "get_layers",
           "from_zarr"]


def deduce_variable_coords(file_obj: Any, key: str) -> Optional[str]:
    """get the name of variable from an object.

    Parameters
    ----------
    file_obj : Union[nc.Dataset, xr.Dataset]
        an instance of netCDF4 Dataset or xarray Dataset

    key : str
        the variable to search in the file

    Returns
    -------
    str | None
        name of the variable from the file
    """
    count = {}
    if hasattr(file_obj, 'coords'):
        # most likely a xarray object
        for item in file_obj.coords.variables:
            if item not in count:
                count[item] = 0
            if regex[key].match(item.lower()) is not None:
                count[item] += 1
            try:
                var_item = file_obj.coords.variables[item]
                var_encoding = getattr(var_item, "encoding")
                var_encoding.update(getattr(var_item, 'attrs'))
                for attr in var_encoding:
                    # if attr != "projectionType":
                    var_attr = var_encoding.get(attr)
                    if isinstance(var_attr, str):
                        var_attr = var_attr.lower()
                    if (isinstance(var_attr, str) and
                        regex[key].match(var_attr) is not None):
                        count[item] += 1
            except Exception as e:
                warnings.warn(f'{e}', RuntimeWarning)
    elif hasattr(file_obj, "dimensions"):
        # most likely a netCDF4 object
        for item in file_obj.dimensions:
            if item not in count:
                count[item] = 0
            if regex[key].match(item.lower()) is not None:
                count[item] += 1

            # use try and except
            try:
                for attr in file_obj[item].ncattrs():
                    # if attr != "projectionType":
                    var_attr = file_obj[item].getncattr(attr)
                    if isinstance(var_attr, str):
                        var_attr = var_attr.lower()
                    if regex[key].match(var_attr) is not None:
                        count[item] += 1
            except Exception as e:
                warnings.warn(f'{e}', RuntimeWarning)

    value = 0
    out_key = ""
    for item, item_value in count.items():
        if item_value > value:
            out_key, value = item, item_value
    if not count:
        out_key = None
    return out_key


def get_layers(arg, nz: numbers.Integral) -> List:
    """Get indices for 3d axis.

    Parameters
    ----------
    arg: numbers.Integral/slice/list/tuple
        index, list of indices, slice along 3rd axis to read 3d data from file.
    nz: numbers.Integral
        length along 3rd axis

    Returns
    -------
    levels: list
        list of indices along the 3rd axis
    """
    if arg is None:
        stride = slice(None)
    if isinstance(arg, numbers.Integral):
        if arg == -1:
            stride = slice(None)
        else:
            stride = slice(arg, arg + 1, None)
    elif isinstance(arg, (list, tuple, np.ndarray)):
        # get unique integer values from list
        stride = list(set([int(level) for level in arg]))
    elif isinstance(arg, slice):
        stride = arg

    levels = list(range(nz))

    if isinstance(stride, slice):
        levels = levels[stride]
    elif isinstance(stride, list):
        levels = list(filter(lambda x: x in stride, levels))
        if not len(levels) > 0:
            levels = get_layers(-1, nz)
    return levels


def get_gdal_geotransform(raster_dimensions: Union["raster.RasterDimensions", Dict]) -> Tuple:
    """Compute geotransform using raster dimensions.

    Parameters
    ----------
    raster_dimensions: raster.RasterDimensions/ dict
        RasterDimensions of a raster.Raster object

    Returns
    -------
    out: tuple
        gdal geotransform tuple representation of raster.RasterDimensions

    Raises
    ------
    TypeError: Input raster dimensions should contain key 'dim'
    """
    if isinstance(raster_dimensions, dict):
        if 'dim' in raster_dimensions:
            ox = raster_dimensions['dim']['ox']
            hx = raster_dimensions['dim']['hx']
            hy = raster_dimensions['dim']['hy']
            oy = raster_dimensions['oy']
            if hy > 0:
                hy = hy * -1
                oy = raster_dimensions['ey']
        else:
            raise TypeError("Input raster dimensions should contain key 'dim'")
    elif isinstance(raster_dimensions, raster.RasterDimensions):
        ox = raster_dimensions.ox
        hx = raster_dimensions.hx
        if raster_dimensions.hy > 0:
            hy = -1 * raster_dimensions.hy
            oy = raster_dimensions.ey
        elif raster_dimensions.hy < 0:
            hy = raster_dimensions.hy
            oy = raster_dimensions.oy
    out = (ox, hx, 0.0, oy, 0.0, hy)
    return out


@supported_libs.RequireLib("gdal")
def return_proj4(gdal_file):
    """Get GDAL Dataset projection as Proj4 string.

    Note
    ----
    Unable to use with gdal, possibly due to the thread safety
    https://gdal.org/development/rfc/rfc16_ogr_reentrancy.html

    Parameters
    ----------
    gdal_file: gdal.Dataset/str
        A GDAL Dataset projection as a proj4 string

    Examples
    --------
    >>> test = gdal.Dataset("test.tif")
    >>> out_str = return_proj4(test)
    """
    out = ""
    if isinstance(gdal_file, gdal.Dataset):
        gdal_dataset = gdal_file
    elif isinstance(gdal_file, str):
        gdal_dataset = gdal.OpenEx(gdal_file)

    if hasattr(gdal_dataset, "GetSpatialRef"):
        spatialRef = gdal_dataset.GetSpatialRef()
        if spatialRef is not None:
            out = spatialRef.ExportToProj4()
    else:
        proj = gdal_dataset.GetProjection()
        if len(proj) > 1:
            proj_ref = osr.SpatialReference()
            proj_ref.ImportFromWkt(proj)
            out = proj_ref.ExportToProj4()
    return out


class DataHandler(object, metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def reader(self, *args, **kwargs):
        raise NotImplementedError("reader method is not implemented")

    @abstractmethod
    def setter(self, *args, **kwargs):
        raise NotImplementedError("setter method is not implemented")

    @abstractmethod
    def writer(self, *args, **kwargs):
        raise NotImplementedError("writer method is not implemented")

    @abstractmethod
    def time(self, *args, **kwargs):
        raise NotImplementedError("time method is not implemented")

    @abstractmethod
    def __exit__(self, *args):
        raise NotImplementedError("exit method is not implemented")


def get_tiles_count(xsize: int, ysize: int, tile_size: int) -> Tuple[int, int]:
    """get the number of tiles along x-direction and y-direction.

    Parameters
    ----------
    xsize : int
        number of grid cells in x-direction
    ysize : int
        number of grid cells in y-direction
    tile_size : int
        number of grid cells in a tile

    Returns
    -------
    Tuple[int, int]
        a tuple of integers with number of tiles in x-direction, y-direction
    """
    xtiles = divmod(xsize, tile_size)
    ytiles = divmod(ysize, tile_size)
    if xtiles[1] == 0:
        xtiles = xtiles[0]
    else:
        xtiles = xtiles[0] + 1

    if ytiles[1] == 0:
        ytiles = ytiles[0]
    else:
        ytiles = ytiles[0] + 1
    return xtiles, ytiles


def get_dimension_index(raster_dimension: Union[List[str], Tuple[str]],
                        variable_dimension: Union[List[str], Tuple[str]]) -> List[int]:
    """get the order of dimension in netcdf variable

    Parameters
    ----------
    raster_dimension : Union[List[str], Tuple[str]]
        a list/ tuple of dimension used in Raster
    variable_dimension : Union[List[str], Tuple[str]]
        a list/ tuple of dimension present in netCDF.Variable

    Returns
    -------
    List[int]
        a list of index of the dimension
    """
    dimension_idx = []
    for dim in raster_dimension:
        if dim in variable_dimension:
            dimension_idx.append(variable_dimension.index(dim))
    return dimension_idx


class NC_Handler(DataHandler):

    def __init__(self,
                 fileName: Optional[Union[str, Any]] = None,
                 base_type: np.dtype = core.REAL,
                 variable_map: Optional[Dict] = None,
                 data_type: np.dtype = core.REAL,
                 raster_name: str = ""):
        # if the filename is a path to a file, ensure it's an absolute path
        if fileName is not None:
            if isinstance(fileName, str) and not utils.is_remote_uri(fileName):
                fileName = pth.abspath(
                    fileName) if pth.exists(fileName) else None
        self._file_name = fileName
        self._file_handler = None
        self.is_thredds = False
        self.use_pydap = False
        self.invert_y = False
        self.data_type = data_type
        self.base_type = base_type
        self.nullValue = raster.getNullValue(data_type)
        self._time_handler = None
        self._variable_map = variable_map
        self._dims = deque()
        self.layers = [0]
        self.raster_name = raster_name

    @property
    def file_info(self) -> Dict:
        return self.get_file_info()

    @supported_libs.RequireLib("netcdf")
    def get_file_info(self, *args, **kwargs) -> Dict:
        """get the information about the file contents

        Returns
        -------
        Dict
            a dictionary with file name, dimensions and variables
        """
        out = {"filename": "", "dimensions": [], "variables": []}

        if hasattr(self, '_file_handler'):
            if self._file_handler is not None:
                if not self._file_handler.isopen():
                    return {}

        if self._file_handler is None:
            # open file is not yet opened
            self.open_file(**kwargs)

        if self._file_handler is not None:
            # add the file name
            if self._file_name is not None:
                if isinstance(self._file_name, str):
                    out['filename'] = self._file_name
            # get the dimensions
            for item in self._file_handler.dimensions:
                dim_size = getattr(self._file_handler.dimensions[item], 'dimtotlen',
                                   getattr(self._file_handler.dimensions[item], "size", None))
                if dim_size is not None:
                    out['dimensions'].append({"name": item, "size": dim_size})
                else:
                    raise ValueError(f"dimension size for {item} is None")
            # get the variables:
            for item in self._file_handler.variables:
                var_info = {"name": item,
                            "dimensions": self._file_handler.variables[item].dimensions,
                            "dtype": self._file_handler.variables[item].dtype,
                            "attrs": {}}
                # get the variable attributes
                for attr in self._file_handler.variables[item].ncattrs():
                    var_info['attrs'][attr] = getattr(self._file_handler.variables[item], attr)
                out['variables'].append(var_info)

            # get the global attributes
            out['global_attrs'] = {
                item: getattr(self._file_handler, item)
                for item in self._file_handler.ncattrs()
            }
        else:
            raise RuntimeError("Unable to open file")

        return out

    @supported_libs.RequireLib("netcdf")
    def open_file(self, *args, **kwargs):
        self.is_thredds = kwargs.get("thredds", self.is_thredds)
        self.use_pydap = kwargs.get("use_pydap", self.use_pydap)

        if self._file_name is None:
            raise ValueError("file_name cannot be None")

        # check file_name and open file
        if not self.is_thredds and not self.use_pydap:
            if isinstance(self._file_name, (str, bytes)):
                # when file is on disc
                if isinstance(self._file_name, bytes):
                    self._file_handler = nc.Dataset(
                        self._file_name.decode(), mode='r')
                elif isinstance(self._file_name, str):
                    self._file_handler = nc.Dataset(self._file_name, mode='r')
            elif isinstance(self._file_name, list):
                _file_list = list(map(lambda item: item.decode()
                                      if isinstance(item, bytes) else item,
                                      self._file_name))
                if len(_file_list) > 1:
                    self._file_handler = nc.MFDataset(_file_list)
                else:
                    self._file_handler = nc.Dataset(_file_list[0])
        elif self.is_thredds:
            # when using thredds
            if self.use_pydap and supported_libs.HAS_PYDAP:
                # open using pydap
                # pydap can be used when thredds server requires
                # authentication

                # Pydap2NC provides a netCDF4.Dataset like interface to
                # pydap.Dataset
                if isinstance(self._file_name, Pydap2NC):
                    self._file_handler = self._file_name
                elif isinstance(self._file_name, str):
                    self._file_handler = Pydap2NC(open_url(self._file_name))
                else:
                    self._file_handler = Pydap2NC(self._file_name)
            else:
                if isinstance(self._file_name, list):
                    _file_list = list(map(lambda item: item.decode()
                                          if isinstance(item, bytes) else item,
                                          self._file_name))
                    if len(_file_list) > 1:
                        self._file_handler = nc.MFDataset(_file_list)
                    else:
                        self._file_handler = nc.Dataset(_file_list[0])
                elif isinstance(self._file_name, (str, bytes)):
                    # open using netcdf4 library
                    if isinstance(self._file_name, str):
                        self._file_handler = nc.Dataset(self._file_name)
                    elif isinstance(self._file_name, bytes):
                        self._file_handler = nc.Dataset(
                            self._file_name.decode())

        if isinstance(self._file_name, (nc.Dataset, nc.MFDataset)):
            # assign nc.Dataset to file_handler when file_name is nc.Dataset
            self._file_handler = self._file_name
            # change file_name to path of file
            if isinstance(self._file_name, nc.Dataset):
                self._file_name = self._file_name.filepath()
            else:
                self._file_name = None

    @property
    def data_vars(self) -> List[str]:
        """data variables as property

        Returns
        -------
        List[str]
            a list of string
        """
        return self.get_data_variables()

    @supported_libs.RequireLib("netcdf")
    def get_data_variables(self) -> List[str]:
        """get name of data variables

        Returns
        -------
        list
            a list of string
        """
        var_names = [item['name'] for item in self.file_info['variables']]
        dim_names = [item['name'] for item in self.file_info['dimensions']]

        scalar_vars = []
        for item in var_names:
            if not len(self._file_handler[item].dimensions) > 0:
                scalar_vars.append(item)

        var_list = list(set(var_names).difference(dim_names).difference(scalar_vars))

        if not len(var_list) > 0:
            raise RuntimeError("No data variables found")
        return var_list

    def clear(self):
        """clear dimensions and layers from instantiated object
        """
        self._dims.clear()
        self.layers = [0]

    @supported_libs.RequireLib("netcdf")
    def reader(self, thredds: bool = False, use_pydap: bool = False, **kwargs):
        self.clear()

        # set thredds and use_pydap arguments
        self.is_thredds = thredds
        self.use_pydap = use_pydap

        if self._file_handler is None:
            # open file if not yet opened
            self.open_file(thredds=thredds, use_pydap=use_pydap)

        if self._file_handler is None:
            raise ValueError("file_handler cannot be identified")

        # use projection information when available in netcdf4 file
        projStr = ""
        if 'crs' in self._file_handler.variables:
            if hasattr(self._file_handler.variables['crs'], "crs_wkt"):
                projStr = utils.proj4_from_wkt(
                    self._file_handler.variables['crs'].getncattr("crs_wkt"))
            elif hasattr(self._file_handler.variables['crs'], "spatial_ref"):
                projStr = utils.proj4_from_wkt(
                    self._file_handler.variables['crs'].getncattr("spatial_ref"))

        # identify and get the time variable
        time_variable = deduce_variable_coords(self._file_handler, "time")
        if time_variable != "":
            try:
                self._time_handler = RasterTime(
                    self._file_handler.variables[time_variable])
                self._time_handler.set_time_bounds()
            except KeyError:
                pass

        if VERBOSITY_LEVEL() <= logging.DEBUG and time_variable != "":
            logger.debug(f"Using {time_variable} as time variable")

        # identify x-dimension from netcdf file
        lon_variable = deduce_variable_coords(self._file_handler, 'longitude')
        if lon_variable == '':
            # try to find 'X' in file
            lon_variable = deduce_variable_coords(self._file_handler, 'X')
        if lon_variable == '':
            raise KeyError("unable to deduce x-dimension from file")

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {lon_variable} as x dimension")

        # get the x-dimension
        lon = self._file_handler.variables[lon_variable]
        nx = self._file_handler.dimensions[lon_variable].size
        self._dims.append(lon_variable)

        # identify y-dimension from netcdf file
        lat_variable = deduce_variable_coords(self._file_handler, 'latitude')
        if lat_variable == '':
            # try to find 'Y' in file
            lat_variable = deduce_variable_coords(self._file_handler, 'Y')
        if lat_variable == '':
            raise KeyError("unable to deduce y-dimension from file")

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {lat_variable} as y dimension")

        # get the y-dimension from netcdf file
        lat = self._file_handler.variables[lat_variable]
        ny = self._file_handler.dimensions[lat_variable].size
        self._dims.appendleft(lat_variable)

        # Get variable name
        if isinstance(self.raster_name, str):
            var_name = self.raster_name
        elif isinstance(self.raster_name, bytes):
            var_name = self.raster_name.decode()
        var_name = self._variable_map.get(var_name, var_name)

        if var_name not in self.data_vars:
            warnings.warn(f"Variable name `{var_name}` is not valid, will use {self.data_vars[0]}",
                          RuntimeWarning)
            var_name = self.data_vars[0]

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {var_name} as variable for Raster object")

        # add support for third dimension
        # get the third dimension to map
        var_dims = kwargs.get("dims")
        if var_dims is None:
            # get variable dimensions
            var_dims = self._file_handler[var_name].dimensions
            filter_dims = filter(lambda s: s not in [lat_variable, lon_variable],
                                 var_dims[::-1])
            try:
                layer_dim_name = next(filter_dims)
            except StopIteration:
                layer_dim_name = "time"
        else:
            layer_dim_name = "time"
            current_size = len(self._dims)

            if not isinstance(var_dims, (tuple, list)):
                if len(var_dims) < current_size:
                    raise ValueError(
                        f"Dimension tuple {var_dims} should be atleast {tuple(self._dims)}")
                else:
                    raise TypeError(
                        f"Dimensions iterable {var_dims} should be a tuple or list")

            invalid_dims = []
            for i in range(current_size):
                offset = len(var_dims) - current_size
                if var_dims[i + offset] != self._dims[i]:
                    invalid_dims.append(var_dims[i + offset])

            if len(invalid_dims) > 0 and len(var_dims) == current_size:
                # throw error when
                raise ValueError(
                    f"Dimension tuple {var_dims} is not valid")

            if len(var_dims) != current_size:
                for item in var_dims:
                    if item not in self._dims:
                        self._dims.appendleft(item)
                if len(self._dims) > current_size:
                    # get the first left dimension name
                    layer_dim_name = list(islice(self._dims, 0, current_size - 1))[-1]

        layer_dim_size = 1
        if any(map(lambda s: s['name'] == layer_dim_name, self.file_info['dimensions'])):
            layer_dim_size = self._file_handler.dimensions.get(layer_dim_name)
            if layer_dim_size is None:
                layer_dim_size = 1
            else:
                layer_dim_size = getattr(layer_dim_size, 'dimtotlen',
                                         getattr(layer_dim_size, 'size', None))

        self.layers = get_layers(kwargs.get("layers", -1), layer_dim_size)
        self.layers = sorted(self.layers)

        # get the size of dimension tuple
        time_is_zlayer = False
        if var_dims is None:
            ndim = len(self._dims)
            time_is_zlayer = any(map(lambda s: s == time_variable, self._dims))
        else:
            ndim = len(var_dims)
            time_is_zlayer = any(map(lambda s: s == time_variable, var_dims))

        if ndim > 2:
            nz = len(self.layers)
            oz = self.base_type(self.layers[0])
            # update bounds of time variable
            # if time_variable != '':
            #     if time_is_zlayer and len(self.layers) >= 1:
            #         print(self._time_handler.get_bounds())
            #         self._time_handler.set_index_bounds(
            #             start_idx=min(self.layers),
            #             end_idx=max(self.layers))
            #         print(self._time_handler.get_bounds())
        else:
            # update these for a 2D raster
            nz = 1
            oz = 0.0
            self.layers = [0]

        # Set time origin
        if time_variable != '':
            # when z-dimension is time, use RasterTime object
            oz = 0.0
            hz = 1.0
            if time_is_zlayer:
                oz = self.base_type(self.time_from_index(self.layers[0]))
                if len(self.layers) > 1:
                    # subtract 1 from total layer number (zero based indexing)
                    upper_limit = min(self.layers[-1] + 1, layer_dim_size - 1)
                    z1 = self.base_type(self.time_from_index(upper_limit))
                    hz = (z1 - oz) / len(self.layers)
                else:
                    # substract 1 from total layer number (zero based indexing)
                    upper_limit = min(self.layers[0], layer_dim_size - 1)
                    z1 = self.base_type(self.time_from_index(upper_limit))
                    hz = z1 - oz
        else:
            # when z-dimension is not time
            if nz >= 1:
                try:
                    z0 = self._file_handler.variables[layer_dim_name][self.layers[0]]
                    z1 = self._file_handler.variables[layer_dim_name][self.layers[1]]
                    hz = (z1 - z0)
                except Exception:
                    if nz == 1:
                        hz = 1
                    else:
                        hz = self.layers[1] - self.layers[0]
            else:
                hz = 1

        time = self.time(0)

        # compute dimension input for instantiating raster.Raster
        hx = lon[1] - lon[0]
        hy = lat[1] - lat[0]

        min_x = min(lon[0], lon[-1])
        if isinstance(min_x, np.ma.MaskedArray):
            ox = self.base_type(min_x.data)
        elif isinstance(min_x, np.ndarray):
            ox = self.base_type(min_x)
        elif isinstance(min_x, numbers.Real):
            ox = self.base_type(min_x)
        ox -= 0.5 * hx

        min_y = min(lat[0], lat[-1])
        if isinstance(min_y, np.ma.MaskedArray):
            oy = self.base_type(min_y)
        elif isinstance(min_y, np.ndarray):
            oy = self.base_type(min_y)
        elif isinstance(min_y, numbers.Real):
            oy = self.base_type(min_y)

        if hy < 0:
            self.invert_y = True
            hy = abs(hy)
        oy -= 0.5 * hy

        return nx, ny, nz, hx, hy, hz, ox, oy, oz, core.str2bytes(projStr), time

    def time(self, tidx: numbers.Integral) -> numbers.Real:
        time = 0.0
        if self._time_handler is not None:
            time = self.time_from_index(tidx)
        return time

    def set_time_bounds(self, start_time: Optional[Union[numbers.Real, str]] = None,
                        end_time: Optional[Union[numbers.Real, str]] = None,
                        dt_format: Optional[str] = None):
        if self._time_handler is not None:
            self._time_handler.set_time_bounds(start_time=start_time,
                                               end_time=end_time,
                                               dt_format=dt_format)
        else:
            raise RuntimeError("No time handle has been set")

    def time_from_index(self, index: numbers.Integral) -> numbers.Real:
        if self._time_handler is not None:
            return self._time_handler.time_from_index(index)
        else:
            raise RuntimeError("No time handle has been set")

    def index_from_time(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_max_time_index(self):
        if self._time_handler is not None:
            return self._time_handler.get_max_time_index()
        else:
            raise RuntimeError("No time handle has been set")

    def get_left_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_left_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_right_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_right_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def writer(self, fileName, jsonConfig):
        # writer_config = json.loads(jsonConfig)
        raise NotImplementedError("writer not yet implemented")

    def has_mapping(self, varname: str) -> bool:
        """check if file variable has been mapped

        Parameters
        ----------
        varname : str
            name of the variable in file

        Returns
        -------
        bool
            True is file variable is mapped, False otherwise
        """
        return varname in self._variable_map.values()

    def update_variable_map(self, varname: str):
        """update variable map, mapping file variable to raster name

        Parameters
        ----------
        varname : str
            name of the variable in file
        """
        if not self.has_mapping(varname):
            self._variable_map.update({self.raster_name: varname})

    @supported_libs.RequireLib("netcdf")
    def check_handler(self):
        if not isinstance(self, NC_Handler):
            raise TypeError("Unable to understand the input class instance")

        if self._file_handler is None:
            raise ValueError("file_handler cannot be identified")

        if not isinstance(self._file_handler, (nc.Dataset, nc.MFDataset, Pydap2NC)):
            raise TypeError("file_handler is of incorrect type")

        if not isinstance(self._file_handler, (Pydap2NC, nc.MFDataset)):
            if self._file_handler.filepath() != self._file_name:
                raise ValueError("Mismatch between filepath '{}' and filename '{}'".format(
                    self._file_handler.filepath(), self._file_name))

    @supported_libs.RequireLib("netcdf")
    def setter(self, ti: int, tj: int, tx: int, ty: int,
               tidx: int, *args, **kwargs) -> Tuple[np.ndarray, int, int]:

        if not self.is_thredds and not self.use_pydap:
            if not isinstance(self._file_handler, nc.MFDataset):
                if not self._file_handler.isopen():
                    raise RuntimeError("file is closed, unable to read data")

        # Check handle
        self.check_handler()

        # Create buffer
        tile_size = raster.TileSpecifications().tileSize
        buf_arr = np.full((len(self.layers), tile_size, tile_size), self.nullValue,
                          dtype=self.data_type)

        # Get dimensions
        # get x-dimension from netcdf file
        lon_variable = deduce_variable_coords(self._file_handler, 'longitude')
        if lon_variable == '':
            # try to find 'X' in file
            lon_variable = deduce_variable_coords(self._file_handler, 'X')
        if lon_variable == '':
            raise KeyError("unable to deduce x-dimension from file")
        lon = self._file_handler.dimensions[lon_variable]

        # get y-dimension from netcdf file
        lat_variable = deduce_variable_coords(self._file_handler, 'latitude')
        if lat_variable == '':
            # try to find 'Y' in file
            lat_variable = deduce_variable_coords(self._file_handler, 'Y')
        if lat_variable == '':
            raise KeyError("unable to deduce y-dimension from file")
        # get dimensions from netcdf file
        lat = self._file_handler.dimensions[lat_variable]

        x_start = ti * tile_size
        x_end = min(min((ti + 1), tx) * tile_size, lon.size)

        if self.invert_y:
            y_start = lat.size - min(min((tj + 1), ty) * tile_size, lat.size)
            y_end = lat.size - tj * tile_size
        else:
            y_start = tj * tile_size
            y_end = min(min((tj + 1), ty) * tile_size, lat.size)

        # Get variable name
        if isinstance(self.raster_name, str):
            var_name = self.raster_name
        elif isinstance(self.raster_name, bytes):
            var_name = self.raster_name.decode()

        var_name = self._variable_map.get(var_name, var_name)

        if var_name not in self.data_vars:
            var_name = self.data_vars[0]

        if var_name in self._file_handler.variables:
            var_shape = self._file_handler.variables[var_name].shape
            var_dims = self._file_handler.variables[var_name].dimensions
        else:
            raise KeyError(
                f"Item {var_name} not in NetCDF variables: {self._file_handler.variables.keys()}")

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Variable {var_name} has dimensions {var_dims} with shape {var_shape}")

        # handle reading 3d Data
        if len(self.layers) > 1:
            # when more than 1 layers to be read
            # here, tidx value is ignored
            z_slice = slice(self.layers[0],
                            self.layers[-1] + 1,
                            self.layers[1] - self.layers[0])
            # set value for axis to be flipped (when invert_y is true, and data is 3d)
            flip_axis = 1
        else:
            if len(var_dims) == 4:
                # when only one layer (spatial layer, stepping in time)
                z_slice = self.layers[0]
            elif len(var_dims) == 3:
                if tidx != self.layers[0]:
                    if tidx == 0:
                        # because there is only one layer in self.layers
                        z_slice = self.layers[tidx]
                    elif tidx > 0 and tidx < var_shape[0]:
                        # this is when tidx is used to step through
                        # the layers
                        z_slice = tidx
                else:
                    # when only one layer (spatial layer, stepping in time)
                    z_slice = self.layers[0]
            # set value for axis to be flipped (when invert_y is true, and data is 2d)
            flip_axis = 0

        xtiles, _ = get_tiles_count(lon.size, lat.size, tile_size)
        tile_idx = ti + tj * xtiles

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"ti: {ti}, tj: {tj}, tile index: {tile_idx}")
            if len(var_dims) >= 3:
                logger.debug(f"z_slice: {z_slice}, tidx: {tidx}, layers: {self.layers}")
            else:
                logger.debug(f"tidx: {tidx}, layers: {self.layers}")

        # Get data
        # Check data dimensions
        if len(var_dims) == 4:
            # read 3D + (time / ensemble) data
            # get the index for ordering dimensions
            dim_index = get_dimension_index(self._dims, var_dims)

            # create initial dimension tuple
            dim_tuple = [z_slice,
                         slice(y_start, y_end),
                         slice(x_start, x_end)]

            # now create a dictionary with indices
            dim_slice = {idx: dim_value for idx,
                         dim_value in zip(dim_index, dim_tuple)}

            # finally add the time index
            for i, _ in enumerate(var_dims):
                if i not in dim_slice:
                    dim_slice[i] = tidx

            # now create a new dimension tuple to read data
            dim_tuple = tuple([dim_slice[i]
                               for i in sorted(dim_slice.keys())])
            temp = self._file_handler.variables[var_name][dim_tuple]
        elif len(var_dims) == 3:
            # read 2D + (time / z) data
            if var_dims[-2:] == tuple(self._dims)[-2:][::-1]:
                # rotate data when oriented time,x,y
                temp = self._file_handler.variables[var_name][z_slice,
                                                              x_start:x_end,
                                                              y_start:y_end]
                temp = np.swapaxes(temp, -1, -2)
            elif var_dims[-2:] == tuple(self._dims)[-2:]:
                # data orientation time,y,x
                temp = self._file_handler.variables[var_name][z_slice,
                                                              y_start:y_end,
                                                              x_start:x_end]
        elif len(var_dims) == 2:
            # read 2D data
            if var_dims == tuple(self._dims)[::-1]:
                # rotate data when oriented x,y
                temp = self._file_handler.variables[var_name][x_start:x_end,
                                                              y_start:y_end]
                temp = np.swapaxes(temp, -1, -2)
            elif var_dims == tuple(self._dims):
                temp = self._file_handler.variables[var_name][y_start:y_end,
                                                              x_start:x_end]
        else:
            raise RuntimeError(
                "Only 2D, 2D + time or 3D + time are currently supported")

        if any(filter(lambda s: s == 1, temp.shape)):
            temp = np.squeeze(temp)

        # Get missing value
        missing_value = None
        if hasattr(self._file_handler.variables[var_name], "missing_value"):
            missing_value = getattr(
                self._file_handler.variables[var_name], "missing_value")
        elif hasattr(self._file_handler.variables[var_name], "_FillValue"):
            missing_value = getattr(
                self._file_handler.variables[var_name], "_FillValue")

        # Fill missing values
        if isinstance(temp, np.ma.MaskedArray):
            temp = np.ma.filled(temp, fill_value=self.nullValue)
        else:
            if missing_value is not None:
                if np.can_cast(missing_value, temp.dtype):
                    try:
                        missing_value = temp.dtype.type(missing_value)
                    except Exception as e:
                        warnings.warn(f"Type Casting Error: {str(e)}", RuntimeWarning)
                else:
                    missing_value = None
            if missing_value is not None:
                temp = np.where(temp == missing_value,
                                self.nullValue, temp)

        # Copy data to buffer
        if temp.ndim == 2:
            zsize = 0
            ysize, xsize = temp.shape
        elif temp.ndim == 3:
            zsize, ysize, xsize = temp.shape
            zsize = slice(zsize)

        # temp = (temp / temp) * tile_idx

        if self.invert_y:
            buf_arr[zsize, :ysize, :xsize] = np.flip(
                temp, axis=flip_axis).astype(self.data_type)
            return buf_arr, ti, (ty - tj)
        else:
            buf_arr[zsize, :ysize, :xsize] = temp.astype(self.data_type)
            return buf_arr, ti, tj

    def close(self):
        if hasattr(self, '_file_handler'):
            if not self.is_thredds and not self.use_pydap and not self._file_handler is None:
                if self._file_handler.isopen():
                    self._file_handler.close()

    @supported_libs.RequireLib("netcdf")
    def __exit__(self, *args):
        if hasattr(self, '_file_handler'):
            if self._file_handler is not None:
                self.close()

    def __del__(self, *args, **kwargs):
        self.close()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


class GDAL_Handler(DataHandler):

    def __init__(self, fileName=None, base_type: np.dtype = core.REAL,
                 data_type: np.dtype = core.REAL,
                 raster_name: str = ""):
        # if the filename is a path to a file, ensure it's an absolute path
        # doesn't check for a valid extension as gdal supports an extensive
        # list of file types
        if fileName is not None:
            if isinstance(fileName, str):
                if pth.exists(fileName) and not utils.is_remote_uri(fileName):
                    fileName = pth.abspath(fileName)
        self._file_name = fileName
        self._file_handler = None
        self.is_thredds = False
        self.use_pydap = False
        self.invert_y = False
        self.data_type = data_type
        self.base_type = base_type
        self.nullValue = raster.getNullValue(data_type)
        self.layers = []
        self.raster_name = raster_name
        self.geotiff_tags = {}

    @property
    def file_info(self) -> Dict:
        return self.get_file_info()

    @supported_libs.RequireLib("gdal")
    def get_file_info(self, *args, **kwargs) -> Dict:
        out = {"filename": "", "dimensions": [], "variables": []}
        if self._file_handler is None:
            self.open_file(*args, **kwargs)

        if self._file_handler is not None:
            try:
                out['filename'] = self._file_handler.GetDescription()
            except Exception as e:
                pass

            raster_count = self._file_handler.RasterCount
            # add raster dimensions
            out['dimensions'].append({"name": raster_count, "size": raster_count})
            out['dimensions'].append({"name": "xsize", "size":self._file_handler.RasterXSize})
            out['dimensions'].append({"name": "ysize", "size":self._file_handler.RasterYSize})

            # check if raster has sub-datasets
            sub_dataset = self._file_handler.GetSubDatasets()
            if len(sub_dataset) > 0:
                # get the sub-datasets info
                for item in sub_dataset:
                    out['variables'].append({"name": item[0]})
        return out

    @property
    def data_vars(self) -> List[str]:
        """data variables as property

        Returns
        -------
        List[str]
            a list of string
        """
        return self.get_data_variables()

    @supported_libs.RequireLib("gdal")
    def get_data_vars(self) -> List[str]:
        out = []
        if len(self.file_info['variables']) > 0:
            out = [item['name'] for item in self.file_info['variables']]
        return out

    def open_file(self, *args, **kwargs):
        if args:
            if isinstance(args[0], bool):
                self.is_thredds = args[0]
        elif kwargs:
            if 'thredds' in kwargs:
                self.is_thredds = kwargs['thredds']

        if self._file_name is None:
            raise ValueError("file_name cannot be None")

        if isinstance(self._file_name, str):
            # patch file path (when needed) for gdal virtual file system
            if self.is_thredds:
                if 'vsicurl' not in self._file_name:
                    self._file_name = f"/vsicurl/{self._file_name}"
                    if self._file_name.endswith('tar') or self._file_name.endswith('tgz'):
                        raise ValueError(
                            "Compressed archives require full path in the archive")
            else:
                if 'vsicurl' in self._file_name:
                    self.is_thredds = True
            self._file_handler = gdal.Open(self._file_name)
        elif isinstance(self._file_name, gdal.Dataset):
            # assign to file_handler, when file_name is gdal.Dataset
            self._file_handler = self._file_name
            # change file_name to path of file
            self._file_name = self._file_name.GetDescription()

    @supported_libs.RequireLib("gdal")
    def reader(self, *args, **kwargs):
        # open file
        self.open_file(*args, **kwargs)

        # checks if gdal managed to open file
        # handles cases where the file extension is not supported by gdal
        if self._file_handler is None or isinstance(self._file_handler, str):
            raise ValueError(f"Unable to open file {self._file_name}")

        # get geotransform
        geotransform = self._file_handler.GetGeoTransform()

        # get gdal driver and the geotiff tags
        driver = self._file_handler.GetDriver()
        if driver.GetDescription() == 'GTiff':
            self.geotiff_tags = get_geotiff_tags(self._file_handler)

        # get projection wkt string as proj4 string
        if kwargs.get("read_projection") is not None:
            if kwargs.get('read_projection'):
                try:
                    projStr = return_proj4(self._file_handler.GetDescription())
                except AttributeError:
                    projStr = return_proj4(self._file_handler)
            else:
                projStr = ""
        else:
            try:
                projStr = return_proj4(self._file_handler.GetDescription())
            except AttributeError:
                projStr = return_proj4(self._file_handler)

        nx = self._file_handler.RasterXSize
        ny = self._file_handler.RasterYSize

        if geotransform[5] < 0:
            self.invert_y = True
        else:
            self.invert_y = False

        # Dummy time variable
        time = self.time(None)

        raster_count = self._file_handler.RasterCount
        if not raster_count > 0:
            sub_dataset = self._file_handler.GetSubDatasets()
            if not len(sub_dataset) > 0:
                raise RuntimeError("No raster band or SubDataset found")

        self.layers = get_layers(kwargs.get("layers", -1), raster_count)
        # add 1 as bands in gdal starts from 1
        self.layers = [i + 1 for i in self.layers]

        nz = len(self.layers)
        hx = geotransform[1]
        hy = abs(geotransform[5])
        hz = 1
        ox = geotransform[0]
        oy = geotransform[3]

        if self.invert_y:
            oy += ny * geotransform[5]
        oz = 0.0

        return nx, ny, nz, hx, hy, hz, ox, oy, oz, core.str2bytes(projStr), time

    def writer(self, fileName: str, jsonConfig: Union[str, Dict]):
        writer_config = json.loads(jsonConfig)
        raise NotImplementedError("writer not yet implemented")

    @staticmethod
    def compute_bounds(ti: int, tj: int, nx: int,
                       ny: int, tileSize: int,
                       tx: numbers.Integral,
                       ty: numbers.Integral,
                       invert_y: bool = True) -> Tuple[float, float, int, int]:

        xoff = min(ti * tileSize, nx)
        xsize = min(min(ti + 1, tx) * tileSize, nx) - xoff

        if invert_y:
            y_start = ny - min(min((tj + 1), ty) * tileSize, ny)
            y_end = ny - min(tj * tileSize, ny)
        else:
            y_start = tj * tileSize
            y_end = min(min((tj + 1), ty) * tileSize, ny)

        yoff = min(y_start, y_end)
        ysize = abs(y_start - y_end)

        return xoff, yoff, xsize, ysize

    @supported_libs.RequireLib("gdal")
    def check_handler(self):
        if not isinstance(self, GDAL_Handler):
            raise TypeError("Unable to understand the input class instance")

        if self._file_handler is None:
            raise ValueError("file_handler could not be located")

        if not isinstance(self._file_handler, gdal.Dataset):
            raise TypeError("file_handler is not an instance of gdal.Dataset")

        if self._file_handler.GetDescription() != self._file_name:
            if self._file_name not in self._file_handler.GetDescription():
                raise ValueError(
                    "Mismatch between file_name and description of file in gdal.Dataset")

    @supported_libs.RequireLib("gdal")
    def setter(self, ti: numbers.Integral, tj: numbers.Integral,
               tx: numbers.Integral, ty: numbers.Integral,
               tidx: int, *args, **kwargs) -> Tuple[np.ndarray, int, int]:

        if self._file_handler is None:
            raise RuntimeError("file handler is closed")

        byteorders = {"little": "<", "big": ">"}
        array_modes = {gdalconst.GDT_Int16: ("%si2" % byteorders[sys.byteorder]),
                       gdalconst.GDT_UInt16: ("%su2" % byteorders[sys.byteorder]),
                       gdalconst.GDT_Int32: ("%si4" % byteorders[sys.byteorder]),
                       gdalconst.GDT_UInt32: ("%su4" % byteorders[sys.byteorder]),
                       gdalconst.GDT_Float32: ("%sf4" % byteorders[sys.byteorder]),
                       gdalconst.GDT_Float64: ("%sf8" % byteorders[sys.byteorder]),
                       gdalconst.GDT_CFloat32: ("%sf4" % byteorders[sys.byteorder]),
                       gdalconst.GDT_CFloat64: ("%sf8" % byteorders[sys.byteorder]),
                       gdalconst.GDT_Byte: ("%sb" % byteorders[sys.byteorder])}

        # raster_index ignored as all data is read

        # Check handler
        self.check_handler()

        # Get type of band 1
        raster_band = self._file_handler.GetRasterBand(1)
        gdal_to_npy = dataset.gdal_dtype_to_numpy(raster_band.DataType)

        # Get missing value
        missing_value = raster_band.GetNoDataValue()
        if missing_value is not None:
            try:
                if not raster_band.DataType < 6:
                    missing_value = gdal_to_npy(missing_value)
                else:
                    if (missing_value - gdal_to_npy(missing_value)) == 0:
                        missing_value = gdal_to_npy(missing_value)
                    else:
                        missing_value = None
            except Exception as _:
                warnings.warn(f"WARNING: GDAL missing value '{missing_value}'" +
                              f" cannot be converted to {gdal_to_npy.__name__}", RuntimeWarning)
                missing_value = None

        # Map or upgrade gdal data to Raster type
        if gdal_to_npy not in [np.float32, np.float64, np.uint32, np.uint8]:
            _temp_type = GDAL_Handler.data_type_compliance(gdal_to_npy)
        else:
            _temp_type = gdal_to_npy

        if _temp_type != self.data_type:
            _temp_type = self.data_type
            # raise TypeError("Mismatch between data type of raster band and class instance")

        # Create empty buffer
        tile_size = raster.TileSpecifications().tileSize
        buf_arr = np.full((len(self.layers), tile_size, tile_size),
                          self.nullValue, dtype=self.data_type)

        # get geotransform
        geotransform = self._file_handler.GetGeoTransform()
        driver = self._file_handler.GetDriver().GetDescription()

        xoff, yoff, xsize, ysize = GDAL_Handler.compute_bounds(ti, tj,
                                                               self._file_handler.RasterXSize,
                                                               self._file_handler.RasterYSize,
                                                               tile_size, tx, ty,
                                                               invert_y=self.invert_y)

        # Get data bounds
        # if self.invert_y:
        #     xoff, yoff, xsize, ysize = GDAL_Handler.compute_bounds(ti, tj,
        #                                                            self._file_handler.RasterXSize,
        #                                                            self._file_handler.RasterYSize,
        #                                                            tile_size)
        # else:
        #     if (driver == 'GTiff' and
        #         geotransform[5] > 0 and
        #         TIFFTAG_GEOTRANSMATRIX in self.geotiff_tags):
        #         # this is when Geotiff hy >= 0, and GEOTRANSMATRIX is defined in geotiff tags
        #         xoff, yoff, xsize, ysize = GDAL_Handler.compute_bounds(ti, ty-tj-1,
        #                                                                self._file_handler.RasterXSize,
        #                                                                self._file_handler.RasterYSize,
        #                                                                tile_size)
        #     else:
        #         xoff, yoff, xsize, ysize = GDAL_Handler.compute_bounds(ti, ty,
        #                                                                self._file_handler.RasterXSize,
        #                                                                self._file_handler.RasterYSize,
        #                                                                tile_size)
        # Read tile from data set
        temp = np.empty(shape=(ysize, xsize), dtype=gdal_to_npy)
        for idx, k in enumerate(self.layers, 0):
            raster_band = self._file_handler.GetRasterBand(k)
            # Read data
            gdal_array.BandRasterIONumPy(raster_band, 0, xoff,
                                         yoff, xsize, ysize, temp,
                                         raster_band.DataType,
                                         gdal.GRA_NearestNeighbour)

            # Check and patch nodata
            if missing_value is not None:
                temp = np.where(temp == missing_value, self.nullValue, temp)

            # Copy data to buffer
            ysize, xsize = temp.shape
            if self.invert_y:
                buf_arr[idx, :ysize, :xsize] = np.flipud(temp[:, :]).astype(_temp_type)
            else:
                buf_arr[idx, :ysize, :xsize] = temp[:, :].astype(_temp_type)

        del temp
        del raster_band
        return buf_arr, ti, tj

    def time(self, *args):
        return 0.0

    @staticmethod
    def data_type_compliance(input_type: np.dtype) -> np.dtype:
        if input_type in [np.uint16]:
            return np.uint32
        elif input_type in [np.int16, np.int32]:
            return np.float32
        else:
            raise TypeError("No mapping for input data type")

    def close(self, *args, **kwargs):
        if hasattr(self, '_file_handler'):
            if isinstance(self._file_handler, gdal.Dataset):
                del self._file_handler
                self._file_handler = None

    @supported_libs.RequireLib("gdal")
    def __exit__(self, *args):
        if hasattr(self, '_file_handler'):
            if self._file_handler is not None:
                self.close()

    def __del__(self, *args, **kwargs):
        self.close()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


class XR_Handler(DataHandler):

    def __init__(self, fileName: Optional[Union[Any, str]] = None,
                 base_type: np.dtype = core.REAL,
                 variable_map: Optional[Dict] = None,
                 data_type: np.dtype = core.REAL,
                 raster_name: str = ""):
        # if the filename is a file, ensure it's an absolute path
        if fileName is not None:
            if isinstance(fileName, str) and not utils.is_remote_uri(fileName):
                fileName = pth.abspath(
                    fileName) if pth.exists(fileName) else None
        self._file_name = fileName
        self._file_handler = None
        self._time_handler = None
        self.is_thredds = False
        self.use_pydap = False
        self.invert_y = False
        self.data_type = data_type
        self.base_type = base_type
        self.nullValue = raster.getNullValue(data_type)
        self._variable_map = variable_map
        self._dims = deque()
        self.layers = [0]
        self.raster_name = raster_name

    def clear(self):
        """clear dimensions and layers from instantiated object
        """
        self._dims.clear()
        self.layers = [0]

    @property
    def file_info(self) -> Dict:
        return self.get_file_info()

    @supported_libs.RequireLib("xarray")
    def get_file_info(self, *args, **kwargs) -> Dict:
        """get the information about the file contents

        Returns
        -------
        Dict
            a dictionary with file name, dimensions and variables
        """
        out = {"filename": "", "dimensions": [], "variables": []}

        if self._file_handler is None:
            # open file is not opened yet
            self.open_file()

        if self._file_handler is not None:
            if self._file_name is not None:
                if isinstance(self._file_name, str):
                    out['filename'] = self._file_name
            if isinstance(self._file_handler, xr.DataArray):
                # handle case when object is xarray DataArray
                for item in self._file_handler.coords:
                    out['dimensions'].append({"name": item,
                                              "size": self._file_handler.coords[item].size})
                var_info = {'name': self._file_handler.name,
                            "dimensions": self._file_handler.dims,
                            "attrs": self._file_handler.attrs,
                            "dtype": self._file_handler.dtype}
                out['variables'].append(var_info)
                global_attrs = {}
            elif isinstance(self._file_handler, xr.Dataset):
                # handle case when object is xarray Dataset
                for item in self._file_handler.dims:
                    out['dimensions'].append({"name": item,
                                              "size": self._file_handler.dims[item]})
                for item in self._file_handler.data_vars:
                    var_info = {"name": item,
                                "dimensions": self._file_handler.variables[item].dims,
                                "dtype": self._file_handler.variables[item].dtype,
                                "attrs": self._file_handler.variables[item].attrs}
                    out['variables'].append(var_info)
                    global_attrs = self._file_handler.attrs.copy()
            # add global attributes
            out['global_attrs'] = global_attrs
        return out

    @supported_libs.RequireLib("xarray")
    def open_file(self, *args, **kwargs):
        # open file without decoding time
        if isinstance(self._file_name, str):
            self._file_handler = xr.open_dataset(self._file_name,
                                                 decode_cf=False,
                                                 decode_times=False,
                                                 engine="netcdf4",
                                                 decode_coords={"grid_mapping": "all"})
        elif isinstance(self._file_name, bytes):
            self._file_handler = xr.open_dataset(self._file_name.decode(),
                                                 decode_cf=False,
                                                 decode_times=False,
                                                 engine="netcdf4",
                                                 decode_coords={"grid_mapping": "all"})
        elif isinstance(self._file_name, list):
            _file_list = [item.decode() if isinstance(item, bytes) else item
                          for item in self._file_name]
            if len(_file_list) > 1:
                self._file_handler = xr.open_mfdataset(_file_list,
                                                       engine="netcdf4",
                                                       decode_coords={"grid_mapping": "all"},
                                                       combine="by_coords",)
            else:
                self._file_handler = xr.open_dataset(_file_list[0],
                                                     engine="netcdf4",
                                                     decode_coords={"grid_mapping": "all"})

        if isinstance(self._file_name, (xr.Dataset, xr.DataArray)):
            # assign file_name to file_handler when input is xr.Dataset
            self._file_handler = self._file_name
            # change file name to path of file
            try:
                source_file = self._file_handler._file_obj._filename
            except AttributeError:
                try:
                    source_file = self._file_handler.encoding['source']
                except Exception:
                    source_file = ""

            self._file_name = source_file

        if self._file_handler is None:
            raise ValueError("file_handler cannot be identified")

    @property
    def data_vars(self) -> List[str]:
        """data variables as property

        Returns
        -------
        List[str]
            a list of string
        """
        return self.get_data_variables()

    @supported_libs.RequireLib("xarray")
    def get_data_variables(self) -> List[str]:
        """get name of data variables

        Returns
        -------
        list
            a list of string
        """
        var_names = [item['name'] for item in self.file_info['variables']]
        dim_names = [item['name'] for item in self.file_info['dimensions']]

        scalar_vars = []
        for item in var_names:
            if isinstance(self._file_handler, xr.Dataset):
                if not len(self._file_handler.data_vars[item].dims) > 0:
                    scalar_vars.append(item)

        var_list = list(set(var_names).difference(dim_names).difference(scalar_vars))
        if not len(var_list) > 0:
            raise RuntimeError("No data variables found")
        return var_list

    def has_mapping(self, varname: str) -> bool:
        """check if file variable has been mapped

        Parameters
        ----------
        varname : str
            name of the variable in file

        Returns
        -------
        bool
            True is file variable is mapped, False otherwise
        """
        return varname in self._variable_map.values()

    def update_variable_map(self, varname: str):
        """update variable map, mapping file variable to raster name

        Parameters
        ----------
        varname : str
            name of the variable in file
        """
        if not self.has_mapping(varname):
            self._variable_map.update({self.raster_name: varname})

    @supported_libs.RequireLib("xarray")
    def reader(self, thredds: bool = False,
               use_pydap: bool = False, **kwargs) -> Tuple:
        self.clear()
        # set thredds flag when provided
        self.is_thredds = thredds

        # open file if not yet opened
        if self._file_handler is None:
            self.open_file()

        if self._file_name is None:
            raise ValueError("file_name cannot be None")

        # get projection information from the file if available
        projStr = ""
        if hasattr(self._file_handler, "variables"):
            # only valid for xr.Dataset
            if 'crs' in self._file_handler.variables:
                if hasattr(self._file_handler.variables['crs'], "crs_wkt"):
                    projStr = utils.proj4_from_wkt(
                        self._file_handler.variables['crs'].crs_wkt)
                elif hasattr(self._file_handler.variables['crs'], "spatial_ref"):
                    projStr = utils.proj4_from_wkt(
                        self._file_handler.variables['crs'].getncattr("spatial_ref"))

        # get the time variable
        time_variable = deduce_variable_coords(self._file_handler, "time")
        if time_variable != "":
            self._time_handler = RasterTime(
                getattr(self._file_handler, time_variable))
            self._time_handler.set_time_bounds()

        if VERBOSITY_LEVEL() <= logging.DEBUG and time_variable != '':
            logger.debug(f"Using {time_variable} as time variable")

        # get x-dimension from netcdf file
        lon_variable = deduce_variable_coords(self._file_handler, 'longitude')
        if lon_variable != '':
            if isinstance(self._file_handler, xr.Dataset):
                if lon_variable not in self._file_handler.dims:
                    lon_variable = ''
            elif isinstance(self._file_handler, xr.DataArray):
                if lon_variable not in self._file_handler.coords:
                    lon_variable = ''

        if lon_variable == '':
            # try to find 'X' in file
            lon_variable = deduce_variable_coords(self._file_handler, 'X')

        if lon_variable == '':
            raise KeyError("unable to deduce x-dimension from file")

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {lon_variable} as x dimension")

        lon = self._file_handler[lon_variable]
        if isinstance(self._file_handler, xr.Dataset):
            nx = self._file_handler.dims[lon_variable]
        elif isinstance(self._file_handler, xr.DataArray):
            nx = self._file_handler.coords[lon_variable].size
        self._dims.append(lon_variable)

        # get y-dimension from netcdf file
        lat_variable = deduce_variable_coords(self._file_handler, 'latitude')
        if lat_variable != '':
            if isinstance(self._file_handler, xr.Dataset):
                if lat_variable not in self._file_handler.dims:
                    lat_variable = ''
            elif isinstance(self._file_handler, xr.DataArray):
                if lat_variable not in self._file_handler.coords:
                    lat_variable = ''
        if lat_variable == '':
            # try to find 'Y' in file
            lat_variable = deduce_variable_coords(self._file_handler, 'Y')
        if lat_variable == '':
            raise KeyError("unable to deduce y-dimension from file")

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {lat_variable} as y dimension")

        # get dimensions from netcdf file
        lat = self._file_handler[lat_variable]
        if isinstance(self._file_handler, xr.Dataset):
            ny = self._file_handler.dims[lat_variable]
        elif isinstance(self._file_handler, xr.DataArray):
            ny = self._file_handler.coords[lat_variable].size
        self._dims.appendleft(lat_variable)

        # Get variable name
        if isinstance(self.raster_name, str):
            var_name = self.raster_name
        elif isinstance(self.raster_name, bytes):
            var_name = self.raster_name.decode()
        var_name = self._variable_map.get(var_name, var_name)

        if var_name not in self.data_vars:
            warnings.warn(f"Variable name `{var_name}` is not valid, will use {self.data_vars[0]}", RuntimeWarning)
            var_name = self.data_vars[0]

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Using {var_name} as variable for Raster object")

        # add support for third dimension
        # get the third dimension to map
        var_dims = kwargs.get("dims")
        if var_dims is None:
            # get variable dimensions
            if isinstance(self._file_handler, xr.Dataset):
                var_dims = self._file_handler.data_vars[var_name].dims
            elif isinstance(self._file_handler, xr.DataArray):
                var_dims = self._file_handler.dims
            filter_dims = filter(lambda s: s not in [lat_variable, lon_variable],
                                 var_dims[::-1])
            try:
                layer_dim_name = next(filter_dims)
            except StopIteration:
                layer_dim_name = "time"
        else:
            layer_dim_name = "time"
            current_size = len(self._dims)
            if not isinstance(var_dims, (tuple, list)):
                if len(var_dims) < current_size:
                    raise ValueError(
                        f"Dimension tuple {var_dims} should be atleast {tuple(self._dims)}")
                else:
                    raise TypeError(
                        f"Dimensions iterable {var_dims} should be a tuple or list")

            invalid_dims = []
            for i in range(current_size):
                offset = len(layer_dim_name) - current_size
                if layer_dim_name[i + offset] != self._dims[i]:
                    invalid_dims.append(layer_dim_name[i + offset])
            if len(invalid_dims) > 0 and current_size == len(layer_dim_name):
                raise ValueError(
                    f"Dimension tuple {layer_dim_name} is not valid")

            if len(var_dims) != current_size:
                for item in var_dims:
                    if item not in self._dims:
                        self._dims.appendleft(item)
                if len(self._dims) > current_size:
                    layer_dim_name = list(islice(self._dims, 0, current_size - 1))[-1]
                else:
                    layer_dim_name = "time"

        layer_dim_size = 1
        if any(map(lambda s: s['name'] == layer_dim_name, self.file_info['dimensions'])):
            if isinstance(self._file_handler, xr.Dataset):
                layer_dim_size = self._file_handler.dims.get(layer_dim_name)
            elif isinstance(self._file_handler, xr.DataArray):
                layer_dim_size = self._file_handler.coords.get(layer_dim_name).size

            if layer_dim_size is None:
                layer_dim_size = 1

        self.layers = get_layers(kwargs.get("layers", -1), layer_dim_size)
        self.layers = sorted(self.layers)

        time_is_zlayer = False
        if var_dims is not None:
            ndim = len(var_dims)
            time_is_zlayer = any(map(lambda s: s == time_variable, var_dims))
        else:
            ndim = len(self._dims)
            time_is_zlayer = any(map(lambda s: s == time_variable, self._dims))

        if ndim > 2:
            nz = len(self.layers)
            oz = self.base_type(self.layers[0])
            # if time_variable != '':
            #     if time_is_zlayer and len(self.layers) > 1:
            #         self._time_handler.set_index_bounds(
            #             start_idx=min(self.layers),
            #             end_idx=max(self.layers))
        else:
            nz = 1
            oz = 0.0
            self.layers = [0]

        # Set time origin
        if time_variable != '':
            # use RasterTime when z-dimension is time
            oz = 0.0
            hz = 1.0
            if time_is_zlayer:
                oz = self.base_type(self.time_from_index(self.layers[0]))
                if len(self.layers) > 1:
                    # subtract 1 from total layer number (zero based indexing)
                    upper_limit = min(self.layers[-1] + 1, layer_dim_size - 1)
                    z1 = self.base_type(self.time_from_index(upper_limit))
                    hz = (z1 - oz) / len(self.layers)
                else:
                    # substract 1 from total layer number (zero based indexing)
                    upper_limit = min(self.layers[0], layer_dim_size - 1)
                    z1 = self.base_type(self.time_from_index(upper_limit))
                    hz = z1 - oz
        else:
            # when z-dimension other than time
            if nz >= 1:
                try:
                    z0 = self._file_handler[layer_dim_name][self.layers[0]]
                    z1 = self._file_handler[layer_dim_name][self.layers[1]]
                    hz = (z1 - z0)
                except Exception:
                    if nz == 1:
                        hz = 1
                    else:
                        hz = self.layers[1] - self.layers[0]
            else:
                hz = 1

        time = self.time(0)
        # compute dimension input for instantiating raster.Raster
        hx = self.base_type(lon[1] - lon[0])
        hy = self.base_type(lat[1] - lat[0])

        min_x = min(lon.values[0], lon.values[-1])
        if isinstance(min_x, np.ma.MaskedArray):
            ox = self.base_type(min.data)
        elif isinstance(min_x, np.ndarray):
            ox = self.base_type(min_x)
        elif isinstance(min_x, numbers.Real):
            ox = self.base_type(min_x)

        ox -= 0.5 * hx

        min_y = min(lat.values[0], lat.values[-1])
        if isinstance(min_y, np.ndarray):
            oy = self.base_type(min_y)
        elif isinstance(min_y, np.ma.MaskedArray):
            oy = self.base_type(min_y.data)
        elif isinstance(min_y, numbers.Real):
            oy = self.base_type(min_y)

        if hy < 0:
            self.invert_y = True
            hy = abs(hy)
        oy -= 0.5 * hy

        return nx, ny, nz, hx, hy, hz, ox, oy, oz, core.str2bytes(projStr), time

    def time(self, tidx: numbers.Integral) -> numbers.Real:
        self.check_handler()
        time = 0.0
        if self._time_handler is not None:
            time = self.time_from_index(tidx)
        return time

    def set_time_bounds(self, start_time: Union[numbers.Real, str],
                        end_time: Union[numbers.Real, str],
                        dt_format: Optional[str] = None):
        if self._time_handler is not None:
            self._time_handler.set_bounds(start_time, end_time)
        else:
            raise RuntimeError("No time handle has been set")

    def time_from_index(self, index: numbers.Integral) -> numbers.Real:
        if self._time_handler is not None:
            return self._time_handler.time_from_index(index)
        else:
            raise RuntimeError("No time handle has been set")

    def index_from_time(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_max_time_index(self):
        if self._time_handler is not None:
            return self._time_handler.get_max_time_index()
        else:
            raise RuntimeError("No time handle has been set")

    def get_left_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_left_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_right_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        if self._time_handler is not None:
            return self._time_handler.get_right_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    @supported_libs.RequireLib("xarray")
    def writer(self, jsonConfig: Union[Dict, str]):
        # writer_config = json.loads(jsonConfig)
        raise NotImplementedError("writer not yet implemented")

    @supported_libs.RequireLib("xarray")
    def check_handler(self):
        if not isinstance(self, XR_Handler):
            raise TypeError("Unable to understand the input class instance")

        if self._file_handler is None:
            raise ValueError("file_handler cannot be identified")

        if not isinstance(self._file_handler, (xr.Dataset, xr.DataArray)):
            raise TypeError("file_handler is of incorrect type")

        try:
            source_file = self._file_handler._file_obj._filename
        except AttributeError:
            try:
                source_file = self._file_handler.encoding['source']
            except Exception:
                source_file = ""

        if source_file != self._file_name and not isinstance(self._file_name, list):
            raise ValueError("Mismatch between filepath and filename")

    @supported_libs.RequireLib("xarray")
    def setter(self, ti: numbers.Integral, tj: numbers.Integral,
               tx: numbers.Integral, ty: numbers.Integral,
               tidx: int, *args, **kwargs) -> Tuple[np.ndarray, int, int]:
        # Check handler
        self.check_handler()

        # Create empty buffer
        tile_size = raster.TileSpecifications().tileSize
        buf_arr = np.full((len(self.layers), tile_size, tile_size), self.nullValue,
                          dtype=self.data_type)

        # get x-dimension from netcdf file
        lon_variable = deduce_variable_coords(self._file_handler, 'longitude')
        # fix for case when coordinates are in projected space
        if lon_variable != '':
            if isinstance(self._file_handler, xr.Dataset):
                if lon_variable not in self._file_handler.dims:
                    lon_variable = ''
            elif isinstance(self._file_handler, xr.DataArray):
                if lon_variable not in self._file_handler.coords:
                    lon_variable = ''
        if lon_variable == '':
            # try to find 'X' in file
            lon_variable = deduce_variable_coords(self._file_handler, 'X')
        if lon_variable == '':
            raise KeyError("unable to deduce x-dimension from file")
        if isinstance(self._file_handler, xr.DataArray):
            lon = self._file_handler[lon_variable].size
        elif isinstance(self._file_handler, xr.Dataset):
            lon = self._file_handler.dims[lon_variable]

        # get y-dimension from netcdf file
        lat_variable = deduce_variable_coords(self._file_handler, 'latitude')
        if lat_variable != '':
            if isinstance(self._file_handler, xr.Dataset):
                if lat_variable not in self._file_handler.dims:
                    lat_variable = ''
            elif isinstance(self._file_handler, xr.DataArray):
                if lat_variable not in self._file_handler.coords:
                    lat_variable = ''
        if lat_variable == '':
            # try to find 'Y' in file
            lat_variable = deduce_variable_coords(self._file_handler, 'Y')
        if lat_variable == '':
            raise KeyError("unable to deduce y-dimension from file")
        # get dimensions from netcdf file
        if isinstance(self._file_handler, xr.Dataset):
            lat = self._file_handler.dims[lat_variable]
        elif isinstance(self._file_handler, xr.DataArray):
            lat = self._file_handler[lat_variable].size

        x_start = ti * tile_size
        x_end = min(min((ti + 1), tx) * tile_size, lon)

        if self.invert_y:
            y_start = lat - min(min((tj + 1), ty) * tile_size, lat)
            y_end = lat - tj * tile_size
        else:
            y_start = tj * tile_size
            y_end = min(min((tj + 1), ty) * tile_size, lat)

        # Get variable name
        if isinstance(self.raster_name, str):
            var_name = self.raster_name
        elif isinstance(self.raster_name, bytes):
            var_name = self.raster_name.decode()

        var_name = self._variable_map.get(var_name, var_name)

        if var_name not in self.data_vars:
            var_name = self.data_vars[0]

        # Get data
        if isinstance(self._file_handler, xr.Dataset):
            if var_name not in self._file_handler.data_vars:
                raise KeyError(f"{var_name} is not present in file object")
            var_shape = self._file_handler.data_vars[var_name].shape
            var_dims = self._file_handler.data_vars[var_name].dims
        elif isinstance(self._file_handler, xr.DataArray):
            var_shape = self._file_handler.shape
            var_dims = self._file_handler.dims

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"Variable {var_name} has dimensions {var_dims} with shape {var_shape}")

        # handle reading 3d Data
        if len(self.layers) > 1:
            # when more than 1 layers to be read
            # here, tidx value is ignored
            z_slice = slice(self.layers[0],
                            self.layers[-1] + 1,
                            self.layers[1] - self.layers[0])
            flip_axis = 1
        else:
            if len(var_dims) == 4:
                # when only one layer (spatial layer, stepping in time)
                z_slice = self.layers[0]
            elif len(var_dims) == 3:
                if tidx != self.layers[0]:
                    if tidx == 0:
                        # because there is only one layer in self.layers
                        z_slice = self.layers[tidx]
                    elif tidx > 0 and tidx < var_shape[0]:
                        # this is when tidx is used to step through
                        # the layers
                        z_slice = tidx
                else:
                    # when only one layer (spatial layer, stepping in time)
                    z_slice = self.layers[0]
            flip_axis = 0

        xtiles, _ = get_tiles_count(lon, lat, tile_size)
        tile_idx = ti + tj * xtiles

        if VERBOSITY_LEVEL() <= logging.DEBUG:
            logger.debug(f"ti: {ti}, tj: {tj}, tile index: {tile_idx}")
            if len(var_dims) >= 3:
                logger.debug(f"z_slice: {z_slice}, tidx: {tidx}, layers: {self.layers}")
            else:
                logger.debug(f"tidx: {tidx}, layers: {self.layers}")

        # Check dimensions
        if len(var_dims) == 4:
            # 3D + (time / ensemble) data
            # get the index for ordering dimensions
            dim_index = get_dimension_index(self._dims, var_dims)

            # create initial dimension tuple
            dim_tuple = [z_slice, slice(
                y_start, y_end), slice(x_start, x_end)]

            # now create a dictionary with indices
            dim_slice = {idx: dim_value for idx,
                         dim_value in zip(dim_index, dim_tuple)}

            # finally add the time index
            for i, _ in enumerate(var_dims):
                if i not in dim_slice:
                    dim_slice[i] = tidx
            # now create a new dimension tuple to read data
            dim_tuple = tuple([dim_slice[i]
                               for i in sorted(dim_slice.keys())])
            if isinstance(self._file_handler, xr.DataArray):
                temp = self._file_handler[dim_tuple].to_masked_array()
            elif isinstance(self._file_handler, xr.Dataset):
                temp = self._file_handler.data_vars[var_name][dim_tuple].to_masked_array(
                )
        elif len(var_dims) == 3:
            # 2D + (time / z) data
            if var_dims[-2:] == tuple(self._dims)[-2:][::-1]:
                # orientation time,x,y
                if isinstance(self._file_handler, xr.Dataset):
                    temp = self._file_handler.data_vars[var_name][z_slice,
                                                                  x_start:x_end,
                                                                  y_start:y_end].to_masked_array()
                elif isinstance(self._file_handler, xr.DataArray):
                    temp = self._file_handler[z_slice,
                                              x_start:x_end,
                                              y_start:y_end].to_masked_array()
                temp = np.swapaxes(temp, -1, -2)
            elif var_dims[-2:] == tuple(self._dims)[-2:]:
                # orientation time,y,x
                if isinstance(self._file_handler, xr.Dataset):
                    temp = self._file_handler.data_vars[var_name][z_slice,
                                                                  y_start:y_end,
                                                                  x_start:x_end].to_masked_array()
                elif isinstance(self._file_handler, xr.DataArray):
                    temp = self._file_handler[z_slice,
                                              y_start:y_end,
                                              x_start:x_end].to_masked_array()
        elif len(var_dims) == 2:
            if var_dims == tuple(self._dims)[::-1]:
                if isinstance(self._file_handler, xr.DataArray):
                    temp = self._file_handler[x_start:x_end,
                                              y_start:y_end].to_masked_array()
                elif isinstance(self._file_handler, xr.Dataset):
                    temp = self._file_handler.data_vars[var_name][x_start:x_end,
                                                                  y_start:y_end].to_masked_array()
                temp = np.swapaxes(temp, -1, -2)
            elif var_dims == tuple(self._dims):
                if isinstance(self._file_handler, xr.Dataset):
                    temp = self._file_handler.data_vars[var_name][y_start:y_end,
                                                                  x_start:x_end].to_masked_array()
                elif isinstance(self._file_handler, xr.DataArray):
                    temp = self._file_handler[y_start:y_end,
                                              x_start:x_end].to_masked_array()
        else:
            raise RuntimeError(
                "Only 2D, 2D + time and 3D + time is currently supported")

        if any(filter(lambda s: s == 1, temp.shape)):
            temp = np.squeeze(temp)
        # Patch data
        temp = np.ma.filled(temp, fill_value=self.nullValue)

        # Copy data to buffer
        if temp.ndim == 2:
            zsize = 0
            ysize, xsize = temp.shape
        elif temp.ndim == 3:
            zsize, ysize, xsize = temp.shape
            zsize = slice(zsize)

        if self.invert_y:
            buf_arr[zsize, :ysize, :xsize] = np.flip(
                temp, axis=flip_axis).astype(self.data_type)
            return buf_arr, ti, (ty - tj)
        else:
            buf_arr[zsize, :ysize, :xsize] = temp.astype(self.data_type)
            return buf_arr, ti, tj

    def close(self):
        if hasattr(self, '_file_handler'):
            if self._file_handler is None:
                return
            if not self.is_thredds and not self.use_pydap:
                try:
                    self._file_handler.close()
                except:
                    pass

    def __del__(self, *args, **kwargs):
        self.close()

    @supported_libs.RequireLib("xarray")
    def __exit__(self, *args):
        if self._file_handler is not None:
            self.close()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


class RIO_Handler(DataHandler):

    def __init__(self, fileName=None, base_type: np.dtype = core.REAL,
                 data_type: np.dtype = core.REAL,
                 raster_name: str = ""):
        # if the filename is a file, ensure it's an absolute path
        if fileName is not None:
            if isinstance(fileName, str) and not utils.is_remote_uri(fileName):
                if pth.exists(fileName):
                    fileName = pth.abspath(fileName)
        self._file_name = fileName
        self._file_handler = None
        self.is_thredds = False
        self.use_pydap = False
        self.invert_y = False
        self.data_type = data_type
        self.base_type = base_type
        self.nullValue = raster.getNullValue(data_type)
        self.layers = []
        self.raster_name = raster_name
        self.geotiff_tags = {}

    @property

    def file_info(self) -> Dict:
        return self.get_file_info()

    @supported_libs.RequireLib("rasterio")

    def get_file_info(self, *args, **kwargs):
        out = {"filename": "", "dimensions": [], "variables": []}

        if self._file_handler is None:
            self.open_file(*args, **kwargs)

        if self._file_handler is not None:
            try:
                out['filename'] = self._file_handler.files[0]
            except Exception as e:
                pass

            # get raster dimensions
            out['dimensions'].append({"name": "count", "size": self._file_handler.count})
            out['dimensions'].append({"name": "xsize", "size": self._file_handler.width})
            out['dimensions'].append({"name": "yszie", "size": self._file_handler.height})

            # get sub datasets
            sub_datasets = self._file_handler.subdatasets
            if len(sub_datasets) > 0:
                for item in sub_datasets:
                    out['variables'].append({
                        "name": item})
        return out

    @property

    def data_vars(self) -> List[str]:
        """data variables as property

        Returns
        -------
        List[str]
            a list of string
        """
        return self.get_data_variables()

    @supported_libs.RequireLib("rasterio")

    def get_data_vars(self) -> List[str]:
        out = []
        if len(self.file_info['variables']):
            out = [item['name'] for item in self.file_info['variables']]
        return out

    @supported_libs.RequireLib("rasterio")
    def open_file(self, *args, **kwargs):
        # Check if using remote file
        if args:
            if isinstance(args[0], bool):
                self.is_thredds = args[0]
        elif kwargs:
            if 'thredds' in kwargs:
                self.is_thredds = kwargs['thredds']

        if self._file_name is None:
            raise ValueError("file_name cannot be None")

        # Patch path (when needed) for gdal virtual file system
        if isinstance(self._file_name, (str, bytes)):
            if isinstance(self._file_name, bytes):
                _file_name = self._file_name.decode()
            elif isinstance(self._file_name, str):
                _file_name = self._file_name

            if self.is_thredds:
                if 'vsicurl' not in _file_name:
                    self._file_name = f"/vsicurl/{_file_name}"
                    if _file_name.endswith('tar') or _file_name.endswith('tgz'):
                        raise ValueError(
                            "Compressed archives require full path in the archive")
            else:
                if 'vsicurl' in _file_name:
                    is_thredds = True
            self._file_handler = rio.open(_file_name, mode='r')
        elif isinstance(self._file_name, rio.DatasetReader):
            # assign file_name to file_handler when input is DatasetReader object
            self._file_handler = self._file_name
            # change file_name to path of file
            self._file_name = self._file_handler.files[0]

    @supported_libs.RequireLib("rasterio")
    def reader(self, *args, **kwargs) -> Tuple:
        # open file
        self.open_file(*args, **kwargs)

        # Get projection information from the file
        projStr = ""
        if hasattr(self._file_handler, 'crs'):
            if getattr(self._file_handler, 'crs') is not None:
                projStr = self._file_handler.crs.to_proj4()
            # workaround for rasterio crs code. geostack projection can't handle
            # rasterio proj4 string when it only has epsg code
            if 'epsg' in projStr:
                # use pyproj to transform wkt to proj4
                try:
                    import pyproj
                    projStr = pyproj.CRS.from_wkt(
                        self._file_handler.crs.to_wkt()).to_proj4()
                except ImportError:
                    projStr = ""

        if self._file_handler is None:
            raise ValueError("Unable to open file %s" % self._file_name)

        # Get geostranform
        geotransform = self._file_handler.get_transform()
        if geotransform[5] < 0:
            self.invert_y = True
        else:
            self.invert_y = False

        if self._file_handler.driver == 'GTiff':
            self.geotiff_tags = get_geotiff_tags(self._file_handler.name)

        time = self.time(None)

        # Compute dimension input for instantiating raster.Raster
        nx = self._file_handler.width
        ny = self._file_handler.height

        raster_count = self._file_handler.count
        if not raster_count > 0:
            sub_datasets = self._file_handler.subdatasets
            if not len(sub_datasets) > 0:
                raise RuntimeError("No raster bands or SubDatasets found")

        self.layers = get_layers(kwargs.get("layers", -1),
                                 raster_count)
        # add 1 as bands in gdal starts from 1
        self.layers = [i + 1 for i in self.layers]

        nz = len(self.layers)

        hx = geotransform[1]
        hy = abs(geotransform[5])
        hz = 1
        ox = geotransform[0]
        oy = geotransform[3]
        if self.invert_y:
            oy += ny * geotransform[5]
        oz = 0.0

        return nx, ny, nz, hx, hy, hz, ox, oy, oz, core.str2bytes(projStr), time

    @staticmethod
    def compute_bounds(ti: numbers.Integral, tj: numbers.Integral,
                       nx: numbers.Integral, ny: numbers.Integral,
                       tileSize: numbers.Integral, tx: numbers.Integral,
                       ty: numbers.Integral, invert_y: bool = True) -> Tuple[float, float, int, int]:
        xoff = min(ti * tileSize, nx)
        xsize = min(min(ti + 1, tx) * tileSize, nx) - xoff

        if invert_y:
            y_start = ny - min(min((tj + 1), ty) * tileSize, ny)
            y_end = ny - min(tj * tileSize, ny)
        else:
            y_start = tj * tileSize
            y_end = min(min((tj + 1), ty) * tileSize, ny)

        yoff = min(y_start, y_end)
        ysize = abs(y_start - y_end)

        return xoff, yoff, xsize, ysize

    def writer(self):
        raise NotImplementedError()

    @supported_libs.RequireLib("rasterio")
    def check_handler(self):
        if not isinstance(self, RIO_Handler):
            raise TypeError("Unable to understand the input class instance")

        if self._file_handler is None:
            raise ValueError("file_handler could not be located")

        if not isinstance(self._file_handler, rio.DatasetReader):
            raise TypeError(
                "file_handler is not an instance of rio.DatasetReader")

        if self._file_handler.files[0] != self._file_name:
            if self._file_name not in self._file_handler.files[0]:
                raise ValueError(
                    "Mismatch between file_name and description of file in rio.DatasetReader")

    @supported_libs.RequireLib("rasterio")
    def setter(self, ti: numbers.Integral, tj: numbers.Integral,
               tx: numbers.Integral, ty: numbers.Integral,
               tidx: int, *args, **kwargs) -> Tuple[np.ndarray, int, int]:

        if self._file_handler.closed:
            raise RuntimeError("Unable to read from closed file")

        # raster_index ignored as all data is read

        # Check handler
        self.check_handler()

        geotransform = self._file_handler.get_transform()

        # Create empty buffer
        tile_size = raster.TileSpecifications().tileSize
        buf_arr = np.full((len(self.layers), tile_size, tile_size), self.nullValue,
                          dtype=self.data_type)


        xoff, yoff, xsize, ysize = RIO_Handler.compute_bounds(ti, tj,
                                                              self._file_handler.width,
                                                              self._file_handler.height,
                                                              tile_size, tx, ty,
                                                              invert_y=self.invert_y)

        # # Get data bounds
        # if self.invert_y:
        #     xoff, yoff, xsize, ysize = RIO_Handler.compute_bounds(ti, tj,
        #                                                           self._file_handler.width,
        #                                                           self._file_handler.height,
        #                                                           tile_size, tx, ty, invert_y=self.invert_y)
        # else:
        #     if (self._file_handler.driver == 'GTiff' and
        #         geotransform[5] > 0 and
        #         TIFFTAG_GEOTRANSMATRIX in self.geotiff_tags):
        #         # this is when Geotiff hy >= 0, and GEOTRANSMATRIX is defined in geotiff tags
        #         xoff, yoff, xsize, ysize = RIO_Handler.compute_bounds(ti, ty-tj-1,
        #                                                               self._file_handler.width,
        #                                                               self._file_handler.height,
        #                                                               tile_size, invert_y=False)
        #     else:
        #         xoff, yoff, xsize, ysize = RIO_Handler.compute_bounds(ti, ty,
        #                                                               self._file_handler.width,
        #                                                               self._file_handler.height,
        #                                                               tile_size)

        # Get bands
        raster_band = self._file_handler.read(indexes=self.layers,
                                              window=Window(
                                                  xoff, yoff, xsize, ysize),
                                              out_dtype=self.data_type)

        # Get missing value
        missing_value = self._file_handler.nodatavals[0]

        # Get raster data type
        raster_dtype = np.dtype(self._file_handler.dtypes[0]).type
        if missing_value is not None:
            try:
                if raster_dtype in [np.float32, np.float64, np.complex_,
                                    np.complex64, np.complex128]:
                    missing_value = raster_dtype(missing_value)
                else:
                    if (missing_value - raster_dtype(missing_value)) == 0:
                        missing_value = raster_dtype(missing_value)
                    else:
                        missing_value = None
            except Exception as _:
                warnings.warn(f"WARNING: Rasterio missing value '{missing_value}' " +
                              f"cannot be converted to {raster_dtype.__name__}", RuntimeWarning)
                missing_value = None

        # Check and patch data
        if missing_value is not None:
            raster_band = np.where(
                raster_band == missing_value, self.nullValue, raster_band)

        # Copy data to buffer
        zsize, ysize, xsize = raster_band.shape
        if self.invert_y:
            buf_arr[:zsize, :ysize, :xsize] = np.flip(raster_band, axis=1)
            return buf_arr, ti, tj
        else:
            buf_arr[:zsize, :ysize, :xsize] = raster_band[:, :, :]
            return buf_arr, ti, tj

    def close(self):
        if hasattr(self, '_file_handler'):
            if isinstance(self._file_handler, rio.DatasetReader):
                if not self._file_handler.closed:
                    self._file_handler.close()
                    del self._file_handler
                    self._file_handler = None

    def __del__(self, *args, **kwargs):
        self.close()

    @supported_libs.RequireLib("rasterio")
    def __exit__(self, *args):
        if self._file_handler is not None:
            self.close()

    def time(self, *args):
        return 0.0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<geostack.readers.%s>" % self.__class__.__name__


@supported_libs.RequireLib("zarr")
@supported_libs.RequireLib("xarray")
def from_zarr(inp_file: str, **kwargs) -> 'raster.RasterFile':
    """read a zarr store into a RasterFile object

    Parameters
    ----------
    inp_file : str
        path to a zarr store

    Returns
    -------
    RasterFile
        an instance of RasterFile object
    """
    ds = xr.open_zarr(inp_file)
    out_raster = raster.RasterFile(filePath=ds, backend='xarray',
                                   name=kwargs.get('name', ''))
    proj4_str = ds.attrs.get("proj4", '')
    if len(proj4_str) > 0:
        out_raster.setProjectionParameters(
            core.ProjectionParameters.from_proj4(proj4_str))
    out_raster.read(jsonConfig=kwargs.get("jsonConfig", {}))
    return out_raster
