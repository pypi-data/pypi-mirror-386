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
from geostack import vector
from geostack.core import REAL

def test_create_raster():
    with pytest.raises(ValueError):
        testRasterA = raster.Raster(name="testRaster A", base_type=REAL,
            data_type=REAL)


def test_set_prop1():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, 2)

    with pytest.raises(ValueError):
        testRasterA.name = "testRaster A"


def test_set_prop2():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, 2)

    with pytest.raises(ValueError):
        testRasterA.name = "testRaster Δ"


def test_set_prop3():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, 2)

    with pytest.raises(ValueError):
        testRasterA.name = "testRaster ü"


def test_raster_1D():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, 2)
    assert round(testRasterA.max(), 1) == 99.9
    assert testRasterA.min() == 1.0


def test_raster2d_resize():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    assert testRasterA.hasData() == True
    assert round(testRasterA.getNearestValue(2, 2), 1) == 99.9
    assert round(testRasterA.max(), 1) == 99.9
    assert testRasterA.min() == 1.0


def test_raster_max():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, i=2, j=2)
    assert round(testRasterA.max(), 1) == 99.9


def test_raster_min():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, i=2, j=2)
    assert round(testRasterA.min(), 1) == 0.0


def test_raster_copy():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterC = raster.Raster.copy("testRasterC", testRasterA)
    assert testRasterC.name == "testRasterC"


def test_raster_data():

    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterC = raster.Raster.copy("testRasterC", testRasterA)
    assert np.allclose(testRasterC, testRasterA) == True


def test_raster2d_properties():
    testRasterA = raster.Raster(name="testRasterA", base_type=REAL,
        data_type=REAL)
    testRasterA.init(5, 1.0, ny=5, hy=1.0)

    testRasterA.setProperty("property0", 99)
    testRasterA.setProperty("property1", "rstr")

    assert int(testRasterA.getProperty("property0")) == 99
    assert testRasterA.getProperty("property1") == "rstr"


def test_raster_sort():
    kvals = np.array([9.0, 7.5, 22.2, 8.1, 3.7])
    testRasterA = raster.Raster(name="testRasterA")
    testRasterA.init(5, 1.0, ny=5, hy=1.0, nz=5, hz=1.0)
    testRasterA.data = kvals[:,None,None] * np.ones(testRasterA.shape)
    raster.sortColumns(testRasterA, inplace=True)

    test_data = testRasterA.hasData()
    test_value1 = round(testRasterA.getCellValue(2, 2, 0), ndigits=1) == 3.7
    test_value2 = round(testRasterA.getCellValue(2, 2, 4), ndigits=1) == 22.2

    assert test_data & test_value1 & test_value2


def test_raster_index_component():
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(300, 1.0, ny=300, hy=1.0)

    vecA = vector.Vector()
    vecA.addPoint([100, 100])
    vecA.addPoint([200, 200])
    vecA.addPoint([100, 200])

    testRasterA.mapVector(vecA, "")

    index0 = testRasterA.indexComponents(f"{testRasterA.name} < 10.0")

    test1 = index0.hasData()
    test2 = index0.getProperty("componentCount") == 3

    index2 = testRasterA.indexComponents(f"{testRasterA.name} < 50.0")

    test3 = index2.hasData()
    test4 = index2.getProperty("componentCount") == 1

    assert all([test1, test2, test3, test4])


def test_raster_indexComponentsVector():
    testRasterA = raster.Raster(name="testRasterA",
                                base_type=REAL,
                                data_type=REAL)
    testRasterA.init(300, 1.0, ny=300, hy=1.0)

    vecA = vector.Vector()
    vecA.addPoint([100, 100])
    vecA.addPoint([200, 200])
    vecA.addPoint([100, 200])

    testRasterA.mapVector(vecA, "")

    componentVector0 = testRasterA.indexComponentsVector(f"{testRasterA.name} < 10.0")
    test1 = isinstance(componentVector0, vector.Vector)
    test2 = componentVector0.getPointCount() == 3

    componentVector3 = testRasterA.indexComponentsVector(f"{testRasterA.name} < 50.0")
    test3 = isinstance(componentVector0, vector.Vector)
    test4 = componentVector3.getPointCount() == 1

    assert all([test1, test2, test3, test4])
