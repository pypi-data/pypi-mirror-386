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

from geostack.core import REAL
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
def subregion():
    region = '''{"features": [{"geometry": {"coordinates": [[[2383894, 2446687], [2450835, 2446687], [2450835, 2489513], [2383894, 2489513], [2383894, 2446687]]], "type": "Polygon"}, "properties": {}, "type": "Feature"}], "type": "FeatureCollection"}'''
    return region

def test_1(tmpdir, datadir, subregion):

    start = time()
    file_path = datadir.join("test_data_2.geojson")
    temp = geoJsonToVector(file_path.strpath, dtype=REAL)
    end = time()
    print("Time taken to process file %f" % (end - start))

    bbox_vector = geoJsonToVector(subregion, dtype=REAL)

    start = time()
    out = temp.region(bbox_vector.getBounds(), GeometryType.NoType)
    end = time()
    print("Time taken to subregion %f" % (end - start))

    file_name = tmpdir.join("test_out_2.geojson")

    with open(file_name.strpath, "w") as outfile:
        outfile.write(vectorToGeoJson(out))
