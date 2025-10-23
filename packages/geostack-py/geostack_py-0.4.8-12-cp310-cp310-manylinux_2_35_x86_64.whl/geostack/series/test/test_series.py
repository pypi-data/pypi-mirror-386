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
import pickle
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.series import Series
from geostack.gs_enums import SeriesInterpolationType, SeriesCappingType

@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.

    ref: https://stackoverflow.com/questions/29627341/pytest-where-to-store-expected-data
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir


@pytest.mark.series
@pytest.mark.parametrize("column,name,expected",
                         [(1, "wind_direction", 180),
                          (2, "wind_speed", 30.0),
                          (3, "temp", 27.5),
                          (4, "rel_hum", 12.5)],)
def test_series(datadir, column, name, expected):
    filePath = datadir.join("test_series.csv")
    inp_series = Series.read_csv_file(filePath.strpath,
                                      parse_date=True,
                                      usecols=[0, column],
                                      dt_format="%Y-%m-%dT%H:%M:%SZ",
                                      skip_header=1)

    test1 = inp_series.getName() == name

    if column == 1:
        inp_series.setInterpolation(SeriesInterpolationType.BoundedLinear)
    else:
        inp_series.setInterpolation(SeriesInterpolationType.Linear)

    x_idx = inp_series.get_xMin()
    if column != 1:
        x_idx += 21600
    test2 = inp_series.inRange(x_idx)

    test3 = False
    if test2:
        test3 = inp_series(x_idx) == expected

    assert test1 & test2


@pytest.mark.series
def test_series_limits(datadir):
    filePath =  datadir.join("test_series_limits.csv")
    inp_series = Series.read_csv_file(filePath.strpath,
                                      parse_date=False,
                                      usecols=[0, 2],
                                      skip_header=1)
    assert inp_series.getName() == 'wind_speed'

    inp_series.setCapping(SeriesCappingType.Uncapped)
    assert np.isnan(inp_series.get(0))

    inp_series.setCapping(SeriesCappingType.Capped)
    assert np.allclose(inp_series.get(20), inp_series.get(0))


@pytest.mark.series
def test_series_name(datadir):
    filePath = datadir.join("test_series.csv")
    inp_series = Series.read_csv_file(filePath.strpath,
                                      parse_date=True,
                                      usecols=[0, 1],
                                      dt_format="%Y-%m-%dT%H:%M:%SZ",
                                      skip_header=1)
    inp_series.setName("wind direction")

@pytest.mark.series
def test_series_pickling(datadir):
    filePath = datadir.join("test_series.csv")
    inp_series = Series.read_csv_file(filePath.strpath,
                                      parse_date=True,
                                      usecols=[0, 1],
                                      dt_format="%Y-%m-%dT%H:%M:%SZ",
                                      skip_header=1)
    inp_series.setName("wind direction")

    obj = pickle.loads(pickle.dumps(inp_series))
    assert obj.getName() == inp_series.getName()
