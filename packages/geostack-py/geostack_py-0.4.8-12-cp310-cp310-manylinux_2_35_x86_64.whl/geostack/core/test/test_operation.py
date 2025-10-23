# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import json
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))
from geostack.core import Json11, ProjectionParameters
from geostack.core import readYaml, Operation
from geostack.raster import Raster, RasterPtrList
from geostack.runner import runScript
from geostack.vector import Vector, VectorPtrList
import pytest

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

@pytest.mark.xfail
@pytest.mark.operation
def test_yaml_reader(datadir):
    configFile = datadir.join("configFile.yaml")
    json_object = readYaml(configFile.strpath)
    assert isinstance(json_object, Json11)
    assert not json_object.is_null()

@pytest.mark.operation
def test_variable_op_json(datadir):
    config = {
                "operations": [
                    {
                        "variables": {
                            "A": [1.0, 1.0, 1.0, 1.0],
                            "B": [1.0, 2.0, 3.0, 4.0],
                            "C": {
                                "size": 4
                            }
                        }
                    },
                    {
                        "runVariablesScript": {
                            "script": "B = A"
                        }
                    }
                ]
            }
    with open(datadir.join("variable_operation_config.json").strpath, "w") as out:
        json.dump(config, out)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("variable_operation_config.json").strpath)

@pytest.mark.operation
def test_variable_op_yaml(datadir):
    config = """
operations:
    - variables:
        A:
            - 1.0
            - 1.0
            - 1.0
            - 1.0
        B:
            - 1.0
            - 2.0
            - 3.0
            - 4.0
        C:
            size: 4
    - runVariablesScript:
        script: B = A
"""
    with open(datadir.join("variable_operation_config.yaml").strpath, "w") as out:
        out.write(config)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("variable_operation_config.yaml").strpath)

@pytest.mark.operation
def test_raster_creation_op(datadir):
    r = Raster(name='r')
    r.init(nx=5, ny=5, nz=1, hx=1.0, hy=1.0, hz=0.0)
    r.setAllCellValues(0.0)
    r.setProjectionParameters(ProjectionParameters.from_epsg("4326"))

    runScript("r = randomNormal(0.0, 1.0);", [ r ])
    r_value = r.getCellValue(0, 0)

    r.write(datadir.join("test_create_raster.tif").strpath)

    config = {
                "operations": [
                    {
                        "createRaster": {
                              "name": "testRasterA",
                              "type": "REAL",
                              "source": f"{datadir.strpath}/test_create_raster.tif",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runRasterScript": {
                            "create": "testRasterB",
                            "script": "testRasterB = testRasterA * 2"
                        }
                    },
                    {
                        "write": {
                            "name": "testRasterB",
                            "destination": f"{datadir.strpath}/output_create_raster.tif"
                        }
                    }
                ]
            }

    r_list = RasterPtrList()
    v_list = VectorPtrList()

    Operation_obj = Operation()
    Operation_obj.run(config['operations'], r_list, v_list)

    print(r_list.size, v_list.size)

    r2 = Raster(name='r2')
    r2.read(f"{datadir.strpath}/output_create_raster.tif")

    assert r2.getCellValue(0, 0) == (r_value * 2)

@pytest.mark.operation
def test_raster_creation_op_json(datadir):

    r = Raster(name='r')
    r.init(nx=5, ny=5, nz=1, hx=1.0, hy=1.0, hz=0.0)
    r.setAllCellValues(0.0)
    r.setProjectionParameters(ProjectionParameters.from_epsg("4326"))

    runScript("r = randomNormal(0.0, 1.0);", [ r ])
    r_value = r.getCellValue(0, 0)

    r.write(datadir.join("test_create_raster.tif").strpath)

    config = {
                "operations": [
                    {
                        "createRaster": {
                              "name": "testRasterA",
                              "type": "REAL",
                              "source": "test_create_raster.tif",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runRasterScript": {
                            "create": "testRasterB",
                            "script": "testRasterB = testRasterA * 2"
                        }
                    },
                    {
                        "write": {
                            "name": "testRasterB",
                            "destination": "output_create_raster.tif"
                        }
                    }
                ]
            }

    with open(datadir.join("create_raster_config.json").strpath, "w") as out:
        json.dump(config, out)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("create_raster_config.json").strpath)

    r2 = Raster(name='r2')
    r2.read("output_create_raster.tif")

    assert r2.getCellValue(0, 0) == (r_value * 2)

@pytest.mark.operation
def test_raster_creation_op_yaml(datadir):

    r = Raster(name='r')
    r.init(nx=5, ny=5, nz=1, hx=1.0, hy=1.0, hz=0.0)
    r.setAllCellValues(0.0)
    r.setProjectionParameters(ProjectionParameters.from_epsg("4326"))

    runScript("r = randomNormal(0.0, 1.0);", [ r ])
    r_value = r.getCellValue(0, 0)

    r.write(datadir.join("test_create_raster.tif").strpath)

    config = """
operations:
    - createRaster:
        name: testRasterA
        projection: +proj=longlat +datum=WGS84 +no_defs +type=crs
        source: test_create_raster.tif
        type: REAL
    - runRasterScript:
        create: testRasterB
        script: testRasterB = testRasterA * 2
    - write:
        destination: output_create_raster.tif
        name: testRasterB
"""

    with open(datadir.join("create_raster_config.yaml").strpath, "w") as out:
        out.write(config)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("create_raster_config.yaml").strpath)

    r2 = Raster(name='r2')
    r2.read("output_create_raster.tif")

    assert r2.getCellValue(0, 0) == (r_value * 2)

@pytest.mark.operation
def test_create_vector_op(datadir):
    vec1 = {"features": [
            {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
                "properties": {"C": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"C": 20}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"C": 30}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 40}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 50}, "type": "Feature"},
            {"geometry": {"coordinates": [2, 0.75], "type": "Point"},
                "properties": {"C": 60}, "type": "Feature"}
            ], "type": "FeatureCollection"}

    vec1 = Vector.from_geojson(vec1)
    vec1.to_geojson(datadir.join("test_create_vector.geojson").strpath)

    config = {
                "operations": [
                    {
                        "createVector": {
                              "name": "testVectorA",
                              "source": f"{datadir.strpath}/test_create_vector.geojson",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runVectorScript": {
                            "name": "testVectorA",
                            "script": "C += 1;"
                        }
                    },
                    {
                        "write": {
                            "name": "testVectorA",
                            "destination": f"{datadir.strpath}/output_create_vector.geojson"
                        }
                    }
                ]
            }

    r_list = RasterPtrList()
    v_list = VectorPtrList()

    Operation_obj = Operation()
    Operation_obj.run(config['operations'], r_list, v_list)

    vec2 = Vector.from_geojson(datadir.join('output_create_vector.geojson').strpath)
    assert vec1.getProperty(0, "C") + 1 == vec2.getProperty(0, "C")

@pytest.mark.operation
def test_create_vector_op_json(datadir):
    vec1 = {"features": [
            {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
                "properties": {"C": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"C": 20}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"C": 30}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 40}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 50}, "type": "Feature"},
            {"geometry": {"coordinates": [2, 0.75], "type": "Point"},
                "properties": {"C": 60}, "type": "Feature"}
            ], "type": "FeatureCollection"}

    vec1 = Vector.from_geojson(vec1)
    vec1.to_geojson(datadir.join("test_create_vector.geojson").strpath)

    config = {
                "operations": [
                    {
                        "createVector": {
                              "name": "testVectorA",
                              "source": "test_create_vector.geojson",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runVectorScript": {
                            "name": "testVectorA",
                            "script": "C += 1;"
                        }
                    },
                    {
                        "write": {
                            "name": "testVectorA",
                            "destination": "output_create_vector.geojson"
                        }
                    }
                ]
            }

    with open(datadir.join("create_vector_config.json").strpath, "w") as out:
        json.dump(config, out)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("create_vector_config.json").strpath)

    vec2 = Vector.from_geojson(datadir.join('output_create_vector.geojson').strpath)
    assert vec1.getProperty(0, "C") + 1 == vec2.getProperty(0, "C")

@pytest.mark.operation
def test_create_vector_op_yaml(datadir):
    vec1 = {"features": [
            {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
                "properties": {"C": 10}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"C": 20}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"C": 30}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 40}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"C": 50}, "type": "Feature"},
            {"geometry": {"coordinates": [2, 0.75], "type": "Point"},
                "properties": {"C": 60}, "type": "Feature"}
            ], "type": "FeatureCollection"}

    vec1 = Vector.from_geojson(vec1)
    vec1.to_geojson(datadir.join("test_create_vector.geojson").strpath)

    config = """
operations:
    - createVector:
        name: testVectorA
        projection: +proj=longlat +datum=WGS84 +no_defs +type=crs
        source: test_create_vector.geojson
    - runVectorScript:
        name: testVectorA
        script: C += 1;
    - write:
        destination: output_create_vector.geojson
        name: testVectorA
"""

    with open(datadir.join("create_vector_config.yaml").strpath, "w") as out:
        out.write(config)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("create_vector_config.yaml").strpath)

    vec2 = Vector.from_geojson(datadir.join('output_create_vector.geojson').strpath)
    assert vec1.getProperty(0, "C") + 1 == vec2.getProperty(0, "C")

@pytest.mark.operation
def test_area_script_op(datadir):
    testRasterA = Raster(name='testRasterA')
    testRasterA.init(nx=21, ny=21, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, 10, 10)

    testRasterA.write(datadir.join('test_raster_areascript.tif').strpath)

    config = {
                "operations": [
                    {
                        "createRaster": {
                              "name": "testRasterA",
                              "type": "REAL",
                              "source": f"{datadir.strpath}/test_raster_areascript.tif",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runAreaScript": {
                            "create": "testRasterB",
                            "width": 3,
                            "script": "if (isValid_REAL(testRasterA)) {if isValid_REAL(output) {output += testRasterA;} else {output = testRasterA;} sum += 1.0;}"
                        }
                    },
                    {
                        "write": {
                            "name": "testRasterB",
                            "destination": f"{datadir.strpath}/output_raster_areascript.tif"
                        }
                    }
                ]
            }

    r_list = RasterPtrList()
    v_list = VectorPtrList()

    Operation_obj = Operation()
    Operation_obj.run(config['operations'], r_list, v_list)

    testRasterB = Raster(name='testRasterB')
    testRasterB.read(f"{datadir.strpath}/output_raster_areascript.tif")

    # Test values
    assert testRasterB.hasData()
    assert round(testRasterB.getCellValue(10, 10), 4) == round(99.9/49.0, 4)

@pytest.mark.operation
def test_area_script_op_json(datadir):
    testRasterA = Raster(name='testRasterA')
    testRasterA.init(nx=21, ny=21, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, 10, 10)

    testRasterA.write(datadir.join('test_raster_areascript.tif').strpath)

    config = {
                "operations": [
                    {
                        "createRaster": {
                              "name": "testRasterA",
                              "type": "REAL",
                              "source": "test_raster_areascript.tif",
                              "projection": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
                        }
                    },
                    {
                        "runAreaScript": {
                            "create": "testRasterB",
                            "width": 3,
                            "script": "if (isValid_REAL(testRasterA)) {if isValid_REAL(output) {output += testRasterA;} else {output = testRasterA;} sum += 1.0;}"
                        }
                    },
                    {
                        "write": {
                            "name": "testRasterB",
                            "destination": "output_raster_areascript.tif"
                        }
                    }
                ]
            }

    with open(datadir.join("areascript_raster_config.json").strpath, "w") as out:
        json.dump(config, out)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("areascript_raster_config.json").strpath)

    testRasterB = Raster(name='testRasterB')
    testRasterB.read("output_raster_areascript.tif")

    # Test values
    assert testRasterB.hasData()
    assert round(testRasterB.getCellValue(10, 10), 4) == round(99.9/49.0, 4)

@pytest.mark.operation
def test_area_script_op_yaml(datadir):
    testRasterA = Raster(name='testRasterA')
    testRasterA.init(nx=21, ny=21, hx=1.0, hy=1.0)
    testRasterA.setAllCellValues(0.0)
    testRasterA.setCellValue(99.9, 10, 10)

    testRasterA.write(datadir.join('test_raster_areascript.tif').strpath)

    config = """
operations:
    - createRaster:
        name: testRasterA
        projection: +proj=longlat +datum=WGS84 +no_defs +type=crs
        source: test_raster_areascript.tif
        type: REAL
    - runAreaScript:
        create: testRasterB
        script: |
            if (isValid_REAL(testRasterA)) {
                if isValid_REAL(output) {
                    output += testRasterA;
                } else {
                output = testRasterA;
                } sum += 1.0;
            }
        width: 3
    - write:
        destination: output_raster_areascript.tif
        name: testRasterB
"""

    with open(datadir.join("areascript_raster_config.yaml").strpath, "w") as out:
        out.write(config)

    Operation_obj = Operation()
    Operation_obj.runFromConfigFile(datadir.join("areascript_raster_config.yaml").strpath)

    testRasterB = Raster(name='testRasterB')
    testRasterB.read("output_raster_areascript.tif")

    # Test values
    assert testRasterB.hasData()
    assert round(testRasterB.getCellValue(10, 10), 4) == round(99.9/49.0, 4)
