# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys

sys.path.insert(0, os.path.realpath('../../../'))
import numpy as np
from geostack.core import PropertyMap, REAL
from geostack.dataset.supported_libs import import_or_skip
import pytest

@pytest.fixture
def scalar_property():
    obj = PropertyMap()
    obj.setProperty("A", "10")
    obj.setProperty('B', 20)
    obj.setProperty("C", 30.0)
    obj.setProperty("D", np.float64(40.0))
    return obj

@pytest.fixture
def vector_property():
    obj = PropertyMap()
    obj.setProperty("Av", ['11', '12', '13', '14', '15'])
    obj.setProperty("Bv", [21, 22, 23, 24, 25])
    obj.setProperty("Cv", [31.0, 32.0, 33.0, 34.0, 35.0])
    obj.setProperty("Dv", list(map(np.float64, [41.0, 42.0, 43.0, 44.0, 45.0])))
    return obj

def test_create_scalar_property(scalar_property):
    scalar_property.setProperty("A $", 1)
    scalar_property.removeProperty("A $")

def test_create_vector_property(vector_property):
    vector_property.setProperty("A v", 1)
    vector_property.removeProperty("A v")

@pytest.mark.parametrize("prop,prop_type,expected",
                         [("A", str, "10"),
                          ("B", int, 20),
                          ("C", float, 30.0),
                          ("D", np.float64, np.float64(40.0))],)
def test_scalar_property(scalar_property, prop, prop_type, expected):
    assert scalar_property.getProperty(prop, prop_type=prop_type) == expected

@pytest.mark.parametrize("prop,prop_type,expected",
                         [("Av", str, ['11', '12', '13', '14', '15']),
                          ("Bv", int, np.array([21, 22, 23, 24, 25], dtype=np.int32)),
                          ("Cv", float, np.array([31.0, 32.0, 33.0, 34.0, 35.0], dtype=REAL)),
                          ("Dv", np.float64, np.array([41.0, 42.0, 43.0, 44.0, 45.0]))],)
def test_vector_property(vector_property, prop, prop_type, expected):
    if prop_type == "str":
        assert vector_property.getProperty(prop, prop_type=prop_type) == expected
    else:
        assert np.all(vector_property.getProperty(prop, prop_type=prop_type) == expected)

@pytest.mark.parametrize("prop,prop_type,expected",
                         [("Av", str, '12'),
                          ("Bv", int, 22),
                          ("Cv", float, 32.0),
                          ("Dv", np.float64, 42.0)])
def test_vector_property_copy(vector_property, prop, prop_type, expected):
    vector_property.copy(f"{prop}", 1, 3)
    assert vector_property.getProperty(f"{prop}", prop_type=prop_type)[3] == expected
