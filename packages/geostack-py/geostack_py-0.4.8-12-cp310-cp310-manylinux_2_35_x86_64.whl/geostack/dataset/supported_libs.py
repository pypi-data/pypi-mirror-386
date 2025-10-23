# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import importlib
from functools import wraps
from typing import Callable, List, Tuple, Optional
import types
from contextlib import closing
from ctypes.util import find_library

flag_list: List[str] = []

__all__ = [*flag_list, "import_or_skip"]

SUPPORTED_LIBS = {"gdal": "gdal",
                  "osr": "osr",
                  "ogr": "ogr",
                  "netcdf": "netCDF4",
                  "rasterio": "rasterio",
                  "xarray": "xarray",
                  "pydap": "pydap",
                  "pyshp": "shapefile",
                  "geopandas": "geopandas",
                  "fiona": "fiona",
                  "pygrib": "pygrib",
                  "cfgrib": "cfgrib",
                  "dask": "dask",
                  "shapely": "shapely",
                  "spatialite": "spatialite",
                  "matplotlib": "matplotlib"}


def import_or_skip(*args, **kwargs) -> Tuple[Optional[types.ModuleType], bool]:
    try:
        out = importlib.import_module(*args, **kwargs)
    except ModuleNotFoundError:
        if args[0] == "gdal" or args[0] == "osr" or args[0] == "ogr":
            try:
                out = importlib.import_module(f".{args[0]}", package="osgeo")
            except ModuleNotFoundError:
                return None, False
        else:
            return None, False
    if out is None:
        return None, False
    return out, True


class RequireLib:
    def __init__(self, libname: str):
        self.libname = libname

    def _dummy_function(self, *args, **kwargs):
        raise ModuleNotFoundError(f"library {self.libname} is not installed")

    def __call__(self, input_function: Callable, *args, **kwargs):
        @wraps(input_function)
        def inner_func(*args, **kwargs):
            if self.libname in SUPPORTED_LIBS:
                if self.libname not in ["geopandas", "netcdf"]:
                    if globals()[f'has_{self.libname}'.upper()]:
                        return input_function(*args, **kwargs)
                    else:
                        return self._dummy_function()
                else:
                    if self.libname == "netcdf":
                        if HAS_NCDF:
                            return input_function(*args, **kwargs)
                        else:
                            return self._dummy_function()
                    elif self.libname == "geopandas":
                        if HAS_GPD:
                            return input_function(*args, **kwargs)
                        else:
                            return self._dummy_function()
        return inner_func


for libname in SUPPORTED_LIBS:
    if libname not in ["geopandas", "netcdf", "pyshp", "spatialite"]:
        lib_flag = f'has_{libname}'.upper()
        if lib_flag not in flag_list:
            flag_list.append(lib_flag)
        try:
            eval(f"{lib_flag}")
        except NameError:
            exec(f"{lib_flag}=False")
        _, globals()[lib_flag] = import_or_skip(SUPPORTED_LIBS[libname])
    else:
        if libname == "netcdf":
            ncdf, HAS_NCDF = import_or_skip(SUPPORTED_LIBS[libname])
            HAS_NCDF = hasattr(ncdf, "Dataset")
            flag_list.append("HAS_NCDF")
        elif libname == "geopandas":
            gpd, HAS_GPD = import_or_skip(SUPPORTED_LIBS[libname])
            HAS_GPD = hasattr(gpd, "GeoDataFrame")
            flag_list.append("HAS_GPD")
        elif libname == "pyshp":
            _, HAS_PYSHP = import_or_skip(SUPPORTED_LIBS[libname])
            flag_list.append("HAS_PYSHP")
        elif libname == "spatialite":
            sqlite3, _ = import_or_skip("sqlite3")
            HAS_SPATIALITE = False
            with closing(sqlite3.connect(":memory:")) as conn:
                with closing(conn.cursor()) as cur:
                    if hasattr(conn, 'enable_load_extension'):
                        conn.enable_load_extension(True)
                        try:
                            conn.load_extension("mod_spatialite")
                            HAS_SPATIALITE = True
                        except sqlite3.OperationalError:
                            lib_path = find_library("mod_spatialite")
                            if lib_path is not None:
                                conn.load_extension(lib_path)
                                HAS_SPATIALITE = True
                    else:
                        HAS_SPATIALITE = False
            flag_list.append("HAS_SPATIALITE")
