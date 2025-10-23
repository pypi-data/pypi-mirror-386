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

from geostack.definitions import GeometryType, VectorIndexingOptions
from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.gs_enums import GeometryType
from geostack.vector import vector
from geostack.core import isInvalid, REAL


@pytest.fixture
def test_geojson():
    _geo_json = """{"features": [
        {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
            "properties": {"A": 1, "level": 0}, "type": "Feature"},
        {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
            "properties": {"A": 2, "level": 1}, "type": "Feature"},
        {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
            "properties": {"A": 3, "level": 2}, "type": "Feature"},
        {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
            "properties": {"A": 4, "level": 3}, "type": "Feature"},
        {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
            "properties": {"A": 5, "level": 4}, "type": "Feature"}
        ], "type": "FeatureCollection"}"""
    return _geo_json


@pytest.mark.vector
@pytest.mark.parametrize('data_type', [REAL, np.uint32])
def test_vec_rasterisation1(test_geojson, data_type):
    vec = geoJsonToVector(test_geojson)

    testRasterA = vec.rasterise(0.02, output_type=data_type)
    assert testRasterA.data_type == data_type

    assert testRasterA.getCellValue(1, 76) == data_type(1.0)
    assert testRasterA.getCellValue(25, 25) == data_type(1.0)
    assert testRasterA.getCellValue(12, 12) == data_type(1.0)
    assert testRasterA.getCellValue(45, 46) == data_type(1.0)
    assert testRasterA.getCellValue(70, 51) == data_type(1.0)

    testRasterB = vec.rasterise(inp_raster=testRasterA,
                                output_type=data_type)
    assert testRasterB.data_type == data_type


@pytest.mark.vector
@pytest.mark.parametrize('data_type, parameters', [(REAL, GeometryType.All),
                                                   (REAL, GeometryType.All | VectorIndexingOptions.Edges),
                                                   (REAL, GeometryType.All | VectorIndexingOptions.Interior),
                                                   (np.uint32, GeometryType.All),])
def test_vec_rasterisation2(test_geojson, data_type, parameters):
    vec = geoJsonToVector(test_geojson)

    if hasattr(parameters, 'value'):
        param_value = parameters.value
    else:
        param_value = parameters

    testRasterC = vec.rasterise(0.02, script="output = A;",
                                output_type=data_type,
                                parameters=param_value)

    assert testRasterC.data_type == data_type

    assert testRasterC.getCellValue(1, 76) == data_type(1.0)

    if parameters == GeometryType.All:
        assert testRasterC.getCellValue(25, 25) == data_type(5.0)
        assert testRasterC.getCellValue(12, 12) == data_type(3.0)
        assert testRasterC.getCellValue(45, 45) == data_type(5.0)
        assert testRasterC.getCellValue(70, 51) == data_type(5.0)
    elif parameters == GeometryType.All | VectorIndexingOptions.Edges:
        assert testRasterC.getCellValue(25, 25) == data_type(5.0)
        assert testRasterC.getCellValue(12, 12) == data_type(2.0)
        assert testRasterC.getCellValue(45, 45) == data_type(2.0)
        assert isInvalid(testRasterC.getCellValue(70, 51))
    elif parameters == GeometryType.All | VectorIndexingOptions.Interior:
        assert testRasterC.getCellValue(25, 25) == data_type(2.0)
        assert testRasterC.getCellValue(12, 12) == data_type(3.0)
        assert testRasterC.getCellValue(45, 45) == data_type(5.0)
        assert testRasterC.getCellValue(70, 51) == data_type(5.0)

    testRasterB = vec.rasterise(inp_raster=testRasterC,
                                output_type=data_type,
                                parameters=param_value)
    assert testRasterB.data_type == data_type


@pytest.mark.vector
@pytest.mark.parametrize('data_type', [REAL, np.uint32])
def test_vec_rasterisation3(test_geojson, data_type):
    vec = geoJsonToVector(test_geojson)

    testRasterC = vec.rasterise(0.02, script="output = min(A, output);",
                                output_type=data_type)

    assert testRasterC.data_type == data_type

    assert testRasterC.getCellValue(1, 76) == data_type(1.0)
    assert testRasterC.getCellValue(25, 25) == data_type(4.0)
    assert testRasterC.getCellValue(12, 12) == data_type(3.0)
    assert testRasterC.getCellValue(45, 45) == data_type(3.0)
    assert testRasterC.getCellValue(70, 51) == data_type(4.0)

    testRasterB = vec.rasterise(inp_raster=testRasterC,
                                output_type=data_type)
    assert testRasterB.data_type == data_type


@pytest.mark.vector
@pytest.mark.parametrize('data_type', [REAL])
def test_vec_rasterisation4(test_geojson, data_type):
    vec = geoJsonToVector(test_geojson)

    testRasterD = vec.rasterise(0.02, script="output = max(A, output);",
                                output_type=data_type)

    assert testRasterD.data_type == data_type

    assert testRasterD.getCellValue(1, 76) == data_type(1.0)
    assert testRasterD.getCellValue(25, 25) == data_type(5.0)
    assert testRasterD.getCellValue(12, 12) == data_type(3.0)
    assert testRasterD.getCellValue(45, 45) == data_type(5.0)
    assert testRasterD.getCellValue(70, 51) == data_type(5.0)

    testRasterB = vec.rasterise(inp_raster=testRasterD,
                                output_type=data_type)
    assert testRasterB.data_type == data_type
