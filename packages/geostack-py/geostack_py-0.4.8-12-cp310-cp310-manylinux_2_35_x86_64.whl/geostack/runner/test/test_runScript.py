# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
import pytest
from geostack.core import REAL, ProjectionParameters
from geostack.raster import Raster, equalSpatialMetrics, RasterBaseList
from geostack.vector import Vector
from geostack.runner import runScript, runVectorScript
from geostack.gs_enums import (RasterCombinationType, RasterNullValueType,
                               RasterResolutionType, ReductionType)

@pytest.mark.runScript
def test_raster1D_script():

    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, 2)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=REAL)
    testRasterB.init(15, 1.0, ox=-5.0)
    testRasterB.setAllCellValues(2.0)

    raster_list = RasterBaseList(dtype=REAL)
    raster_list.add_raster(testRasterA)
    raster_list.add_raster(testRasterB)

    script = "output = 100.0 + testRasterA * testRasterB;"
    testRasterC = runScript(script, raster_list, output_type=REAL,
                            parameter=RasterCombinationType.Union)

    assert testRasterC.hasData()
    assert round(testRasterC.max(), 1) == 299.8
    assert testRasterC.min() == 102.0
    assert round(testRasterC.getCellValue(7), 1) == 299.8
    assert round(testRasterC.getNearestValue(2.5), 1) == 299.8
    assert round(testRasterC.getBilinearValue(2.5), 1) == 299.8

@pytest.mark.runScript
def test_raster1d_raster2d_script():
    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(5, 1.0)
    testRasterA.setAllCellValues(1.0)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=REAL)
    testRasterB.init(15, 1.0, ny=15, hy=1.0, ox=-5.0, oy=-5.0)
    testRasterB.setAllCellValues(2.0)
    script = "output = testRasterA + testRasterB;"
    testRasterC = runScript(script, [testRasterA, testRasterB],
                            output_type=REAL,
                            parameter=RasterCombinationType.Union)

    assert testRasterC.hasData()
    assert testRasterC.max() == 3.0
    assert testRasterC.getCellValue(5, 5) == 3.0
    assert testRasterC.getNearestValue(0.0, 0.0) == 3.0

@pytest.mark.runScript
def test_raster2d_float_script():

    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=REAL)
    testRasterB.init(nx=15, ny=15, hx=1.0, hy=1.0, ox=-5.0, oy=-5.0)
    testRasterB.setAllCellValues(2.0)
    #
    script = "output = 100.0 + testRasterA * testRasterB;"
    testRasterC = runScript(script, [testRasterA, testRasterB],
                            output_type=REAL,
                            parameter=RasterCombinationType.Union)
    assert testRasterC.hasData()
    assert round(testRasterC.max(), 1) == 299.8
    assert round(testRasterC.min(), 1) == 102.0
    assert round(testRasterC.getCellValue(7, 7), 1) == 299.8
    assert round(testRasterC.getNearestValue(2.5, 2.5), 1) == 299.8
    assert round(testRasterC.getBilinearValue(2.5, 2.5), 1) == 299.8

@pytest.mark.runScript
def test_raster_resize2D():
    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterA.resize2D(3, 3, 1, 1)

    assert testRasterA.hasData()
    assert round(testRasterA.getNearestValue(2, 2), 1) == 99.9
    assert round(testRasterA.max(), 1) == 99.9
    assert round(testRasterA.min(), 1) == 1.0

@pytest.mark.runScript
def test_raster2d_int_script():
    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=np.uint32)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(1)
    testRasterA.setCellValue(99, i=2, j=2)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=np.uint32)
    testRasterB.init(nx=15, ny=15, hx=1.0, hy=1.0, ox=-5.0, oy=-5.0)
    testRasterB.setAllCellValues(2)
    #
    script = "output = 100.0 + testRasterA * testRasterB;"
    testRasterC = runScript(script, [testRasterA, testRasterB],
                            output_type=np.uint32,
                            parameter=RasterNullValueType.Zero)

    assert testRasterC.hasData()
    assert testRasterC.max() == 298
    assert testRasterC.min() == 100
    assert testRasterC.getCellValue(7, 7) == 298
    assert testRasterC.getNearestValue(2.5, 2.5) == 298

@pytest.mark.runScript
def test_raster_int_float_script():

    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(nx=50, ny=50, hx=0.1, hy=0.1)
    testRasterA.setAllCellValues(0.0)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=np.uint32)
    testRasterB.init(nx=50, ny=50, hx=0.1, hy=0.1)
    testRasterB.setAllCellValues(0)
    #
    script = "output = x*y;"
    testRasterA = runScript(script, [testRasterA],
                            output_type=REAL,
                            parameter=RasterCombinationType.Union)
    testRasterA.setProperty("name", "testRasterA")

    script = "output = testRasterA;"
    testRasterC = runScript(script, [testRasterB, testRasterA],
                            output_type=np.uint32,
                            parameter=RasterCombinationType.Union)
    testRasterC.setProperty("name", "testRasterC")

    assert testRasterA.hasData()
    assert round(testRasterA.getCellValue(26, 14), 4) == (2.65 * 1.45)
    assert testRasterC.hasData()
    assert testRasterC.getCellValue(26, 14) == 3

@pytest.mark.runScript
def test_sampling_2d():
    testRasterA = Raster(name="testRasterA",
                         base_type=REAL,
                         data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterB = Raster(name="testRasterB",
                         base_type=REAL,
                         data_type=REAL)
    testRasterB.init(nx=20, ny=20, hx=0.25, hy=0.25)

    script = "output = testRasterA;"
    testRasterB = runScript(script, [testRasterA, testRasterB],
                            output_type=REAL,
                            parameter=RasterResolutionType.Minimum)

    assert testRasterA.hasData()
    assert testRasterA.getNearestValue(
        2.5, 2.5) == testRasterB.getNearestValue(2.5, 2.5)

    testRasterB = Raster(name="testRasterB",
                         base_type=REAL,
                         data_type=REAL)
    testRasterB.init(nx=20, ny=20, hx=0.25, hy=0.25)

    script = "output = testRasterA;"
    testRasterB = runScript(script, [testRasterA.get_raster_base(),
                                     testRasterB.get_raster_base()],
                            output_type=REAL,
                            parameter=RasterResolutionType.Minimum)

    assert testRasterA.hasData()
    assert testRasterA.getNearestValue(
        2.5, 2.5) == testRasterB.getNearestValue(2.5, 2.5)

@pytest.mark.runScript
def test_intersection():
    testRasterA = Raster(name="testRasterA", base_type=REAL,
                         data_type=REAL)
    testRasterA.init(nx=5, ny=5, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(1.0)
    testRasterA.setCellValue(99.9, i=2, j=2)

    testRasterB = Raster(name="testRasterB", base_type=REAL,
                         data_type=REAL)
    testRasterB.init(nx=20, ny=20, hx=0.25, hy=0.25, ox=-4.0, oy=-4.0)
    testRasterB.setAllCellValues(-1.0)

    # script = "output = testRasterA + testRasterB;"
    # testRasterC = runScript(script, [testRasterA, testRasterB],
    #                         parameter=RasterResolutionType.Minimum,
    #                         output_type=REAL)

    # assert testRasterC.hasData() == True
    # assert testRasterC.getCellValue(17, 17) == 0.0

@pytest.mark.runVectorScript
def test_vector_script():
    r = Raster(name="r")
    r.init(10, 1.0, ny=10, hy=1.0, ox=-5.0, oy=-5.0)
    r.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    runScript("r = hypot((REAL)x, (REAL)y);", [r])

    assert round(r.getCellValue(9, 1), 5) == 5.70088

    v = r.cellCentres()
    v.setProperty(0, "vx", 0.0)
    v.setProperty(0, "vy", 0.0)

    # test with raster
    v = runVectorScript("REALVEC2 g = grad(r); vx = g.x; vy = g.y;", v, inputRasters=[r],
                        reductionType=ReductionType.Mean)
    out = v.getProperty(11, "vx", propType=REAL), v.getProperty(
        11, "vy", propType=REAL)
    assert (round(out[0], 5), round(out[1], 5)) == (round(-0.703481912612915, 5), round(-0.703481912612915, 5))

    # test with raster base
    v = runVectorScript("REALVEC2 g = grad(r); vx = g.x; vy = g.y;", v,
                        inputRasters=[r.get_raster_base()],
                        reductionType=ReductionType.Mean)
    out = v.getProperty(11, "vx", propType=REAL), v.getProperty(
        11, "vy", propType=REAL)
    assert (round(out[0], 5), round(out[1], 5)) == (round(-0.703481912612915, 5), round(-0.703481912612915, 5))


@pytest.mark.runScript
@pytest.mark.parametrize("op, expected", [("min", 1), ("max", 5), ("mean", 3), ("sum", 15)])
def test_raster3d(op, expected):

    base_raster = Raster(name="base")
    base_raster.init(256, 1.0, ny=256, hy=1.0)
    base_raster.setProjectionParameters(ProjectionParameters.from_epsg(4326))

    test = Raster(name="test")
    test.init(256, 1.0, ny=256, nz=5, hy=1.0, hz=1.0)
    test.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    test.setAllCellValues(0.0)
    script = """
    for (uint k=0; k<test_layers; k++){
        test[k] = k+1;
    }
    """
    runScript(script, [base_raster, test])

    if op in ["min", "max"]:
        script = """
        output = 1.0;
        for (uint k=0; k<test_layers; k++){
            output = %s(output, test[k]);
        }
        """ % (op)
    elif op == "sum":
        script = """
        output = 0.0;
        for (uint k=0; k<test_layers; k++){
            output += test[k];
        }
        """
    elif op == "mean":
        script = """
        output = 0.0;
        for (uint k=0; k<test_layers; k++){
            output += test[k]/test_layers;
        }
        """
    output = runScript(script, [base_raster, test])
    assert expected == output.getCellValue(0, 0), "test on 3d raster failed"


@pytest.mark.runScript
def test_raster_random_state():
    test = Raster(name="test")
    test.init(256, 1.0, ny=256, hy=1.0)
    test.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    test.setAllCellValues(0.0)

    # ensure values are different
    for i in range(10):
        runScript("test = random;", [test])
        if i == 0:
            old_value = test[0, 0]
        else:
            assert test[0, 0] != old_value
            old_value = test[0, 0]

    # ensure values are same
    test.saveRandomState()
    for i in range(10):
        runScript("test = random;", [test])
        if i == 0:
            old_value = test[0, 0]
        else:
            assert test[0, 0] == old_value
            old_value = test[0, 0]
        test.restoreRandomState()


@pytest.mark.runScript
def test_raster_layer_indexing():
    prec = Raster(name='prec')
    prec.init(nx=72, ny=72, nz=240, hx=0.04, hy=0.04,
              hz=1.0, ox=110.0, oy=1.5, oz=1)
    prec.setAllCellValues(2.0)

    scriptA = """
        uint season_idx[] = {10,11,12,13,14};
        uint season_count = 19;
        prec_NDJFM = 0.0;

        for (uint i = 0; i < season_count; i++) {
            REAL value = 0.0;
            for (uint j = 0; j < 5; j++) {
                uint idx = season_idx[j];
                value += prec[idx + i * 12];
            }
            prec_NDJFM += value / season_count;
        }
    """

    rasterdim = prec.getRasterDimensions()

    prec_NDJFM = Raster('prec_NDJFM')
    prec_NDJFM.init(nx=rasterdim.nx, ny=rasterdim.ny, hx=rasterdim.hx,
                    hy=rasterdim.hy, ox=rasterdim.ox, oy=rasterdim.oy)

    runScript(scriptA, [prec_NDJFM, prec])

    # exception catch
    scriptB = """
        uint season_idx[] = {10,11,12,13,14};
        uint season_count = 19;
        prec_NDJFM = 0.0;

        for (uint i = 0; i < season_count; i++) {
            REAL value = 0.0;
            for (uint j = 0; j < 5; j++) {
                value += prec[season_idx[j] + i * 12];
            }
            prec_NDJFM += value / season_count;
        }
    )"""

    with pytest.raises(RuntimeError):
        runScript(scriptB, [prec_NDJFM, prec])
