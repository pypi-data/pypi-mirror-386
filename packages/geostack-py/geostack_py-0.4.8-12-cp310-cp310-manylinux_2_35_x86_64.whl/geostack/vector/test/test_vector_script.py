# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from distutils import dir_util
from time import time
sys.path.insert(0, os.path.realpath('../../../'))

import inspect
import numpy as np
import pytest
from geostack.vector import Vector
from geostack.io import geoJsonToVector
from geostack.core import REAL
from geostack.core import Solver


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


@pytest.mark.vector
@pytest.mark.parametrize("script, jsonConfig",
                         [("vecA = vecA * 2.0;", None),
                          ("vecA = addValue(vecA, 2.0);", {"userDefinedFunctions": "REAL addValue(REAL a, REAL v) {return (a + v);}"})])
def test_runscript(datadir, script, jsonConfig):

    start = time()
    file_path = datadir.join("test_data_2.geojson")
    fileVector = geoJsonToVector(file_path.strpath, dtype=REAL)
    end = time()
    print("Time taken to process file %f" % (end - start))

    if fileVector.hasProperty('vecA'):
        fileVector.removeProperty('vecA')

    fileVector.addProperty("vecA")
    if jsonConfig is not None:
        fileVector.runScript("vecA = 2.90;")
    else:
        fileVector.runScript("vecA = 2.9;")

    point_idx = None
    line_idx = None
    poly_idx = None
    if fileVector.getPointCount() > 0:
        point_idx = next(fileVector.getPointIndexes())
        point_value = fileVector.getProperty(point_idx, "vecA")
    if fileVector.getLineStringCount() > 0:
        line_idx = next(fileVector.getLineStringIndexes())
        line_value = fileVector.getProperty(line_idx, "vecA")
    if fileVector.getPolygonCount() > 0:
        line_idx = next(fileVector.getPolygonIndexes())
        poly_value = fileVector.getProperty(poly_idx, "vecA")

    method_signature = inspect.signature(fileVector.runScript)

    if len(method_signature.parameters) >= 2:
        fileVector.runScript(script, jsonConfig)

        if jsonConfig is not None:
            if point_idx is not None:
                assert round(fileVector.getProperty(point_idx, "vecA"), 2) == round(point_value + 2, 2)

            if line_idx is not None:
                assert round(fileVector.getProperty(line_idx, "vecA"), 2) == round(line_value + 2, 2)

            if poly_idx is not None:
                assert round(fileVector.getProperty(poly_idx, "vecA"), 2) == round(poly_value + 2, 2)
        else:
            if point_idx is not None:
                assert round(fileVector.getProperty(point_idx, "vecA"), 2) == round(point_value * 2, 2)

            if line_idx is not None:
                assert round(fileVector.getProperty(line_idx, "vecA"), 2) == round(line_value * 2, 2)

            if poly_idx is not None:
                assert round(fileVector.getProperty(poly_idx, "vecA"), 2) == round(poly_value * 2, 2)
