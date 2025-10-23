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
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.vector import VectorPtrList
from geostack.gs_enums import GeometryType
from geostack.vector import vector
from geostack.core import ProjectionParameters
import pickle


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


@pytest.fixture
def vector_object():
    c = vector.Coordinate.from_list([144.9631, -37.8136])
    vec = vector.Vector()
    pointIdx = vec.addPoint(c)
    vec.setProperty(pointIdx, "newproperty", "newstr")
    return vec

def test_vector_initialization():
    c = vector.Coordinate.from_list([144.9631, -37.8136])
    vec = vector.Vector()
    pointIdx = vec.addPoint(c)
    vec.setProperty(pointIdx, "newproperty", "newstr")
    assert vec.getPointCoordinate(pointIdx) == c
    assert vec.getProperty(pointIdx, "newproperty", str) == "newstr"

@pytest.mark.parametrize("proj", [4326, "4326"])
def test_native_vector_writer(datadir, vector_object, proj):
    outfile = datadir.join("test_vector_write.geojson")
    if isinstance(proj, str):
        vector_object.setProjectionParameters(proj)
    else:
        vector_object.setProjectionParameters(ProjectionParameters.from_epsg(proj))
    vector_object.write(outfile.strpath, GeometryType.All)

@pytest.mark.parametrize("proj", [4326, "4326"])
def test_native_vector_reader(datadir, vector_object, proj):
    outfile = datadir.join("test_vector_write.geojson")
    if isinstance(proj, str):
        vector_object.setProjectionParameters(proj)
    else:
        vector_object.setProjectionParameters(ProjectionParameters.from_epsg(proj))
    vector_object.write(outfile.strpath, GeometryType.All)
    inpfile = vector.Vector()
    inpfile.read(datadir.join("test_vector_write.geojson").strpath)
    assert inpfile.getGeometryIndexes().size == vector_object.getGeometryIndexes().size

def test_vector_copy(vector_object):
    v2 = vector.Vector(vector_object)
    assert v2.getGeometryIndexes().size == vector_object.getGeometryIndexes().size


def test_vector_assign(vector_object):
    v2 = vector.Vector.assign(vector_object)
    assert v2.getGeometryIndexes().size == vector_object.getGeometryIndexes().size


def test_pickling(datadir):
    v2 = geoJsonToVector(datadir.join('test_data_2.geojson').strpath,
                         enforceProjection=False)

    with open(datadir.join('test_vec.pkl').strpath, 'wb') as out:
        pickle.dump(v2, out)

    with open(datadir.join('test_vec.pkl').strpath, 'rb') as inp:
        v3 = pickle.load(inp)

    assert v2.bounds == v3.bounds
    assert v2.getPointCount() == v3.getPointCount()
    assert v2.getLineStringCount() == v3.getLineStringCount()
    assert v2.getPolygonCount() == v3.getPolygonCount()

def test_vector_list(datadir):
    c = vector.Coordinate.from_list([144.9631, -37.8136])
    vec1 = vector.Vector()
    pointIdx = vec1.addPoint(c)
    vec1.setProperty(pointIdx, "newproperty", "newstr")

    c = vector.Coordinate.from_list([145.9631, -36.8136])
    vec2 = vector.Vector()
    pointIdx = vec2.addPoint(c)
    vec2.setProperty(pointIdx, "newproperty", "newstr")

    v_list = VectorPtrList()
    v_list.add_vector(vec1)
    v_list.add_vector(vec2)

    assert v_list.size == 2

    vec1 = v_list.get_vector(0)
    assert vec1.getPointCount() == 1

    vec2 = v_list.get_vector(1)
    assert vec2.getPointCount() == 1

    v_list2 = VectorPtrList([vec1, vec2])
    assert v_list2.size == 2

    vec1 = v_list2.get_vector(0)
    assert vec1.getPointCount() == 1

    vec2 = v_list2.get_vector(1)
    assert vec2.getPointCount() == 1
