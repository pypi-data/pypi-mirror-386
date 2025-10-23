# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import pytest
from distutils import dir_util
from datetime import datetime
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
from geostack import raster
from geostack.dataset import supported_libs
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


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_seconds(datadir):

    # Read test file
    filePath = datadir.join("test_seconds.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)


    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 31, 23, 59, 59)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 1, 1, 0, 0, 1)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_minutes(datadir):

    # Read test file
    filePath = datadir.join("test_minutes.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 31, 23, 59)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 1, 1, 0, 1)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_hours(datadir):

    # Read test file
    filePath = datadir.join("test_hours.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 31, 23)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 1, 1, 1)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_days(datadir):

    # Read test file
    filePath = datadir.join("test_days.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 31)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 1, 2)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_weeks(datadir):

    # Read test file
    filePath = datadir.join("test_weeks.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 25)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 1, 8)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_months(datadir):

    # Read test file
    filePath = datadir.join("test_months.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 12, 1)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1971, 2, 1)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_years(datadir):

    # Read test file
    filePath = datadir.join("test_years.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="rh", filePath=filePath.strpath,
                                 backend="netcdf")
    testFile.read(layers=-1)

    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(0)) == datetime(1970, 1, 1)
    assert datetime.utcfromtimestamp(testFile.getTimeFromIndex(1)) == datetime(1972, 1, 1)
