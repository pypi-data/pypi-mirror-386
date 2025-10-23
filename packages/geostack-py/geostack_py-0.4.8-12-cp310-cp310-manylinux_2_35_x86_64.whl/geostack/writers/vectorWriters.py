# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import os.path as pth
import sqlite3
from sqlite3 import Error
import numpy as np
from typing import Optional, Union, List, Any
from functools import partial
import warnings
from contextlib import closing
import numbers
from ctypes.util import find_library

from .. import gs_enums
from .. import readers
from ..dataset.supported_libs import HAS_GPD, RequireLib, HAS_SPATIALITE

if HAS_GPD:
    import geopandas as gpd
    if not hasattr(gpd, "GeoDataFrame"):
        HAS_GPD = False
        warnings.warn("Geopandas is not installed correctly", ImportWarning)
    else:
        from shapely import wkt
        try:
            from geopandas.geodataframe import CRS
        except ImportError:
            from pyproj.crs import CRS
        import pandas as pd

from ..vector import vector
from ..io import vectorItemToGeoWKT
from ..gs_enums import GeometryType

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

__all__ = ["to_geopandas", "to_database"]

try:
    from dataclasses import dataclass

    @dataclass
    class DbFlags:
        Polygon: int = 0
        Point: int = 0
        LineString: int = 0
except ImportError:
    class DbFlags:
        __slots__ = ()
        Polygon: int = 0
        Point: int = 0
        LineString: int = 0


@RequireLib("geopandas")
@RequireLib("shapely")
def from_wkt(input_vector: "vector.Vector") -> Union[List[str], np.ndarray]:
    """convert a vector object to a list (or ndarray) of geowkt strings.

    Parameters
    ----------
    input_vector : vector.Vector
        an instance of a vector object

    Returns
    -------
    Union[List[str], np.ndarray]
        a list (or ndarray) of geowkt strings.
    """

    item_to_wkt = partial(vectorItemToGeoWKT, input_vector)
    if hasattr(gpd.GeoSeries, "from_wkt"):
        method = getattr(gpd.GeoSeries, "from_wkt")
        geom_arr = list(map(item_to_wkt, input_vector.getGeometryIndexes()))
    else:
        method = getattr(gpd, "GeoSeries")
        geoms = map(wkt.loads, map(
            item_to_wkt, input_vector.getGeometryIndexes()))
        geom_arr = np.array(list(geoms), dtype=object)

    try:
        out = method(geom_arr)
    except MemoryError:
        for i, geom in enumerate(geom_arr, 0):
            if i == 0:
                out = method([geom])
            else:
                if hasattr(out, 'append'):
                    out = out.append(method([geom]))
                elif hasattr(gpd, 'concat'):
                    out = gpd.concat([out, method([geom])])
    return out


@RequireLib("geopandas")
def to_geopandas(vector_object: "vector.Vector", file_path: Optional[str] = None):
    """Create geopandas object from Vector object.

    Parameters
    ----------
    vector_object: vector.Vector
        an instance of vector object
    file_path: str, Optional
        name of outfile file to write, default is None

    Returns
    -------
    out: geopandas.GeoDataFrame
        an instance of geopandas data from instantiated from vector object

    Examples
    --------
    >>> from geostack.vector import Vector
    >>> from geostack.utils import get_epsg

    >>> vec = Vector()
    >>> vec.addPoint([0, 0])
    >>> vec.setProjectionParameters(get_epsg(4326))
    >>> df = to_geopandas(vec)
    """
    _check_input_args(vector_object, file_path)

    # get projection parameters from the Vector object
    vec_proj = vector_object.getProjectionParameters().to_proj4()
    if len(vec_proj) > 0:
        crs = CRS.from_proj4(vec_proj)
    else:
        crs = None
    # convert geometries to GeoSeries
    vec_ds = from_wkt(vector_object)

    # get the properties
    prop_names = vector_object.properties.getPropertyNames()
    prop_values = {prop: vector_object.properties.getProperty(prop)
                   for prop in prop_names}
    prop_values.update({"geometry": vec_ds})

    # create geopandas GeoDataFrame
    out = gpd.GeoDataFrame(prop_values, crs=crs)

    if file_path is not None:
        if pth.splitext(file_path)[-1].lower()(".shp"):
            out.to_file(file_path)
        elif pth.splitext(file_path)[-1].lower() in ['.json', '.geojson']:
            out.to_file(file_path, driver="GeoJSON")
    else:
        return out


@RequireLib("spatialite")
def to_database(inp_vector: "vector.Vector",
                file_name: Optional[str] = None,
                epsg_code: int = 4326,
                geom_type: "GeometryType" = GeometryType.Polygon):
    """Create a SQLite database from Vector object.

    Parameters
    ----------
    input_vector: vector.Vector
        an instance of vector object
    file_name: str
        name of outfile file to write
    epsg_code: int
        epsg code for the projection of vector object,
        this is used to specify SRID in the database
    geom_type: GeometryType.Polygon
        geometry type to write to the database

    Returns
    -------
    Nil

    Examples
    --------
    >>> from geostack.vector import Vector
    >>> from geostack.utils import get_epsg

    >>> vec = Vector()
    >>> vec.addPoint([0, 0])
    >>> vec.setProjectionParameters(get_epsg(4326))

    >>> to_database(vec, "test.sqlite", epsg_code=4326, geom_type=GeometryType.Point)
    """
    _check_input_args(inp_vector, file_name)

    db_flags = DbFlags()

    # get the properties
    prop_names = list(filter(lambda prop: inp_vector.getProperties().getPropertyStructure(prop) == gs_enums.PropertyStructure.Vector,
                             inp_vector.properties.getPropertyNames()))
    prop_types = {prop: inp_vector.properties.getPropertyType(prop)
                  for prop in prop_names}

    # create column name string from property names
    prop_columns = []
    for prop in prop_names:
        prop_type = prop_types.get(prop)
        if prop_type == int:
            prop_columns.append(f"{prop} INTEGER")
        elif prop_type == float:
            prop_columns.append(f"{prop} FLOAT")
        elif prop_type == str:
            prop_columns.append(f"{prop} VARCHAR(2048)")
    prop_columns = ','.join(prop_columns)
    geom_idx = inp_vector.getGeometryIndexes()

    db_file_name = os.environ.get("SPATIALITE_DB_PATH", file_name)

    if pth.exists(db_file_name):
        raise FileNotFoundError(
            f"file {file_name} exists, specify a different name")

    # name of the table for the DB
    db_name = pth.splitext(pth.basename(db_file_name))[0]
    db_name = db_name.replace("-", "_")

    # open database and write data
    with closing(sqlite3.connect(f"file:{db_file_name}?mode=rwc",
                                 check_same_thread=False,
                                 uri=True)) as conn:
        conn.enable_load_extension(True)
        try:
            conn.load_extension(os.environ.get("SPATIALITE_LIBRARY_PATH",
                                               "mod_spatialite"))
        except sqlite3.OperationalError:
            lib_path = find_library("mod_spatialite")
            if lib_path is not None:
                conn.load_extension(lib_path)
        conn.enable_load_extension(False)
        conn.execute("SELECT InitSpatialMetadata();")
        cursor = conn.cursor()

        executor = partial(readers.DBHandler.execute_command, cursor)

        # ascertain the geometries to be written
        table_names = []
        for item, value in [["Point", inp_vector.getPointCount()],
                            ["LineString", inp_vector.getLineStringCount()],
                            ["Polygon", inp_vector.getPolygonCount()]]:
            if value > 0:
                table_names.append(item)

        for name in table_names:
            geom_id = "GEOM_ID"
            executor(f"""CREATE TABLE {db_name.upper()}_{name}(
                     {geom_id} INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, {prop_columns});""")

            if getattr(db_flags, name) != 1:
                if epsg_code is not None:
                    executor(
                        f"SELECT AddGeometryColumn('{db_name.upper()}_{name}', 'geometry', {epsg_code}, '{name.upper()}', 2);")
                else:
                    executor(
                        f"SELECT AddGeometryColumn('{db_name.upper()}_{name}', 'geometry', '{name.upper()}', 2);")
                executor(
                    f"SELECT CreateMbrCache('{db_name.upper()}_{name}', 'geometry');")
                setattr(db_flags, name, 1)

        # iterate through the geometries
        for i, idx in enumerate(geom_idx, 0):
            geom_type = inp_vector.getGeometryType(idx)

            if geom_type == GeometryType.Polygon:
                name = "Polygon"
            elif geom_type == GeometryType.LineString:
                name = "LineString"
            elif geom_type == GeometryType.Point:
                name = "Point"

            # get the WKT string for the geometry
            geom_wkt = vectorItemToGeoWKT(inp_vector, idx)

            prop_values = map(
                lambda item: fix_nan(inp_vector.getProperty(idx, item)), prop_names)
            prop_values = ','.join(map(value_to_str, prop_values))

            # write the row information to the database
            cmd = f"INSERT INTO {db_name.upper()}_{name}({','.join(prop_names)},geometry)"
            if epsg_code is not None:
                cmd += f" VALUES({prop_values},GeomFromText('{geom_wkt}', {epsg_code}));"
            else:
                cmd += f" VALUES({prop_values},GeomFromText('{geom_wkt}'));"
            executor(cmd)
        conn.commit()
        cursor.close()


def value_to_str(value: Any) -> str:
    """convert a property value to str

    Parameters
    ----------
    value : Any
        a property value to be written to database

    Returns
    -------
    str
        a property value converted to str
    """
    if value == 'NULL':
        return value
    elif isinstance(value, str):
        return f"'{value}'"
    elif isinstance(value, numbers.Integral):
        return f"{value:d}"
    elif isinstance(value, numbers.Real):
        return f"{value:f}"
    else:
        return f"{value}"


def fix_nan(item: Any) -> Any:
    """fix nan with Null value for SQlite

    Parameters
    ----------
    item : Any
        a value of property

    Returns
    -------
    Any
        a value replaced with null value when possible
    """
    if isinstance(item, numbers.Real):
        if np.isnan(item):
            return 'NULL'
        else:
            return item
    elif item is None:
        return 'NULL'
    else:
        return item


def _check_input_args(vector_object: "vector.Vector", file_path: str = None):
    """internal function to check the arguments for geopandas writer

    Parameters
    ----------
    vector_object : vector.Vector
        an instance of vector object
    file_path : str, optional
        path of the file to be written, by default None

    Raises
    ------
    TypeError
        input vector should be an instance of Vector
    TypeError
        input file path should be a string
    ValueError
        path doesn't exist
    """
    if not isinstance(vector_object, vector.Vector):
        raise TypeError("Input vector object should be an instance of Vector")
    if file_path is not None:
        if not isinstance(file_path, str):
            raise TypeError("Input file path should be a string")
        if not pth.isdir(pth.dirname(file_path)):
            raise ValueError(f"path {pth.dirname(file_path)} doesn't exist")
