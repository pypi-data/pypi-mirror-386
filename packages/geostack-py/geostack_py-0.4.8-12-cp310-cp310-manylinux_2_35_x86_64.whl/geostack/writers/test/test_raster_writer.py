# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))
from distutils import dir_util

import numpy as np
import pytest
from geostack.core import ProjectionParameters
from geostack import raster
from geostack.writers import netcdfWriter
from geostack.writers import rasterWriters
from geostack.dataset import supported_libs


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


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_raster_gdal(datadir):
    test_native = raster.Raster("testA")
    test_native.init(10, 1.0, ny=10, hy=1.0)
    test_native.data = np.random.random(test_native.shape)
    test_native.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    rasterWriters.writeRaster(datadir.join(
        "test_gdal.tif").strpath, test_native)
    assert os.path.exists(datadir.join("test_gdal.tif").strpath)


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_raster_netcdf(datadir):
    test_native = raster.Raster("testA")
    test_native.init(10, 1.0, ny=10, hy=1.0)
    test_native.data = np.random.random(test_native.shape)
    test_native.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    netcdfWriter.write_to_netcdf(
        test_native, datadir.join("test_netcdf.nc").strpath)

    assert os.path.exists(datadir.join("test_netcdf.nc").strpath)


@pytest.mark.xarray
@pytest.mark.skipif(not supported_libs.HAS_XARRAY, reason="xarray library is not installed")
def test_raster_xarray():
    import xarray as xr

    test_native = raster.Raster("testA")
    test_native.init(10, 1.0, ny=10, hy=1.0)
    test_native.data = np.random.random(test_native.shape)
    test_native.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    obj = rasterWriters.to_xarray(test_native)
    assert isinstance(obj, xr.DataArray)
