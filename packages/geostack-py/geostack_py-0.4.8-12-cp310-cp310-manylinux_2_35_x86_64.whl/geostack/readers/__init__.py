# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os.path as pth
from xml.etree import ElementTree
from .rasterReaders import DataHandler, NC_Handler, GDAL_Handler
from .rasterReaders import XR_Handler, RIO_Handler, get_gdal_geotransform, from_zarr
from .vectorReaders import from_ogr, from_geopandas, from_pyshp, from_fiona, DBHandler
from .gribReader import GRIB_Handler, get_ftp_file
from . import timeutils
from . import ftputils
from .ftputils import Ftp
from .timeutils import RasterTime, TimeArray, gribTime
from . import ncutils


def parse_cf_standard_name_table(source=None):
    """
    """
    if not source:
        source = pth.join(
            pth.dirname(__file__), "data", "cf-standard-name-table.xml"
        )
    root = ElementTree.parse(source).getroot()

    # Build dictionaries
    info = {}
    table: dict = {}
    aliases = {}
    for child in root:
        if child.tag == "entry":
            key = child.attrib.get("id")
            table[key] = {}
            for item in ["canonical_units", "grib", "amip", "description"]:
                parsed = child.findall(item)
                attr = item.replace("canonical_", "")
                table[key][attr] = (parsed[0].text or "") if parsed else ""
        elif child.tag == "alias":
            alias = child.attrib.get("id")
            key = child.findall("entry_id")[0].text
            aliases[alias] = key
        else:
            info[child.tag] = child.text

    return info, table, aliases
