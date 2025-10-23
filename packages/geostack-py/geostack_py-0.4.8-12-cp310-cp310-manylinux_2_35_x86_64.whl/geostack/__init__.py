# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
geostack
==========

A python interface to Geostack, a high performance geospatial analytics
library, with a focus on providing a generic framework to perform
analytics on a variety of geospatial datasets.

The main classes in geostack are: class:`geostack.vector.Vector`,
`geostack.raster.Raster`

To use these classes, you will need compile and install the c++ geostack
library and cython interface to the c++ library.

"""
import os
import platform

SOURCE_PATH = os.path.dirname(os.path.abspath(__file__))

# hack in the path to packaged library
if os.path.exists(os.path.join(SOURCE_PATH, '.libs')):
    GEOSTACK_HOME = os.path.join(SOURCE_PATH, '.libs')
    flag = 'GEOSTACK_HOME' in os.environ
    if not flag:
        os.environ['GEOSTACK_HOME'] = SOURCE_PATH
    else:
        if GEOSTACK_HOME not in os.environ['GEOSTACK_HOME']:
            os.environ['GEOSTACK_HOME'] = os.path.join(SOURCE_PATH, '.libs')

    if platform.system().lower() == "linux":
        flag = 'LD_LIBRARY_PATH' in os.environ
        if not flag:
            os.environ['LD_LIBRARY_PATH'] = SOURCE_PATH
        else:
            if SOURCE_PATH not in os.environ['LD_LIBRARY_PATH']:
                if len(os.environ['LD_LIBRARY_PATH']) > 0:
                    os.environ['LD_LIBRARY_PATH'] = (f"{SOURCE_PATH}:" +
                        os.environ['LD_LIBRARY_PATH'])
                else:
                    os.environ['LD_LIBRARY_PATH'] = SOURCE_PATH

import logging

from . import core
from . import dataset
from . import io
from . import raster
from . import readers
from . import runner
from . import series
from . import solvers
from . import utils
from . import vector
from . import writers
from ._version import version, __version__
from . import definitions
from . import gs_enums
