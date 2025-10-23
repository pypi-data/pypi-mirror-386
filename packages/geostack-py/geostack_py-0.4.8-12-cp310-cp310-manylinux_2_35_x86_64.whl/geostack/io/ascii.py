# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numpy as np
from ._cy_ascii import cyAscii_d_d, cyAscii_f_f
from .. import raster
from ..core import REAL, str2bytes
import json
from typing import Union, Dict, Optional
from pathlib import PurePath

class AsciiHandler:
    def __init__(self, dtype: np.dtype = REAL):
        self._handle = None
        self.dtype = dtype
        if self.dtype == np.float64:
            self._handle = cyAscii_d_d()
        elif self.dtype == np.float32:
            self._handle = cyAscii_f_f()

# read ascii to a raster
# @file_name: name of the file (string type) to be read
# @dtype: optional argument, data type of raster class instance
#
    def read(self, fileName: str, jsonConfig: Optional[Union[str, Dict]] = None,
             input_raster: Optional["raster.Raster"] = None):
        '''write ascii to raster file

        Parameters
        ----------
        file_name : name of the file to be read, string type
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the input file.
        dtype : (optional) type of raster instance, np.float32 or np.float64

        Returns
        -------
        Nil

        Examples
        --------
        >>> out = AsciiHandler(dtype=np.float32)
        >>> out.read("testRasterA.asc")
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

# write raster to ascii file
# @this: an instance of raster class
# @file_name: name of the file (string type) to be written
#
    def write(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
              input_raster: Optional['raster.Raster'] = None):
        '''write raster to ascii file

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
        >>> this = Raster("testRasterA")
        >>> this.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.asc"
        >>> ascii = AsciiHandler()
        >>> ascii.write(file_name, "", input_raster=this)
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
                    "Need input_raster or a raster object in AsciiHandler")

    @property
    def raster(self) -> "raster.Raster":
        if hasattr(self, "_raster_handler"):
            return self._raster_handler

    @raster.setter
    def raster(self, input_raster: "raster.Raster") -> None:
        if not isinstance(input_raster, raster.Raster):
            raise TypeError(
                "input_raster should be an instance of raster.Raster")
        if self.dtype != input_raster.base_type:
            raise TypeError(
                "Mismatch between data type of AsciiHandler and input_raster")
        self._raster_handler = input_raster

    @staticmethod
    def to_raster(fileName: str, dtype: np.dtype = REAL,
                  jsonConfig: Optional[Union[str, Dict]] = None) -> "AsciiHandler":
        """
        Examples
        --------
        >>> AsciiHandler.to_raster(test, "testRasterA.asc")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        ascii_handler = AsciiHandler(dtype=dtype)
        ascii_handler.read(fileName, jsonConfig=jsonConfig)
        return ascii_handler

    @staticmethod
    def from_raster(output_raster: "raster.Raster", fileName: str,
                    jsonConfig: Optional[Union[str, Dict]] = None):
        """
        Examples
        --------
        >>> test = Raster(name="testRasterA")
        >>> test.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.asc"
        >>> AsciiHandler.from_raster(test, file_name, "")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        if isinstance(output_raster, raster.Raster):
            ascii_handler = AsciiHandler(dtype=output_raster.base_type)
            ascii_handler.write(fileName, jsonConfig=jsonConfig,
                                input_raster=output_raster)
        else:
            raise TypeError(
                "output_raster should be an instance of raster.Raster class")

    @staticmethod
    def readAsciiFile(fileName: str, dtype: np.dtype = REAL,
                      jsonConfig: Optional[Union[str, Dict]] = None):
        """
        Examples
        --------
        >>> file_name = "testRasterA.asc"
        >>> out = AsciiHandler.readAsciiFile(file_name)
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        ascii_handler = AsciiHandler(dtype=dtype)
        ascii_handler.read(fileName, jsonConfig=jsonConfig)
        return ascii_handler

    def __repr__(self):
        return "<class 'geostack.io.%s'>" % self.__class__.__name__
