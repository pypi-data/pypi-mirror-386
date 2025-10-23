# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import warnings
import pytest
import math
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
from geostack import raster
from geostack.dataset import supported_libs
from geostack.readers import get_ftp_file
import pytest


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


@pytest.mark.pygrib
@pytest.mark.skipif(not supported_libs.HAS_PYGRIB, reason="grib library is not installed")
def test_bom_file(datadir):
    # Read test file
    filePath = datadir.join(os.path.join(
        "IDY25001.APS3.group1.slv.2019092506.006.surface.grb2"))
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    variable_map = dict(u10=dict(name="10 metre U wind component",
                                 typeOfLevel="heightAboveGround",
                                 stepType="instant"),)

    # Try to read using grib
    testFile = raster.RasterFile(filePath=filePath.strpath, backend="grib",
                                 variable_map=variable_map, name="u10")
    testFile.read()

    # check raster dimensions
    raster_dims = testFile.getRasterDimensions()
    assert raster_dims.nx == 427 and raster_dims.ny == 512

    # get data of file tile
    temp = testFile.getData()

    # check raster min and max value
    assert np.isclose(temp.min(), -10.8)
    assert np.isclose(temp.max(), 14.3)


@pytest.mark.pygrib
@pytest.mark.skipif(not supported_libs.HAS_PYGRIB, reason="pygrib library is not installed")
def test_multi_time(datadir):
    filePath = datadir.join(os.path.join("ds.maxt.bin"))
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    variable_map = dict(tmax=dict(name="Maximum temperature",
                                  typeOfLevel="surface", stepType="max"),)
    filein = raster.RasterFile(filePath=filePath.strpath, backend="grib",
                               variable_map=variable_map, name="tmax")
    filein.read()
    # read first index
    temp = np.ma.masked_invalid(filein.getData())
    assert np.isclose(temp.min(), 291.5) and np.isclose(temp.max(), 314.30002)

    # move time index to second
    filein.setTimeIndex(1)
    temp = np.ma.masked_invalid(filein.getData())
    assert np.isclose(temp.min(), 291.5) and np.isclose(temp.max(), 314.80002)


@pytest.mark.pygrib
@pytest.mark.skipif(not supported_libs.HAS_PYGRIB, reason="pygrib library is not installed")
def test_lambert_grid(datadir):
    filePath = datadir.join(os.path.join("eta.grb"))
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    variable_map = dict(
        u10=dict(name="10 metre U wind component",
                 typeOfLevel="heightAboveGround",
                 stepType="instant"),)
    filein = raster.RasterFile(name="u10", filePath=filePath.strpath,
                               backend='grib', variable_map=variable_map)
    filein.read()
    assert filein.data.max() == 18.0 and filein.data.min() == -11.0
