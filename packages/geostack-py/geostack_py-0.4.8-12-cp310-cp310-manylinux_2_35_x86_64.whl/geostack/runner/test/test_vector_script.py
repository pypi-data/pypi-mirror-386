# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
import pytest
from geostack.raster import Raster
from geostack.vector import Vector
from geostack.runner import runScript, runVectorScript
from geostack.io import vectorToGeoJson
from geostack.gs_enums import ReductionType
from geostack.core import REAL


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


@pytest.mark.runVectorScript
@pytest.fixture
def vector_object(tmpdir):
    # Create raster layer
    A = Raster(name = "A")

    # Initialize Raster
    A.init(nx = 10, ny = 10, hx = 10.0, hy = 10.0)

    runScript("A = x*y;", [A])

    # Write Raster
    A.write(tmpdir.join('_out_vector_script_raster.tiff').strpath)

    # Create vector
    v = Vector()
    v.addPolygon( [ [ [2.5, 2.5], [2.5, 37.5], [37.5, 37.5], [37.5, 2.5] ] ] )
    v.addPolygon( [ [ [97.5, 97.5], [97.5, 62.5], [62.5, 62.5], [62.5, 97.5] ] ] )
    v.addProperty("max")
    v.addProperty("min")

    # Run script
    runVectorScript("max = A;", v, [A], ReductionType.Maximum)
    runVectorScript("min = A;", v, [A], ReductionType.Minimum)

    # Write vector
    with open(tmpdir.join('_out_vector_script.json').strpath, 'w') as outfile:
        outfile.write(vectorToGeoJson(v, enforceProjection = False))
    return v


@pytest.mark.runVectorScript
@pytest.mark.parametrize("i, vmin, vmax", [(0, 25.0, 1225.0), (1, 4225.0, 9025.0)])
def test_vector_script(vector_object, i, vmin, vmax):
    assert round(vector_object.getProperty(i, "max", REAL), 2) == vmax
    assert round(vector_object.getProperty(i, "min", REAL), 2) == vmin


@pytest.mark.runVectorScript
def test_vector_script_double(datadir):
    fin = datadir.join("vic_simple.shp")
    vec = Vector.from_shapefile(fin.strpath, dtype=np.float64)
    count = vec.getPolygonCount()
    vec.runScript("if (area > 1000.0) keep = false;")
    assert vec.getPolygonCount() < count
