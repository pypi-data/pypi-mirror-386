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

from geostack import raster
from geostack import gs_enums
from geostack.dataset import supported_libs
from geostack.io import geoJsonToVector, vectorToGeoJson
from geostack.gs_enums import GeometryType
from geostack.core import ProjectionParameters, REAL
from geostack.vector import Coordinate, Vector, BoundingBox
from geostack.raster import Raster


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
def fileVector(datadir):
    start = time()
    file_path = datadir.join("test_data_2.geojson")
    file_vector = geoJsonToVector(file_path.strpath, dtype=REAL)
    end = time()
    print("Time taken to process file %f" % (end - start))
    return file_vector


@pytest.fixture
def proj_EPSG3111_REAL():
    proj_EPSG3111 = "(+proj=lcc +lat_1=-36 +lat_2=-38 +lat_0=-37 +lon_0=145 +x_0=2500000 +y_0=2500000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs)"
    _proj_EPSG3111_REAL = ProjectionParameters.from_proj4(proj_EPSG3111)

    return _proj_EPSG3111_REAL


@pytest.fixture
def proj_EPSG4326_REAL():
    projPROJ4_EPSG4326 = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
    _proj_EPSG4326_REAL = ProjectionParameters.from_proj4(projPROJ4_EPSG4326)
    return _proj_EPSG4326_REAL


@pytest.fixture
def proj_EPSG3577_REAL():
    projPROJ4_EPSG3577 = "(+proj=aea +lat_1=-18 +lat_2=-36 +lat_0=0 +lon_0=132 +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs)"
    _proj_EPSG3577_REAL = ProjectionParameters.from_proj4(projPROJ4_EPSG3577)
    return _proj_EPSG3577_REAL


def test_vec_attached(datadir, fileVector):
    testX = 144.3288723
    testY = -37.0938227

    expectedGeomIds = np.array([764, 2472, 2473, 2883, 2502, 1582])
    attachedGeomIds = fileVector.attached(Coordinate(testX, testY))

    assert np.array_equal(expectedGeomIds, attachedGeomIds)

def test_vec_nearest(datadir, fileVector):

    nearestGeoJson = """{"features": [{"geometry": {"coordinates": [144.07501, -37.28393], "type": "Point"}, "properties": {"radius": 0.05}, "type": "Feature"}], "type": "FeatureCollection"}"""
    nearestPointVector = geoJsonToVector(nearestGeoJson)
    nearestVector = fileVector.nearest(nearestPointVector.getBounds())

    with open(datadir.join("out_test_data_nearest.geojson").strpath, "w") as out:
        out.write(vectorToGeoJson(nearestVector))

    with open(datadir.join("out_test_data_nearest_point.geojson").strpath, "w") as out:
        out.write(vectorToGeoJson(nearestPointVector))

    start = time()
    fileVector.deduplicateVertices()
    end = time()
    print("Time taken to deduplicate %f" % (end - start))

def test_vec_nearestGeom_coord(datadir, fileVector):
    expectedGeomID = 2232
    queryCoord = Coordinate(144.446358, -37.286379)

    nearestGeomID = fileVector.nearestGeom(queryCoord)
    assert nearestGeomID == expectedGeomID

def test_vec_nearestGeom_coordProj(proj_EPSG4326_REAL, proj_EPSG3577_REAL):
    v = Vector()
    v.setProjectionParameters(proj_EPSG4326_REAL)
    v.addPoint([150, -40])
    v.addPoint([140, -30])
    expGeomID = v.addPoint([144.9631, -37.8136])
    v.addPoint([140, -40])
    v.addPoint([150, -30])

    queryCoord = Coordinate(1146469.071166, -4192119.31810244)
    nearestGeomID = v.nearestGeom(queryCoord, proj=proj_EPSG3577_REAL)
    assert nearestGeomID == expGeomID

def test_vec_nearestNGeoms_coord(datadir, fileVector):
    expectedGeomIDs = {
        # Points
        515, 1104, 1105, 1106, 1389,
        # Linestrings
        1620, 1847, 1849, 1853, 2049, 2050, 2710, 2717, 2794
    }
    queryCoord = Coordinate(143.954401, -37.372831)

    nearestGeomIDs = set(fileVector.nearestNGeoms(queryCoord, len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_vec_nearestGeom_vector(datadir, fileVector):
    expectedGeomID = 2232
    v = Vector()
    v.setProjectionParameters(fileVector.getProjectionParameters())
    v.addPoint([147.446358, -37.286379])
    v.addLineString(
        [
            [144.446358, -37.286379],
            [145.446358, -37.286379],
            [146.446358, -37.286379],
        ]
    )

    # Test the default search behaviour: SearchStrategy.AllVertices
    v_out = fileVector.nearestGeom(v)
    assert len(v_out.getGeometryIndexes()) == 1
    nearestGeomID = v_out.getGeometryIndexes()[0]
    assert nearestGeomID == expectedGeomID

    # Test the SearchStrategy.ByVertex
    v.addPoint([1, -1])
    expectedGeomIDs = { 1673, 1733 }
    v_out = fileVector.nearestGeom(v, search_strategy = gs_enums.SearchStrategy.ByVertex)
    assert set(v_out.getGeometryIndexes()) == expectedGeomIDs

def test_vec_nearestGeom_vectorProj(proj_EPSG4326_REAL, proj_EPSG3577_REAL):
    v = Vector()
    v.setProjectionParameters(proj_EPSG4326_REAL)
    v.addPoint([150, -40])
    v.addPoint([140, -30])
    expGeomID = v.addPoint([144.9631, -37.8136])
    v.addPoint([140, -40])
    v.addPoint([150, -30])

    queryVector = Vector()
    queryVector.setProjectionParameters(proj_EPSG3577_REAL)
    queryVector.addPoint([1146469.071166, -4192119.31810244])

    # Test the default search behaviour: SearchStrategy.AllVertices
    v_out = v.nearestGeom(queryVector)
    assert len(v_out.getGeometryIndexes()) == 1
    nearestGeomID = v_out.getGeometryIndexes()[0]
    assert nearestGeomID == expGeomID

    # Test the SearchStrategy.ByVertex
    queryVector.addPoint([1, -1])
    expectedGeomIDs = { 1, 2 }
    v_out = v.nearestGeom(queryVector, search_strategy = gs_enums.SearchStrategy.ByVertex)
    assert set(v_out.getGeometryIndexes()) == expectedGeomIDs

def test_vec_nearestNGeoms_vector(datadir, fileVector):
    expectedGeomIDs = {
        1731, 1733, 2958, 2959
    }
    v = Vector()
    v.setProjectionParameters(fileVector.getProjectionParameters())
    v.addPoint([144.4540630, -37.2447518])
    v.addLineString(
        [
            [144.44921, -37.23271],
            [144.45292, -37.23621]
        ]
    )

    nearestGeomIDs = set(fileVector.nearestNGeoms(v, len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_vec_nearestGeom_bbox(datadir, fileVector):
    expectedGeomID = 2958
    bbox = BoundingBox.from_list(
        [[143.453996, -38.237063],
         [145.453996, -36.237063]]
    )

    nearestGeomID = fileVector.nearestGeom(bbox)
    assert nearestGeomID == expectedGeomID

def test_vec_nearestNGeoms_bbox(datadir, fileVector):
    expectedGeomIDs = {1731, 2958}
    bbox = BoundingBox.from_list(
        [[143.453996, -38.237063],
         [145.453996, -36.237063]]
    )

    nearestGeomIDs = set(fileVector.nearestNGeoms(bbox, len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_vec_nearestGeom_raster(datadir, fileVector):
    expectedGeomID = 2958
    r = Raster()
    r.setProjectionParameters(fileVector.getProjectionParameters())
    r.init_with_bbox(
        BoundingBox.from_list([[144.453989, -37.237056],
                               [144.553989, -37.137056]]),
        0.01
    )

    nearestGeomID = fileVector.nearestGeom(r)
    assert nearestGeomID == expectedGeomID

def test_vec_nearestNGeoms_raster(datadir, fileVector):
    expectedGeomIDs = {1731, 2958}
    r = Raster()
    r.setProjectionParameters(fileVector.getProjectionParameters())
    r.init_with_bbox(
        BoundingBox.from_list([[144.453989, -37.237056],
                               [144.553989, -37.137056]]),
        0.01
    )

    nearestGeomIDs = set(fileVector.nearestNGeoms(r, len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_vec_region(datadir, fileVector):

    boundsGeoJson = """{"features": [{"geometry": {"coordinates": [[[143.73701, -37.46474], [143.73701, -37.13560], [144.41891, -37.13560], [144.41891, -37.46474], [143.73701, -37.46474]]], "type": "Polygon"}, "properties": {}, "type": "Feature"}], "type": "FeatureCollection"}"""
    boundsVector = geoJsonToVector(boundsGeoJson)

    regionVector = fileVector.region(boundsVector.getBounds())
    with open(datadir.join("out_test_data_region.geojson").strpath, "w") as out:
        out.write(vectorToGeoJson(regionVector))

    with open(datadir.join("out_test_data_bounds.geojson").strpath, "w") as out:
        out.write(vectorToGeoJson(boundsVector))


def test_vec_nearest(datadir, fileVector, proj_EPSG3111_REAL):

    fileVector = fileVector.convert(proj_EPSG3111_REAL)

    nearestGeoJson = """{"features": [{"geometry": {"coordinates": [144.07501, -37.28393], "type": "Point"}, "properties": {"radius": 0.05}, "type": "Feature"}], "type": "FeatureCollection"}"""
    nearestPointVector = geoJsonToVector(nearestGeoJson)

    nearestPointVector = nearestPointVector.convert(proj_EPSG3111_REAL)


def test_vec_mapDistance(datadir, fileVector, proj_EPSG3111_REAL):

    # test map distance when resolution and bounds are given
    testRasterise = fileVector.mapDistance(50.0, geom_type=GeometryType.LineString)
    # testRasterise.setProjectionParameters(proj_EPSG3111_REAL)

    # test map distance when a raster is given
    testRasterise2 = fileVector.mapDistance(inp_raster=testRasterise)
    assert np.allclose(testRasterise, testRasterise2)


def test_vec_mapVector(datadir, fileVector, proj_EPSG3111_REAL):

    nearestGeoJson = """{"features": [{"geometry": {"coordinates": [144.07501, -37.28393], "type": "Point"}, "properties": {"radius": 0.05}, "type": "Feature"}], "type": "FeatureCollection"}"""
    nearestPointVector = geoJsonToVector(nearestGeoJson)
    nearestPointVector = nearestPointVector.convert(proj_EPSG3111_REAL)

    # test map distance when resolution and bounds are given
    fileVector = fileVector.convert(proj_EPSG3111_REAL)
    testRasterise = fileVector.mapDistance(50.0, geom_type=GeometryType.LineString)

    testRasterise.mapVector(nearestPointVector, widthPropertyName="radius")
    testRasterise.write(datadir.join("out_test_data_distance.tif").strpath)


def test_vec_vectorise(datadir, fileVector, proj_EPSG3111_REAL, proj_EPSG4326_REAL):

    # test map distance when resolution and bounds are given
    testRasterise = fileVector.mapDistance(50.0, geom_type=GeometryType.LineString)

    contourVector = testRasterise.vectorise([10.0, 80.0])
    contourVector = contourVector.convert(proj_EPSG4326_REAL)

    with open(datadir.join("out_test_data_contour.geojson").strpath, "w") as out:
        out.write(vectorToGeoJson(contourVector))


def test_vec_sample_raster(datadir, fileVector, proj_EPSG3111_REAL):
    fileVector = fileVector.convert(proj_EPSG3111_REAL)
    testRasterise = fileVector.mapDistance(50.0, geom_type=GeometryType.LineString)

    pointVector = fileVector.convert(GeometryType.Point)
    pointVector.pointSample(testRasterise)


@pytest.mark.gdal
@pytest.mark.skipif(not supported_libs.HAS_GDAL, reason="gdal library is not installed")
def test_vec_sample_rasterfile(datadir, fileVector, proj_EPSG3111_REAL):
    fileVector = fileVector.convert(proj_EPSG3111_REAL)
    testRasterise = fileVector.mapDistance(50.0, geom_type=GeometryType.LineString)

    testRasterise.write(datadir.join("out_test_data_distance.tif").strpath)

    inpRaster = raster.RasterFile(filePath=datadir.join("out_test_data_distance.tif").strpath,
                                  name="rasterised", backend="gdal")
    inpRaster.read()

    pointVector = fileVector.convert(GeometryType.Point)
    pointVector.pointSample(inpRaster)
