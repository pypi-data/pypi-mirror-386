# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import json
import math
import numpy as np
from time import time
import pytest
from distutils import dir_util
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.vector import vector
from geostack.solvers import Particle


@pytest.mark.particle
def test_particle_solver():
    # Create particles
    p = vector.Vector()
    for c in range(10):
        p.addPoint([0]*4)

    # Create solver configuration
    config = {"dt": 0.001,
              "initialisationScript": '''
                   radius = 1.0;
                   velocity.x = sqrt(9.8/4.0);
                   velocity.y = sqrt(9.8/4.0);
                   velocity.z = sqrt(9.8/2.0);
                ''',
              "advectionScript": '''
                   time += dt;
                   if (position.z < 0.0) {
                       radius = -1.0;
                    }
                ''',
              "updateScript": "acceleration.z = -9.8;"
            }

    jsonConfig = json.dumps(config)

    # instantiate and initialize solver
    solver = Particle()
    initSuccess = solver.init(jsonConfig, p)

    # Run solver
    runSuccess = True
    i = 0
    while (runSuccess & (i < 1000)):
        runSuccess = solver.step()
        i += 1

    x = p.getCoordinate(0).p
    y = p.getCoordinate(0).q
    test_data = abs(math.sqrt(x*x+y*y)-1.0 < 1.0E-3)

    solver.getParticles()
    assert all([initSuccess, runSuccess, test_data])
