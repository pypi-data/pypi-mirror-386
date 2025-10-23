# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os.path as pth

import numpy as np
from collections import OrderedDict
from .. import raster
from . import supported_libs

__all__ = ["gdal_dtype_to_numpy", "numpy_to_gdal_dtype", "get_band_values"]


@supported_libs.RequireLib("gdal")
def gdal_dtype_to_numpy(input_type):
    '''
    map gdal datatype to a numpy data to maintain consistency between the input data and
    output data used for data processing
    '''
    from osgeo import gdal, gdalconst

    if not isinstance(input_type, int):
        raise ValueError(
            "input_type should be integer value returned by gdalconst")
    gdal_dtype = None
    for item in gdalconst.__dict__:
        if item.startswith("GDT"):
            if input_type == getattr(gdalconst, item):
                gdal_dtype = item

    if gdal_dtype is None:
        raise AttributeError(
            "Argument %d is not a gdal data type" % input_type)

    if 'GDT_C' in gdal_dtype:
        str_pattern = "GDT_C"
    else:
        str_pattern = "GDT_"

    if gdal_dtype == "GDT_Byte":
        return np.uint8

    if hasattr(np, gdal_dtype.replace(str_pattern, "").lower()):
        return getattr(np, gdal_dtype.replace(str_pattern, "").lower())
    else:
        raise AttributeError("numpy doesnt have %s data type" %
                             gdal_dtype.replace(str_pattern, "").lower())


@supported_libs.RequireLib("gdal")
def numpy_to_gdal_dtype(input_type):
    '''
    map numpy type to gdal data types
    '''
    from osgeo import gdal, gdalconst

    if input_type not in [np.uint8, np.uint16, np.uint32]:
        if hasattr(gdalconst, "GDT_%s" % np.dtype(input_type).name.title()):
            return getattr(gdalconst, "GDT_%s" % np.dtype(input_type).name.title())
        else:
            raise AttributeError("%s is not a recognized gdal type" %
                                 np.dtype(input_type).name)
    elif input_type == np.uint8:
        return gdalconst.GDT_Byte
    elif input_type in [np.uint16, np.uint32]:
        name_map = {"uint16": "UInt16", "uint32": "UInt32"}
        return getattr(gdalconst, "GDT_%s" % name_map.get(np.dtype(input_type).name))


@supported_libs.RequireLib("gdal")
def get_band_values(raster_handle, raster_coords):
    """
    extract values from raster_handle for given list of raster indices
    """
    from osgeo import gdal, gdalconst

    if isinstance(raster_handle, gdal.Dataset):
        missing_value = raster_handle.GetRasterBand(1).GetNoDataValue()
        data_out = {}
        for i in range(raster_handle.RasterCount):
            npy_type = gdal_dtype_to_numpy(
                raster_handle.GetRasterBand(i + 1).DataType)
            out = np.zeros(shape=len(raster_coords), dtype=npy_type)
            for j, point in enumerate(raster_coords, 0):
                out[j] = raster_handle.GetRasterBand(i + 1).ReadAsArray(xoff=int(point[0]),
                                                                        yoff=int(
                                                                            point[1]),
                                                                        win_xsize=1,
                                                                        win_ysize=1)
            data_out[f"Band_{(i+1):d}"] = np.copy(out)
            data_out[f"Band_{(i + 1):d}"] = np.where(data_out[f"Band_{(i + 1):d}"] == missing_value,
                                                     np.nan, data_out[f"Band_{(i + 1):d}"])
    elif isinstance(raster_handle, gdal.Band):
        npy_type = gdal_dtype_to_numpy(raster_handle.DataType)
        data_out = np.zeros(shape=len(raster_coords), dtype=npy_type)
        missing_value = raster_handle.GetNoDataValue()
        for j, point in enumerate(raster_coords, 0):
            data_out[j] = raster_handle.ReadAsArray(xoff=int(point[0]),
                                                    yoff=int(point[1]),
                                                    win_xsize=1,
                                                    win_ysize=1)
        data_out = np.where(data_out == missing_value, np.nan, data_out)
    return data_out


class Dataset:
    def __init__(self, filePath, thredds=False, use_pydap=False,
                 backend="netcdf"):
        self._file_handle = None
        self.is_open = False
        self.is_closed = True
        self._supported_backends = ['xarray', "netcdf", "rasterio", "gdal"]
        self.variables = OrderedDict()

        self.Open(filePath, thredds=thredds, use_pydap=use_pydap,
                  backend=backend)

    def _check_file_argument(self, other):
        if isinstance(other, str):
            if not pth.exists(other):
                raise ValueError(f"Input path {other} doesn't exist")
            else:
                if not pth.isfile(other):
                    raise ValueError(f"Input argument {other} is not a file")
        else:
            raise TypeError("File name should be of string type")

    def Open(self, filePath, thredds=False, use_pydap=False,
             backend="netcdf"):

        if backend is not None and isinstance(backend, str):
            if backend not in self._supported_backends:
                raise ValueError(f"{backend} is not recognised")
        else:
            raise TypeError("Value of backend should be of string type")
        if backend == "netcdf":
            self._parse_ncdf(filePath, thredds=thredds,
                             use_pydap=use_pydap)
        elif backend == "xarray":
            self._parse_xarray(filePath, thredds=thredds,
                               use_pydap=use_pydap)
        elif backend == "gdal":
            self._parse_gdal(filePath)
        elif backend == "rasterio":
            self._parse_rasterio(filePath)

        self.is_open = True
        self.is_closed = False

    def _prune_dims(self, inp_dims):
        out_dims = []
        for item in inp_dims:
            if item.lower() in ['lon', 'longitude', 'lat', 'latitude', 'x', 'y']:
                out_dims.append(item)
        return out_dims

    def is_dims_subset(self, var_dims, dim_names):
        return set(dim_names).issubset(list(var_dims))

    @supported_libs.RequireLib("netcdf")
    def _parse_ncdf(self, other, thredds=False, use_pydap=False):
        import netCDF4 as nc

        if thredds:
            self._file_handle = nc.Dataset(other)
        else:
            self._file_handle = nc.Dataset(other, mode='r')

        nc_dims = self._prune_dims(list(self._file_handle.dimensions.keys()))

        for var in self._file_handle.variables:
            if (var not in self.variables and
                    self.is_dims_subset(self._file_handle.variables[var].dimensions, nc_dims)):
                self.variables[var] = raster.RasterFile(filePath=self._file_handle,
                                                        backend="netcdf")
                self.variables[var].read(thredds=thredds, use_pydap=use_pydap)
                self.variables[var].setProperty("name", var)
                for attr in self._file_handle.variables[var].ncattrs():
                    if not self.variables[var].hasProperty(attr) and not attr.startswith("_"):
                        self.variables[var].setProperty(attr,
                                                        self._file_handle.variables[var].getncattr(attr))
                if not hasattr(self, var):
                    setattr(self, var, self.variables[var])

    @supported_libs.RequireLib("xarray")
    def _parse_xarray(self, other, thredds=False, use_pydap=False):
        import xarray as xr

        self._file_handle = xr.open_supported_libs(other)

        xr_dims = self._prune_dims(list(self._file_handle.dims.keys()))

        for var in self._file_handle.variables:
            if (var not in self.variables and
                    self.is_dims_subset(self._file_handle.variables[var].dims, xr_dims)):
                self.variables[var] = raster.RasterFile(filePath=self._file_handle,
                                                        backend="xarray")
                self.variables[var].read(thredds=thredds, use_pydap=use_pydap)
                self.variables[var].setProperty("name", var)
                for attr in self._file_handle.variables[var].attrs:
                    if not self.variables[var].hasProperty(attr) and not attr.startswith("_"):
                        self.variables[var].setProperty(attr,
                                                        self._file_handle.variables[var].attrs[attr])
                if not hasattr(self, var):
                    setattr(self, var, self.variables[var])

    @supported_libs.RequireLib("rasterio")
    def _parse_rasterio(self, other):
        import rasterio

        if not isinstance(other, str):
            raise TypeError("Input argument should be str")
        if not pth.exists(other) or not pth.isfile(other):
            raise FileNotFoundError(f"File {other} can not be located")

        self._file_handle = rasterio.open(other)

        raster_count = self._file_handle.count
        for i in range(raster_count):
            var = None
            if len(self._file_handle.descriptions) > 0:
                var = self._file_handle.descriptions[i]
            if var is None or not len(var) > 0:
                var = f"band{i+1}"
            if var not in self.variables:
                self.variables[var] = raster.RasterFile(filePath=self._file_handle,
                                                        backend="rasterio")
                self.variables[var].read()
                self.variables[var].setProperty("name", var)
                self.variables[var].update_time(i + 1)
                if not hasattr(self, var):
                    setattr(self, var, self.variables[var])

    @supported_libs.RequireLib("gdal")
    def _parse_gdal(self, other):
        from osgeo import gdal, gdalconst

        if not isinstance(other, str):
            raise TypeError("Input argument should be str")
        if not pth.exists(other) or not pth.isfile(other):
            raise FileNotFoundError(f"File {other} can not be located")
        self._file_handle = gdal.OpenEx(other)
        raster_count = self._file_handle.RasterCount
        for i in range(raster_count):
            var = self._file_handle.GetRasterBand(i + 1).GetDescription()
            if var is None or not len(var) > 0:
                var = f"band{i+1}"
            if var not in self.variables:
                self.variables[var] = raster.RasterFile(filePath=self._file_handle,
                                                        backend="gdal")
                self.variables[var].read()
                self.variables[var].setProperty("name", var)
                self.variables[var].update_time(i + 1)
                if not hasattr(self, var):
                    setattr(self, var, self.variables[var])

    def close(self):
        if supported_libs.HAS_NCDF:
            if isinstance(self._file_handle, nc.Dataset):
                if self._file_handle.isopen():
                    self._file_handle.close()
        if supported_libs.HAS_XARRAY:
            if isinstance(self._file_handle, xr.supported_libs):
                self._file_handle.close()
        if supported_libs.HAS_GDAL:
            if isinstance(self._file_handle, gdal.Dataset):
                del self._file_handle
        if supported_libs.HAS_RASTERIO:
            if isinstance(self._file_handle, rasterio):
                if not self._file_handle.closed:
                    self._file_handle.close()
        self.is_open = False
        self.is_closed = True

    def __exit__(self, *args, **kwargs):
        if self.is_open:
            self.close()

    def __repr__(self):
        return "class <'geostack.dataset.%s'>" % self.__class__.__name__


if __name__ == "__main__":
    pass
