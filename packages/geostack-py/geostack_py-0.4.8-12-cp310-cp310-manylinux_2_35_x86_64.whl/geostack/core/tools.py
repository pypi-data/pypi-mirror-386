# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re

__all__ = ['is_valid_name']


def is_valid_name(input_name: str) -> bool:
    """check if input name is valid

    Parameters
    ----------
    input_name : str
        name of a Geostack object/ Property

    Returns
    -------
    bool
        True if valid False otherwise
    """

    if not isinstance(input_name, (str, bytes)):
        return True

    if isinstance(input_name, bytes):
        input_name = input_name.decode()

    if re.search("[\\s]", input_name, re.UNICODE) is not None:
        rc = re.match("[a-zA-Z0-9_$]\\s*[a-zA-Z0-9_$]", input_name, re.UNICODE) is None
    else:
        rc = True

    return rc
