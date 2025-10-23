# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from time import time
import pytest
sys.path.insert(0, os.path.realpath('../../../'))
from geostack.core import ProjectionParameters
from geostack.io import geoJsonToVector
from geostack.gs_enums import GeometryType


@pytest.fixture
def geojson():
    # GeoJSON string
    geojson = '''{
        "features": [
            {"geometry": {"coordinates": [0, 0.5], "type": "Point"},
                "properties": {"r": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"r": 20}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"r": 30}, "type": "Feature"},
            {"geometry": {"coordinates": [1, 0.5], "type": "Point"},
                "properties": {"r": 50}, "type": "Feature"}
            ], "type": "FeatureCollection"
        }'''
    return geojson


@pytest.fixture
def vector(geojson):
    # Parse GeoJSON
    v = geoJsonToVector(geojson, enforceProjection=False)
    return v

@pytest.mark.xfail
def test_to_points(vector):
    v2 = vector.convert(GeometryType.Point)
    assert vector.getPointCount() == 2
    assert vector.getLineStringCount() == 1

    assert v2.getPointCount() == 16
    assert v2.getLineStringCount() == 0

@pytest.mark.xfail
def test_to_lines(vector):
    v3 = vector.convert(GeometryType.LineString)
    assert v3.getPointCount() == 0
    assert v3.getLineStringCount() == 21

@pytest.mark.xfail
def test_to_point_or_lines(vector):
    v4 = vector.convert(GeometryType.Point | GeometryType.LineString)
    assert v4.getPointCount() == 20
    assert v4.getLineStringCount() == 21

@pytest.mark.xfail
def test_to_polygon(vector):
    v4 = vector.convert(GeometryType.Polygon)
    assert v4.getPolygonCount() == 4

@pytest.mark.parametrize("proj", ["3111", 3111])
def test_vector_reprojection(vector, proj):
    vector.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    if isinstance(proj, str):
        v4 = vector.convert(proj)
    else:
        v4 = vector.convert(ProjectionParameters.from_epsg(proj))
    assert v4.getPolygonCount() == vector.getPolygonCount()