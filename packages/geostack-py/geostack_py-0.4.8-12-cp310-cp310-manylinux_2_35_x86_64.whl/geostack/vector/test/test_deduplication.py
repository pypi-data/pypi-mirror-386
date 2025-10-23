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

def test_1(datadir):
    start = time()
    file_path = datadir.join("test_data_2.geojson")
    temp = geoJsonToVector(file_path.strpath, dtype=REAL)
    end = time()
    print("Time taken to process file %f" % (end - start))

    start = time()
    temp.deduplicateVertices()
    end = time()
    print("Time taken to deduplicate %f" % (end - start))
