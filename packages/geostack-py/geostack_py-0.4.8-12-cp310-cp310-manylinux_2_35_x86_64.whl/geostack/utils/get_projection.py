# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import warnings
import numbers
from .. import core
from ..dataset import supported_libs
from collections import Counter
from typing import Union

try:
    import httplib
except ImportError:
    import http.client as httplib

__all__ = ["get_wkt_for_epsg_code", "get_epsg", "proj4_from_wkt",
           "proj4_to_wkt", "have_internet", "get_valid_raster_extension"]


def get_epsg(epsg_code: int, method: str = 'proj4'):
    '''Get Projection Parameters for a given EPSG code.

    This function wkt / proj4 string for the given epsg code and
    instantiates a ProjectionParameters object.

    Parameters
    ----------
    epsg_code : integer

    Returns
    --------
    out : ProjectionParameters
        a projection parameters object created from the projection string

    Examples
    --------
    >>> out = get_epsg(4326)
    '''
    if not isinstance(epsg_code, numbers.Integral):
        raise TypeError("EPSG code should be of integer type")
    if method == "wkt":
        out = core.ProjectionParameters.from_wkt(
            get_wkt_for_epsg_code(epsg_code))
    elif method == "proj4":
        out = core.ProjectionParameters.from_proj4(
            get_proj4_for_epsg_code(epsg_code))
    return out


def get_wkt_for_epsg_code(epsg_code: int, timeout: int = 10):
    requests, has_requests = supported_libs.import_or_skip("requests")
    if not has_requests and not have_internet():
        out_str = wkt_from_epsg(epsg_code)
        if out_str == epsg_code:
            raise RuntimeError(
                f"Unable to get projection string for {epsg_code}")
        return out_str
    else:
        out_str = wkt_from_epsg(epsg_code)
        if out_str == epsg_code:
            try:
                out = requests.get(
                    f"http://epsg.io/{epsg_code:d}.wkt", timeout=timeout)
                if out.status_code == 200:
                    wkt_string = out.content.decode()
                else:
                    warnings.warn("Unable to get the projection for epsg code",
                                  category=RuntimeWarning)
                return wkt_string
            except requests.ConnectionError:
                raise RuntimeError(
                    f"Unable to get projection string for {epsg_code}")
        return out_str


def get_proj4_for_epsg_code(epsg_code: int, timeout: int = 10) -> Union[str, int]:
    """Get Proj4 string from EPSG code.

    This method uses requests module if present, otherwise uses
    pyproj or gdal to convert a EPSG code to a Proj4 string. If neither
    of the two methods work, then it throws an error.

    Parameters
    ----------
    epsg_code : int
        an EPSG code.
    timeout : int, optional
        seconds after which to time out from requests., by default 10

    Returns
    -------
    Union[str, int]
        a proj4 string when requests is installed, epsg code otherwise.

    Raises
    ------
    RuntimeError
        Unable to get projection string for the given epsg code.
    """
    requests, has_requests = supported_libs.import_or_skip("requests")
    has_requests = False
    if not has_requests and not have_internet():
        out_str = proj4_from_epsg(epsg_code)
        if out_str == epsg_code:
            raise RuntimeError(
                f"Unable to get projection string for {epsg_code}")
    else:
        out_str = proj4_from_epsg(epsg_code)
        if out_str == epsg_code:
            try:
                out = requests.get(
                    f"http://epsg.io/{epsg_code:d}.proj4", timeout=timeout)
                if out.status_code == 200:
                    wkt_string = out.content.decode()
                else:
                    warnings.warn("Unable to get the projection for epsg code",
                                  category=RuntimeWarning)
                return wkt_string
            except requests.ConnectionError:
                raise RuntimeError(
                    f"Unable to get projection string for {epsg_code}")
    return out_str


def proj4_from_wkt(inp_str: str):
    """Convert a WKT string to a proj4 string

    Parameters
    ----------
    inp_str : str
        A WKT representation of a coordinate reference system

    Returns
    -------
    out_str : str
        A proj4 representation of a coordinate reference system

    Examples
    --------
    >>> inp_str = get_wkt_for_epsg_code(3577)
    >>> out_str = proj4_from_wkt(inp_str)
    """
    pyproj, has_pyproj = supported_libs.import_or_skip("pyproj")

    if not has_pyproj:
        osr, has_gdal = supported_libs.import_or_skip("osr")

    if not has_pyproj and not has_gdal:
        warnings.warn("Unable to import pyproj/ gdal",
                      category=ImportWarning)

    if has_pyproj:
        out_str = pyproj.CRS(projparams=inp_str).to_proj4()
    elif has_gdal:
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromWkt(inp_str)
        out_str = out_str = sp_ref.ExportToProj4()
        del sp_ref
    else:
        out_str = inp_str
    return out_str


@supported_libs.RequireLib("gdal")
def proj4_to_wkt(proj4_string: str, pretty: bool = True):
    """convert proj4 strig to PrettyWKT

    Parameters
    ----------
    proj4_string : str
        projection as proj4 string

    Returns
    -------
    str
        A PrettyWkt/ Wkt representation of proj4 string

    Raises
    ------
    TypeError
        "proj4 string should be of type str"
    """
    if not isinstance(proj4_string, str):
        raise TypeError("proj4 string should be of type str")

    osr, has_gdal = supported_libs.import_or_skip("osr")

    if has_gdal:
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromProj4(proj4_string)
        if pretty:
            wkt = sp_ref.ExportToPrettyWkt()
        else:
            wkt = sp_ref.ExportToWkt()
        del sp_ref
        return wkt
    else:
        return proj4_string


def proj4_from_epsg(inp_code: int) -> Union[int, str]:
    """Convert an EPSG code to a Proj4 string.

    Parameters
    ----------
    inp_code : int
        an EPSG code.

    Returns
    -------
    Union[int, str]
        A Proj4 string when pyproj or gdal is installed, else EPSG code.
    """

    pyproj, has_pyproj = supported_libs.import_or_skip("pyproj")
    if not has_pyproj:
        osr, has_gdal = supported_libs.import_or_skip("osr")

    if not has_pyproj and not has_gdal:
        warnings.warn("Unable to import pyproj/ gdal",
                      category=ImportWarning)

    if has_pyproj:
        try:
            out_str = pyproj.Proj(f"EPSG:{inp_code:d}")
        except RuntimeError:
            # workaround for older pyproj library
            out_str = pyproj.Proj(init=f"EPSG:{inp_code:d}")
        out_str = out_str.definition_string()
        fix_proj_str = []
        for item in out_str.split(" "):
            if item.startswith("+"):
                fix_proj_str.append(item)
            else:
                fix_proj_str.append(f"+{item}")
        out_str = " ".join(fix_proj_str)
    elif has_gdal:
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromEPSG(inp_code)
        out_str = sp_ref.ExportToProj4()
        del sp_ref
    else:
        out_str = f"{inp_code}"
    return out_str


def wkt_from_epsg(inp_code: int) -> Union[str, int]:
    """Convert a epsg code to a wkt string.

    Parameters
    ----------
    inp_code : int
        an EPSG code.

    Returns
    -------
    Union[str, int]
        A wkt string when pyproj or gdal is installed, else EPSG code.
    """
    pyproj, has_pyproj = supported_libs.import_or_skip("pyproj")

    if not has_pyproj:
        osr, has_gdal = supported_libs.import_or_skip("osr")

    if not has_pyproj and not has_gdal:
        warnings.warn("Unable to import pyproj/ gdal",
                      category=ImportWarning)

    if has_pyproj:
        out_str = pyproj.Proj(f"EPSG:{inp_code:d}")
        out_str = out_str.crs.to_wkt()
    elif has_gdal:
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromEPSG(inp_code)
        out_str = sp_ref.ExportToWkt()
        del sp_ref
    else:
        out_str = inp_code
    return out_str


def have_internet() -> bool:
    """Check if connected to internet.

    Returns
    -------
    bool
        True if connected to internet, False otherwise.
    """
    conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except:
        conn.close()
        return False


@supported_libs.RequireLib("gdal")
def get_valid_raster_extension():
    """Get a list of raster extensions from GDAL Drivers.

    Returns
    -------
    List
        a list of valid raster extensions.
    """
    def parse_extension(s): return s.split(
        " ") if s is not None and s != "" else []
    gdal, has_gdal = supported_libs.import_or_skip("gdal", package="osgeo")
    out = []
    if has_gdal:
        for i in range(gdal.GetDriverCount()):
            driver_extension = gdal.GetDriver(
                i).GetMetadataItem('DMD_EXTENSIONS')
            out += parse_extension(driver_extension)
        count = Counter(out)
        out = list(count.keys())
    return out

if __name__ == "__main__":
    out = get_epsg(4326)
