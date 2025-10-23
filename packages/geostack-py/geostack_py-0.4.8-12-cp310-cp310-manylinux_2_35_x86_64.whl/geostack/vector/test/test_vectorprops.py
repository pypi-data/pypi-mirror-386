# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import numpy as np
import pytest
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.vector import Coordinate
from geostack.io import geoJsonToVector
from geostack.core import REAL

@pytest.fixture
def temp():
    testGeoJson = '''{"features": [
        {"geometry": {"coordinates": [0, 0.5], "type": "Point"},
            "properties": {"p0": "pstr", "p1": 1, "p2": 1.1000000000000001}, "type": "Feature"},
        {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
            "properties": {"l0": "lstr", "l1": 2, "l2": 2.2000000000000002}, "type": "Feature"},
        {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
            "properties": {"y0": "ystr", "y1": 3, "y2": 3.2999999999999998}, "type": "Feature"}], "type": "FeatureCollection"}'''
    out_vector = geoJsonToVector(testGeoJson, dtype=REAL)
    return out_vector

def test_global_property(temp):
    temp.setGlobalProperty("name", "test_vector")
    temp.setGlobalProperty("crs", 4326)
    assert(temp.getGlobalProperty("name") == "test_vector")
    assert(temp.getGlobalProperty("crs") == 4326)

def test_point_property(temp):
    pointIndexes = temp.getPointIndexes()
    assert temp.getProperty(pointIndexes[0], "p0", str) == "pstr"

def test_property_name(temp):
    temp.addProperty("p 0")
    temp.removeProperty("p 0")

def test_line_string_property(temp):
    lineStringIndexes = temp.getLineStringIndexes()
    assert temp.getProperty(lineStringIndexes[0], "l1", int) == 2

def test_polygon_property(temp):
    polygonIndexes = temp.getPolygonIndexes()
    assert round(temp.getProperty(polygonIndexes[0], "y2", REAL), ndigits=1) == 3.3

def test_add_point(temp):
    point_idx = temp.addPoint([144.9631, -37.8136])
    temp.setProperty(point_idx, "newproperty", "newstr")
    out = temp.getPointCoordinate(point_idx)
    assert round(REAL(out[0]), 4) == REAL(144.9631) and round(REAL(out[1]), 4) == REAL(-37.8136)

def test_add_linestring(temp):
    linestring_idx = temp.addLineString([[144.9631, -37.8136],
                                         [144.9731, -37.8236]])
    temp.setProperty(linestring_idx, "newproperty", "newstr")
    out = temp.getLineStringCoordinates(linestring_idx)
    assert round(REAL(out[0][0]), 4) == REAL(144.9631) and round(REAL(out[0][1]), 4) == REAL(-37.8136)

def test_add_polygon(temp):
    polygon_idx = temp.addPolygon([[[144.9631, -37.8136],
                                    [144.9731, -37.8236],
                                    [144.9631, -37.8136]]])
    temp.setProperty(polygon_idx, "newproperty", "newstr")
    out = temp.getPolygonCoordinates(polygon_idx)
    assert round(REAL(out[0][0][0]), 4) == REAL(144.9631) and round(REAL(out[0][0][1]), 4) == REAL(-37.8136)

def test_clone_point(temp):
    point_idx = temp.addPoint([144.9631, -37.8136])
    temp.setProperty(point_idx, "newproperty", "newstr")
    clone_idx = temp.clone(point_idx)
    assert temp.getProperty(clone_idx, "newproperty") == 'newstr'

def test_clone_linestring(temp):
    linestring_idx = temp.addLineString([[144.9631, -37.8136],
                                         [144.9731, -37.8236]])
    temp.setProperty(linestring_idx, "newproperty", "newstr")
    clone_idx = temp.clone(linestring_idx)
    assert temp.getProperty(clone_idx, "newproperty") == 'newstr'

def test_clone_polygon(temp):
    polygon_idx = temp.addLineString([[144.9631, -37.8136],
                                      [144.9731, -37.8236],
                                      [144.9631, -37.8136]])
    temp.setProperty(polygon_idx, "newproperty", "newstr")
    clone_idx = temp.clone(polygon_idx)
    assert temp.getProperty(clone_idx, "newproperty") == 'newstr'
