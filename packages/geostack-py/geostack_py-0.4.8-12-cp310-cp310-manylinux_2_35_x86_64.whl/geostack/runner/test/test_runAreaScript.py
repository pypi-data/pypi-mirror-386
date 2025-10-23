# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

import pytest
from geostack.raster import Raster
from geostack.runner import runAreaScript

@pytest.mark.runScript
def test_runAreaScript():

    testRasterA = Raster(name="testRasterA")
    testRasterA.init(nx=21, hx=1.0, ny=21, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, 10, 10)

    #Run script
    script = """

    // Average
    if (isValid_REAL(testRasterA)) {
        if isValid_REAL(output) {
            output += testRasterA;
        } else {
            output = testRasterA;
        }
        sum+=1.0;
    }
    """

    # with raster
    output = runAreaScript(script, testRasterA, 3)

    # Test values
    assert output.hasData()
    assert round(output.getCellValue(10, 10), 5) == round((99.9 / 49.0), 5)

    # with raster base
    output = runAreaScript(script, testRasterA.get_raster_base(), 3)

    # Test values
    assert output.hasData()
    assert round(output.getCellValue(10, 10), 5) == round((99.9 / 49.0), 5)
