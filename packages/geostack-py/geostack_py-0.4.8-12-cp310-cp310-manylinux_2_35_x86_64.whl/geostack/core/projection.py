# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numbers
from typing import Dict, Union, Optional
import numpy as np
from ._cy_projection import (_convert_points_f, _convert_points_f_str, _convert_f, _convert_d,
                             _convert_f_str, _convert_d_str,
                             _convert_points_d, _convert_points_d_str, _convert_pointvector_f,
                             _convert_pointvector_d, _convert_pointvector_f_str,
                             _convert_pointvector_d_str)
from ._cy_projection import _ProjectionParameters_d, _ProjectionParameters_f
from ._cy_projection import parseWKT_d, parsePROJ4_d
from ._cy_projection import _toPROJ4_d, _toWKT_d
from ._cy_projection import fromEPSG_d, cy_projParamsFromEPSG
from ._cy_projection import _parseProjString
from .property import REAL
from . import str2bytes
from .. import vector

__all__ = ["convert", "ProjectionParameters",
           "projParamsFromEPSG", "_ProjectionParameters_d",
           "_ProjectionParameters_f", "parseProjString"]


def parseProjString(projString: Union[int, str]):
    """Get Proj4 parameters from EPSG code

    Parameters
    ----------
    projString: Union[str, int]
        projection information as integer/string

    Returns
    -------
    out: str
        ProjectionParameters
    """
    out = ProjectionParameters(dtype=np.float64)
    out._handle = _parseProjString(str(projString))
    return out


def projParamsFromEPSG(epsgCode: Union[int, str]):
    """Get Proj4 parameters from EPSG code

    Parameters
    ----------
    EPSG: Union[str, int]
        EPSG code as string

    Returns
    -------
    out: str
        proj4 string
    """
    return cy_projParamsFromEPSG(str(epsgCode))


def check_list_type(input_list):
    """Check type of input list.

    A helper function to check whether the input list is a nested list or not.

    Parameters
    ----------
    input_list : list
        List of Coordinates

    Returns
    ------
    out : int
        1 if list of points or 2 for list of lists

    Examples
    --------
    >>> points = [2418625, 2465403]
    >>> out = check_list_type(points)
    """
    if isinstance(input_list, list):
        if not len(input_list) > 0:
            raise ValueError("Input list cannot be empty")
        if isinstance(input_list[0], list):
            return 2
        elif isinstance(input_list[0], numbers.Real):
            return 1
    else:
        raise TypeError("input argument should be a list")


class ProjectionParameters:
    """Wrapper class for ProjectionParameters.

    Parameters
    ---------
    dtype : np.float32/np.float64
        Datatype for ProjectionParameters instance
    """

    def __init__(self, dtype=np.float64):
        if dtype is not None:
            if dtype == np.float32:
                self._handle = _ProjectionParameters_f()
                self.dtype = dtype
            elif dtype == np.float64:
                self._handle = _ProjectionParameters_d()
                self.dtype = dtype
            else:
                raise ValueError("dtype should be np.float32/np.float64")
        else:
            self._handle = None
            self.dtype = None

        self.inp_proj_str = ""

    @staticmethod
    def from_proj_param(other: "ProjectionParameters") -> "ProjectionParameters":
        """Copy operation for ProjectionParameters.

        Parameters
        ----------
        other : ProjectionParameters
            An instance of Projection Parameters

        Returns
        -------
        out : ProjectionParameters
            Returns an instance of ProjectionParameters using input argument.

        Examples
        --------
        >>> import numpy as np
        >>> proj_real = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
        >>> proj_real = ProjectionParameters.from_proj4(proj_real,
        ...                                             dtype=np.float32)
        >>> out = ProjectionParameters(proj_real)
        """
        if isinstance(other, _ProjectionParameters_d):
            out = ProjectionParameters(dtype=np.float64)
            out._handle = other
        elif isinstance(other, _ProjectionParameters_f):
            out = ProjectionParameters(dtype=np.float32)
            out._handle = other
        elif isinstance(other, ProjectionParameters):
            out = ProjectionParameters(dtype=other.dtype)
            out._handle = other._handle
            if len(other.inp_proj_str) > 0:
                out.inp_proj_str = other.inp_proj_str
        else:
            raise TypeError(
                "other should be an instance of ProjectionParameters")
        return out

    @staticmethod
    def from_epsg(epsgCode: Union[str, int], dtype=np.float64) -> "ProjectionParameters":
        """create ProjectionParameters object from EPSG code.

        Parameters
        ----------
        epsgCode : Union[str, int]
            EPSG code

        Returns
        -------
        ProjectionParameters
            an instance of ProjectionParameters

        Examples
        --------
        >>> ProjectionParameters.from_epsg(4326)
        """
        out = ProjectionParameters(dtype=None)
        out.inp_proj_str = epsgCode
        if dtype == np.float64:
            out._handle = fromEPSG_d(epsgCode)
            out.dtype = dtype
        else:
            raise ValueError("dtype should be np.float32/np.float64")
        return out

    @staticmethod
    def from_proj4(inpString: str, dtype=np.float64) -> "ProjectionParameters":
        """Create ProjectionParameters from Proj4 string.

        Parameters
        ----------
        inpString: str
            A Proj4 string.

        Returns
        -------
        out: ProjectionParameters
            Returns an instance of ProjectionParameters created from Proj4 string.

        Examples
        --------
        >>> import numpy as np
        >>> proj_real = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
        >>> proj_real = ProjectionParameters.from_proj4(proj_real,
        ...                                             dtype=np.float32)
        """
        out = ProjectionParameters(dtype=None)
        out.inp_proj_str = inpString
        if dtype == np.float64:
            out._handle = parsePROJ4_d(inpString)
            out.dtype = dtype
        else:
            raise ValueError("dtype should be np.float32/np.float64")
        return out

    @staticmethod
    def from_wkt(inpString: str, dtype=np.float64) -> "ProjectionParameters":
        """Parse WKT string to a ProjectionParameters instance.

        Parameters
        ----------
        inpString: str
            A projection string in WKT format.

        Returns
        -------
        out: ProjectionParameters
            An instance of ProjectionParameters object.

        Examples
        --------
        >>> prj_str = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
        >>> src_prj = ProjectionParameters.from_wkt(prj_str)
        """
        out = ProjectionParameters(dtype=None)
        out.inp_proj_str = inpString
        if dtype == np.float64:
            out._handle = parseWKT_d(inpString)
            out.dtype = dtype
        else:
            raise ValueError("dtype should be np.float32/np.float64")
        return out

    def to_wkt(self) -> str:
        """Convert ProjectionParameters object to wkt string.

        Parameters
        ----------
        Nil

        Returns
        -------
        out: str
            A WKT string.

        Examples
        --------
        >>> proj_real = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
        >>> proj_real = ProjectionParameters.from_proj4(proj_real,
        ...                                             dtype=np.float32)
        >>> out = proj_real.to_wkt()
        """
        out = _toWKT_d(self._handle)
        if isinstance(out, bytes):
            return out.encode()
        else:
            return out

    def to_proj4(self) -> str:
        """Convert ProjectionParameters object to proj4 string.

        Parameters
        ----------
        Nil

        Returns
        -------
        out: str
            A Proj4 string.

        Examples
        --------
        >>> proj_real = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
        >>> proj_real = ProjectionParameters.from_proj4(proj_real,
        ...                                             dtype=np.float32)
        >>> out = proj_real.to_proj4()
        """
        out = _toPROJ4_d(self._handle)
        if isinstance(out, bytes):
            return out.encode()
        else:
            return out

    @staticmethod
    def from_dict(inpDict: Dict, dtype=np.float64) -> "ProjectionParameters":
        """Method to instantiate ProjectionParameters from a dictionary containing proj.4 parameters

        Parameters
        ----------
        inpDict: dict
            Proj4 parameters

        dtype: numpy.dtype, default=np.float64
            Datatype for Projection Parameters

        Returns
        -------
        out: ProjectionParameters
            A instance of ProjectionParameters

        Examples
        --------
        >>> proj_str = "(+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs)"
        >>> proj_dict = proj4_to_dict(proj_str)
        >>> out = ProjectionParameters.from_dict(proj_dict, dtype=np.float32)
        """
        if not isinstance(inpDict, dict):
            raise TypeError("inpDict should be a dictionary")
        out = ProjectionParameters(dtype=None)
        if dtype == np.float32:
            out._handle = _ProjectionParameters_f.from_dict(inpDict)
            out.dtype = dtype
        elif dtype == np.float64:
            out._handle = _ProjectionParameters_d.from_dict(inpDict)
            out.dtype = dtype
        else:
            raise ValueError('dtype should be np.float32/np.float64')
        return out

    def to_dict(self) -> Dict:
        """Projection parameters to a dictionary.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : dict
            Projection parameters mapped to a dictionary

        Examples
        --------
        >>> proj_params = out.to_dict()
        """
        return self._handle.to_dict()

    @property
    def type(self):
        return self._handle.type

    @property
    def cttype(self):
        return self._handle.cttype

    @property
    def a(self):
        return self._handle.a

    @property
    def f(self):
        return self._handle.f

    @property
    def x0(self):
        return self._handle.x0

    @property
    def k0(self):
        return self._handle.k0

    @property
    def fe(self):
        return self._handle.fe

    @property
    def fn(self):
        return self._handle.fn

    @property
    def phi_0(self):
        return self._handle.phi_0

    @property
    def phi_1(self):
        return self._handle.phi_1

    @property
    def phi_2(self):
        return self._handle.phi_2

    def __eq__(self, other: "ProjectionParameters"):
        if not isinstance(other, ProjectionParameters):
            raise TypeError(
                "Input argument should be an instance of ProjectionParameters")
        elif self.dtype != other.dtype:
            raise TypeError(
                "Mismatch between dtype for input argument and class instance")
        return self._handle == other._handle

    def __ne__(self, other: "ProjectionParameters"):
        if not isinstance(other, ProjectionParameters):
            raise TypeError(
                "Input argument should be an instance of ProjectionParameters")
        elif self.dtype != other.dtype:
            raise TypeError(
                "Mismatch between dtype for input argument and class instance")
        return self._handle != other._handle

    def __str__(self):
        proj_dict = self.to_dict()
        proj_string = '\n'.join(
            [f"    {item:6s}:  {proj_dict[item]}" for item in proj_dict])
        return proj_string

    def __repr__(self):
        return "<class 'geostack.core.%s>'\n%s" % (self.__class__.__name__, str(self))


def convert(coordinate_input: Union["vector.Coordinate",
                                    "vector.CoordinateVector"],
            proj_to: Union[str, "ProjectionParameters"],
            proj_from: Union[str, "ProjectionParameters"],
            dtype: np.dtype = REAL) -> Optional[Union[np.ndarray, "vector.Coordinate"]]:
    """convert input coordinate from source projection to an output projection

    This function converts the projection of co-ordinate in-place, i.e. the value of the
    input co-ordinate is changed from projection from "proj_from" to a projection "proj_to".

    Parameters
    ----------
    coordinate_input: Coordinate
        Am instance of coordinate class in vector module
    proj_to: str/ProjectionParameters
        A proj4 string or an instance of ProjectionParameters
    proj_from: str/ProjectionParameters
        A proj4 string or an instance of ProjectionParameters

    Returns
    -------
    out: bool
        Returns True if coordinate converted else False.

    Examples
    --------
    >>> proj_to = ProjectionParameters.from_proj4(EPS4283)
    >>> proj_from = ProjectionParameters.from_proj4(EPSG3111)
    >>> c0 = [144.9631, -37.8136]
    >>> input_coordinate = Coordinate(p=c0[0], q=c0[1])
    >>> out = convert(input_coordinate, proj_to, proj_from)
    """
    if not isinstance(proj_to, (str, ProjectionParameters, dict)):
        raise TypeError(
            "proj_to is not str or instance of ProjectionParameters")
    if not isinstance(proj_from, (str, ProjectionParameters, dict)):
        raise TypeError(
            "proj_from is not of string or instance of ProjectionParameters")

    _proj_to = proj_to
    _proj_from = proj_from

    assert isinstance(_proj_from, (str, ProjectionParameters)), "destination projection type is not valid"
    assert isinstance(_proj_to, (str, ProjectionParameters)), "source projection type is not valid"

    if isinstance(coordinate_input, list):
        if check_list_type(coordinate_input) == 1:
            if isinstance(coordinate_input[0], numbers.Real):
                _c = vector.Coordinate(p=dtype(coordinate_input[0]),
                                       q=dtype(coordinate_input[1]))
            else:
                raise TypeError("list doesn't contain real numbers")
        elif check_list_type(coordinate_input) == 2:
            _c = np.array(coordinate_input, dtype=dtype)
    elif isinstance(coordinate_input, np.ndarray):
        _c = coordinate_input
    elif isinstance(coordinate_input, vector.Coordinate):
        _c = coordinate_input
    elif isinstance(coordinate_input, vector.CoordinateVector):
        _c = coordinate_input

    out = None

    if isinstance(_c, vector.Coordinate):
        if isinstance(_proj_from, str) and isinstance(_proj_to, str):
            if _c._dtype == np.float32:
                out = _convert_f_str(_c._handle, _proj_to, _proj_from)
            elif _c._dtype == np.float64:
                out = _convert_d_str(_c._handle, _proj_to, _proj_from)
        else:
            if _c._dtype == np.float32:
                out = _convert_f(_c._handle, _proj_to._handle, _proj_from._handle)
            elif _c._dtype == np.float64:
                out = _convert_d(_c._handle, _proj_to._handle, _proj_from._handle)
        return out
    elif isinstance(_c, np.ndarray):
        if isinstance(_proj_from, str) and isinstance(_proj_to, str):
            if _c.dtype == np.float32:
                out = _convert_points_f_str(_c, _proj_to, _proj_from)
            elif _c.dtype == np.float64:
                out = _convert_points_d_str(_c, _proj_to, _proj_from)
        else:
            if _c.dtype == np.float32:
                out = _convert_points_f(_c, _proj_to._handle, _proj_from._handle)
            elif _c.dtype == np.float64:
                out = _convert_points_d(_c, _proj_to._handle, _proj_from._handle)
        return np.asanyarray(out)
    elif isinstance(_c, vector.CoordinateVector):
        if isinstance(_proj_from, str) and isinstance(_proj_to, str):
            if _c._dtype == np.float32:
                _convert_pointvector_f_str(_c._handle, _proj_to, _proj_from)
            elif _c._dtype == np.float64:
                _convert_pointvector_d_str(_c._handle, _proj_to, _proj_from)
        else:
            if _c._dtype == np.float32:
                _convert_pointvector_f(_c._handle, _proj_to._handle, _proj_from._handle)
            elif _c._dtype == np.float64:
                _convert_pointvector_d(_c._handle, _proj_to._handle, _proj_from._handle)
    else:
        return out
