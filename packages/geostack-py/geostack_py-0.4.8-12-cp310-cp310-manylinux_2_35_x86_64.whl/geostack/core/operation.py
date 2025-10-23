# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
from typing import Dict, Union, List, Tuple
import re
import json
from pathlib import Path
import numpy as np
from .json11 import Json11
from ._cy_operation import Operation_d, Operation_f, cy_readYaml
from .property import REAL
from . import str2bytes
from .. import vector
from .. import raster

__all__ = ["Operation", "readYaml"]

def readYaml(configFile: Union[str, bytes]) -> Json11:
    """read YAML file and parse into a JSON11 object

    Parameters
    ----------
    configFile : str
        path of YAML config file or YAML configfile contents as string

    Returns
    -------
    Json11
        JSON11 object from parsed YAML file
    """

    if re.search(":", configFile) is not None:
        configFileStr = str2bytes(configFile)
    elif Path(configFile).is_file():
        with open(configFile, 'r') as inp:
            configFileStr = str2bytes(inp.read())
    else:
        raise ValueError(f"Unable to deduce configFile value {configFile}")

    out = Json11()
    out._handle = cy_readYaml(configFileStr)
    return out

class Operation:
    def __init__(self, dtype: np.dtype=REAL) -> None:
        self._dtype = dtype
        if self._dtype == np.float64:
            self._obj = Operation_d
        else:
            self._obj = Operation_f

    def runFromConfigFile(self, configFileName: str) -> None:
        """run Operation from config file

        Parameters
        ----------
        configFileName : str
            path to configFile
        """
        self._obj.runFromConfigFile(str2bytes(configFileName))

    def run(self, jsonConfig: Union[str, Dict, List],
            raster_list: Union[List[Union['raster.Raster',
                                          'raster.RasterFile',
                                          'raster.RasterBase']],
                               'raster.RasterPtrList'],
            vector_list: Union[List['vector.Vector'], 'vector.VectorPtrList']) -> None:
        """run Operation specified in json config over a list of Rasters and Vectors

        Parameters
        ----------
        jsonConfig : Union[Dict, str]
            configuration for Operation as json string or dictionary
        raster_list : List[Union[raster.Raster, raster.RasterFile, raster.RasterBase]]
            list of Rasters
        vector_list : List[vector.Vector]
            list of Vectors
        """
        if isinstance(raster_list, raster.RasterPtrList):
            _raster_list = raster_list
        else:
            _raster_list = raster.RasterPtrList(raster_list, dtype=self._dtype)

        if isinstance(vector_list, vector.VectorPtrList):
            _vector_list = vector_list
        else:
            _vector_list = vector.VectorPtrList(vector_list, dtype=self._dtype)

        if isinstance(jsonConfig, str):
            _jsonConfig = str2bytes(jsonConfig)
        elif isinstance(jsonConfig, (dict, list)):
            _jsonConfig = str2bytes(json.dumps(jsonConfig))

        self._obj.run(_jsonConfig,
                      _raster_list._handle,
                      _vector_list._handle)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "<class 'geostack.core.%s>'" % (self.__class__.__name__)
