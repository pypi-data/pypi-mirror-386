# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import numpy as np
from time import time
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.raster import raster
from geostack.vector import vector
from geostack.solvers import Multigrid
from geostack.runner import runScript

@pytest.mark.multigrid
def test_multigrid():
    # create forcing grid
    pf = raster.Raster(name="f")
    pf.init(500, 1.0, ny=500, hy=1.0)
    pf.setAllCellValues(0.0)
    pf.setCellValue(100.0, 250, 250)

    inputLayers = raster.RasterPtrList()
    inputLayers.append(pf)

    # create solver configuration
    config = {
        "initialisationScript": "b = f;"
    }

    # initialise solver
    solver = Multigrid()
    initSuccess = solver.init(json.dumps(config), inputLayers=inputLayers)

    # run solver
    runSuccess = True & solver.step()

    # get solution raster
    u = solver.getSolution()

    # test two points of raster for zero second derivative
    d_50_50 = (u.getCellValue(49, 50) +
               u.getCellValue(51, 50) +
               u.getCellValue(50, 49) +
               u.getCellValue(50, 51) -
               4.0 * u.getCellValue(50, 50))

    test_value1 = abs(d_50_50) < 1.00e-3

    d_400_100 = (u.getCellValue(399, 100) +
                 u.getCellValue(401, 100) +
                 u.getCellValue(400, 99) +
                 u.getCellValue(400, 101) -
                 4.0 * u.getCellValue(400, 100))

    test_value2 = abs(d_400_100) < 1.00e-3

    assert all([initSuccess, runSuccess, test_value1, test_value2])


@pytest.mark.multigrid
@pytest.mark.parametrize("size", [256, 512, 1024])
def test_pyramids(size):
    testA = raster.Raster("f")
    testA.init(nx=size, hx=1.0, ny=size, hy=1.0)
    runScript("f = x * y;", [testA])

    raster_list = raster.RasterPtrList()
    raster_list.append(testA)

    solver = Multigrid()
    solver.init(jsonConfig={"initialisationScript": "b = f;"}, inputLayers=raster_list)

    solver.pyramids()

    dim_in = solver.getForcing().getRasterDimensions()

    for level in range(0, 8):
        dims = solver.getForcingLevel(level).getRasterDimensions()
        assert dims.nx == dim_in.nx >> level
        assert dims.ny == dim_in.ny >> level
        assert abs(solver.getForcingLevel(level).getBilinearValue(int(size/2), int(size/2)) - int(size/2) * int(size/2)) < 1.0e5
