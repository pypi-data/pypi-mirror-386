# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numpy as np
from ._cy_flt import cyFlt_d_d, cyFlt_f_f
from .. import raster
import json
from typing import Union, Dict, Optional
from pathlib import PurePath
from ..core import REAL, str2bytes


class FltHandler:
    def __init__(self, dtype: np.dtype = REAL):
        self._handle = None
        self.dtype = dtype
        if self.dtype == np.float64:
            self._handle = cyFlt_d_d()
        elif self.dtype == np.float32:
            self._handle = cyFlt_f_f()

# read flt to a raster
# @file_name: name of the file (string type) to be read
# @dtype: optional argument, data type of raster class instance
#
    def read(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
             input_raster: Optional["raster.Raster"] = None):
        '''read flt file to a raster

        Parameters
        ----------
        file_name : string type
            name of the file to be read
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the input file.
        dtype : np.float32/np.float64 (optional)
            type of raster instance

        Returns
        -------
        Nil

        Examples
        --------
        >>> out = FltHandler()
        >>> out.read("testRasterA.flt")
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
                        "Type mismatch between input raster and AsciiHandler")
                self._raster_handler = input_raster
            else:
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")
        if isinstance(fileName, (str, bytes)):
            self._handle.read(str2bytes(fileName),
                              self._raster_handler._handle, _json_config)

# write raster to flt file
# @this: an instance of raster class
# @file_name: name of the file (string type) to be written
#
    def write(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
              input_raster: Optional['raster.Raster'] = None):
        '''write raster to flt file

        Parameters
        ----------
        file_name: name of the file for writing raster, string type
        jsonConfig : Optional[Union[str, dict]], optional
            A string or dictionary containing configuration for the output file.
        input_raster: Raster
            an instance of raster class to be written out

        Returns
        -------
        Nil

        Examples
        --------
        >>> this = Raster("testRasterA", np.float32)
        >>> this.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.flt"
        >>> out = FltHandler(input_raster=this)
        >>> out.write(file_name, "")
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

        if input_raster is not None:
            if not isinstance(input_raster, raster.Raster):
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")
            if isinstance(fileName, (str, bytes)):
                self._handle.write(str2bytes(fileName),
                                   input_raster._handle, _json_config)
        else:
            if hasattr(self, "_raster_handler"):
                if isinstance(fileName, (str, bytes)):
                    self._handle.write(
                        str2bytes(fileName), self.raster._handle, _json_config)
            else:
                raise RuntimeError(
                    "Need input_raster or a raster object in FltHandler")

    @property
    def raster(self) -> "raster.Raster":
        if hasattr(self, "_raster_handler"):
            return self._raster_handler

    @raster.setter
    def raster(self, input_raster: "raster.Raster"):
        if not isinstance(input_raster, raster.Raster):
            raise TypeError(
                "input_raster should be an instance of raster.Raster")
        if self.dtype != input_raster.base_type:
            raise TypeError(
                "Mismatch between data type of FltHandler and input_raster")
        self._raster_handler = input_raster

    @staticmethod
    def to_raster(fileName: str, dtype: np.dtype = REAL,
                  jsonConfig: Optional[Union[str, Dict]] = None) -> "FltHandler":
        """
        Examples
        --------
        >>> test = Raster()
        >>> FltHandler.to_raster(test, "testRasterA.flt")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        flt_handler = FltHandler(dtype=dtype)
        flt_handler.read(fileName, jsonConfig=jsonConfig)
        return flt_handler

    @staticmethod
    def from_raster(output_raster: "raster.Raster", fileName: str,
                    jsonConfig: Optional[Union[str, Dict]] = None):
        """
        Examples
        --------
        >>> test = Raster(name="testRasterA")
        >>> test.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.flt"
        >>> FltHandler.from_raster(test, file_name, "")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        if isinstance(output_raster, raster.Raster):
            flt_handler = FltHandler(dtype=output_raster.base_type)
            flt_handler.write(fileName, jsonConfig=jsonConfig,
                              input_raster=output_raster)
        else:
            raise TypeError(
                "output_raster should be an instance of raster.Raster class")

    @staticmethod
    def readFltFile(fileName: str, dtype: np.dtype = REAL,
                    jsonConfig: Optional[Union[str, Dict]] = None) -> "FltHandler":
        """
        Examples
        --------
        >>> file_name = "testRasterA.flt"
        >>> out = FltHandler.readFltFile(file_name)
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        flt_handler = FltHandler(dtype=dtype)
        flt_handler.read(fileName, jsonConfig=jsonConfig)
        return flt_handler

    def __repr__(self):
        return "<class 'geostack.io.%s'>" % self.__class__.__name__
