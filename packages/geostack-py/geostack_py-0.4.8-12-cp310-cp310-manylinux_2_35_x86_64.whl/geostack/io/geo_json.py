# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os.path as pth
import numpy as np
import json
from ._cy_geojson import (geoJson_d, geoJson_f)
from .. import vector
from ..vector._cy_vector import _Vector_d, _Vector_f
from collections import OrderedDict
from typing import Union, Dict
from ..dataset import import_or_skip
from pathlib import PurePath
from ..core import REAL, str2bytes

global HAS_GEOJSON

geojson, HAS_GEOJSON = import_or_skip("geojson")


__all__ = ["geoJsonToVector", "vectorToGeoJson"]


def geoJsonToVector(this: Union[Dict, str], enforceProjection: bool = True,
                    dtype: np.dtype = REAL) -> "vector.Vector":
    '''Convert geojson to a vector object

    Parameters
    ----------
    this: dict/json/str
        A python dictionary or a json string or a file name
    enforceProjection: bool
        Set projection to EPSG:4326
    dtype: np.float32/np.float64 (Optional)
        data type of vector class

    Returns
    -------
    out: Vector object
        An instance of vector class

    Examples
    --------
    >>> import numpy as np
    >>> out = geoJsonToVector(_TEST_GSON, dtype=np.float32)
    '''
    if isinstance(this, (dict, OrderedDict)):
        if dtype is not None:
            if dtype != np.float32 and dtype != np.float64:
                raise ValueError(
                    "dtype can be either numpy.float32 or numpy.float64")
        if dtype is None:
            out = geoJson_f.geoJsonToVector(str2bytes(json.dumps(
                this)), enforceProjection)
        elif dtype == np.float32:
            out = geoJson_f.geoJsonToVector(str2bytes(json.dumps(
                this)), enforceProjection)
        elif dtype == np.float64:
            out = geoJson_d.geoJsonToVector(str2bytes(json.dumps(
                this)), enforceProjection)
        return vector.Vector._from_vector(out)
    elif isinstance(this, str):
        if dtype is not None:
            if dtype != np.float32 and dtype != np.float64:
                raise ValueError(
                    "dtype can be either numpy.float32 or numpy.float64")
        if dtype is None:
            if not this.lstrip().startswith("{"):
                if pth.isfile(this):
                    if isinstance(this, PurePath):
                        this = str(this)
                    out = geoJson_f.geoJsonFileToVector(
                        str2bytes(this), enforceProjection)
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                out = geoJson_f.geoJsonToVector(
                    str2bytes(this), enforceProjection)
        elif dtype == np.float32:
            if not this.lstrip().startswith("{"):
                if pth.isfile(this):
                    if isinstance(this, PurePath):
                        this = str(this)

                    out = geoJson_f.geoJsonFileToVector(
                        str2bytes(this), enforceProjection)
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                if isinstance(this, PurePath):
                    this = str(this)

                out = geoJson_f.geoJsonToVector(
                    str2bytes(this), enforceProjection)
        elif dtype == np.float64:
            if not this.lstrip().startswith("{"):
                if pth.isfile(this):
                    if isinstance(this, PurePath):
                        this = str(this)
                    out = geoJson_d.geoJsonFileToVector(
                        str2bytes(this), enforceProjection)
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                out = geoJson_d.geoJsonToVector(
                    str2bytes(this), enforceProjection)
        return vector.Vector._from_vector(out)
    else:
        raise TypeError("%s is not an acceptable type of argument" %
                        type(this).__name__)


def vectorToGeoJson(this: "vector.Vector", enforceProjection: bool = True,
                    writeNullProperties: bool = False) -> str:
    '''Convert vector object to a geojson object

    Parameters
    ----------
    this: Vector object
        An instance of vector class
    enforceProjection: bool
        Force projection of output to EPSG:4326

    Returns
    -------
    out: str
        A GeoJSON string

    Examples
    --------
    >>> import numpy as np
    >>> this = geoJsonToVector(_TEST_GSON, dtype=np.float32)
    >>> out = vectoToGeoJson(this)
    '''
    if isinstance(this, (vector.Vector, _Vector_d, _Vector_f)):
        if isinstance(this, vector.Vector):
            if this._dtype == np.float32:
                out = geoJson_f.vectorToGeoJson(this._handle,
                                                enforceProjection=enforceProjection,
                                                writeNullProperties=writeNullProperties)
                return out
            elif this._dtype == np.float64:
                out = geoJson_d.vectorToGeoJson(this._handle,
                                                enforceProjection=enforceProjection,
                                                writeNullProperties=writeNullProperties)
                return out
        elif isinstance(this, _Vector_d):
            out = geoJson_d.vectorToGeoJson(this,
                                            enforceProjection=enforceProjection,
                                            writeNullProperties=writeNullProperties)
            return out
        elif isinstance(this, _Vector_f):
            out = geoJson_f.vectorToGeoJson(this,
                                            enforceProjection=enforceProjection,
                                            writeNullProperties=writeNullProperties)
            return out
    else:
        raise TypeError(
            "Incorrect input type, only instance of vector python or cython class")
