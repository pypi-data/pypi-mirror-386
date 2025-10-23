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


@pytest.mark.raster_container
@pytest.mark.parametrize("container",
                         [None, list, tuple])
def test_raster_base_set(container):
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
                                data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setAllCellValues(1.0)

    testRasterB = raster.Raster(name="testRasterB", base_type=REAL,
                                data_type=REAL)
    testRasterB.init(5, 1.0, ny=5, hy=1.0)
    testRasterB.setAllCellValues(2.0)

    base_list = raster.RasterBaseList()
    if container is None:
        base_list.append(testRasterA)
        base_list.append(testRasterB)
    elif container is list:
        base_list.from_object([testRasterA, testRasterB])
    elif container is tuple:
        base_list.from_object((testRasterA, testRasterB))

    assert base_list.size == 2
    assert len(base_list) == base_list.size == 2


@pytest.mark.raster_container
def test_raster_base_get():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
                                data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setAllCellValues(1.0)

    testRasterB = raster.Raster(name="testRasterB", base_type=REAL,
                                data_type=REAL)
    testRasterB.init(5, 1.0, ny=5, hy=1.0)
    testRasterB.setAllCellValues(2.0)

    base_list = raster.RasterBaseList()
    base_list.append(testRasterA)
    base_list.append(testRasterB)

    raster_a = base_list.get_raster(0)
    assert raster_a.getDimensions() == testRasterA.dimensions

    raster_b = base_list.get_raster(1)
    assert raster_b.getDimensions() == testRasterB.dimensions


@pytest.mark.raster_container
@pytest.mark.parametrize("container",
                         [None, list, tuple])
def test_raster_ptr_set(container):
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
                                data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setAllCellValues(1.0)

    testRasterB = raster.Raster(name="testRasterB", base_type=REAL,
                                data_type=REAL)
    testRasterB.init(5, 1.0, ny=5, hy=1.0)
    testRasterB.setAllCellValues(2.0)

    base_list = raster.RasterPtrList()
    if container is None:
        base_list.append(testRasterA)
        base_list.append(testRasterB)
    elif container is list:
        base_list.from_object([testRasterA, testRasterB])
    elif container is tuple:
        base_list.from_object((testRasterA, testRasterB))

    assert base_list.size == 2
    assert len(base_list) == base_list.size == 2


@pytest.mark.raster_container
def test_raster_ptr_get():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
                                data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setAllCellValues(1.0)

    testRasterB = raster.Raster(name="testRasterB", base_type=REAL,
                                data_type=REAL)
    testRasterB.init(5, 1.0, ny=5, hy=1.0)
    testRasterB.setAllCellValues(2.0)

    base_list = raster.RasterPtrList()
    base_list.append(testRasterA)
    base_list.append(testRasterB)

    raster_a = base_list.get_raster(0)
    assert raster_a.getDimensions() == testRasterA.dimensions

    raster_b = base_list.get_raster(1)
    assert raster_b.getDimensions() == testRasterB.dimensions
