# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numpy as np
import json
from ._cy_gsr import cyGsr_d_d, cyGsr_f_f
from .. import raster
from typing import Union, Dict, Optional
from pathlib import PurePath
from ..core import REAL, str2bytes

class GsrHandler:
    def __init__(self, dtype: np.dtype = REAL):
        self._handle = None
        self.dtype = dtype
        if self.dtype == np.float64:
            self._handle = cyGsr_d_d()
        elif self.dtype == np.float32:
            self._handle = cyGsr_f_f()

# read gsr to a raster
# @file_name: name of the file (string type) to be read
# @dtype: optional argument, data type of raster class instance
#
    def read(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
             input_raster: Optional["raster.Raster"] = None):
        '''read gsr file to a raster

        Parameters
        ----------
        file_name: str
            Name of the file to be read.
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the input file.
        input_raster: Raster object
            An instance of raster object to read the gsr file into.

        Returns
        -------
        Nil

        Examples
        --------
        >>> out = GsrHandler()
        >>> out.read("testRasterA.gsr")
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
                        "Type mismatch between input raster and GsrHandler")
                self._raster_handler = input_raster
            else:
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")
        if isinstance(fileName, (str, bytes)):
            self._handle.read(str2bytes(fileName), self._raster_handler._handle,
                              _json_config)

# write raster to gsr file
# @this: an instance of raster class
# @file_name: name of the file (string type) to be written
#
    def write(self, fileName: str, jsonConfig: Optional[Union[str, Dict]] = None,
              input_raster: "raster.Raster" = None):
        '''write raster to gsr file

        Parameters
        ----------
        file_name: str
            Name of the file for writing raster
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the output file.
        input_raster: Raster object
            An instance of raster class to be written out

        Returns
        -------
        Nil

        Examples
        --------
        >>> this = Raster("testRasterA", np.float32)
        >>> this.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.gsr"
        >>> gsr = GsrHandler(input_raster=this)
        >>> gsr.write(file_name)
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
                    self._handle.write(str2bytes(fileName),
                                       self.raster._handle, _json_config)
            else:
                raise RuntimeError(
                    "Need input_raster or a raster object in GsrHandler")

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
                "Mismatch between data type of GsrHandler and input_raster")
        self._raster_handler = input_raster

    @staticmethod
    def to_raster(fileName: str, dtype: np.dtype = REAL,
                  jsonConfig: Optional[Union[str, Dict]] = None) -> "GsrHandler":
        """
        Examples
        --------
        >>> test = Raster()
        >>> GsrHandler.to_raster(test, "testRasterA.gsr")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        gsr_handler = GsrHandler(dtype=dtype)
        gsr_handler.read(fileName, jsonConfig=jsonConfig)
        return gsr_handler

    @staticmethod
    def from_raster(output_raster: "raster.Raster", fileName: str,
                    jsonConfig: Optional[Union[Dict, str]] = None):
        """
        Examples
        --------
        >>> test = Raster(name="testRasterA")
        >>> test.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.gsr"
        >>> GsrHandler.from_raster(test, file_name, "")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        if isinstance(output_raster, raster.Raster):
            gsr_handler = GsrHandler(dtype=output_raster.base_type)
            gsr_handler.write(fileName, jsonConfig=jsonConfig,
                              input_raster=output_raster)
        else:
            raise TypeError(
                "output_raster should be an instance of raster.Raster class")

    @staticmethod
    def readGsrFile(fileName: str, dtype: np.dtype = REAL,
                    jsonConfig: Union[str, Dict] = None) -> "GsrHandler":
        """
        Examples
        --------
        >>> file_name = "testRasterA.gsr"
        >>> out = GsrHandler.readGsrFile(file_name)
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        gsr_handler = GsrHandler(dtype=dtype)
        gsr_handler.read(fileName, jsonConfig=jsonConfig)
        return gsr_handler

    def __repr__(self):
        return self.__class__.__name__
