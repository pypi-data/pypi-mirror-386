# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import numpy as np
import pytest
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.io import vectorToGeoWKT, parseStrings, parseString, geoWKTToVector
from geostack.vector import Vector, Coordinate


@pytest.fixture
def input_geowkt():
    return "GEOMETRYCOLLECTION (POINT (0.000000 0.500000), LINESTRING (0.000000 0.000000, 1.000000 1.000000, 2.000000 0.000000, 3.000000 1.000000), POLYGON ((0.000000 0.000000, 1.000000 0.000000, 1.000000 1.000000, 0.000000 1.000000, 0.000000 0.000000), (0.250000 0.250000, 0.250000 0.750000, 0.750000 0.750000, 0.750000 0.250000, 0.250000 0.250000)))"


@pytest.fixture
def test_vector(input_geowkt):
    v = geoWKTToVector(input_geowkt, dtype=np.float64)
    return v


def test_converters(test_vector, input_geowkt):
    output = vectorToGeoWKT(test_vector)
    assert output == input_geowkt


def test_point():
    vec = Vector(dtype=np.float64)
    vec.addPoint([0.0, 0.0])
    assert vectorToGeoWKT(vec) == "POINT (0.000000 0.000000)"


def test_linestring():
    vec = Vector(dtype=np.float64)
    vec.addLineString([[0.0, 0.0], [1.0, 1.0]])
    assert vectorToGeoWKT(
        vec) == "LINESTRING (0.000000 0.000000, 1.000000 1.000000)"


def test_polygon():
    vec = Vector(dtype=np.float64)
    vec.addPolygon([[[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]])
    assert vectorToGeoWKT(
        vec) == "POLYGON ((0.000000 0.000000, 1.000000 1.000000, 2.000000 2.000000, 0.000000 0.000000))"


def test_parse_string():
    vec = Vector(dtype=np.float64)

    ids = parseString(vec, "POINT (0.0 0.5)")
    assert ids.size == 1
    assert ids[0] == 0
    assert vec.getPointCoordinate(ids[0]) == Coordinate(
        0.0, 0.5, dtype=np.float64)

    ids = parseString(vec, "POINT (1.0 1.5)")
    assert ids.size == 1
    assert ids[0] == 1
    assert vec.getPointCoordinate(ids[0]) == Coordinate(
        1.0, 1.5, dtype=np.float64)

    ids = parseStrings(vec, ["POINT (2.0 2.5)", "POINT (3.0 3.5)"])
    assert ids.size == 2
    assert (ids[0] == 2) & (ids[1] == 3)
    assert vec.getPointCoordinate(ids[0]) == Coordinate(
        2.0, 2.5, dtype=np.float64)
    assert vec.getPointCoordinate(ids[1]) == Coordinate(
        3.0, 3.5, dtype=np.float64)
