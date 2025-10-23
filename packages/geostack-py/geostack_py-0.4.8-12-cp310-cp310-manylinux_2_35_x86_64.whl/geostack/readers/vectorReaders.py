# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os
import time
import os.path as pth
import sqlite3
from sqlite3 import Error
from typing import Optional, List, Tuple, Any
from itertools import chain, repeat
import numpy as np
from ctypes.util import find_library
from .. import core
from ..dataset import supported_libs


if supported_libs.HAS_GDAL:
    from osgeo import ogr
    os.environ['GDAL_CACHEMAX'] = "100"

if supported_libs.HAS_GPD:
    import geopandas as gpd
    import pandas as pd

if supported_libs.HAS_PYSHP:
    import shapefile

if supported_libs.HAS_FIONA:
    import fiona

from .. import core, io, vector, raster
from .. import utils

__all__ = ['from_geopandas', "from_pyshp", "from_ogr", "from_fiona",
           'DBHandler']


@supported_libs.RequireLib("geopandas")
def get_column_names(this: Any):
    if isinstance(this, pd.DataFrame):
        column_names = this.columns
    elif isinstance(this, pd.Series):
        column_names = this.keys()
    return column_names


@supported_libs.RequireLib("fiona")
def from_fiona(file_path: str, dtype: np.dtype = core.REAL):
    """Create Vector object using fiona.

    Parameters
    ----------
    file_path: str/fiona.Collection
        path of the file to be read or a fiona Collection object
    dtype: np.dtype
        data type for the vector object to be created

    Returns
    -------
    vec: vector.Vector
        a vector object instantiated from fiona.Collection
    """

    def conform_type(inp):
        if isinstance(inp, float):
            if dtype == np.float64:
                return dtype(inp)
            else:
                return inp
        else:
            return inp

    if isinstance(file_path, str):
        datain = fiona.open(file_path, mode="r")
    elif isinstance(file_path, fiona.Collection):
        datain = file_path

    vec = vector.Vector(dtype=dtype)

    vec.setProjectionParameters(
        core.ProjectionParameters.from_wkt(datain.crs_wkt))

    for item in datain.keys():
        geom = datain[item]['geometry']
        props = datain[item]['properties']
        if geom['type'] == 'LineString':
            idx = vec.addLineString(geom['coordinates'])
            for prop in props:
                if props[prop] is None:
                    vec.setProperty(idx, prop, "")
                else:
                    vec.setProperty(idx, prop, conform_type(props[prop]))
        elif geom['type'] == "Point":
            idx = vec.addPoint(geom['coordinates'])
            for prop in props:
                if props[prop] is None:
                    vec.setProperty(idx, prop, "")
                else:
                    vec.setProperty(idx, prop, conform_type(props[prop]))
        elif geom['type'] in "Polygon":
            coords = np.squeeze(geom['coordinates'])
            if coords.ndim == 1:
                idx = vec.addPolygon([np.squeeze(_coords) for _coords in coords])
                for prop in props:
                    if props[prop] is None:
                        vec.setProperty(idx, prop, "")
                    else:
                        vec.setProperty(idx, prop, conform_type(props[prop]))
            else:
                idx = vec.addPolygon([coords])
                for prop in props:
                    if props[prop] is None:
                        vec.setProperty(idx, prop, "")
                    else:
                        vec.setProperty(idx, prop, conform_type(props[prop]))
        elif geom['type'] == "MultiPolygon":
            for coords in geom['coordinates']:
                try:
                    _coords = np.squeeze(coords)
                except:
                    _coords = coords

                if isinstance(_coords, list):
                    _multi_poly = []
                    for __coords in _coords:
                        _multi_poly.append(np.squeeze(__coords))
                    idx = vec.addPolygon(_multi_poly)
                    for prop in props:
                        if props[prop] is None:
                            vec.setProperty(idx, prop, "")
                        else:
                            vec.setProperty(idx, prop, conform_type(props[prop]))
                elif _coords.ndim == 1:
                    _multi_poly = []
                    for __coords in _coords:
                        _multi_poly.append(np.squeeze(__coords))
                    idx = vec.addPolygon(_multi_poly)
                    for prop in props:
                        if props[prop] is None:
                            vec.setProperty(idx, prop, "")
                        else:
                            vec.setProperty(idx, prop, conform_type(props[prop]))
                else:
                    idx = vec.addPolygon([_coords])
                    for prop in props:
                        if props[prop] is None:
                            vec.setProperty(idx, prop, "")
                        else:
                            vec.setProperty(idx, prop, conform_type(props[prop]))

    if isinstance(file_path, str):
        datain.close()
    return vec


@supported_libs.RequireLib("geopandas")
def from_geopandas(file_path: str, dtype: np.dtype = core.REAL):
    """Create Vector object using geopandas.

    Parameters
    ----------
    file_path: str/geopandas.GeoDataFrame
        path of the file to be read or a geopandas GeoDataFrame object
    dtype: np.dtype
        data type for the vector object to be created

    Returns
    -------
    vec: vector.Vector
        a vector object created from geopandas GeoDataFrame
    """
    if isinstance(file_path, str):
        datain = gpd.read_file(file_path)
    elif isinstance(file_path, (gpd.GeoDataFrame, gpd.GeoSeries)):
        datain = file_path

    try:
        # try with the native wkt reader
        column_names = filter(lambda item: item != "geometry", datain.columns)
        vec = vector.Vector(dtype=dtype)

        geom_to_wkt = lambda s: s.wkt
        multi_to_single = lambda s: ([geom_to_wkt(s)] if s.type not in ['MultiPolygon']
                                     else list(map(geom_to_wkt, s.geoms)))
        io.parseStrings(vec, chain.from_iterable(map(multi_to_single,
                                                     datain.geometry)))

        for column in column_names:
            prop_values = []
            for geom, value in zip(datain.geometry, datain[column].values):
                if geom.type in ['MultiPolygon']:
                    prop_values += repeat(value, len(geom.geoms))
                else:
                    prop_values += [value]
            vec.setPropertyValues(column, prop_values)

    except RuntimeError:
        # handle cases which are not yet supported in native reader
        vec = _from_geopandas(file_path, dtype)

    return vec


@supported_libs.RequireLib("geopandas")
def _from_geopandas(file_path: str, dtype: np.dtype = core.REAL):
    """Create Vector object using geopandas.

    Parameters
    ----------
    file_path: str/geopandas.GeoDataFrame
        path of the file to be read or a geopandas GeoDataFrame object
    dtype: np.dtype
        data type for the vector object to be created

    Returns
    -------
    vec: vector.Vector
        a vector object created from geopandas GeoDataFrame
    """
    prop_type_map = {"string": str,
                     "int": int,
                     "double": np.float64 if dtype == np.float64 else float}

    if isinstance(file_path, str):
        datain = gpd.read_file(file_path)
    elif isinstance(file_path, (gpd.GeoDataFrame, gpd.GeoSeries)):
        datain = file_path

    nrows = datain.shape[0]

    vec = vector.Vector(dtype=dtype)

    if isinstance(datain, gpd.GeoSeries):
        if datain.dtype.name != "geometry":
            raise TypeError("geoseries should be of dtype `geometry`")

    for i in range(nrows):
        if isinstance(datain, gpd.GeoDataFrame):
            _obj = datain.iloc[i]
            props = {'string':{}, 'int':{}, 'double':{}}
            for item in get_column_names(_obj):
                if item != "geometry":
                    if isinstance(getattr(_obj, item), str):
                        if _obj.get(item) is not None:
                            props['string'][item] = _obj.get(item)
                        else:
                            props['string'][item] = ""
                    elif isinstance(getattr(_obj, item), int):
                        if _obj.get(item) is not None:
                            props['int'][item] = _obj.get(item)
                        else:
                            props['string'][item] = ""
                    elif isinstance(getattr(_obj, item), float):
                        if _obj.get(item) is not None:
                            props['double'][item] = _obj.get(item)
                        else:
                            props['string'][item] = ""
            _geom = getattr(_obj, 'geometry')
        elif isinstance(datain, gpd.GeoSeries):
            _geom = datain.iloc[i]
        if _geom.type == 'MultiPolygon':
            for j, _geo_obj in enumerate(_geom, 0):
                _geo_coords = _geo_obj.__geo_interface__['coordinates']
                _coords = np.squeeze(_geo_coords)
                if _coords.ndim == 1:
                    _multi_poly = []
                    for k in range(len(_coords)):
                        __coords = np.squeeze(_coords[k])
                        _multi_poly.append(__coords)
                    poly_idx = vec.addPolygon(_multi_poly)
                    if isinstance(datain, gpd.GeoDataFrame):
                        for _item in props:
                            if len(props[_item]) > 0:
                                prop_type = prop_type_map.get(_item)
                                for _prop in props[_item]:
                                    vec.setProperty(poly_idx, _prop, props[_item][_prop], propType=prop_type)
                else:
                    poly_idx = vec.addPolygon([_coords])
                    if isinstance(datain, gpd.GeoDataFrame):
                        for _item in props:
                            if len(props[_item]) > 0:
                                prop_type = prop_type_map.get(_item)
                                for _prop in props[_item]:
                                    vec.setProperty(poly_idx, _prop, props[_item][_prop], propType=prop_type)
        elif _geom.type == 'Polygon':
            _geo_coords = _geom.__geo_interface__['coordinates']
            _coords = np.squeeze(_geo_coords)
            if _coords.ndim == 1:
                _coords = [np.squeeze(item) for item in _coords]
            else:
                _coords = [_coords]
            poly_idx = vec.addPolygon(_coords)
            if isinstance(datain, gpd.GeoDataFrame):
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(poly_idx, _prop, props[_item][_prop], propType=prop_type)
        elif _geom.type == "Point":
            idx = vec.addPoint([_geom.x, _geom.y])
            if isinstance(datain, gpd.GeoDataFrame):
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)
        elif _geom.type == "LineString":
            idx = vec.addLineString(list(_geo_obj))
            if isinstance(datain, gpd.GeoDataFrame):
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)

    # get projection information
    if hasattr(datain, "crs") and datain.crs is not None:
        proj_str = datain.crs.to_proj4()
        proj_params = core.ProjectionParameters.from_proj4(proj_str)
        vec.setProjectionParameters(proj_params)

    return vec


@supported_libs.RequireLib("gdal")
def from_ogr(file_path: str, dtype: np.dtype = core.REAL, **kwargs):
    """Create Vector object using GDAL's OGR.

    Parameters
    ----------
    file_path: str/fiona.Collection
        path of the file to be read or a ogr.DataSource/ogr.Layer object
    dtype: np.dtype
        data type for the vector object to be created

    Returns
    -------
    vec: vector.Vector
        a vector object created from a ogr.DataSource/ ogr.Layer
    """

    prop_type_map = {"string": str,
                     "int": int,
                     "int32": int,
                     "int64": int,
                     "double": np.float64 if dtype == np.float64 else float}

    driver = kwargs.get("driver")

    if isinstance(file_path, str):
        if pth.splitext(file_path)[-1].lower() == ".shp":
            driver = ogr.GetDriverByName("ESRI Shapefile")
        elif pth.splitext(file_path)[-1].lower() in [".json", ".geojson"]:
            driver = ogr.GetDriverByName("GeoJSON")
        if driver is not None:
            if isinstance(driver, str):
                driver = ogr.GetDriverByName(driver)
        assert driver is not None, "unable to get a driver"
        datain = driver.Open(file_path)
    elif isinstance(file_path, ogr.DataSource):
        datain = file_path
    elif isinstance(file_path, ogr.Layer):
        datain = None

    if datain is not None:
        layer_count = datain.GetLayerCount()
    else:
        layer_count = 1

    #this part converts the vector information into geostack Vector object
    vec = vector.Vector(dtype=dtype)

    for i in range(layer_count):
        if datain is not None:
            data_layer = datain.GetLayerByIndex(i)
        elif datain is None and isinstance(file_path, ogr.Layer):
            data_layer = file_path
        layer_type = ogr.GeometryTypeToName(data_layer.GetGeomType())
        spatial_ref = data_layer.GetSpatialRef()
        for j, data_feature in enumerate(data_layer, 0):
            field_count = data_feature.GetFieldCount()
            props = {'string': {}, 'int': {}, 'double': {}}
            for k in range(field_count):
                field_def = data_feature.GetFieldDefnRef(k)
                if ogr.GetFieldTypeName(field_def.GetType()) == 'String':
                    field_value = data_feature.GetField(k)
                    if field_value is not None:
                        props['string'][field_def.GetName()] = field_value
                    else:
                        props['string'][field_def.GetName()] = raster.getNullValue(str)
                elif ogr.GetFieldTypeName(field_def.GetType()) == 'Integer':
                    field_value = data_feature.GetField(k)
                    if field_value is not None:
                        props['int'][field_def.GetName()] = field_value
                    else:
                        props['int'][field_def.GetName()] = raster.getNullValue(int)
                elif ogr.GetFieldTypeName(field_def.GetType()) == 'Real':
                    field_value = data_feature.GetField(k)
                    if field_value is not None:
                        props['double'][field_def.GetName()] = field_value
                    else:
                        props['double'][field_def.GetName()] = raster.getNullValue(np.float64)
                elif ogr.GetFieldTypeName(field_def.GetType()) == 'DateTime':
                    field_value = data_feature.GetField(k)
                    if field_value is not None:
                        props['string'][field_def.GetName()] = field_value
                    else:
                        props['string'][field_def.GetName()] = raster.getNullValue(str)
            geom = data_feature.GetGeometryRef()
            if layer_type == "Point":
                idx = vec.addPoint(geom.GetPoint_2D())
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)
            elif layer_type == "Line String":
                idx = vec.addLineString(geom.GetPoints())
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)
            elif layer_type in ["Polygon", "Multi Polygon", "3D Polygon"]:
                poly = []
                for k in range(geom.GetGeometryCount()):
                    _geom = geom.GetGeometryRef(k)
                    _geom_count = _geom.GetGeometryCount()
                    if _geom_count > 0:
                        _poly = []
                        for n in range(_geom_count):
                            __geom = _geom.GetGeometryRef(n)
                            points = np.array(__geom.GetPoints())
                            _poly.append(points)
                        poly.append(_poly)
                    else:
                        points = np.array(_geom.GetPoints())
                        poly.append(points)

                for item in poly:
                    if isinstance(item, list):
                        poly_idx = vec.addPolygon(item)
                    else:
                        poly_idx = vec.addPolygon([item])
                    for _item in props:
                        if len(props[_item]) > 0:
                            prop_type = prop_type_map.get(_item)
                            for _prop in props[_item]:
                                vec.setProperty(poly_idx, _prop, props[_item][_prop],
                                                propType=prop_type)

    if spatial_ref is not None:
        vec.setProjectionParameters(
            core.ProjectionParameters.from_wkt(spatial_ref.ExportToWkt()))

    if isinstance(file_path, str):
        del(datain)
        datain = None
    return vec


@supported_libs.RequireLib("pyshp")
def from_pyshp(file_path: str, dtype: np.dtype = core.REAL):
    """Create Vector object using pyshp's shapefile.

    Parameters
    ----------
    file_path: str/fiona.Collection
        path of the file to be read or a shapefile.Reader object
    dtype: np.dtype
        data type for the vector object to be created

    Returns
    -------
    vec: vector.Vector
        a vector object created from a shapefile.Reader

    """
    prop_type_map = {"string": str,
                     "int": int,
                     "int32": int,
                     "int64": int,
                     "double": np.float64 if dtype == np.float64 else float}

    if isinstance(file_path, str):
        datain = shapefile.Reader(pth.realpath(file_path))
    elif isinstance(file_path, shapefile.Reader):
        datain = file_path

    if pth.exists(f"{datain.shapeName}.prj"):
        with open(f"{datain.shapeName}.prj", "r") as inp:
            proj_param = inp.read()
        shape_proj = core.ProjectionParameters.from_wkt(proj_param)
    else:
        shape_proj = None

    n_shapes = datain.numRecords
    data_fields = datain.fields

    vec = vector.Vector(dtype=dtype)

    for i in range(n_shapes):
        props = {'string':{}, 'int':{}, 'double':{}}
        for j, item in enumerate(data_fields[1:], 0):
            if item[1] == 'C':
                props['string'][item[0]] = datain.record(i=i)[j]
            elif item[1] == "N":
                props['int'][item[0]] = datain.record(i=i)[j]
            elif item[1] == 'F':
                props['double'][item[0]] = datain.record(i=i)[j]
        geom = datain.shape(i=i)
        geom_points = geom.points
        if datain.shapeTypeName == "POINT":
            idx = vec.addPoint(geom_points[0])
            for _item in props:
                if len(props[_item]) > 0:
                    prop_type = prop_type_map.get(_item)
                    for _prop in props[_item]:
                        vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)
        elif datain.shapeTypeName == "POLYLINE":
            idx = vec.addLineString(geom_points)
            for _item in props:
                if len(props[_item]) > 0:
                    prop_type = prop_type_map.get(_item)
                    for _prop in props[_item]:
                        vec.setProperty(idx, _prop, props[_item][_prop], propType=prop_type)
        elif datain.shapeTypeName in ["POLYGON", "POLYGONZ"]:
            geom_parts = geom.parts
            for k in range(len(geom_parts)):
                if k == len(geom_parts)-1:
                    _coords = np.squeeze(geom_points[geom_parts[k]:len(geom_points)])
                else:
                    _coords = np.squeeze(geom_points[geom_parts[k]:geom_parts[k+1]])
                poly_idx = vec.addPolygon([_coords])
                for _item in props:
                    if len(props[_item]) > 0:
                        prop_type = prop_type_map.get(_item)
                        for _prop in props[_item]:
                            vec.setProperty(poly_idx, _prop, props[_item][_prop], propType=prop_type)

    if shape_proj is not None:
        vec.setProjectionParameters(shape_proj)
    if isinstance(file_path, str):
        datain.close()
    return vec


class DBHandler:
    @supported_libs.RequireLib("spatialite")
    def __init__(self, file_name: Optional[str] = None):
        # get the database filename
        db_file_name = os.environ.get(
            "SPATIALITE_DB_PATH", file_name)

        if file_name is None or not pth.isfile(file_name):
            raise ValueError("File name is not provided / or not valid")

        # create database connection
        self.conn = sqlite3.connect(f"file:{db_file_name}?mode=ro",
                                    check_same_thread=False, uri=True)
        self.conn.enable_load_extension(True)
        try:
            self.conn.load_extension(os.environ.get("SPATIALITE_LIBRARY_PATH",
                                                    "mod_spatialite"))
        except sqlite3.OperationalError:
            lib_path = find_library("mod_spatialite")
            if lib_path is not None:
                self.conn.load_extension(lib_path)
        self.conn.enable_load_extension(False)

        # get the cursor
        self.cursor = self.conn.cursor()

    def get_table_names(self, cmd: Optional[str] = None) -> List[str]:
        """get the user defined table names

        Parameters
        ----------
        cmd: str
            a sql command

        Returns
        -------
        List[str]
            a list of user defined types
        """
        if cmd is None:
            cmd = """SELECT * FROM sqlite_schema WHERE type = 'table'
                     AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'spatialite_%'
                     AND name NOT LIKE 'virts_%' AND name NOT LIKE 'views_%'
                     AND name not LIKE 'geometry_%' AND name NOT LIKE 'sql_%'
                     AND name not LIKE 'spatial_%' AND name not LIKE '%_licenses'
                     AND name != 'ElementaryGeometries' AND name != 'KNN'"""
        out = self.executor(cmd)
        return out.fetchall()

    def get_geometry_cols(self) -> List[Tuple]:
        """get the geometry column names

        Returns
        -------
        List[str]
            a list of string with column names
        """

        cmd = f"""
        SELECT "f_table_name", "f_geometry_column", "geometry_type"
        FROM "geometry_columns"
        """
        out = self.executor(cmd)
        return out.fetchall()

    def to_vector(self, sql: Optional[str] = None,
                  cur: Optional[sqlite3.Cursor] = None,
                  columns: List[str] = None) -> 'vector.Vector':
        """convert rows from database to a Vector object

        Parameters
        ----------
        sql : str
            a sql command
        cur : sqlite3.cursor
            sqlite cursor from executing sql command
        columns : List[str]
            a list of string with column names

        Returns
        -------
        Vector
            a Vector object
        """
        if not len(columns) > 0:
            raise ValueError("No column names provided")

        assert sql is not None or cur is not None, "either sql statement or sql cursor is provided"

        if sql is not None:
            sql_statement = sql.format(column_str=','.join(columns))
            cursor = self.executor(sql_statement)
        elif cur is not None:
            cursor = cur

        db_rows = cursor.fetchall()
        vec = vector.Vector()

        for row in db_rows:
            row_id = io.parseString(vec, row[0])
            for name, value in zip(columns, row[1:]):
                vec.setProperty(row_id[0], name, value)
        return vec

    def get_column_names(self, table_name: str) -> List[str]:
        """get the column names from the table

        Parameters
        ----------
        table_name : str
            name of the table

        Returns
        -------
        List[str]
            a list of column names from given table
        """
        cmd = f"PRAGMA table_info('{table_name}')"
        table_cols = self.executor(cmd)
        return table_cols.fetchall()

    def executor(self, cmd: str) -> sqlite3.Cursor:
        """execute a command on the database

        Parameters
        ----------
        cmd : str
            a sql command

        Returns
        -------
        sqlite3.Cursor
            sqlite cursor object after execting command
        """
        out = self.execute_command(self.cursor, cmd)
        return out

    def get_srid(self, table_name: Optional[str] = None) -> List[int]:
        """get the srid of the table

        Parameters
        ----------
        table_name : Optional[str]
            name of the table, default is None

        Returns
        -------
        List[int]
            epsg code of the projection
        """

        cmd = "SELECT srid FROM geometry_columns"
        if table_name is not None:
            cmd += f""" WHERE f_table_name = '{table_name}'"""
        cursor = self.executor(cmd)
        rc = cursor.fetchone()

        if rc is None:
            cmd = "SELECT srid FROM geometry_columns"
            if table_name is not None:
                cmd += f""" WHERE f_table_name = '{table_name.lower()}'"""
            cursor = self.executor(cmd)
            rc = cursor.fetchone()

        if rc is None:
            raise ValueError(f"f_table_name '{table_name}' is not valid")
        return rc[0]

    def filter_with_bounds(self, db_name: str,
                           bbox: 'vector.BoundingBox',
                           epsg_code: Optional[int] = 4326,
                           cmd: Optional[str] = None) -> sqlite3.Cursor:
        """get objects within the bounding box

        Parameters
        ----------
        bbox : vector.BoundingBox
            bounding box
        epsg_code: Optional[int]
            epsg code for the bounding box projection

        Returns
        -------
        sqlite3.Cursor
            a sqlite cursor object
        """
        # get the srid from the table
        table_srid = self.get_srid(table_name=db_name)

        if table_srid != epsg_code:
            # project bounding box object
            try:
                _bbox = bbox.convert(utils.get_epsg(table_srid),
                                     utils.get_epsg(epsg_code))
            except StopIteration:
                raise RuntimeError("No srid found in database")
        else:
            _bbox = bbox

        if cmd is None:
            # create a default command
            query = f"""
                SELECT *
                FROM '{db_name}' a WHERE
                (ST_Within(a.geometry, ST_GeomFromTEXT('{_bbox.to_wkt()}', {epsg_code})) OR
                ST_Intersects(a.geometry, ST_GeomFromTEXT('{_bbox.to_wkt()}', {epsg_code})) OR
                ST_Touches(a.geometry, ST_GeomFromTEXT('{_bbox.to_wkt()}', {epsg_code})));
            """
        else:
            # format a user defined command
            query = cmd.format(db_name=db_name,
                               bbox_wkt=_bbox.to_wkt(),
                               epsg_code=epsg_code)

        cursor = self.executor(query)
        return cursor

    def close(self) -> None:
        """close the database object
        """
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def execute_command(cursor: sqlite3.Cursor, cmd: str) -> sqlite3.Cursor:
        try:
            out = cursor.execute(cmd)
        except Error:
            raise RuntimeError("Unable to execute command")
        return out

    def __enter__(self) -> 'DBHandler':
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


if __name__ == "__main__":

    file_path = "./aus-states-09072015.shp"
    start = time.time()
    vec = from_geopandas(file_path)
    end = time.time()
    print(f"Time taken by geopandas to geostack = (end - start)")

    start = time.time()
    vec = from_ogr(file_path)
    end = time.time()
    print(f"Time taken by ogr to geostack = {(end - start)}")

    start = time.time()
    vec = from_pyshp(file_path)
    end = time.time()
    print(f"Time taken by pyshp to geostack = (end - start)")

    out = io.vectorToGeoJson(vec)
    core.Json11.load(out).dumps("./test2.geojson")

    print(f"Time taken to write to geojson = {(time.time() - end)}")
