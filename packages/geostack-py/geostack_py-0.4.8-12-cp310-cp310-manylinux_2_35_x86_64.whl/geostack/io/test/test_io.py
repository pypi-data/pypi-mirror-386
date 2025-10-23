# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import numpy as np
from time import time
from typing import Dict, Union
sys.path.insert(0, os.path.realpath('../../../'))

import pytest
from geostack.core import REAL, ProjectionParameters
from geostack.runner import runScript
from geostack.io import AsciiHandler, GsrHandler
from geostack.io import FltHandler, GeoTIFFHandler
from geostack.io import JsonHandler
from geostack.raster import Raster
from geostack.core import ProjectionParameters

@pytest.mark.io
def test_ascii(tmpdir):
    file_name = tmpdir.join("testRaster.asc")
    testA = Raster(name="testA")
    testA.init(10, 1.0, ny=10, hy=1.0)
    testA.setAllCellValues(2.0)

    asc = AsciiHandler()
    asc.write(file_name.strpath, "", input_raster=testA)
    asc.read(file_name.strpath)

    assert np.allclose(asc.raster.data, testA.data)

@pytest.mark.io
def test_flt(tmpdir):
    file_name = tmpdir.join("testRaster.flt")
    testA = Raster(name="testA")
    testA.init(10, 1.0, ny=10, hy=1.0)
    testA.setAllCellValues(2.0)

    flt = FltHandler()
    flt.write(file_name.strpath, "", input_raster=testA)
    flt.read(file_name.strpath)

    assert np.allclose(flt.raster.data, testA.data)

@pytest.mark.io
def test_gsr(tmpdir):
    file_name = tmpdir.join("testRaster.gsr")
    testA = Raster(name="testA")
    testA.init(10, 1.0, ny=10, hy=1.0)
    testA.setAllCellValues(2.0)

    gsr = GsrHandler()
    gsr.write(file_name.strpath, "", input_raster=testA)
    del gsr
    gsr = GsrHandler()
    gsr.read(file_name.strpath)

    assert np.allclose(gsr.raster.data, testA.data)
    del gsr

@pytest.mark.io
def test_tiff(tmpdir):
    file_name = tmpdir.join("testRaster.tif")
    testA = Raster(name="testA")
    testA.init(10, 1.0, ny=10, hy=1.0)
    testA.setAllCellValues(2.0)
    testA.setProjectionParameters(ProjectionParameters.from_epsg(4283))

    tif = GeoTIFFHandler()
    tif.write(file_name.strpath, "", input_raster=testA)
    del tif
    tif = GeoTIFFHandler()
    tif.read(file_name.strpath)

    assert np.allclose(tif.raster.data, testA.data)
    del tif

@pytest.mark.io
@pytest.mark.parametrize("jsonConfig", ["",
                                        {"legacy": True, "compress": False,
                                         "encoding": "ascii"},
                                        {"legacy": False, "compress": True,
                                         "encoding": "ascii"},
                                        {"legacy": True, "compress": True,
                                         "encoding": "base64"},
                                        {"legacy": False, "compress": False,
                                         "encoding": "base64"},
                                        {"legacy": False, "compress": False,
                                         "encoding": "base64", "noDataValue": -999.0}])
def test_raster_json(tmpdir, jsonConfig: Union[str, Dict]):
    file_name = tmpdir.join("testRaster.json")
    testA = Raster(name="testA")
    testA.init(10, 1.0, ny=10, hy=1.0)
    runScript("testA = randomNormal(0, 1);", [testA])
    testA.setProjectionParameters(ProjectionParameters.from_epsg(4283))

    json_obj = JsonHandler()
    json_obj.write(file_name.strpath, jsonConfig=jsonConfig, input_raster=testA)
    del json_obj

    with pytest.raises((RuntimeError, SystemError)) as excinfo:
        json_obj = JsonHandler()
        json_obj.read(file_name.strpath)
        assert 'not available' in str(excinfo.value)
