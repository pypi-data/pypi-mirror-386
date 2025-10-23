# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os.path as pth
import numpy as np
from typing import List
from ._cy_geowkt import (geoWKT_d, geoWKT_f)
from .. import vector
from .. import core
from ..vector._cy_vector import _Vector_d, _Vector_f
from ..core import REAL, str2bytes

__all__ = ["geoWKTToVector", "vectorToGeoWKT",
           "vectorItemToGeoWKT", "parseString",
           "parseStrings"]


def geoWKTToVector(this: str, dtype: np.dtype = REAL) -> "vector.Vector":
    '''Convert geoWKT to a vector object

    Parameters
    ----------
    this: str
        a WKT string or a file name
    dtype: np.float32/np.float64 (Optional)
        data type of vector class

    Returns
    -------
    out: Vector object
        An instance of vector class

    Examples
    --------
    >>> import numpy as np
    >>> out = geoWKTToVector(_TEST_WKT, dtype=np.float32)
    '''
    if isinstance(this, str):
        if dtype is not None:
            if dtype != np.float32 and dtype != np.float64:
                raise ValueError(
                    "dtype can be either numpy.float32 or numpy.float64")
        if dtype is None:
            if this.rstrip().endswith(")"):
                if pth.isfile(this):
                    out = geoWKT_f.geoWKTFileToVector(str2bytes(this))
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                out = geoWKT_f.geoWKTToVector(str2bytes(this))
        elif dtype == np.float32:
            if not this.rstrip().endswith(")"):
                if pth.isfile(this):
                    out = geoWKT_f.geoWKTFileToVector(str2bytes(this))
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                out = geoWKT_f.geoWKTToVector(str2bytes(this))
        elif dtype == np.float64:
            if not this.rstrip().endswith(")"):
                if pth.isfile(this):
                    out = geoWKT_d.geoWKTFileToVector(str2bytes(this))
                else:
                    raise FileNotFoundError(f"file {this} doesn't exist")
            else:
                out = geoWKT_d.geoWKTToVector(str2bytes(this))
        return vector.Vector._from_vector(out)
    else:
        raise TypeError("%s is not an acceptable type of argument" %
                        type(this).__name__)


def vectorToGeoWKT(this: "vector.Vector") -> str:
    '''Convert vector object to a geowkt object

    Parameters
    ----------
    this: Vector object
        An instance of vector class

    Returns
    -------
    out: str
        A GeoWKT string

    Examples
    --------
    >>> import numpy as np
    >>> this = geoWKTToVector(_TEST_WKT, dtype=np.float32)
    >>> out = vectorToGeoWKT(this)
    '''
    if isinstance(this, (vector.Vector, _Vector_d, _Vector_f)):
        if isinstance(this, vector.Vector):
            if this._dtype == np.float32:
                out = geoWKT_f.vectorToGeoWKT(this._handle)
            elif this._dtype == np.float64:
                out = geoWKT_d.vectorToGeoWKT(this._handle)
        elif isinstance(this, _Vector_d):
            out = geoWKT_d.vectorToGeoWKT(this)
        elif isinstance(this, _Vector_f):
            out = geoWKT_f.vectorToGeoWKT(this)
        return out.decode()
    else:
        raise TypeError(
            "Incorrect input type, only instance of vector python or cython class")


def vectorItemToGeoWKT(this: "vector.Vector", index: int) -> str:
    '''Convert vector object to a geowkt object

    Parameters
    ----------
    this: Vector object
        An instance of vector class
    index: int
        index of the geometry object

    Returns
    -------
    out: str
        A GeoWKT string

    Examples
    --------
    >>> import numpy as np
    >>> this = geoWKTToVector(_TEST_WKT, dtype=np.float32)
    >>> out = vectorItemToGeoWKT(this, 0)
    '''
    if isinstance(this, (vector.Vector, _Vector_d, _Vector_f)):
        if isinstance(this, vector.Vector):
            if this._dtype == np.float32:
                out = geoWKT_f.vectorItemToGeoWKT(this._handle, index)
            elif this._dtype == np.float64:
                out = geoWKT_d.vectorItemToGeoWKT(this._handle, index)
        elif isinstance(this, _Vector_d):
            out = geoWKT_d.vectorItemToGeoWKT(this, index)
        elif isinstance(this, _Vector_f):
            out = geoWKT_f.vectorItemToGeoWKT(this, index)
        return core.bytes2str(out)
    else:
        raise TypeError(
            "Incorrect input type, only instance of vector python or cython class")


def parseString(this: "vector.Vector", geoWKTStr: str) -> np.ndarray:
    '''Convert geowkt string to a vector geometry and add to a Vector object

    Parameters
    ----------
    this: Vector object
        An instance of vector class
    geoWKTStr: str
        a vector geometry as a geowkt string

    Returns
    -------
    out: np.ndarray[np.uint32]
        an ndarray with indices of geometries added

    Examples
    --------
    >>> import numpy as np
    >>> this = geoWKTToVector(_TEST_WKT, dtype=np.float32)
    >>> out = parseString(this, _TEST_WKT)
    '''

    if isinstance(this, vector.Vector):
        obj = this._handle
    elif isinstance(this, (_Vector_d, _Vector_f)):
        obj = this

    if this._dtype == np.float32:
        out = geoWKT_f.parseString(obj, core.str2bytes(geoWKTStr))
    elif this._dtype == np.float64:
        out = geoWKT_d.parseString(obj, core.str2bytes(geoWKTStr))
    return np.asanyarray(out)


def parseStrings(this: "vector.Vector", geoWKTStrList: List[str]) -> np.ndarray:
    '''Convert a list of geowkt strings to vector geometries and add to a Vector object

    Parameters
    ----------
    this: Vector object
        An instance of vector class
    geoWKTStrList: List[str]
        a list of vector geometries as a list of geowkt string

    Returns
    -------
    out: np.ndarray[np.uint32]
        an ndarray with indices of geometries added

    Examples
    --------
    >>> import numpy as np
    >>> this = geoWKTToVector(_TEST_WKT, dtype=np.float32)
    >>> out = parseStrings(this, [_TEST_WKT])
    '''

    if isinstance(this, vector.Vector):
        obj = this._handle
    elif isinstance(this, (_Vector_d, _Vector_f)):
        obj = this

    wkt_string_list = list(map(core.str2bytes, geoWKTStrList))

    if this._dtype == np.float32:
        out = geoWKT_f.parseStrings(
            obj, wkt_string_list)
    elif this._dtype == np.float64:
        out = geoWKT_d.parseStrings(
            obj, wkt_string_list)
    return np.asanyarray(out)
