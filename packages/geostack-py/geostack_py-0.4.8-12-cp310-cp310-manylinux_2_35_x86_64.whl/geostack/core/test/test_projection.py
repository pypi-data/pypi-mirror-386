# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
from functools import partial

sys.path.insert(0, os.path.realpath('../../../'))
import numpy as np
from geostack.core import convert, ProjectionParameters
from geostack.vector import Coordinate
from geostack.core import Json11, REAL
from geostack.dataset.supported_libs import import_or_skip
import pytest

global HAS_PYPROJ

pyproj, HAS_PYPROJ = import_or_skip("pyproj")

if HAS_PYPROJ:
    from pyproj import Proj
    try:
        from pyproj import Transformer
        def transform(p1, p2, *args):
            transformer = Transformer.from_crs(p1, p2, always_xy=True)
            return transformer.transform(*args)
    except ImportError:
        import pyproj
        def transform(p1, p2, *args):
            proj1 = Proj(init=p1)
            proj2 = Proj(init=p1)
            method = partial(pyproj.transform, proj1, proj2)
            return method(*args)

@pytest.fixture
def EPSG4326():
    return 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'

@pytest.fixture
def EPSG4283():
    return 'GEOGCS["GDA94",DATUM["Geocentric_Datum_of_Australia_1994",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6283"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4283"]]'

@pytest.fixture
def EPSG3111():
    return 'PROJCS["GDA94 / Vicgrid94",GEOGCS["GDA94",DATUM["Geocentric_Datum_of_Australia_1994",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6283"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4283"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",-36],PARAMETER["standard_parallel_2",-38],PARAMETER["latitude_of_origin",-37],PARAMETER["central_meridian",145],PARAMETER["false_easting",2500000],PARAMETER["false_northing",2500000],AUTHORITY["EPSG","3111"],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'

@pytest.fixture
def EPSG3577():
    return 'PROJCS["GDA94 / Australian Albers",GEOGCS["GDA94",DATUM["Geocentric_Datum_of_Australia_1994",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6283"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4283"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",-18],PARAMETER["standard_parallel_2",-36],PARAMETER["latitude_of_center",0],PARAMETER["longitude_of_center",132],PARAMETER["false_easting",0],PARAMETER["false_northing",0],AUTHORITY["EPSG","3577"],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'

@pytest.fixture
def EPSG28355():
    return 'PROJCS["GDA94 / MGA zone 55",GEOGCS["GDA94",DATUM["Geocentric_Datum_of_Australia_1994",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6283"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4283"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",147],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","28355"]]'

@pytest.fixture
def c0():
    return [144.9631, -37.8136]

def test_first(c0, EPSG4326, EPSG3111):
    c1 = Coordinate(p=c0[0], q=c0[1], dtype=REAL)
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG3111)
    out = convert(c1, _to, _from)
    out = convert(c1, _from, _to)
    assert np.hypot(c0[0] - c1.p, c0[1] - c1.q) < 1.0e-4

def test_second(c0, EPSG4326, EPSG28355):
    c2 = Coordinate(p=c0[0], q=c0[1])
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG28355)
    convert(c2, _to, _from)
    convert(c2, _from, _to)
    assert np.hypot(c0[0] - c2.p, c0[1] - c2.q) < 1.0e-4

def test_third(c0, EPSG4326, EPSG3577):
    c3 = Coordinate(p=c0[0], q=c0[1])
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG3577)
    convert(c3, _to, _from)
    convert(c3, _from, _to)
    assert np.hypot(c0[0] - c3.p, c0[1] - c3.q) < 1.0e-4

@pytest.mark.skipif(not HAS_PYPROJ, reason="No pyproj installed")
def test_fourth(c0, EPSG4326, EPSG3111):

    c1 = Coordinate(p=c0[0], q=c0[1], dtype=np.float64)
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG3111)
    convert(c1, _to, _from)

    c1_x, c1_y = transform('epsg:4326', 'epsg:3111', c0[0], c0[1])
    assert np.hypot(c1_x - c1.p, c1_y - c1.q) < 1.6

@pytest.mark.skipif(not HAS_PYPROJ, reason="No pyproj installed")
def test_fifth(c0, EPSG4326, EPSG4283):
    c1 = Coordinate(p=c0[0], q=c0[1], dtype=REAL)
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG4283)
    convert(c1, _to, _from)

    c1_x, c1_y = transform('epsg:4326', 'epsg:4283', c0[0], c0[1])
    assert np.hypot(c1_x - c1.p, c1_y - c1.q) < 1.6

@pytest.mark.skipif(not HAS_PYPROJ, reason="No pyproj installed")
def test_sixth(c0, EPSG4326, EPSG3577):
    c1 = Coordinate(p=c0[0], q=c0[1])
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG3577)
    convert(c1, _to, _from)

    c1_x, c1_y = transform('epsg:4326', 'epsg:3577', c0[0], c0[1])
    assert np.hypot(c1_x - c1.p, c1_y - c1.q) < 1.6

@pytest.mark.skipif(not HAS_PYPROJ, reason="No pyproj installed")
def test_seventh(c0, EPSG4326, EPSG28355):
    c1 = Coordinate(p=c0[0], q=c0[1])
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG28355)
    convert(c1, _to, _from)

    c1_x, c1_y = transform('epsg:4326', 'epsg:28355', c0[0], c0[1])
    assert np.hypot(c1_x - c1.p, c1_y - c1.q) < 2

def test_eighth(c0, EPSG4326, EPSG3111):
    _from = ProjectionParameters.from_wkt(EPSG4326)
    _to = ProjectionParameters.from_wkt(EPSG3111)
    points = [[144.0, -37.5], [144.1, -37.6], [144.2, -37.7], [144.3, -37.8]]
    out = convert(points, _to, _from)
    out = convert(out, _from, _to)
    count = 0
    for i in range(len(points)):
        count += (np.hypot(points[i][0] - out[i][0], points[i][1] - out[i][1]) < 1.0e-4)
    assert count == len(points)

def test_with_proj_str(c0):
    _from, _to ='4326', '3111'
    points = [[144.0, -37.5], [144.1, -37.6], [144.2, -37.7], [144.3, -37.8]]
    out = convert(points, _to, _from)
    out = convert(out, _from, _to)
    count = 0
    for i in range(len(points)):
        count += (np.hypot(points[i][0] - out[i][0], points[i][1] - out[i][1]) < 1.0e-4)
    assert count == len(points)