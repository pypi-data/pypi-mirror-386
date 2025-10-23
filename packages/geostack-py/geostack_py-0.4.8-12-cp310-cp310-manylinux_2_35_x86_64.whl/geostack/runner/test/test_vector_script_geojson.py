# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
import pytest
from geostack.raster import Raster
from geostack.runner import runScript, runVectorScript
from geostack.io import geoJsonToVector
from geostack.gs_enums import ReductionType
from geostack.vector import Vector
from geostack.core import REAL


@pytest.fixture
def geojson_to_vector():

    geojson = '''{"features": [
            {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
                "properties": {"C": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"C": 20}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"C": 30}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 40}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 50}, "type": "Feature"},
            {"geometry": {"coordinates": [2, 0.75], "type": "Point"},
                "properties": {"C": 60}, "type": "Feature"}
            ], "type": "FeatureCollection"}'''

    v = geoJsonToVector(geojson, False)
    v.addProperty("A")
    v.addProperty("B")

    r = Raster(name="r")
    delta = 0.02
    r.init(nx=150, ny=150, hx=delta, hy=delta)

    runScript("r = x;", [r])

    runVectorScript("A = r;", v, [r], ReductionType.Minimum)
    runVectorScript("B = r;", v, [r], ReductionType.Maximum)

    return v


@pytest.mark.runVectorScript
@pytest.mark.parametrize("i, A, B, C", [(0, 0.010000, 0.010000, 10.000000),
                                        (1, 0.010000, 2.990000, 20.000000),
                                        (2, 0.010000, 1.010000, 30.000000),
                                        (3, 0.490000, 1.510000, 40.000000),
                                        (4, 0.490000, 1.510000, 50.000000),
                                        (5, 2.010000, 2.010000, 60.000000)])
def test_vector_script_geojson(geojson_to_vector, i, A, B, C):
    # for i in range(6):
    #    print(f"A: {v.getProperty(i, 'A')}, B: {v.getProperty(i, 'B')}, C: {v.getProperty(i, 'C')}")
    assert round(geojson_to_vector.getProperty(i, "A", REAL), 2) == A
    assert round(geojson_to_vector.getProperty(i, "B", REAL), 2) == B
    assert round(geojson_to_vector.getProperty(i, "C", REAL), 2) == C


@pytest.mark.runVectorScript
def test_filtering_runScript(geojson_to_vector):
    v2 = Vector.assign(geojson_to_vector)
    v2.runScript("if (C < 30) keep = false;")
    assert v2.getGeometryIndexes().size != geojson_to_vector.getGeometryIndexes().size


@pytest.mark.runVectorScript
def test_filtering_runVectorScript(geojson_to_vector):
    v2 = Vector.assign(geojson_to_vector)
    runVectorScript("if (C < 30) keep = false;", v2)
    assert v2.getGeometryIndexes().size != geojson_to_vector.getGeometryIndexes().size
