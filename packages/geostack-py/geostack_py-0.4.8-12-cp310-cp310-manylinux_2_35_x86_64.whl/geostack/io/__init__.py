# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import io
import csv
from typing import Union, Optional
import numpy as np
from .geo_json import geoJsonToVector, vectorToGeoJson
from .shapefile import shapefileToVector, vectorToShapefile
from .ascii import AsciiHandler
from .flt import FltHandler
from .gsr import GsrHandler
from .raster_json import JsonHandler
from .geotiff import GeoTIFFHandler
from .netcdf import NetCDFHandler
from .geowkt import (geoWKTToVector,
                     vectorToGeoWKT,
                     vectorItemToGeoWKT,
                     parseString,
                     parseStrings)
from .. import gs_enums
from .. import vector
from .. import core


def vectorToCSV(inpVector: "vector.Vector", filename: Optional[str] = None) -> Union[None, io.StringIO]:
    """write a vector object to a CSV file.

    Parameters
    ----------
    inpVector : Vector
        an instance of a Vector object
    filename : str, optional, default is None
        name and path of the csv file being written

    Returns
    -------
    Union[io.StringIO, None]
        StringIO buffered object when filename is None, None otherwise

    Examples
    --------
    >>> from geostack.vector import Vector
    >>> from geostack.utils import get_epsg
    >>> vec = Vector()
    >>> vec.addPoint([0, 0])
    >>> vec.setProjectionParameters(get_epsg(4326))
    >>> vectorToCSV(vec, "test.csv")
    """

    if filename is not None:
        out = open(filename, 'w')
        dataout = csv.writer(out, delimiter=',')
    else:
        dataout = io.StringIO()

    prop_names = list(filter(lambda prop: inpVector.getProperties().getPropertyStructure(prop) == gs_enums.PropertyStructure.Vector,
                             inpVector.properties.getPropertyNames()))
    header = ["WKT"] + [item for item in prop_names]
    if filename is None:
        dataout.write(','.join(header) + '\n')
    else:
        dataout.writerow(header)

    geom_idx = inpVector.getGeometryIndexes()

    for i in geom_idx:
        row = [vectorItemToGeoWKT(inpVector, i)]
        row += [inpVector.getProperty(i, name) for name in prop_names]
        if filename is None:
            row_values = [item if isinstance(
                item, str) else f'{item}' for item in row]
            if i < geom_idx.size - 1:
                dataout.write(','.join(row_values) + '\n')
            else:
                dataout.write(','.join(row_values))
        else:
            dataout.writerow(row)

    if filename is not None:
        out.close()
    else:
        return dataout


def csvToVector(filename: str, dtype: np.dtype = np.float32) -> "vector.Vector":
    """Read a csv file to a Vector object

    Parameters
    ----------
    filename : str
        name and path of the csv being read
    dtype : np.dtype, optional
        data type of the Vector object, by default np.float32

    Returns
    -------
    Vector
        an instance of Vector object created from CSV file

    Raises
    ------
    RuntimeError
        No WKT column found in header
    RuntimeError
        No WKT geometry was added to Vector object

    Examples
    --------
    >>> cat test.csv
    id,WKT,name
    0,"POINT (0 0)",dummy

    >>> vec = csvToVector("test.csv")
    >>> vec.getPointIndexes().size
    1
    """
    out = vector.Vector(dtype=dtype)
    props = {}
    with open(filename, 'r') as inp:
        datainp = csv.reader(inp, delimiter=',', skipinitialspace=True)
        for i, row in enumerate(datainp, 0):
            if i == 0:
                idx = None
                header = []
                columns = []
                for k, item in enumerate(row, 0):
                    if isinstance(item, (str, bytes)):
                        if core.str2bytes(item).lower() != b"wkt":
                            header.append(item)
                            columns.append(k)
                        else:
                            idx = k
                    else:
                        columns.append(k)
                        header.append(item)
                if idx is None:
                    raise RuntimeError("No WKT column found in header")

                props = {item: [] for item in header}
            else:
                parseString(out, row[idx])
                for k, name in zip(columns, header):
                    props[name].append(row[k])

    if out.getGeometryIndexes().size == 0:
        raise RuntimeError("No WKT geometry was added to Vector object")

    for key in props:
        out.setPropertyValues(key, props[key])
    return out
