# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import numpy as np
from time import time
import pytest
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.utils import zonal_stats
from geostack.runner import runVectorScript
from geostack.gs_enums import ReductionType
from geostack.vector import Vector
from geostack.raster import Raster
from geostack.core import ProjectionParameters, REAL


@pytest.fixture
def proj_4326():
    epsg_4326 = ProjectionParameters.from_proj4(
        "+proj=longlat +datum=WGS84 +no_defs")
    return epsg_4326


@pytest.fixture
def test_vector(proj_4326):
    vec = Vector()
    vec.addPolygon([np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])])
    vec.setProjectionParameters(proj_4326)
    vec.addProperty("raster_values")
    return vec


@pytest.fixture
def float_raster(proj_4326):
    random_data = np.random.randint(
        0, high=50, size=100).reshape((10, 10)).astype(REAL)

    testA = Raster(name='testA', data_type=REAL)
    testA.init(10, 0.1, ny=10, hy=0.1)
    testA.setProjectionParameters(proj_4326)
    testA.data = random_data
    return testA


@pytest.fixture
def int_raster(proj_4326):
    random_data = np.random.randint(
        0, high=50, size=100).reshape((10, 10)).astype(np.uint32)

    testA = Raster(name='testA', data_type=np.uint32)
    testA.init(10, 0.1, ny=10, hy=0.1)
    testA.setProjectionParameters(proj_4326)
    testA.data = random_data
    return testA

@pytest.mark.parametrize("stat_list",
                         [("mean min max median std var"),
                          (["mean", "min", "max", "median", "std", "var"]),
                          (None)],)
def test_float_stats(test_vector, float_raster, stat_list):
    vec = runVectorScript("raster_values = testA;", test_vector, [float_raster],
                          reductionType=ReductionType.NoReduction)
    stats = zonal_stats(vec, float_raster, stats=stat_list)
    if isinstance(stat_list, str):
        _stats = [item.strip() for item in stat_list.split()]
        assert sorted([item.split("_")[1]
                      for item in stats.keys()]) == sorted(_stats)
    elif isinstance(stat_list, list):
        assert sorted([item.split("_")[1]
                      for item in stats.keys()]) == sorted(stat_list)
    elif stat_list is None:
        assert sorted([item.split("_")[1] for item in stats.keys()]) == sorted(['min', 'max',
                                                                                'mean', 'count'])


@pytest.mark.parametrize("stat_list",
                         [("mean min max median std var majority minority variety"),
                          (["mean", "min", "max", "majority", "minority", "variety"]),
                          (None)],)
def test_int_stats(test_vector, int_raster, stat_list):
    vec = runVectorScript("raster_values = testA;", test_vector, [int_raster],
                          reductionType=ReductionType.NoReduction)
    stats = zonal_stats(vec, int_raster, stats=stat_list)
    if isinstance(stat_list, str):
        _stats = [item.strip() for item in stat_list.split()]
        assert sorted([item.split("_")[1]
                      for item in stats.keys()]) == sorted(_stats)
    elif isinstance(stat_list, list):
        assert sorted([item.split("_")[1]
                      for item in stats.keys()]) == sorted(stat_list)
    elif stat_list is None:
        assert sorted([item.split("_")[1] for item in stats.keys()]) == sorted(['min', 'max',
                                                                                'mean', 'count'])
