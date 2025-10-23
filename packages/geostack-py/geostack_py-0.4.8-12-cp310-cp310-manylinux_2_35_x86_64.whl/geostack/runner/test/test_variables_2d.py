# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
import pytest
from geostack.raster import Raster
from geostack.runner import runScript

@pytest.mark.runScript
@pytest.mark.parametrize("variable,value",
                         [("varA", 99.9),
                          ("varB", 88.8),
                          ("varC", 77.7)],)
def test_raster_variables(variable, value):
    testRasterA = Raster(name="testRasterA")
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setVariableData(variable, value)

    runScript(f"testRasterA = testRasterA::{variable};", [testRasterA])
    test_data = testRasterA.hasData()
    test_value = round(testRasterA.getNearestValue(1, 1), ndigits=1) == value

    assert test_data & test_value


@pytest.mark.runScript
def test_multiple_variables():
    testRasterA = Raster(name="testRasterA")
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    total_value = 0.0
    for var, value in [("varA", 99.9), ("varB", 88.8), ("varC", 77.7)]:
        total_value += value
        testRasterA.setVariableData(var, value)

    runScript("testRasterA = testRasterA::varA+testRasterA::varB+testRasterA::varC;",
              [testRasterA])

    test_data = testRasterA.hasData()
    test_value = round(testRasterA.getNearestValue(1, 1), ndigits=1) == total_value

    assert test_data & test_value


@pytest.mark.runScript
def test_arr_variable():
    # Create rasters
    testRasterA = Raster(name="testRasterA")
    testRasterA.init(5, 1.0, ny=5, hy=1.0)
    testRasterA.setVariableData("varA", 99.9)
    testRasterA.setVariableData("varB", 88.8)
    testRasterA.setVariableData("varC", 77.7)
    testRasterA.setVariableData("arrD", 111.0, 0)
    testRasterA.setVariableData("arrD", 111.1, 1)
    testRasterA.setVariableData("arrD", 111.2, 2)
    testRasterA.setVariableData("arrD", 111.3, 3)

    # Run script
    runScript(
        "testRasterA = testRasterA::varA+testRasterA::varB+testRasterA::varC+testRasterA::arrD;",
        [testRasterA] )

    # Test values
    assert testRasterA.hasData()
    assert round(testRasterA.getNearestValue(1, 1), ndigits=1) == 99.9+88.8+77.7+111.0

    # Run script
    runScript(
        "testRasterA = testRasterA::arrD[2]; testRasterA::arrD[3] = 999.9",
        [testRasterA] )

    # Test values
    assert testRasterA.hasData()
    assert round(testRasterA.getNearestValue(1, 1), ndigits=1) == 111.2
    assert round(testRasterA.getVariableData("arrD", 3), ndigits=1) == 999.9
