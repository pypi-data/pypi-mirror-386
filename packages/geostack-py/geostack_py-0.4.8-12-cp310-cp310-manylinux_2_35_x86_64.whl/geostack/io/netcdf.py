# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import numpy as np
from ._cy_netcdf import cyNetCDF_d_d, cyNetCDF_f_f
from .. import raster
import json
from typing import Union, Dict, Optional
from pathlib import PurePath
from ..core import REAL, str2bytes

__all__ = ['NetCDFHandler']


class NetCDFHandler:
    def __init__(self, dtype: np.dtype = REAL):
        self._handle = None
        self.dtype = dtype
        if self.dtype == np.float64:
            self._handle = cyNetCDF_d_d()
        elif self.dtype == np.float32:
            self._handle = cyNetCDF_f_f()

# read NetCDF to a raster
# @file_name: name of the file (string type) to be read
# @dtype: optional argument, data type of raster class instance
#
    def read(self, fileName: str, jsonConfig: Optional[Union[str, Dict]] = None,
             input_raster: Optional['raster.Raster'] = None) -> None:
        '''read NetCDF file to a raster

        Parameters
        ----------
        file_name : name of the file to be read, string type
        jsonConfig : Optional[Union[str, Dict]], optional
            A string or dictionary containing configuration for the input file, by default None.
        input_raster : Optional[Raster], optional
            an instance of a Raster object

        Returns
        -------
        Nil

        Examples
        --------
        >>> out = NetCDFHandler(dtype=np.float32)
        >>> out.read("testRasterA.nc", jsonConfig={"variable": "testA"})
        '''
        if jsonConfig is None:
            _json_config = str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = str2bytes(json.dumps(jsonConfig))

        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        if input_raster is None:
            self._raster_handler = raster.Raster(base_type=self.dtype)
        else:
            if isinstance(input_raster, raster.Raster):
                if input_raster.base_type != self.dtype:
                    raise TypeError(
                        "Type mismatch between input raster and NetCDFHandler")
                self._raster_handler = input_raster
            else:
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")

        if isinstance(fileName, (str, bytes)):
            self._handle.read(str2bytes(fileName),
                              self._raster_handler._handle, _json_config)

# write raster to NetCDF file
# @this: an instance of raster class
# @file_name: name of the file (string type) to be written
#
    def write(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
              input_raster: Optional['raster.Raster'] = None) -> None:
        '''write raster to a NetCDF file

        Parameters
        ----------
        file_name: name of the file for writing raster, string type
        jsonConfig : Optional[Union[str, Dict]], optional
            A string or dictionary containing configuration for the output file, by default None.
        input_raster: Optional[Raster]
            an instance of raster class to be written out

        Returns
        -------
        Nil

        Examples
        --------
        >>> this = Raster("testRasterA")
        >>> this.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.nc"
        >>> NetCDF = NetCDFHandler()
        >>> NetCDF.write(file_name, "", input_raster=this)
        '''
        if jsonConfig is None:
            _json_config = str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = str2bytes(json.dumps(jsonConfig))

        if input_raster is not None:
            if not isinstance(input_raster, raster.Raster):
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")
            if isinstance(fileName, (str, bytes)):
                self._handle.write(str2bytes(fileName),
                                   input_raster._handle, _json_config)
        else:
            if hasattr(self, "_raster_handler"):
                if isinstance(fileName, (bytes, str)):
                    self._handle.write(
                        str2bytes(fileName), self.raster._handle, _json_config)
            else:
                raise RuntimeError(
                    "Need input_raster or a raster object in NetCDFHandler")

    @property
    def raster(self) -> "raster.Raster":
        if hasattr(self, "_raster_handler"):
            return self._raster_handler

    @raster.setter
    def raster(self, input_raster: "raster.Raster") -> None:
        """Set a raster object.

        Parameters
        ----------
        input_raster : Raster
            an instance of a raster object

        Raises
        ------
        TypeError
            input raster should be an instance of raster.Raster
        TypeError
            Mismatch between data type of NetCDFHandler and input_raster
        """
        if not isinstance(input_raster, raster.Raster):
            raise TypeError(
                "input_raster should be an instance of raster.Raster")
        if self.dtype != input_raster.base_type:
            raise TypeError(
                "Mismatch between data type of NetCDFHandler and input_raster")
        self._raster_handler = input_raster

    @staticmethod
    def to_raster(fileName: str, dtype: np.dtype = REAL,
                  jsonConfig: Optional[Union[str, Dict]] = None) -> "NetCDFHandler":
        """reader a netcdf file to a raster object.

        Parameters
        ----------
        fileName : str
            path of the netcdf file
        dtype : np.dtype, optional
            data type to instantiate a Raster object, by default np.float32
        jsonConfig : Optional[Union[str, Dict]], optional
            configuration used in the reader, by default None

        Returns
        -------
        NetCDFHandler
            an instance of the netcdf handler object

        Examples
        --------
        >>> NetCDFHandler.to_raster(test, "testRasterA.nc")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        NetCDF_handler = NetCDFHandler(dtype=dtype)
        NetCDF_handler.read(fileName, jsonConfig=jsonConfig)
        return NetCDF_handler

    @staticmethod
    def from_raster(output_raster: "raster.Raster", fileName: str,
                    jsonConfig: Optional[Union[str, Dict]] = None) -> None:
        """
        Examples
        --------
        >>> test = Raster(name="testRasterA")
        >>> test.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.nc"
        >>> NetCDFHandler.from_raster(test, file_name, "")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        if isinstance(output_raster, raster.Raster):
            NetCDF_handler = NetCDFHandler(dtype=output_raster.base_type)
            NetCDF_handler.write(fileName, jsonConfig=jsonConfig,
                                 input_raster=output_raster)
        else:
            raise TypeError(
                "output_raster should be an instance of raster.Raster class")

    @staticmethod
    def readNetCDFFile(fileName: str, dtype: np.dtype = REAL,
                       jsonConfig: Optional[Union[str, Dict]] = None) -> "NetCDFHandler":
        """
        Examples
        --------
        >>> file_name = "testRasterA.nc"
        >>> out = NetCDFHandler.readNetCDFFile(file_name)
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        NetCDF_handler = NetCDFHandler(dtype=dtype)
        NetCDF_handler.read(fileName, jsonConfig=jsonConfig)
        return NetCDF_handler

    def __repr__(self):
        return "<class 'geostack.io.%s'>" % self.__class__.__name__
