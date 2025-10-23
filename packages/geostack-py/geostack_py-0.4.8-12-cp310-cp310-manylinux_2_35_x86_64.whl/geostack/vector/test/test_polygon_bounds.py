# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import numpy as np
import pytest
sys.path.insert(0, os.path.realpath('../../../'))
from geostack.io import geoJsonToVector
from geostack.vector import Vector, BoundingBox
from geostack.core import REAL

global temp, pb

@pytest.fixture
def testGeoJson():
    GeoJson = '''{"features": [{"geometry": {"coordinates": [0, 0.5], "type": "Point"}, "properties": {"p0": "pstr", "p1": 1, "p2": 1.1000000000000001}, "type": "Feature"}, {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"}, "properties": {"l0": "lstr", "l1": 2, "l2": 2.2000000000000002}, "type": "Feature"}, {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"}, "properties": {"y0": "ystr", "y1": 3, "y2": 3.2999999999999998}, "type": "Feature"}], "type": "FeatureCollection"}'''
    return GeoJson

def test_geojson(testGeoJson):
    global temp, pb

    temp = geoJsonToVector(testGeoJson, dtype=REAL)
    pb = temp.getPolygon(next(temp.getPolygonIndexes())).bounds
    assert isinstance(pb, BoundingBox)

def test_x_bounds():
    global pb
    assert pb[0][0] < pb[1][0]

def test_y_bounds():
    global pb
    assert pb[0][1] < pb[1][1]
