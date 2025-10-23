# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import math
sys.path.insert(0, os.path.realpath('../../../'))
import pytest
from geostack.solvers import ODE
from geostack.core import Variables
from geostack.series import Series


@pytest.mark.ode
def test_ode_1():
    """
    solve eq.: dv/dt = -3.0 * t ^ 2 * e ^ v
    initial value: v(0) = 0
    """

    # create a config
    config = json.dumps({
        "dt": 0.01,
        "adaptiveMaximumSteps": 10,
        "adaptiveTolerance": 1e-3,
        "functionScripts": [
            {"v": "return -3.0 * t * t * exp(v);"}
        ],
        "outputSeries": {
            "v": "time"
        }
    })

    # create variables
    variables = Variables()
    variables.set("v", 0.0)

    solver = ODE()
    initSuccess = solver.init(config,
                              variables)

    assert initSuccess

    time = 0.0
    for i in range(100):
        solver.step()
        time += 0.01

    numerical = variables.get("v")
    analytic = -math.log(math.pow(time, 3.0) + 1.0)

    # solver.getSeries()

    assert abs(numerical - analytic) <= 1e-3

    vSeries = solver.getSeries("v", "time")
    assert isinstance(vSeries, Series)


@pytest.mark.ode
def test_ode_2():
    """
    solve eq.: du/dt = u / t + 3 * sqrt(t / u)
    initial value: u(1) = 1
    """

    config = json.dumps({
        "dt": 0.01,
        "adaptiveMaximumSteps": 10,
        "adaptiveTolerance": 1e-3,
        "functionScripts": [{"u": "return (u/t)+3.0*sqrt(t/u);"}],
        "outputSeries": {
            "u": "time"
        }
    })

    variables = Variables()
    variables.set("u", 1.0)

    solver = ODE()
    initSuccess = solver.init(config,
                              variables)

    assert initSuccess

    time = 1.0
    solver.setTime(time)
    for i in range(100):
        solver.step()
        time += 0.01

    numerical = variables.get("u")
    analytic = time*math.pow(4.5 * math.log(time)+1.0, 2.0 / 3.0)

    assert abs(numerical - analytic) <= 1e-3

    uSeries = solver.getSeries("u", "time")
    assert isinstance(uSeries, Series)


@pytest.mark.ode
def test_ode_3():
    """
    solve eqns:
        dx/dt = αx - βxy
        dy/dt = δxy - γy

    where:
        α = 1.1
        β = 0.4
        δ = 0.1
        γ = 0.4

    for initial value:
        x = 10.0
        y = 10.0
    """

    config = json.dumps({
        "dt": 0.1,
        "adaptiveMaximumSteps": 10,
        "adaptiveTolerance": 1e-3,
        "functionScripts": [
            {
                "x": """REAL α = 1.1;
                        REAL β = 0.4;
                        return α * x - β * x * y;"""},
            {
                "y": """REAL δ = 0.1;
                        REAL γ = 0.4;
                        return δ * x * y - γ * y;"""}
            ],
        "outputSeries": {
            "y": "x",
            "x": "time"
        }
        })

    variables = Variables()
    variables.set("x", 10.0)
    variables.set("y", 10.0)

    solver = ODE()
    initSuccess = solver.init(config,
                              variables)

    assert initSuccess

    time = 0.0
    for _ in range(1000):
        solver.step()
        time += 0.1

    numerical_x = variables.get("x")
    numerical_y = variables.get("y")

    assert abs(numerical_x - 27.2473) <= 1e-3
    assert abs(numerical_y - 4.55964) <= 1e-3

    ySeries = solver.getSeries("y", "x")
    assert isinstance(ySeries, Series)


@pytest.mark.ode
@pytest.mark.xfail
def test_ode_4():
    """
    solve eqns:
        dx/dt = σ(x - y)
        dy/dt = x(ρ - z) - y
        dz/dt = xy - βz

    where:
        σ = 10.0
        ρ = 28.0
        β = 8.0 / 3.0

    for initial value:
        x = 10.0
        y = 10.0
        z = 10.0
    """
    config = json.dumps({
        "dt": 0.1,
        "adaptiveMaximumSteps": 10,
        "adaptiveTolerance": 1e-3,
        "functionScripts": [
            {
                "x": """REAL σ = 10.0;
                        return σ * (y - x);"""},
            {
                "y": """REAL ρ = 28.0;
                        return x * (ρ - z) - y;"""},
            {
                "z": """REAL β = 8.0 / 3.0;
                        return x * y - β * z;"""}],
        "outputSeries": {
            "x": "time",
            "y": "time",
            "z": "time"
        }
    })

    variables = Variables()
    variables.set("x", 10.0)
    variables.set("y", 10.0)
    variables.set("z", 10.0)

    solver = ODE()
    initSuccess = solver.init(config,
                              variables)

    assert initSuccess

    time = 0
    for _ in range(1000):
        solver.step()
        time += 0.1

    numerical_x = variables.get("x")
    numerical_y = variables.get("y")
    numerical_z = variables.get("z")

    assert numerical_x > -25 and numerical_x < 25
    assert numerical_y > -25 and numerical_y < 25
    assert numerical_z > -25 and numerical_z < 25

    xSeries = solver.getSeries("x", "time")
    assert isinstance(xSeries, Series)


@pytest.mark.ode
def test_ode_5():
    """
    solve eqns:
        d^2x/dt^2 = 0
        d^2y/dt^2 = -1

    where:
        g = 1

    for initial value:
        x(0) = 0
        y(0) = 0
        u(0) = dx(0)/dt = 2
        v(0) = dy(0)/dt = 2
    """

    config = json.dumps({
        "dt": 0.1,
        "adaptiveMaximumSteps": 10,
        "adaptiveTolerance": 1e-3,
        "functionScripts": [
            {
                "x": "return u;",
            },
            {
                "y": "return v;",
            },
            {
                "u": "return 0.0;",
            },
            {
                "v": "return -1;"
            }
        ],
        "outputSeries": {
            "y": "x",
            "x": "time"
        }
    })

    variables = Variables()
    variables.set("x", 0.0)
    variables.set("y", 0.0)
    variables.set("u", 2.0)
    variables.set("v", 2.0)

    solver = ODE()
    initSuccess = solver.init(config,
                              variables)

    assert initSuccess

    time = 0.0
    for _ in range(100):
        solver.step()
        time += 0.1
        if (variables.get('y') < 0.0):
            break

    numerical_x = variables.get("x")
    numerical_y = variables.get("y")

    assert abs(time - 4.0) <= 1e-3
    assert abs(numerical_x - 8) <= 1e-3
    assert abs(numerical_y - 0) <= 1e-3

    ySeries = solver.getSeries("y", "x")
    assert isinstance(ySeries, Series)
