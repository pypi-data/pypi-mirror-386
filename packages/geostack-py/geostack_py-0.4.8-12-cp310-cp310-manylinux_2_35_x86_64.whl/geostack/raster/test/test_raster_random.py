# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys

sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
from geostack import raster
from geostack import runner
from geostack import gs_enums


def test_random():
    testA = raster.Raster(name="testA")
    testA.init(100, 1.0, ny=100, hy=1.0)
    testA.setReductionType(gs_enums.ReductionType.Mean)
    runner.runScript("testA = random;", [testA])

    assert abs(testA.reduceVal - 0.5) < 0.1


def test_random_normal():
    testB = raster.Raster(name="testB")
    testB.init(100, 1.0, ny=100, hy=1.0)
    testB.setReductionType(gs_enums.ReductionType.Mean)

    runner.runScript("testB = randomNormal(5.0, 1.0);", [testB])
    assert abs(testB.reduceVal - 5.0) < 0.1
