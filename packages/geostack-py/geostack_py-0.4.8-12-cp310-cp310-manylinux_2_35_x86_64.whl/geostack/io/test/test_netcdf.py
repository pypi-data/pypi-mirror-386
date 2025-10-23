# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from distutils import dir_util
import numpy as np
sys.path.insert(0, os.path.realpath('../../../'))

import pytest
from geostack.io import NetCDFHandler
from geostack.raster import Raster


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


def test_file_structure(datadir):
    file_path = datadir.join("geostack_test_file.nc")
    ncfile = NetCDFHandler()
    ncfile.read(file_path.strpath)
    assert ncfile.raster.shape == (2, 5, 5)
    assert ncfile.raster.getBounds().to_list() == [
        [-0.9375, -90.625, 0.0, 0.0], [8.4375, -84.375, 2.0, 0.0]]
    assert ncfile.raster.dimensions.hx == 1.875
    assert ncfile.raster.dimensions.hy == 1.25


def test_file_data(datadir):
    data = np.array([[[32., 56., 12., 91., 25.],
                      [12., 61., 80., 69., 72.],
                      [56., 97., 29., 32., 62.],
                      [2., 63., 32., 76., 12.],
                      [38., 54., 30., 54., 6.], ],
                     [[42., 53., 68., 8., 50.],
                      [56., 94., 96., 97., 76.],
                      [12., 4., 29., 84., 19.],
                      [72., 42., 79., 17., 72.],
                      [5., 33., 71., 62., 5.], ]])

    file_path = datadir.join("geostack_test_file.nc")
    ncfile = NetCDFHandler()
    ncfile.read(file_path.strpath)
    ncfile.raster.name = "tas"

    assert np.allclose(ncfile.raster.data, data)

    testA = Raster(name="testA")
    testA.read(file_path.strpath, jsonConfig={"variable": "tas"})
    assert np.allclose(testA.data, data)


def test_variable_attributes(datadir):
    file_path = datadir.join("geostack_test_file.nc")
    ncfile = NetCDFHandler()
    ncfile.read(file_path.strpath)
    ncfile.raster.name = "tas"
    props = ncfile.raster.toJson()
    assert 'tas' in props['variables']
    assert props['variables']['tas']['units'] == "K"
    assert props['variables']['tas']['standard_name'] == "air_temperature"
    assert props['variables']['tas']['long_name'] == "Near-Surface Air Temperature"


def test_global_attributes(datadir):
    file_path = datadir.join("geostack_test_file.nc")
    ncfile = NetCDFHandler()
    ncfile.read(file_path.strpath)
    props = ncfile.raster.toJson()
    assert props['global']['Conventions'] == 'CF-1.7'
    assert props['global']['variable_id'] == 'tas'
