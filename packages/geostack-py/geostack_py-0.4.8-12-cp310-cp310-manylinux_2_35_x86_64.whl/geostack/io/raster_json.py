# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numpy as np
import json
from ._cy_raster_json import cyJson_d_d, cyJson_f_f
from .. import raster
from typing import Union, Dict, Optional
from pathlib import PurePath
from ..core import REAL, str2bytes

class JsonHandler:
    def __init__(self, dtype: np.dtype = REAL):
        self._handle = None
        self.dtype = dtype
        if self.dtype == np.float64:
            self._handle = cyJson_d_d()
        elif self.dtype == np.float32:
            self._handle = cyJson_f_f()

# read JSON to a raster
# @file_name: name of the file (string type) to be read
# @dtype: optional argument, data type of raster class instance
#
    def read(self, fileName: str, jsonConfig: Optional[Union[Dict, str]] = None,
             input_raster: Optional["raster.Raster"] = None):
        '''read JSON file to a raster

        Parameters
        ----------
        file_name: str
            Name of the file to be read.
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the input file.
        input_raster: Raster object
            An instance of raster object to read the json file into.

        Returns
        -------
        Nil

        Examples
        --------
        >>> out = JsonHandler()
        >>> out.read("testRasterA.json")
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
                        "Type mismatch between input raster and JsonHandler")
                self._raster_handler = input_raster
            else:
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")

        if isinstance(fileName, (str, bytes)):
            self._handle.read(str2bytes(fileName),
                              self._raster_handler._handle,
                              _json_config)

# write raster to JSON file
# @this: an instance of raster class
# @file_name: name of the file (string type) to be written
#
    def write(self, fileName: str, jsonConfig: Optional[Union[str, Dict]] = None,
              input_raster: "raster.Raster" = None):
        '''write raster to JSON file

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
        >>> file_name = "testRasterA.json"
        >>> raster_json = JsonHandler(input_raster=this)
        >>> raster_json.write(file_name)
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
                    "Need input_raster or a raster object in JsonHandler")

    def toJson(self, input_raster: Optional[Union["raster.Raster",
                                                  "raster.RasterFile"]] = None,
               compress: Optional[bool] = True,
               jsonConfig: Optional[Union[Dict, str]] = None) -> Dict:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        input_raster : Optional[Union[raster.Raster, raster.RasterFile]], optional
            _description_, by default None
        compress : Optional[bool], optional
            _description_, by default True
        jsonConfig : Optional[Union[Dict, str]], optional
            _description_, by default None

        Returns
        -------
        Dict
            _description_
        """
        _out = "{}"

        if jsonConfig is None:
            _json_config = str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = str2bytes(json.dumps(jsonConfig))

        if input_raster is not None:
            if not isinstance(input_raster, (raster.Raster, raster.RasterFile)):
                raise TypeError(
                    "input_raster should be an instance of raster.Raster")
            if hasattr(self, '_handle'):
                cy_obj = "_handle"
                if hasattr(getattr(self, "_handle"), "cy_raster_obj"):
                    cy_obj = "_handle.cy_raster_obj"

            _out = self._handle.toJson(cy_obj, compress,
                                       _json_config)
        else:
            if hasattr(self, "_raster_handler"):
                _out = self._handle.toJson(self.raster._handle,
                                          compress, _json_config)
            else:
                raise RuntimeError(
                    "Need input_raster or a raster object in JsonHandler")
        out = json.loads(_out)
        return out

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
                "Mismatch between data type of JsonHandler and input_raster")
        self._raster_handler = input_raster

    @staticmethod
    def to_raster(fileName: str, dtype: np.dtype = REAL,
                  jsonConfig: Optional[Union[str, Dict]] = None) -> "JsonHandler":
        """
        Examples
        --------
        >>> test = Raster()
        >>> JsonHandler.to_raster(test, "testRasterA.json")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        json_handler = JsonHandler(dtype=dtype)
        json_handler.read(fileName, jsonConfig=jsonConfig)
        return json_handler

    @staticmethod
    def from_raster(output_raster: "raster.Raster", fileName: str,
                    jsonConfig: Optional[Union[Dict, str]] = None):
        """
        Examples
        --------
        >>> test = Raster(name="testRasterA")
        >>> test.init(nx=5, ny=5, hx=1.0, hy=1.0)
        >>> file_name = "testRasterA.json"
        >>> JsonHandler.from_raster(test, file_name, "")
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        if isinstance(output_raster, raster.Raster):
            json_handler = JsonHandler(dtype=output_raster.base_type)
            json_handler.write(fileName, jsonConfig=jsonConfig,
                               input_raster=output_raster)
        else:
            raise TypeError(
                "output_raster should be an instance of raster.Raster class")

    @staticmethod
    def readJsonFile(fileName: str, dtype: np.dtype = REAL,
                    jsonConfig: Union[str, Dict] = None) -> "JsonHandler":
        """
        Examples
        --------
        >>> file_name = "testRasterA.json"
        >>> out = JsonHandler.readJsonFile(file_name)
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)
        json_handler = JsonHandler(dtype=dtype)
        json_handler.read(fileName, jsonConfig=jsonConfig)
        return json_handler

    def __repr__(self):
        return self.__class__.__name__
