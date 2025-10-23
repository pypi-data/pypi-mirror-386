# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import sys

sys.path.insert(0, os.path.realpath('../../../'))
import numpy as np
from geostack.core import isValid, isInvalid

def test_valid():
    assert not(isValid(np.nan))
    assert isValid(2.0)

def test_invalid():
    assert not(isInvalid(2.0))
    assert isInvalid(np.nan)
