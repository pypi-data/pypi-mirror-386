# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys
import pickle

sys.path.insert(0, os.path.realpath('../../../'))
import numpy as np
from geostack.core import Variables
import pytest


@pytest.mark.variables
def test_1():
    var = Variables()
    assert not var.hasData


@pytest.mark.variables
def test_2():
    var = Variables()
    var.set("varA", 77.7)
    var.set("varB", 88.8)
    test_data = var.hasData
    test_a = round(var.get("varA"), ndigits=1) == 77.7
    test_b = round(var.get("varB"), ndigits=1) == 88.8

    assert test_data & test_a & test_b


@pytest.mark.variables
def test_3():
    var = Variables()
    with pytest.raises(ValueError):
        var.set("var A", 77.7)


@pytest.mark.variables
@pytest.mark.parametrize("operation",
                         ["*", "+", "-", "/", ">", "<", "=="])
def test_runscript(operation):
    vars = Variables()

    # define vector variables
    vars.set("a", list(range(10)))
    vars.set("b", list(map(lambda i: i * 2, range(10))))

    a = vars['a']
    b = vars['b']

    # define scalar variables
    vars.set("c", 3.0)

    c = vars['c']

    # call runScript
    script = f"a = b {operation} c;"
    vars.runScript(script)

    _locals = locals()

    script = f"a = b {operation} c"
    exec(script, globals(), _locals)

    assert np.allclose(_locals['a'], vars['a'])


@pytest.mark.variables
def test_variables_pickling():
    var = Variables()
    var.set("varA", 77.7)
    var.set("varB", 88.8)

    obj = pickle.loads(pickle.dumps(var))
    assert obj.get("varA") == var.get('varA')
