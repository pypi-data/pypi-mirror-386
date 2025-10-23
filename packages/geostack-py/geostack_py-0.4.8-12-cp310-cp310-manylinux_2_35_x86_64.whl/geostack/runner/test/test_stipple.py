# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

import numpy as np
import pytest
from geostack.raster import Raster
from geostack.runner import stipple, runScript
from geostack.io import vectorToGeoJson
from geostack.vector import Coordinate

@pytest.mark.runScript
def test_stipple():
    # Create raster layer
    A = Raster(name = "A")

    # Initialize Raster
    A.init(nx = 10, ny = 10, hx = 10.0, hy = 10.0)

    runScript("A = x*y;", [A])

    # Run script (with raster)
    v = stipple("""x += count*0.1;
                   y += count*0.1;
                   aaa = A;
                   bbb = x;
                   create = A < 25*25;""",
                [A],
                ["aaa", "bbb"],
                3)

    assert v.getPointCount() == 72

    props = v.getProperties().getPropertyNames()

    assert props == set(['aaa', 'bbb'])

    # Run script (with raster base)
    v = stipple("""x += count*0.1;
                   y += count*0.1;
                   aaa = A;
                   bbb = x;
                   create = A < 25*25;""",
                [A.get_raster_base()],
                ["aaa", "bbb"],
                3)

    assert v.getPointCount() == 72

    props = v.getProperties().getPropertyNames()

    assert props == set(['aaa', 'bbb'])
