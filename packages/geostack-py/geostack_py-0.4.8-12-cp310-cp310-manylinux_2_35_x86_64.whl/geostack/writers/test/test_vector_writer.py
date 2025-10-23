# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

import pytest
from geostack.definitions import GeometryType
from geostack import vector
from geostack.core import ProjectionParameters
from geostack.writers import vectorWriters
from geostack.dataset import supported_libs


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


@pytest.mark.geopandas
@pytest.mark.skipif(not supported_libs.HAS_GPD, reason="geopandas library is not installed")
def test_vector_gpd():
    import geopandas as gpd
    vec = vector.Vector()
    vec.addPoint([0, 0])
    vec.addLineString([[0, 0], [1, 0]])
    vec.setProjectionParameters(ProjectionParameters.from_epsg(4326))
    obj = vectorWriters.to_geopandas(vec)

    assert isinstance(obj, gpd.GeoDataFrame)


@pytest.mark.spatialite
@pytest.mark.skipif(not supported_libs.HAS_SPATIALITE, reason="spatialite library is not installed")
def test_db_writer(tmpdir, datadir):
    filePath = datadir.join("vic_simple.shp")
    vec = vector.Vector.from_shapefile(filePath.strpath)

    out_file = tmpdir.join("vic_simple.db")

    vectorWriters.to_database(vec, out_file.strpath, epsg_code=4326,
                              geom_type=GeometryType.Polygon)
