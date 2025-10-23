# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys

sys.path.insert(0, os.path.realpath('../../../'))

import pytest
import numpy as np
from geostack.vector import Coordinate

@pytest.mark.xfail
def test_coordinate():
    # print("\n@@@@ Testing vector class\n")

    #vertex
    v = Coordinate.from_list([144.9631, -37.8136])
    geoHash = v.getGeoHash()

    assert geoHash == "r1r0fsnzuczz"
