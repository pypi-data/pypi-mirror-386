# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import warnings
import json
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
from geostack.core import REAL, ProjectionParameters
from geostack.utils import have_internet
from geostack import raster, vector
from geostack.dataset import supported_libs
from geostack.runner import runScript
from geostack.readers.rasterReaders import return_proj4
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
def test_netcdf(datadir):

    # Read test file
    filePath = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.009.surface.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    testFile = raster.RasterFile(name="u10", filePath=filePath.strpath, backend="netcdf")
    testFile.read()
    testFile.setProperty("name", "u10", prop_type=str)
    if testFile.hasData():
        dims = testFile.dimensions.to_dict()
        test1 = dims['dim']['nx'] == 681 and dims['dim']['ny'] == 700
        test2 = round(testFile.getCellValue(0, j=0), 2) == 2.1
        assert test1 == test2, "Netcdf read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_netcdf_name(datadir):

    # Read test file
    filePath = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.009.surface.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using netcdf
    with pytest.raises(ValueError):
        testFile = raster.RasterFile(name="u 10", filePath=filePath.strpath, backend="netcdf")

    testFile = raster.RasterFile(name="u10", filePath=filePath.strpath, backend="netcdf")
    testFile.read()
    with pytest.raises(ValueError):
        testFile.setProperty("name", "u 10", prop_type=str)
    if testFile.hasData():
        dims = testFile.dimensions.to_dict()
        test1 = dims['dim']['nx'] == 681 and dims['dim']['ny'] == 700
        test2 = round(testFile.getCellValue(0, j=0), 2) == 2.1
        assert test1 == test2, "Netcdf read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_netcdf_multi(datadir):

    # Read test file
    file1 = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.009.surface.nc")
    file2 = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.010.surface.nc")
    if any(map(lambda f: not os.path.exists(f), [file1.strpath, file2.strpath])):
        raise FileNotFoundError(
            f'file {os.path.basename(file1.strpath)} or ' +
            f'{os.path.basename(file2.strpath)} does not exist.')

    # Try to read using netcdf
    with pytest.raises(ValueError):
        testFile = raster.RasterFile(name="u 10",
                                     filePath=[file1.strpath, file2.strpath],
                                     backend="netcdf")

    testFile = raster.RasterFile(name="u10", filePath=[file1.strpath, file2.strpath],
                                 backend="netcdf")
    testFile.read(layers=-1)

    with pytest.raises(ValueError):
        testFile.setProperty("name", "u 10", prop_type=str)

    if testFile.hasData():
        dims = testFile.dimensions.to_dict()
        test1 = dims['dim']['nx'] == 681 and dims['dim']['ny'] == 700
        test2 = round(testFile.getCellValue(0, j=0), 2) == 2.1
        assert test1 == test2, "Netcdf read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_gdal(tmpdir):

    # Create test file
    temp = raster.Raster(name="testRasterA")
    temp.init(10, 1.0, ny=10, hy=1.0)
    temp.data = np.random.random((10, 10)).astype(REAL)
    filePath = tmpdir.join("gs_test.tif")
    temp.setProjectionParameters(ProjectionParameters.from_epsg(4283))
    temp.write(filePath.strpath, jsonConfig="")

    # Try to read using gdal
    testFile = raster.RasterFile(name="test", filePath=filePath.strpath, backend="gdal")
    testFile.read()
    if testFile.hasData():
        assert np.allclose(temp.data, testFile.data)
    else:
        raise RuntimeError("Unable to initialize RasterFile")
    del testFile


@pytest.mark.rasterio
@pytest.mark.skipif(not supported_libs.HAS_RASTERIO, reason="rasterio library is not installed")
def test_rasterio(tmpdir):

    # Create test file
    temp = raster.Raster(name="testRasterA")
    temp.init(10, 1.0, ny=10, hy=1.0)
    temp.data = np.random.random((10, 10)).astype(REAL)
    filePath = tmpdir.join("gs_test.tif")
    temp.setProjectionParameters(ProjectionParameters.from_epsg(4283))
    temp.write(filePath.strpath, jsonConfig="")

    # Try to read using rasterio
    testFile = raster.RasterFile(name="test", filePath=filePath.strpath, backend="rasterio")
    testFile.read()
    if testFile.hasData():
        assert np.allclose(temp.data, testFile.data)
    else:
        raise RuntimeError("Unable to initialize RasterFile")
    del testFile


@pytest.mark.xarray
@pytest.mark.skipif(not supported_libs.HAS_XARRAY, reason="xarray library is not installed")
def test_xarray(datadir):
    # Read test file
    filePath = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.009.surface.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read using xarray
    testFile = raster.RasterFile(name="u10", filePath=filePath.strpath,
                                 backend="xarray")
    testFile.read()
    testFile.setProperty("name", "u10", prop_type=str)
    if testFile.hasData():
        dims = testFile.dimensions.to_dict()
        test1 = dims['dim']['nx'] == 681 and dims['dim']['ny'] == 700
        test2 = round(testFile.getCellValue(0, j=0), 2) == 2.1
        assert test1 == test2, "xarray read test failed"
    else:
        raise RuntimeError("Unable to initialize RasterFile")


@pytest.mark.xarray
@pytest.mark.skipif(not supported_libs.HAS_XARRAY, reason="xarray library is not installed")
def test_xarray_multi(datadir):
    # Read test file
    file1 = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.009.surface.nc")
    file2 = datadir.join(
        "IDY25006.APS3.wind.10m.2019121112.010.surface.nc")
    if any(map(lambda f: not os.path.exists(f), [file1.strpath, file2.strpath])):
        raise FileNotFoundError(
            f'file {os.path.basename(file1.strpath)} or ' +
            f'{os.path.basename(file2.strpath)} does not exist.')

    # Try to read using xarray
    testFile = raster.RasterFile(name="u10",
                                 filePath=[file1.strpath, file2.strpath],
                                 backend="xarray")
    testFile.read(layers=-1)
    testFile.setProperty("name", "u10", prop_type=str)

    if testFile.hasData():
        dims = testFile.dimensions.to_dict()
        test1 = dims['dim']['nx'] == 681 and dims['dim']['ny'] == 700
        test2 = round(testFile.getCellValue(0, j=0), 2) == 2.1
        assert test1 == test2, "xarray read test failed"
    else:
        raise RuntimeError("Unable to initialize RasterFile")


@pytest.fixture
def filePath():
    out = "https://thredds.nci.org.au/thredds/dodsC/ua6_4/CMIP5/derived/CMIP5/GCM/native/BCC/bcc-csm1-1-m/rcp45/mon/atmos/Amon/r1i1p1/latest/spi/time-in-drought/spi_Amon_bcc-csm1-1-m_rcp45_r1i1p1_anntot-percent-in-drought_native.nc"
    return out


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netCDF4 library is not installed")
def test_opendap(filePath):

    # Try to read using opendap
    if not have_internet():
        warnings.warn("unable to use opendap as not connected to internet")
    else:
        testFile = raster.RasterFile(name="SPI_12_2050_drought",
                                     filePath=filePath,
                                     backend="netcdf")
        testFile.read(thredds=True)
        if testFile.hasData():
            dims = testFile.dimensions.to_dict()
            test1 = dims['dim']['nx'] == 320 and dims['dim']['ny'] == 160
            test2 = round(testFile.data[0, 0], 2) == 23.75
            assert test1 == test2, "netcdf opendap read test failed"
        else:
            raise RuntimeError("Unable to initialize RasterFile")


@pytest.fixture
def vsiPath():
    out = "/vsicurl/https://thredds.nci.org.au/thredds/fileServer/fk4/dlcd/2.1/DLCDv2-1data/DLCD_v2-1_MODIS_EVI_10_20110101-20121231.tif"
    return out


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_gdal_vsi(vsiPath):

    # Try to read using vsi
    if not have_internet():
        warnings.warn("unable to use vsi as not connected to internet")
    else:
        testFile = raster.RasterFile(filePath=vsiPath,
                                     name="evi",
                                     backend="gdal")
        testFile.read()
        if testFile.hasData():
            test1 = testFile.dimensions.nx == 19161 and testFile.dimensions.ny == 14902
            test2 = round(testFile.getCellValue(5000, j=5000), 2) == 18.0
            assert test1 == test2, "gdal vsi read test failed"
        else:
            raise RuntimeError("Unable to initialize RasterFile")


@pytest.mark.rasterio
@pytest.mark.skipif(not supported_libs.HAS_RASTERIO, reason="rasterio library is not installed")
def test_rio_vsi(vsiPath):

    # Try to read using vsi
    if not have_internet():
        warnings.warn("unable to use vsi as not connected to internet")
    else:
        testFile = raster.RasterFile(filePath=vsiPath,
                                     name="evi",
                                     backend="rasterio")
        testFile.read()
        if testFile.hasData():
            test1 = testFile.dimensions.nx == 19161 and testFile.dimensions.ny == 14902
            test2 = round(testFile.getCellValue(5000, j=5000), 2) == 18.0
            assert test1 == test2, "gdal vsi read test failed"
        else:
            raise RuntimeError("Unable to initialize RasterFile")


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
@pytest.mark.parametrize("layers,nz,expected",
                         [(0, 1, 981.0),
                          (-1, 6, 1015.83),
                          ([0, 2, 4], 3, 1010.17),
                          (slice(0, 4, 2), 2, 887.75)],)
def test_gdal_multiband(datadir, layers, nz, expected):
    # Read test file
    filePath = datadir.join("multiband.tif")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read multiband tif file
    testFile = raster.RasterFile(
        filePath=filePath.strpath, name="red", backend="gdal")
    testFile.read(layers=layers)
    if testFile.hasData():
        test1 = testFile.dimensions.nx == 256 and testFile.dimensions.ny == 256
        test3 = testFile.dimensions.nz == nz
        if nz > 1:
            script = """
            output = 0.0;
            for (uint k=0; k<red_layers; k++){
                output += red[k] / red_layers;
            }
            """
            output = runScript(script, [testFile])
            test2 = expected == round(output.getCellValue(0, j=0, k=0), 2)
        else:
            test2 = expected == round(testFile.getCellValue(0, j=0, k=0), 2)
        # test2 = round(testFile.getCellValue(0, j=0), 2) == -6.9
        assert test1 == test2 == test3, "gdal multiband read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.rasterio
@pytest.mark.skipif(not supported_libs.HAS_RASTERIO, reason="rasterio library is not installed")
@pytest.mark.parametrize("layers,nz,expected",
                         [(0, 1, 981.0),
                          (-1, 6, 1015.83),
                          ([0, 2, 4], 3, 1010.17),
                          (slice(0, 4, 2), 2, 887.75)],)
def test_rio_multiband(datadir, layers, nz, expected):
    # Read test file
    filePath = datadir.join("multiband.tif")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read multiband tif file
    testFile = raster.RasterFile(
        filePath=filePath.strpath, name="red", backend="rasterio")
    testFile.read(layers=layers)
    if testFile.hasData():
        test1 = testFile.dimensions.nx == 256 and testFile.dimensions.ny == 256
        test3 = testFile.dimensions.nz == nz
        if nz > 1:
            script = """
            output = 0.0;
            for (uint k=0; k<red_layers; k++){
                output += red[k] / red_layers;
            }
            """
            output = runScript(script, [testFile])
            test2 = expected == round(output.getCellValue(0, j=0, k=0), 2)
        else:
            test2 = expected == round(testFile.getCellValue(0, j=0, k=0), 2)
        # test2 = round(testFile.getCellValue(0, j=0), 2) == -6.9
        assert test1 == test2 == test3, "rasterio multiband read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf library is not installed")
def test_nc_reader(datadir):
    filepath = datadir.join("geostack_test_file.nc")

    test_native = raster.Raster("testA")
    test_native.read(filepath.strpath, jsonConfig={
                     "variable": "tas", "layers": [0]})

    test_ncdf4 = raster.RasterFile(name="testA", variable_map="tas",
                                   filePath=filepath.strpath,
                                   backend="netcdf")
    test_ncdf4.read()

    assert test_native.dimensions.ox == test_ncdf4.dimensions.ox
    assert test_native.dimensions.nx == test_ncdf4.dimensions.nx
    assert test_native.dimensions.oy == test_ncdf4.dimensions.oy
    assert test_native.dimensions.ny == test_ncdf4.dimensions.ny
    assert test_native.dimensions.nz == test_ncdf4.dimensions.nz
    assert test_native.dimensions.hx == test_ncdf4.dimensions.hx
    assert test_native.dimensions.hy == test_ncdf4.dimensions.hy


@pytest.mark.xarray
@pytest.mark.skipif(not supported_libs.HAS_XARRAY, reason="xarray library is not installed")
def test_xr_reader(datadir):
    filepath = datadir.join("geostack_test_file.nc")

    test_native = raster.Raster("testA")
    test_native.read(filepath.strpath, jsonConfig={
                     "variable": "tas", "layers": [0]})

    test_ncdf4 = raster.RasterFile(name="testA", variable_map="tas",
                                   filePath=filepath.strpath,
                                   backend="xarray")
    test_ncdf4.read()

    assert test_native.dimensions.ox == test_ncdf4.dimensions.ox
    assert test_native.dimensions.nx == test_ncdf4.dimensions.nx
    assert test_native.dimensions.oy == test_ncdf4.dimensions.oy
    assert test_native.dimensions.ny == test_ncdf4.dimensions.ny
    assert test_native.dimensions.nz == test_ncdf4.dimensions.nz
    assert test_native.dimensions.hx == test_ncdf4.dimensions.hx
    assert test_native.dimensions.hy == test_ncdf4.dimensions.hy


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_tiff_gdal(datadir):
    filepath = datadir.join("multiband.tif")

    test_native = raster.Raster("testA")
    test_native.read(filepath.strpath)

    test_gdal = raster.RasterFile(name="testA",
                                  filePath=filepath.strpath,
                                  backend="gdal")
    test_gdal.read(layers=[0, 1, 2, 3, 4, 5])

    assert test_native.dimensions == test_gdal.dimensions


@pytest.mark.rasterio
@pytest.mark.skipif(not supported_libs.HAS_RASTERIO, reason="rasterio library is not installed")
def test_tiff_rio(datadir):
    filepath = datadir.join("multiband.tif")

    test_native = raster.Raster("testA")
    test_native.read(filepath.strpath)

    test_rio = raster.RasterFile(name="testA",
                                 filePath=filepath.strpath,
                                 backend="rasterio")
    test_rio.read(layers=[0, 1, 2, 3, 4, 5])

    assert test_native.dimensions == test_rio.dimensions


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf4 library is not installed")
@pytest.mark.parametrize("layers,nz,expected",
                         [(0, 1, 0.9555732011795044),
                          (-1, 10, 0.4632977247238159),
                          ([0, 2, 4], 3, 0.528213620185852),
                          (slice(0, 4, 2), 2, 0.7198922634124756)],)
def test_netcdf_3d(layers, nz, expected, datadir):
    dims = ("height", "latitude", "longitude")
    filePath = datadir.join("geostack_multi_step.nc")
    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read multiband tif file
    testFile = raster.RasterFile(
        filePath=filePath.strpath, name="testA", backend="netcdf")
    testFile.read(layers=layers, dims=dims)
    if testFile.hasData():
        test1 = testFile.dimensions.nx == 64 and testFile.dimensions.ny == 64
        test3 = testFile.dimensions.nz == nz
        if nz > 1:
            script = f"""
            output = 0.0;
            for (uint k=0; k<{testFile.name}_layers; k++){{
                output += {testFile.name}[k] / {testFile.name}_layers;
            }}
            """
            output = runScript(script, [testFile])
            test2 = round(expected, 2) == round(
                output.getCellValue(0, j=0, k=0), 2)
        else:
            test2 = round(expected, 2) == round(
                testFile.getCellValue(0, j=0, k=0), 2)
        # test2 = round(testFile.getCellValue(0, j=0), 2) == -6.9
        assert test1 == test2 == test3, "netcdf 3d read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.netcdf4
@pytest.mark.skipif(not supported_libs.HAS_NCDF, reason="netcdf4 library is not installed")
@pytest.mark.parametrize("layers,nz,expected",
                         [(0, 1, 0.9555732011795044),
                          (-1, 10, 0.4632977247238159),
                          ([0, 2, 4], 3, 0.528213620185852),
                          ("[:4:2]", 2, 0.7198922634124756)],)
def test_netcdf_3d_jsonConfig(layers, nz, expected, datadir):
    dims = ("height", "latitude", "longitude")
    filePath = datadir.join("geostack_multi_step.nc")
    jsonConfig = json.dumps({"layers": layers, "dims": list(dims)})

    if not os.path.exists(filePath.strpath):
        raise FileNotFoundError(
            f'file {os.path.basename(filePath.strpath)} does not exist.')

    # Try to read multiband tif file
    testFile = raster.RasterFile(
        filePath=filePath.strpath, name="testA", backend="netcdf")
    testFile.read(jsonConfig=jsonConfig)
    if testFile.hasData():
        test1 = testFile.dimensions.nx == 64 and testFile.dimensions.ny == 64
        test3 = testFile.dimensions.nz == nz
        if nz > 1:
            script = f"""
            output = 0.0;
            for (uint k=0; k<{testFile.name}_layers; k++){{
                output += {testFile.name}[k] / {testFile.name}_layers;
            }}
            """
            output = runScript(script, [testFile])
            test2 = round(expected, 2) == round(
                output.getCellValue(0, j=0, k=0), 2)
        else:
            test2 = round(expected, 2) == round(
                testFile.getCellValue(0, j=0, k=0), 2)
        # test2 = round(testFile.getCellValue(0, j=0), 2) == -6.9
        assert test1 == test2 == test3, "netcdf 3d read test failed"
    else:
        raise RuntimeError("Unable to initialize DataFileHandler")


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_raster_file_index_component(tmpdir):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(300, 1.0, ny=300, hy=1.0)

    vecA = vector.Vector()
    vecA.addPoint([100, 100])
    vecA.addPoint([200, 200])
    vecA.addPoint([100, 200])

    testRasterA.mapVector(vecA, "")

    file_name = tmpdir.join("testRasterA.tif")
    testRasterA.write(file_name.strpath)

    testRasterA = raster.RasterFile(filePath=file_name.strpath,
                                    name='testRasterA',
                                    backend='gdal')
    testRasterA.read()

    index0 = testRasterA.indexComponents(f"{testRasterA.name} < 10.0")

    test1 = index0.hasData()
    test2 = index0.getProperty("componentCount") == 3

    index2 = testRasterA.indexComponents(f"{testRasterA.name} < 50.0")

    test3 = index2.hasData()
    test4 = index2.getProperty("componentCount") == 1

    assert all([test1, test2, test3, test4])


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_raster_indexComponentsVector(tmpdir):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(300, 1.0, ny=300, hy=1.0)

    vecA = vector.Vector()
    vecA.addPoint([100, 100])
    vecA.addPoint([200, 200])
    vecA.addPoint([100, 200])

    testRasterA.mapVector(vecA, "")

    file_name = tmpdir.join("testRasterA.tif")
    testRasterA.write(file_name.strpath)

    testRasterA = raster.RasterFile(filePath=file_name.strpath,
                                    name='testRasterA',
                                    backend='gdal')
    testRasterA.read()

    componentVector0 = testRasterA.indexComponentsVector(f"{testRasterA.name} < 10.0")
    test1 = isinstance(componentVector0, vector.Vector)
    test2 = componentVector0.getPointCount() == 3

    componentVector3 = testRasterA.indexComponentsVector(f"{testRasterA.name} < 50.0")
    test3 = isinstance(componentVector0, vector.Vector)
    test4 = componentVector3.getPointCount() == 1

    assert all([test1, test2, test3, test4])
