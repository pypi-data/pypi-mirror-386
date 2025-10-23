# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import io
import sys
import json
import numpy as np
from time import time
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))
from geostack.core import REAL
from geostack.io import csvToVector, vectorToCSV, geoJsonToVector


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

@pytest.mark.skipif(REAL != np.float32, reason="skip if not single precision")
def test_vector_to_csv(datadir):
    vec = geoJsonToVector(datadir.join("test_data.json").strpath)
    out_csv = vectorToCSV(vec, filename=None)
    csv_file = io.StringIO()
    with open(datadir.join("test_data.json").strpath) as inp:
        for row in inp:
            csv_file.write(row + "\n")
    assert out_csv.read() == csv_file.read()

@pytest.mark.skipif(REAL != np.float32, reason="skip if not single precision")
def test_csv_to_vector(datadir):
    vec = geoJsonToVector(datadir.join("test_data.json").strpath)
    csv_vec = csvToVector(datadir.join("test_data.csv").strpath)
    assert vec.getPolygonCount() == csv_vec.getPolygonCount()
    assert vec.getBounds().to_list() == csv_vec.getBounds().to_list()
