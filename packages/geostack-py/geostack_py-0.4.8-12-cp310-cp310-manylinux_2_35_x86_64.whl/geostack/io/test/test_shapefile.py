# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import io
import os
import sys
import json
import numpy as np
from time import time
import pytest
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.core import REAL
from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.io import shapefileToVector, vectorToShapefile
from geostack.gs_enums import GeometryType
from geostack.vector import Vector


@pytest.fixture
def testPoint():
    Point = '''{"features": [{"geometry": {"coordinates": [0, 0.5], "type": "Point"}, "properties": {"p0": "p", "p1": 1, "p2": 1.1000000000000001}, "type": "Feature"}], "type": "FeatureCollection", "bbox": [0, 0.5, 0, 0.5]}'''
    return Point


@pytest.fixture
def testLineString():
    LineString = '''{"features": [{"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"}, "properties": {"l0": "lstr", "l1": 2, "l2": 2.2000000000000002}, "type": "Feature"}], "type": "FeatureCollection", "bbox": [0, 0, 3, 1]}'''
    return LineString


@pytest.fixture
def testPolygon():
    Polygon = '''{"features": [{"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"}, "properties": {"y0": "ystr", "y1": 3, "y2": 3.2999999999999998}, "type": "Feature"}], "type": "FeatureCollection", "bbox": [0, 0, 1, 1]}'''
    return Polygon


def test_write_point(tmpdir, testPoint):
    file_name = tmpdir.join("test_point.shp")
    inpVector = geoJsonToVector(testPoint, dtype=REAL)
    out = vectorToShapefile(inpVector, file_name.strpath,
                            geom_type=GeometryType.Point)
    assert out


def test_write_linestring(tmpdir, testLineString):
    file_name = tmpdir.join("test_linestring.shp")
    inpVector = geoJsonToVector(testLineString, dtype=REAL)
    out = vectorToShapefile(inpVector, file_name.strpath,
                            geom_type=GeometryType.LineString)
    assert out


def test_write_polygon(tmpdir, testPolygon):
    file_name = tmpdir.join("test_polygon.shp")
    inpVector = geoJsonToVector(testPolygon, dtype=REAL)
    out = vectorToShapefile(inpVector, file_name.strpath,
                            geom_type=GeometryType.Polygon)
    assert out


def test_read_point(tmpdir, testPoint):
    file_name = tmpdir.join("test_point.shp")
    out = Vector.from_geojson(testPoint).to_shapefile(file_name.strpath,
                                                      geom_type=GeometryType.Point)
    assert out
    inpVector = shapefileToVector(file_name.strpath, dtype=REAL)
    assert isinstance(inpVector, Vector)

def test_read_linestring(tmpdir, testLineString):
    file_name = tmpdir.join("test_linestring.shp")
    out = Vector.from_geojson(testLineString).to_shapefile(file_name.strpath,
                                                           geom_type=GeometryType.LineString)
    assert out
    inpVector = shapefileToVector(file_name.strpath, dtype=REAL)
    assert isinstance(inpVector, Vector)

def test_read_polygon(tmpdir, testPolygon):
    file_name = tmpdir.join("test_polygon.shp")
    out = Vector.from_geojson(testPolygon).to_shapefile(file_name.strpath,
        geom_type=GeometryType.Polygon)
    assert out
    inpVector = shapefileToVector(file_name.strpath, dtype=REAL)
    assert isinstance(inpVector, Vector)
