# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
from typing import Optional, Dict, Union
import numpy as np
from ._cy_shapefile import shapefile_d, shapefile_f
from ..vector._cy_vector import _Vector_d, _Vector_f
from .. import core
from .. import vector
from .. import gs_enums
from .. import core
from pathlib import PurePath
from ..core import REAL


__all__ = ["shapefileToVector", "vectorToShapefile"]


def shapefileToVector(filename: str, boundingBox: Optional["vector.BoundingBox"] = None,
                      boundRegionProj: Optional['core.ProjectionParameters'] = None,
                      jsonConfig : Union[Dict, str] = "", dtype: np.dtype = REAL) -> "vector.Vector":
    """Read a shapefile into a Vector object.

    Parameters
    ----------
    filename : str
        path of the shapefile
    boundingBox: BoundingBox, optional
        an instance of BoundingBox object
    boundRegionProj: ProjectionParameters, optional
        projection of the boundingBox
    jsonConfig : Union[dict, str]
        configuration parameters are json string or dictionary
    dtype : np.dtype, optional
        data type for the instance of the Vector object, by default np.float32

    Returns
    -------
    Vector
        an instance of a Vector object

    Raises
    ------
    ValueError
        `dtype` can be either numpy.float32 or numpy.float64
    TypeError
        data type of `filename` is not acceptable
    """
    if boundingBox is None:
        bounds = boundingBox
    elif isinstance(boundingBox, vector.BoundingBox):
        bounds = boundingBox._handle
    elif isinstance(boundingBox, (vector._BoundingBox_d,
                                  vector._BoundingBox_f)):
        bounds = boundingBox
    else:
        raise TypeError("Bounding box is not of valid type")

    if boundRegionProj is None:
        boundRegionProj = core.ProjectionParameters()._handle
    elif isinstance(boundRegionProj, core.ProjectionParameters):
        boundRegionProj = boundRegionProj._handle
    elif isinstance(boundRegionProj, core._ProjectionParameters_d):
        boundRegionProj = boundRegionProj
    else:
        raise TypeError("Bound region projection is not of valid type")
    if isinstance(jsonConfig, dict):
        _jsonConfig = core.str2bytes(json.dumps(jsonConfig))
    elif isinstance(jsonConfig, (str, bytes)):
        _jsonConfig = core.str2bytes(jsonConfig)
    else:
        raise TypeError("unable to deduce type of jsonConfig")

    if isinstance(filename, str):
        if isinstance(filename, PurePath):
            filename = str(filename)

        if dtype is not None:
            if dtype != np.float32 and dtype != np.float64:
                raise ValueError(
                    "dtype can be either numpy.float32 or numpy.float64")
        if dtype is None:
            out = shapefile_f.shapefileToVector(core.str2bytes(filename),
                                                boundingBox=bounds,
                                                boundRegionProj=boundRegionProj,
                                                jsonConfig=_jsonConfig)
        elif dtype == np.float32:
            out = shapefile_f.shapefileToVector(core.str2bytes(filename),
                                                boundingBox=bounds,
                                                boundRegionProj=boundRegionProj,
                                                jsonConfig=_jsonConfig)
        elif dtype == np.float64:
            out = shapefile_d.shapefileToVector(core.str2bytes(filename),
                                                boundingBox=bounds,
                                                boundRegionProj=boundRegionProj,
                                                jsonConfig=_jsonConfig)
    else:
        raise TypeError(
            f"{type(filename).__name__} is not an acceptable type of argument")

    return vector.Vector._from_vector(out)


def vectorToShapefile(vectorInp: "vector.Vector", filename: str,
                      geom_type: Optional["gs_enums.GeometryType"] = None) -> bool:
    """write a vector object to a shapefile.

    Parameters
    ----------
    vectorInp : Vector
        an instance of a Vector object.
    filename : str
        path and name of the shapefile.
    geom_type : gs_enums.GeometryType, optional
        vector geometry type to save to shapefile, by default None

    Returns
    -------
    bool
        True if shapefile is written, False otherwise

    Raises
    ------
    ValueError
        No geometry type is specified
    TypeError
        `geom_type` should be an instance of gs_enums.GeometryType
    TypeError
        Incorrect input type, only instance of vector python or cython class
    """
    if geom_type is None:
        raise ValueError("No geometry type is specified")
    elif not isinstance(geom_type, gs_enums.GeometryType):
        raise TypeError(
            "'geom_type' should be an instance of gs_enums.GeometryType")

    if isinstance(filename, PurePath):
        filename = str(filename)

    if isinstance(vectorInp, (vector.Vector, _Vector_d, _Vector_f)):
        if isinstance(vectorInp, vector.Vector):
            if vectorInp._dtype == np.float32:
                out = shapefile_f.vectorToShapefile(vectorInp._handle,
                                                    core.str2bytes(filename),
                                                    geom_type.value)
            elif vectorInp._dtype == np.float64:
                out = shapefile_d.vectorToShapefile(vectorInp._handle,
                                                    core.str2bytes(filename),
                                                    geom_type.value)
        elif isinstance(vectorInp, _Vector_d):
            out = shapefile_d.vectorToShapefile(vectorInp,
                                                core.str2bytes(filename),
                                                geom_type.value)
        elif isinstance(vectorInp, _Vector_f):
            out = shapefile_f.vectorToShapefile(vectorInp,
                                                core.str2bytes(filename),
                                                geom_type.value)
    else:
        raise TypeError(
            "Incorrect input type, only instance of vector python or cython class")
    return out
