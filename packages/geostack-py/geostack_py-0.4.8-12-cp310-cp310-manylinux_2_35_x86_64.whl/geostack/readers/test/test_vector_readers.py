# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

import sqlite3
from geostack.definitions import GeometryType, PropertyStructure
from geostack.core import isValid
from geostack import vector
from geostack.dataset import supported_libs
from geostack.readers.vectorReaders import (from_fiona,
                                            from_geopandas,
                                            from_pyshp,
                                            from_ogr, DBHandler)
from geostack.writers import vectorWriters
import pytest


@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.

    ref: https://stackoverflow.com/questions/29627341/pytest-where-to-store-expected-data
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))
    return tmpdir


@pytest.mark.vectorReaders
@pytest.mark.skipif(not supported_libs.HAS_GPD, reason="geopandas library is not installed")
def test_geopandas(datadir):
    # Read test file
    filePath = datadir.join("vic_simple.shp")
    vec = from_geopandas(filePath.strpath)
    assert isinstance(vec, vector.Vector)
    assert vec.hasData()
    assert all(map(isValid, vec.getProperties().getProperty("id").tolist()))


@pytest.mark.vectorReaders
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal/ogr library is not installed")
def test_ogr(datadir):
    # Read test file
    filePath = datadir.join("vic_simple.shp")
    vec = from_ogr(filePath.strpath)
    assert isinstance(vec, vector.Vector)
    assert vec.hasData()
    assert all(map(isValid, vec.getProperties().getProperty("id").tolist()))


@pytest.mark.vectorReaders
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal/ogr library is not installed")
def test_gdb_reader(datadir):
    # Read test file
    filePath = datadir.join("Sample_Data.gdb")
    vec = from_ogr(filePath.strpath, driver='OpenFileGDB')
    assert isinstance(vec, vector.Vector)
    assert vec.hasData()
    prop_names = list(filter(lambda prop: vec.getProperties().getPropertyStructure(prop) == PropertyStructure.Vector,
                             vec.properties.getPropertyNames()))
    assert len(prop_names) == 14


@pytest.mark.vectorReaders
@pytest.mark.skipif(not supported_libs.HAS_PYSHP, reason="pyshp library is not installed")
def test_pyshp(datadir):
    # Read test file
    filePath = datadir.join("vic_simple.shp")
    vec = from_pyshp(filePath.strpath)
    assert isinstance(vec, vector.Vector)
    assert vec.hasData()
    assert all(map(isValid, vec.getProperties().getProperty("id").tolist()))


@pytest.mark.vectorReaders
@pytest.mark.xfail
@pytest.mark.skipif(not supported_libs.HAS_FIONA, reason="fiona library is not installed")
def test_fiona(datadir):
    # Read test file
    filePath = datadir.join("vic_simple.shp")
    vec = from_fiona(filePath.strpath)
    assert isinstance(vec, vector.Vector)
    assert vec.hasData()
    assert all(map(isValid, vec.getProperties().getProperty("id").tolist()))


@pytest.mark.spatialite
@pytest.mark.skipif(not supported_libs.HAS_SPATIALITE, reason="spatialite library is not installed")
def test_db_reader(tmpdir, datadir):
    filePath = datadir.join("vic_simple.shp")
    vec = vector.Vector.from_shapefile(filePath.strpath)
    out_file = tmpdir.join("vic_simple.db")

    # write Vector to a database
    vectorWriters.to_database(vec, out_file.strpath, epsg_code=4326,
                              geom_type=GeometryType.Polygon)

    # read Vector from a database
    vec_db = DBHandler(file_name=out_file.strpath)
    assert isinstance(vec_db.conn, sqlite3.Connection)
    assert isinstance(vec_db.cursor, sqlite3.Cursor)

    # get table names
    table_names = vec_db.get_table_names()
    assert table_names is not None and isinstance(table_names, list)

    # get geom columns
    geom_cols = vec_db.get_geometry_cols()
    assert geom_cols is not None and isinstance(geom_cols, list)

    # get column names
    column = vec_db.get_column_names("VIC_SIMPLE_Polygon")
    assert column is not None and isinstance(column, list)

    # get SRID
    srid = vec_db.get_srid("VIC_SIMPLE_Polygon")
    assert srid == 4326

    # convert to vector
    db_cols = list(map(lambda item: item[1], column))
    vec2 = vec_db.to_vector("""SELECT ST_AsText(geometry) as 'GEOMETRY', {column_str}
                               FROM VIC_SIMPLE_Polygon""", columns=db_cols[:-1])
    assert isinstance(vec2, vector.Vector)
    assert vec2.getPolygonCount() == vec.getPolygonCount()

    # filter with bounds
    c0 = vector.Coordinate(146.6470, -38.9861)
    c1 = vector.Coordinate(146.7354, -38.8932)
    bounds = vector.BoundingBox(min_coordinate=c0,
                                max_coordinate=c1)

    cur = vec_db.filter_with_bounds("VIC_SIMPLE_Polygon",
                                    bounds, 4326)
    assert isinstance(cur, sqlite3.Cursor)
    rc = cur.fetchall()
    assert isinstance(rc, list)
    assert len(rc) == 4

    vec_db.close()
