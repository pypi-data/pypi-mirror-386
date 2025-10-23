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

from geostack.core import Variables, REAL
from geostack.vector import vector
from geostack.raster import raster
from geostack.runner import runScript
from geostack.solvers import NetworkFlowSolver
from geostack.io import vectorToGeoJson, geoJsonToVector


@pytest.mark.networkflow
def test_network_flow():
    inp_json = '''{"features":[
                  {"geometry":{"coordinates":[[100,140],[100,0]],"type":"LineString"},"properties":{"constant":100,"diameter":0.3,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[100,0],[100,-165.818]],"type":"LineString"},"properties":{"constant":100,"diameter":0.3,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[100,0],[-10,0]],"type":"LineString"},"properties":{"constant":100,"diameter":0.2,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[100,-165.818],[-10,-120]],"type":"LineString"},"properties":{"constant":100,"diameter":0.18,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[-10,0],[-10,-120]],"type":"LineString"},"properties":{"constant":100,"diameter":0.18,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[-10,0],[-120,0]],"type":"LineString"},"properties":{"constant":100,"diameter":0.2,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[-10,-120],[-120,-120]],"type":"LineString"},"properties":{"constant":100,"diameter":0.18,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[100,140],[-60,140]],"type":"LineString"},"properties":{"constant":100,"diameter":0.2,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[-60,140],[-120,0]],"type":"LineString"},"properties":{"constant":100,"diameter":0.18,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[[-120,0],[-120,-120]],"type":"LineString"},"properties":{"constant":100,"diameter":0.18,"type":1},"type":"Feature"},
                  {"geometry":{"coordinates":[100,140],"type":"Point"},"properties":{"flow":0.126},"type":"Feature"},
                  {"geometry":{"coordinates":[100,0],"type":"Point"},"properties":{"flow":-0.025},"type":"Feature"},
                  {"geometry":{"coordinates":[100,-165.818],"type":"Point"},"properties":{"flow":-0.05},"type":"Feature"},
                  {"geometry":{"coordinates":[-10,0],"type":"Point"},"properties":{"flow":0},"type":"Feature"},
                  {"geometry":{"coordinates":[-10,-120],"type":"Point"},"properties":{"flow":0},"type":"Feature"},
                  {"geometry":{"coordinates":[-60,140],"type":"Point"},"properties":{"flow":0},"type":"Feature"},
                  {"geometry":{"coordinates":[-120,0],"type":"Point"},"properties":{"flow":-0.025},"type":"Feature"}],"type":"FeatureCollection"}'''

    vec = geoJsonToVector(inp_json)

    solver = NetworkFlowSolver()
    init_success = solver.init(vec, {})
    assert init_success

    run_success = solver.run()
    assert run_success

    vec_network = solver.getNetwork()
    line_idx = vec_network.getLineStringIndexes()
    props = vec.getProperties()

    flow = props.getProperty("flow", prop_type=REAL)
