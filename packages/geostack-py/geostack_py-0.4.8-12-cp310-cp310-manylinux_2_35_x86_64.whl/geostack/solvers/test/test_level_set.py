# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import math
import numpy as np
from time import time
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.core import Variables
from geostack.vector import vector
from geostack.raster import raster
from geostack.runner import runScript
from geostack.solvers import LevelSet


@pytest.mark.levelset
def test_level_set1(tmpdir):
    # create starting conditions
    v = vector.Vector()
    v.addPoint(vector.Coordinate.from_list([0.0, 0.0]))
    v.setProperty(0, "radius", 10)

    # create type raster
    pType = raster.Raster(name="type")
    pType.init(1000, 1.0, ny=1000, hy=1.0, ox=-500.0, oy=-500.0)
    runScript("type = x > 0 && x < 100 && y > 0 && y < 100 ? 2 : 1;", [pType])

    # create input and output raster list
    inputLayers = raster.RasterPtrList()
    inputLayers.append(pType)

    output_raster = raster.Raster(name="output")
    outputLayers = raster.RasterPtrList()
    outputLayers.append(output_raster)

    # create variables
    variables = Variables()
    variables.set("varA", 77.7)
    variables.set("varB", 88.8)
    variables.set("varC", 11.0, 0)
    variables.set("varC", 22.0, 1)
    variables.set("varC", 33.0, 2)
    variables.set("varD", 44.0, 0)
    variables.set("varD", 55.0, 1)
    variables.set("varD", 66.0, 2)

    # create solver configuration
    config = {"resolution": 0.5,
              "initialisationScript": "class = type;",
              "buildScript": "if (class == 1) { speed = 0.5;} else if (class == 2) {speed = 2.0;}",
              "updateScript": """
               output = class * varA + varB + varC[2]; for (int i = 0; i< varD_length; i++) {output += varD[i];}
               output2 = _distance;""",
              "outputLayers": "output2"
              }
    jsonConfig = json.dumps(config)

    # instantiate the solver
    solver = LevelSet()
    test_init = solver.init(jsonConfig, v, variables, inputLayers=inputLayers,
                            outputLayers=outputLayers)

    output2 = solver.getOutput("output2")

    # run solver
    test_run = True
    while (test_run & (solver.parameters.time < 100.0)):
        test_run = test_run & solver.step()

    # test arrival values

    arrival_raster = solver.getArrival()
    test1 = abs(arrival_raster.getBilinearValue(0.0, -50.0)-80.0) < 1.0
    test2 = abs(arrival_raster.getBilinearValue(-50.0, 0.0)-80.0) < 1.0
    m_sqrt1_2 = math.sqrt(1.0 / 2.0)
    test3 = abs(arrival_raster.getBilinearValue(-50.0*m_sqrt1_2, -50.0*m_sqrt1_2)-80.0) < 1.0
    test4 = abs(arrival_raster.getBilinearValue(50.0*m_sqrt1_2, 50.0*m_sqrt1_2)-20.0) < 1.0

    test5 = output_raster.getNearestValue(0, -50.0) == (1*77.7+88.8+33+44+55+66)
    test6 = output_raster.getNearestValue(-50.0, 0) == (1*77.7+88.8+33+44+55+66)
    test7 = output_raster.getNearestValue(-50.0*m_sqrt1_2, -50.0*m_sqrt1_2) == (1*77.7+88.8+33+44+55+66)
    test8 = round(output_raster.getNearestValue(50.0*m_sqrt1_2, 50.0*m_sqrt1_2), ndigits=1) == (2*77.7+88.8+33+44+55+66)

    output2.indexComponents(f"{output2.name} < -10")
    output2.indexComponentsVector(f"{output2.name} < -10")

    assert all([test_init, test_run, test1, test2, test3, test4,
                test5, test6, test7, test8])


@pytest.mark.levelset
def test_level_set2(tmpdir):
    # create starting conditions
    v = vector.Vector()
    v.addPoint(vector.Coordinate.from_list([0.0, 0.0]))
    v.setProperty(0, "radius", 10)

    # create type raster
    pType = raster.Raster(name="type")
    pType.init(1000, 1.0, ny=1000, hy=1.0, ox=-500.0, oy=-500.0)
    runScript("type = x > 0 && x < 100 && y > 0 && y < 100 ? 2 : 1;", [pType])

    # create input and output raster list
    inputLayers = raster.RasterPtrList()
    inputLayers.append(pType)

    output_raster = raster.Raster(name="output")
    outputLayers = raster.RasterPtrList()
    outputLayers.append(output_raster)

    # create variables
    variables = Variables()
    variables.set("varA", 77.7)
    variables.set("varB", 88.8)
    variables.set("varC", 11.0, 0)
    variables.set("varC", 22.0, 1)
    variables.set("varC", 33.0, 2)
    variables.set("varD", 44.0, 0)
    variables.set("varD", 55.0, 1)
    variables.set("varD", 66.0, 2)

    # create solver configuration
    config = {"resolution": 0.5,
              "initialisationScript": "class = type;",
              "buildScript": "if (class == 1) { speed = 0.5;} else if (class == 2) {speed = 2.0;}",
              "updateScript": """
                output = class * varA + varB + varC[2]; for (int i = 0; i< varD_length; i++) {output += varD[i];};
                output2 = _distance;""",
              "outputLayers": "output2"}
    jsonConfig = json.dumps(config)

    # instantiate the solver
    solver = LevelSet()
    test_init = solver.init(jsonConfig, v, variables, inputLayers=inputLayers,
                            outputLayers=outputLayers)

    # run solver
    test_run = True
    while (test_run & (solver.parameters.time < 100.0)):
        test_run = test_run & solver.step()

    # test arrival values

    arrival_raster = solver.getArrival()
    test1 = abs(arrival_raster.getBilinearValue(0.0, -50.0)-80.0) < 1.0
    test2 = abs(arrival_raster.getBilinearValue(-50.0, 0.0)-80.0) < 1.0
    m_sqrt1_2 = math.sqrt(1.0 / 2.0)
    test3 = abs(arrival_raster.getBilinearValue(-50.0*m_sqrt1_2, -50.0*m_sqrt1_2)-80.0) < 1.0
    test4 = abs(arrival_raster.getBilinearValue(50.0*m_sqrt1_2, 50.0*m_sqrt1_2)-20.0) < 1.0

    output2 = solver.getOutput("output2")

    with pytest.raises(NotImplementedError):
        output2.getNearestValue(0, -50.0)

    with pytest.raises(NotImplementedError):
        output2.getNearestValue(-50.0, 0)

    with pytest.raises(NotImplementedError):
        output2.getNearestValue(-50.0*m_sqrt1_2, -50.0*m_sqrt1_2)

    with pytest.raises(NotImplementedError):
        output2.getNearestValue(50.0*m_sqrt1_2, 50.0*m_sqrt1_2)

    output2.indexComponents(f"{output2.name} < -10")

    output2.indexComponentsVector(f"{output2.name} < -10")

    assert all([test_init, test1, test2, test3, test4,
                output2.getDimensions() == output_raster.dimensions])
