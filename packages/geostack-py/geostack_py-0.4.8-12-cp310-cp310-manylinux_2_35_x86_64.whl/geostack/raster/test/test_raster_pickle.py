# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
from distutils import dir_util
import pickle
from uuid import uuid4
sys.path.insert(0, os.path.realpath('../../../'))

import pytest
import numpy as np
from geostack import raster
from geostack import dataset

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
@pytest.mark.skipif(not dataset.supported_libs.HAS_NCDF,
                    reason="netcdf library is not installed")
@pytest.mark.parametrize("filename,i,j,var",
                       [("IDY25006.APS3.wind.10m.2019121112.009.surface.nc", 350, 350, 'v10'),
                        ('geostack_test_file.nc', 3, 3, 'tas')])
def test_rasterfile_nc(datadir, filename, i, j, var):
    file = datadir.join(filename)
    fin = raster.RasterFile(filePath=file.strpath,
                            name=var,
                            backend='netcdf')
    fin.read(layers=0)
    x = fin.getCellValue(i=i, j=j, k=0)

    fout = f"{uuid4()}.pkl"
    with open(datadir.join(fout).strpath, 'wb') as out:
        pickle.dump(fin, out)

    with open(datadir.join(fout).strpath, 'rb') as inp:
        fin_c = pickle.load(inp)

    y = fin_c.getCellValue(i=i, j=j, k=0)
    assert x == y

@pytest.mark.gdal
@pytest.mark.skipif(not dataset.supported_libs.HAS_GDAL,
                    reason="gdal library is not installed")
def test_rasterfile_gdal(datadir):
    file = datadir.join("multiband.tif")

    i, j = 128, 128
    fin = raster.RasterFile(filePath=file.strpath,
                            name='multiband',
                            backend='gdal')
    fin.read(layers=0)
    x = fin.getCellValue(i=i, j=j, k=0)

    fout = f"{uuid4()}.pkl"
    with open(datadir.join(fout).strpath, 'wb') as out:
        pickle.dump(fin, out)

    with open(datadir.join(fout).strpath, 'rb') as inp:
        fin_c = pickle.load(inp)

    y = fin_c.getCellValue(i=i, j=j, k=0)
    assert x == y

def test_raster_obj(datadir):
    file = datadir.join("multiband.tif")

    i, j = 128, 128
    fin = raster.Raster(name='multiband')
    fin.read(file.strpath)
    x = fin.getCellValue(i=i, j=j, k=0)

    fout = f"{uuid4()}.pkl"
    with open(datadir.join(fout).strpath, 'wb') as out:
        pickle.dump(fin, out)

    with open(datadir.join(fout).strpath, 'rb') as inp:
        fin_c = pickle.load(inp)

    y = fin_c.getCellValue(i=i, j=j, k=0)
    assert x == y
