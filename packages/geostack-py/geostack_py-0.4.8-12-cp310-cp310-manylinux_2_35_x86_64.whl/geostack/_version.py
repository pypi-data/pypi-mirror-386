# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections import namedtuple
from .core import get_geostack_version

# add the version information
version_parser = namedtuple("GEOSTACK_VER",
                            ["major", "minor", "patch"])
version = version_parser(**get_geostack_version())

__version__ = f"{version.major}.{version.minor}.{version.patch}"
