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

from geostack.core import REAL, ProjectionParameters
from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.gs_enums import GeometryType

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

@pytest.fixture
def testGeoJson():
    GeoJson = '''{"features": [{"geometry": {"coordinates": [0, 0.5], "type": "Point"}, "properties": {"p0": "pstr", "p1": 1, "p2": 1.1000000000000001}, "type": "Feature"}, {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"}, "properties": {"l0": "lstr", "l1": 2, "l2": 2.2000000000000002}, "type": "Feature"}, {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"}, "properties": {"y0": "ystr", "y1": 3, "y2": 3.2999999999999998}, "type": "Feature"}], "type": "FeatureCollection", "bbox": [0, 0, 3, 1]}'''
    return GeoJson

def test_geojson(testGeoJson):

    temp = geoJsonToVector(testGeoJson, dtype=np.float64)
    assert testGeoJson == vectorToGeoJson(temp, enforceProjection=False)

def test_geojson_large(datadir):
    start = time()
    file_path = datadir.join("test_data_2.geojson")
    temp = geoJsonToVector(file_path.strpath, dtype=REAL)
    end = time()
    print("Time taken to process file %f" % (end - start))

    start = time()
    testRasterize = temp.mapDistance(50.0, geom_type=GeometryType.LineString)
    end = time()
    print("Time taken to rasterize = %f" % (end - start))

    start = time()
    contourVector = testRasterize.vectorise(1000.0)
    end = time()
    file_name = datadir.join("test_data_CONTOUR.geojson")
    print("Time taken to vectorise %f" % (end - start))
    with open(file_name.strpath, "w") as out:
        out.write(vectorToGeoJson(contourVector))

    print("finished writing geojson")
