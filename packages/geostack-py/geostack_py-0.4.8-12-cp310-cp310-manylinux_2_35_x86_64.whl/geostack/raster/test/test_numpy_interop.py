# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys

sys.path.insert(0, os.path.realpath('../../../'))

import pytest
import numpy as np
from geostack import raster
from geostack.core import REAL


@pytest.mark.npyio
@pytest.mark.parametrize("xslice",
                         [slice(None, 10),
                          slice(240, 279),
                          slice(None, None, 10)],)
def test_1d_getter(xslice):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ox=0)
    testRasterA.data = np.random.random(testRasterA.shape)

    assert np.allclose(testRasterA[xslice],
                       testRasterA.data[xslice])


@pytest.mark.npyio
@pytest.mark.parametrize("xslice,yslice",
                         [(slice(None, 10), slice(None, 10)),
                          (slice(240, 279), slice(30, 40)),
                          (slice(None, None, 10), slice(None, None, 5))],)
def test_2d_getter(xslice, yslice):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ny=512, hy=1.0, ox=0, oy=-90)
    testRasterA.data = np.random.random(testRasterA.shape)

    assert np.allclose(testRasterA[yslice, xslice],
                       testRasterA.data[yslice, xslice])


@pytest.mark.npyio
@pytest.mark.parametrize("xslice,yslice,zslice",
                         [(slice(None, 10), slice(None, 10), 0),
                          (slice(240, 279), slice(30, 40), slice(None)),
                          (slice(None, None, 10), slice(None, None, 5), slice(None, None, 2))],)
def test_3d_getter(xslice, yslice, zslice):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ny=512, hy=1.0,
                     nz=10, hz=1.0, ox=0, oy=-90, oz=0)
    testRasterA.data = np.random.random(testRasterA.shape)

    assert np.allclose(testRasterA[zslice, yslice, xslice],
                       testRasterA.data[zslice, yslice, xslice])


@pytest.mark.npyio
@pytest.mark.parametrize("xslice,xsize",
                         [(slice(None, 10), 10),
                          (slice(240, 279), 39),
                          (slice(None, None, 10), 52)],)
def test_1d_setter(xslice, xsize):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ox=0)
    testRasterA.data = np.random.random(testRasterA.shape)

    random_data = np.random.random((xsize,))
    testRasterA[xslice] = random_data

    assert np.allclose(testRasterA[xslice],
                       random_data)


@pytest.mark.npyio
@pytest.mark.parametrize("xslice,yslice,xsize,ysize",
                         [(slice(None, 10), slice(None, 10), 10, 10),
                          (slice(240, 279), slice(240, 279), 39, 39),
                          (slice(None, None, 10), slice(None, None, 10), 52, 52),
                          (0, slice(None, None, 10), 0, 52),
                          (slice(None, None, 10), 0, 52, 0)],)
def test_2d_setter(xslice, yslice, xsize, ysize):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ny=512, hy=1.0,
                     ox=0, oy=-90)

    testRasterA.data = np.random.random(testRasterA.shape)

    if xsize == 0 or ysize == 0:
        if xsize > 0:
            random_data = np.random.random((xsize,))
        elif ysize > 0:
            random_data = np.random.random((ysize,))
    else:
        random_data = np.random.random((ysize, xsize,))

    testRasterA[yslice, xslice] = random_data
    assert np.allclose(testRasterA[yslice, xslice],
                       random_data)


@pytest.mark.npyio
@pytest.mark.parametrize("xslice,yslice,zslice,xsize,ysize,zsize",
                         [(slice(None, 10), slice(None, 10), slice(None, 2), 10, 10, 2),
                          (slice(240, 279), slice(240, 279), slice(None), 39, 39, 10),
                          (slice(None, None, 10), slice(None, None, 10), slice(6, None), 52, 52, 4),
                          (slice(None, None, 10), 0, slice(6, None), 52, 0, 4),
                          (0, slice(None, None, 10), slice(6, None), 0, 52, 4)],)
def test_3d_setter(xslice, yslice, zslice, xsize, ysize, zsize):
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(512, hx=1.0, ny=512, hy=1.0,
                     nz=10, hz=1.0, ox=0, oy=-90, oz=0)

    testRasterA.data = np.random.random(testRasterA.shape)

    if xsize == 0 or ysize == 0:
        if ysize > 0:
            random_data = np.random.random((zsize, ysize,))
        elif xsize > 0:
            random_data = np.random.random((zsize, xsize,))
    else:
        random_data = np.random.random((zsize, ysize, xsize,))

    testRasterA[zslice, yslice, xslice] = random_data

    assert np.allclose(testRasterA[zslice, yslice, xslice],
                       random_data)
