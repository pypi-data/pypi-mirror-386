# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import numpy as np
from time import time
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.gs_enums import GeometryType
from geostack.vector import vector

@pytest.fixture
def test_geojson():
    _geo_json = """{"features": [
            {"geometry": {"coordinates": [143, -36], "type": "Point"}, "properties": {}, "type": "Feature"},
            {"geometry": {"coordinates": [144, -37, 1], "type": "Point"}, "properties": {}, "type": "Feature"},
            {"geometry": {"coordinates": [145, -38, 1], "type": "Point"}, "properties": {"time": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [146, -39, 2], "type": "Point"}, "properties": {"time": 10}, "type": "Feature"}
            ], "type": "FeatureCollection"}"""
    return _geo_json

def test_vec_subregion(test_geojson):

    out = geoJsonToVector(test_geojson)
    bbox = vector.BoundingBox.from_list([[143, -36], [143, -36]])
    r0 = out.region(bbox, geom_type=GeometryType.Point)
    p0 = r0.getPointIndexes()
    assert p0.size == 1
    assert r0.getPointCoordinate(p0[0]).to_list() == [143, -36, 0, 0]

    bbox = vector.BoundingBox.from_list([[143, -36, 0.5], [146, -39, 1.5]])
    r1 = out.region(bbox, geom_type=GeometryType.Point)
    p1 = r1.getPointIndexes()
    assert p1.size == 1
    assert r1.getPointCoordinate(p1[0]).to_list() == [144, -37, 1, 0]

    bbox = vector.BoundingBox.from_list([[143, -36, 0, 10], [146, -39, 2, 10]])
    r2 = out.region(bbox, geom_type=GeometryType.Point)
    p2 = r2.getPointIndexes()
    assert p2.size == 2
    assert r2.getPointCoordinate(p2[0]).to_list() == [145, -38, 1, 10]
    assert r2.getPointCoordinate(p2[1]).to_list() == [146, -39, 2, 10]
