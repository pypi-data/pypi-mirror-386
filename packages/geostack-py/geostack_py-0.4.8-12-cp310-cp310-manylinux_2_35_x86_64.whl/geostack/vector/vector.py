# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
from io import StringIO
import json
import numpy as np
import numpy.typing as npt
from copy import deepcopy
from typing import Union, List, Iterable, Dict, Tuple, Optional, Any
from itertools import accumulate, chain, repeat
import numbers
from functools import partial, singledispatchmethod
import warnings
import ctypes
from ._cy_vector import (_Coordinate_d,
                         _Coordinate_f,
                         _Vector_d, _RTree_d, _KDTree_d,
                         _Vector_f, _RTree_f, _KDTree_f,
                         triangles_to_indices_f,
                         triangles_to_indices_d)
from ._cy_vector import IndexList as _IndexList
from ._cy_vector import _BoundingBox_d, _BoundingBox_f
from ._cy_vector import _CoordinateVector_d, _CoordinateVector_f
from ._cy_vector import _VectorPtrList_d, _VectorPtrList_f
from .. import io
from .. import core
from .. import gs_enums
from ..raster import raster
from .. import utils
from .. import writers
from .. import readers
from ..dataset import supported_libs
from pathlib import PurePath

fiona, _ = supported_libs.import_or_skip("fiona")
shapefile, _ = supported_libs.import_or_skip("shapefile")
ogr, _ = supported_libs.import_or_skip("ogr", package="osgeo")

if supported_libs.HAS_GPD:
    import geopandas as gpd

__all__ = ["Coordinate", "Vector", "BoundingBox",
           "IndexList", "RTree", "KDTree", "CoordinateVector",
           "IndexList", "RTree", "KDTree", 'VectorPtrList']


class RTree:
    def __init__(self, dtype: np.dtype = core.REAL) -> None:
        if dtype == np.float32:
            self._handle = _RTree_f()
        elif dtype == np.float64:
            self._handle = _RTree_d()
        else:
            raise ValueError("dtype should be np.float32/np.float64")
        self._dtype = dtype

    @property
    def dtype(self) -> np.dtype:
        """get the datatype of RTree object

        Returns
        -------
        np.dtype
            data type of RTree
        """
        return self._dtype

    def insert(self, v: Vector, idx: int) -> None:
        """insert a vector geometry into RTree

        Parameters
        ----------
        v : Vector
            a Vector object
        idx : int
            index of Vector geometry to be inserted
        """
        self._handle.insert(v._handle, idx)

    def search(self, bbox: BoundingBox, gtypes: gs_enums.GeometryType) -> np.ndarray:
        """search geometry types enclosed in the BoundingBox within the RTree

        Parameters
        ----------
        bbox : BoundingBox
            BoundingBox used for searching vector geometries
        gtypes : gs_enums.GeometryType
            geometry types to be searched

        Returns
        -------
        np.ndarray
            a ndarray with geometry id
        """
        out = self._handle.search(bbox._handle, gtypes)
        return np.asanyarray(out)

    def nearest(self, bbox: BoundingBox, gtypes: gs_enums.GeometryType) -> np.ndarray:
        """geometry types nearest to the BoundingBox within the RTree

        Parameters
        ----------
        bbox : BoundingBox
            BoundingBox used for finding nearest vector geometries
        gtypes : gs_enums.GeometryType
            geometry types to be searched

        Returns
        -------
        np.ndarray
            a ndarray with geometry id
        """
        out = self._handle.nearest(bbox._handle, gtypes)
        return np.asanyarray(out)

    def getBounds(self) -> BoundingBox:
        """get bounds of RTree

        Returns
        -------
        BoundingBox
            a BoundingBox object
        """
        out = BoundingBox(input_bbox=self._handle.getBounds(),
                          dtype=self._dtype)
        return out

    def clear(self) -> None:
        """clear RTree object
        """
        self._handle.clear()

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % (self.__class__.__name__)

class KDTree:
    def __init__(self, v: Vector=None, idxs: npt.ArrayLike = None, dtype: np.dtype = core.REAL) -> None:
        if dtype not in (np.float32, np.float64):
            raise ValueError("dtype should be np.float32/np.float64")

        if v is not None:
            v = v._handle
            if dtype == np.float32:
                kdtreeHandle = _KDTree_f
            elif dtype == np.float64:
                kdtreeHandle = _KDTree_d
            if idxs is None:
                self._handle = kdtreeHandle(v)
            else:
                self._handle = kdtreeHandle(v, np.asanyarray(idxs, np.uint32))
        self._dtype = dtype

    @property
    def dtype(self) -> np.dtype:
        """get the datatype of this KDTree object

        Returns
        -------
        np.dtype
            data type of KDTree
        """
        return self._dtype

    def build(self, v: Vector, idxs: npt.ArrayLike = None) -> None:
        """build this KDTree from the geometries of v with indices of idxs

        Parameters
        ----------
        v : Vector
            a Vector object
        idxs: Iterable[numbers.Integral]
            geometry indices on which to build this KDTree from
        """
        if idxs is None:
            self._handle.build(v._handle)
        else:
            self._handle.buildWithIndexes(v._handle, np.asanyarray(idxs, np.uint32))

    def nearest(
        self,
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster],
        *,
        search_strategy: gs_enums.SearchStrategy = gs_enums.SearchStrategy.AllVertices,
        idx: numbers.Integral = None,
        idxs: npt.ArrayLike[numbers.Integral] = None,
        proj: core.ProjectionParameters = None
    ) -> np.uint32:
        """find the nearest geometry from the KDTree

        Parameters
        ----------
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster]
        - Coordinate: the coordinate is directly used in the search. Can
        optionally specify `proj`, otherwise is assumed to adopt this KDTree's
        projection
        - Vector: the vertices of the vector geometries are used. Can optionally
        specify `idx` or `idxs` to determine which particular geometry(ies) used
        - BoundingBox: the centroid is used. Can optionally specify `proj`,
        otherwise is assumed to adopt this KDTree's projection
        - Raster: the vertices of the footprint are used

        search_strategy: gs_enums.SearchStrategy
            The strategy when searching for the geometries nearest a query vector.
            For gs_enums.SearchStrategy.AllVertices (default), the result will
            be a single geometry that is nearest any vertex of the query vector.
            For gs_enums.SearchStrategy.ByVertex, the result will be a list of geometries,
            each one nearest a Point in the query vector. The LineStrings and Polygons in
            the query vector are ignored.

        idx: numbers.Integeral
            The geom id of the vector geometry

        idxs: npt.ArrayLike[numbers.Integral]
            The geom ids of the vector geometries

        proj: core.ProjectionParameters
            The projection of `obj`

        Returns
        -------
        np.uint32
            the geometry id of the nearest geometry
        """
        if isinstance(obj, Coordinate):
            if proj is None:
                return self._handle.nearestFromCoord(obj._handle)
            return self._handle.nearestFromCoordProj(obj._handle, proj._handle)
        if isinstance(obj, Vector):
            if idxs is not None:
                return self._handle.nearestFromGeoms(obj._handle, idxs)
            if idx is not None:
                return self._handle.nearestFromGeom(obj._handle, idx)
            return self._handle.nearestFromVec(obj._handle, search_strategy)
        if isinstance(obj, BoundingBox):
            if proj is None:
                return self._handle.nearestFromBBox(obj._handle)
            return self._handle.nearestFromBBoxProj(obj._handle, proj._handle)
        if isinstance(obj, raster.Raster):
            return self._handle.nearestFromRaster(obj._handle)
        raise TypeError(f"Invalid type {type(obj)}")

    def nearestN(
        self,
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster],
        n: numbers.Integral,
        *,
        idx: numbers.Integral = None,
        idxs: npt.ArrayLike[numbers.Integral] = None,
        proj: core.ProjectionParameters = None
    ) -> npt.NDArray[np.uint32]:
        """find the nearest `n` geometries from the KDTree

        Parameters
        ----------
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster]
        - Coordinate: the coordinate is directly used in the search. Can
        optionally specify `proj`, otherwise is assumed to adopt this KDTree's
        projection
        - Vector: the vertices of the vector geometries are used. Can optionally
        specify `idx` or `idxs` to determine which particular geometry(ies) used
        - BoundingBox: the centroid is used. Can optionally specify `proj`,
        otherwise is assumed to adopt this KDTree's projection
        - Raster: the vertices of the footprint are used

        n: numbers.Integral
            Number of nearest geometries

        idx: numbers.Integeral
            The geom id of the vector geometry

        idxs: npt.ArrayLike[numbers.Integral]
            The geom ids of the vector geometries

        proj: core.ProjectionParameters
            The projection of `obj`

        Returns
        -------
        npt.NDArray[np.uint32]
            an ndarray of geometry ids of the nearest geometries
        """
        out = None
        if isinstance(obj, Coordinate):
            if proj is None:
                out = self._handle.nearestNFromCoord(obj._handle, n)
            else:
                out = self._handle.nearestNFromCoordProj(obj._handle, n, proj._handle)
        elif isinstance(obj, Vector):
            if idxs is not None:
                out = self._handle.nearestNFromGeoms(obj._handle, n, idxs)
            if idx is not None:
                out = self._handle.nearestNFromGeom(obj._handle, n, idx)
            out = self._handle.nearestNFromVec(obj._handle, n)
        elif isinstance(obj, BoundingBox):
            if proj is None:
                out = self._handle.nearestNFromBBox(obj._handle, n)
            else:
                out = self._handle.nearestNFromBBoxProj(obj._handle, n, proj._handle)
        elif isinstance(obj, raster.Raster):
            out = self._handle.nearestNFromRaster(obj._handle, n)
        if out is not None:
            return np.asanyarray(out)
        raise TypeError(f"Invalid type {type(obj)}")

    def getGeomCount(self) -> numbers.Integral:
        """get the number of geometries stored
        """
        return self._handle.getGeomCount()

    def getNodeCount(self) -> numbers.Integral:
        """get the number of nodes stored
        """
        return self._handle.getNodeCount()

    def getProjectionParameters(self) -> core.ProjectionParameters:
        """get the projection
        """
        return self._handle.getProjectionParameters()

    def print(self, indentAmount: numbers.Integral=None) -> None:
        """print the KDTree

        Parameters
        ----------
        indentAmount : numbers.Integral
            Indentation increase per level.
        """
        if indentAmount is None:
            self._handle.print()
        else:
            self._handle.printWithIndent(indentAmount)

    def clear(self) -> None:
        """clear KDTree object
        """
        self._handle.clear()

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % (self.__class__.__name__)


class CoordinateVector:
    def __init__(self, dtype: Optional[np.dtype] = core.REAL) -> None:
        self._dtype = dtype
        if dtype == np.float32:
            self._handle = _CoordinateVector_f()
        elif dtype == np.float64:
            self._handle = _CoordinateVector_d()

    def from_array(self, inp: np.ndarray) -> None:
        if isinstance(inp, np.ndarray):
            points = inp.astype(self._dtype)
        else:
            raise TypeError("Input should be list/ np.ndarray")

        if points.ndim == 2 and points.shape[1] >= 2:
            _points = points.copy()
            for _ in range(4 - points.shape[1]):
                _points = np.c_[_points, np.zeros(
                    points.shape[0], dtype=self._dtype)]
        else:
            raise TypeError("If a numpy array is provided, it should be of" +
                            " shape npoints x 2 is expected")
        self._handle.from_array(_points)

    def to_array(self) -> np.ndarray:
        out = self._handle.to_array()
        return np.asanyarray(out)

    @property
    def size(self) -> int:
        return self._handle.size

    def __len__(self) -> int:
        return self._handle.__len__()

    def clear(self) -> None:
        """clear CoordinateVector object
        """
        self._handle.__dealloc__()

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % (self.__class__.__name__)


class IndexList:
    def __init__(self, index_list: Union['IndexList', '_IndexList']):
        if not isinstance(index_list, (_IndexList, IndexList)):
            raise TypeError(
                "index_list should be an instance of cython index list")
        if isinstance(index_list, _IndexList):
            self._handle = index_list
        elif isinstance(index_list, IndexList):
            self._handle = index_list._handle

    @property
    def size(self) -> numbers.Integral:
        return self._handle.size

    def as_array(self) -> np.ndarray:
        return np.asanyarray(self._handle.as_array())

    def __contains__(self, idx) -> bool:
        return self._handle.contains(idx)

    def __iter__(self):
        return iter(self._handle)

    def __next__(self):
        return next(self._handle)

    def __getitem__(self, index):
        return self._handle[index]

    def __len__(self) -> numbers.Integral:
        return len(self._handle)

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % (self.__class__.__name__)


class Coordinate:
    def __init__(self, p: Optional[Union[numbers.Real, float]] = None,
                 q: Optional[Union[numbers.Real, float]] = None,
                 r: Optional[Union[numbers.Real, float]] = None,
                 s: Optional[Union[numbers.Real, float]] = None,
                 coordinate: 'Coordinate' = None,
                 dtype: np.dtype = core.REAL):
        '''Coordinate class wrapper for c++ object.

        Parameters
        ----------
        p: float, Optional, default is None
            x-axis coordinate
        q: float, Optional, default is None
            y-axis coordinate
        r: float, Optional, default is None
            z-axis coordinate
        s: float, Optional, default is None
            t-axis coordinate
        coordinate: Coordinate, Optional, default is None
            an instance of Coordinate object
        dtype: np.dtype, Optional, default is np.float32
            data type for Coordinate object, [np.float32, np.float64]

        Returns
        -------
        Coordinate
            Instance of coordinate object


        Examples
        --------
        >>> # when no argument specified
        >>> c0 = Coordinate()

        >>> # when p, q are specified
        >>> c1 = Coordinate(p=130.0, q=-34.0, dtype=np.float32)

        >>> # when a Coordinate object is specified
        >>> c2 = Coordinate(coordinate=c1)
        '''

        self._handle: Optional[Union[_Coordinate_d, _Coordinate_f]]
        self._dtype: Optional[np.dtype]

        if coordinate is not None:
            # from a coordinate object
            if isinstance(coordinate, Coordinate):
                if coordinate._dtype == np.float32:
                    self._handle = _Coordinate_f(cc=coordinate._handle)
                elif coordinate._dtype == np.float64:
                    self._handle = _Coordinate_d(cc=coordinate._handle)
                self._dtype = coordinate._dtype
            elif isinstance(coordinate, _Coordinate_d):
                self._handle = _Coordinate_d(cc=coordinate)
                self._dtype = np.float64
            elif isinstance(coordinate, _Coordinate_f):
                self._handle = _Coordinate_f(cc=coordinate)
                self._dtype = np.float32
        elif all(map(lambda s: s is not None, [p, q])):
            # from p,q,r,s
            if dtype not in [float, np.float32, np.float64]:
                raise TypeError("dtype should be np.float32/np.float64")

            self._dtype = np.float32 if dtype in [
                float, np.float32] else np.float64

            check_none = lambda c: 0.0 if c is None else c
            _coords = list(map(self._dtype, map(check_none, [p, q, r, s])))

            if self._dtype == np.float64:
                self._handle = _Coordinate_d(_coords[0], _coords[1],
                                             _coords[2], _coords[3])
            elif self._dtype == np.float32:
                self._handle = _Coordinate_f(_coords[0], _coords[1],
                                             _coords[2], _coords[3])
        elif all(map(lambda s: s is None, [p, q, r, s])):
            # when no value for p,q,r,s specified
            self._handle = None
            self._dtype = None

    @staticmethod
    def _from_coordinate(inp_coordinate):
        """Instantiate Coordinate object from a Cython object.

        Parameters
        ----------
        inp_coordinate : _Coordinate_f/ _Coordinate_d
            An instance of float or double type Coordinate object.

        Returns
        -------
        out: Coordinate
            An instance of Python Coordinate object
        """
        if isinstance(inp_coordinate, _Coordinate_d):
            out = Coordinate()
            out._dtype = np.float64
            out._handle = inp_coordinate
        elif isinstance(inp_coordinate, _Coordinate_f):
            out = Coordinate()
            out._dtype = np.float32
            out._handle = inp_coordinate
        elif isinstance(inp_coordinate, Coordinate):
            return Coordinate._from_coordinate(inp_coordinate._handle)
        else:
            raise TypeError(f"{inp_coordinate} is not of valid type")
        return out

    @staticmethod
    def from_list(other: List, dtype: np.dtype = core.REAL) -> "Coordinate":
        if not isinstance(other, list):
            raise TypeError("input argument should be a list")
        if len(other) < 2:
            raise ValueError("length of input list should be at least 2")
        _other = deepcopy(other)
        _other.extend([0] * (4 - len(other)))
        if dtype == np.float32:
            return Coordinate._from_coordinate(_Coordinate_f.from_list(_other))
        elif dtype == np.float64:
            return Coordinate._from_coordinate(_Coordinate_d.from_list(_other))

    def getCoordinate(self) -> Tuple[float, float]:
        '''get the coordinates of the object

        Parameters
        ----------
        Nil

        Returns
        -------
        out: tuple of coordinate (p, q)

        Examples
        --------
        >>> c = Coordinate(p=130.0, q=-34.0)
        >>> c.getCoordinate()
        (130.0, -34.0)
        '''
        if hasattr(self, "_handle"):
            return self._handle.getCoordinate()
        else:
            raise AttributeError("Coordinate class is not yet initialized")

    def maxCoordinate(self, this: "Coordinate", other: "Coordinate") -> "Coordinate":
        """Instantiate Coordinate object with the maximum of two input coordinates.

        Parameters
        ----------
        this : Coordinate
            An instance of Coordinate object
        other : Coordinate
            An instance of Coordinate object

        Returns
        -------
        out : Coordinate
            A Coordinate instance with the maximum of the input Coordinates

        Raises
        ------
        TypeError
            Type mismatch between two input coordinates
        RuntimeError
            Input Coordinate not initialized
        TypeError
            Input arguments should be instance of coordinates
        """
        assert self._handle is not None, "Coordinate is not instantiated"
        if isinstance(this, Coordinate) and isinstance(other, Coordinate):
            if this._handle is not None or other._handle is not None:
                raise RuntimeError("input coordinates are not initialized")
            assert self._dtype == this._dtype == other._dtype, "data type mismatch"
            return Coordinate._from_coordinate(self._handle.maxCoordinate(this._handle,
                                                                          other._handle))
        else:
            raise TypeError("Input argument should be instance of Coordinate")

    def minCoordinate(self, this: "Coordinate", other: "Coordinate") -> "Coordinate":
        """Instantiate Coordinate object with the minimum of two input coordinates.

        Parameters
        ----------
        this : Coordinate
            An instance of Coordinate object
        other : Coordinate
            An instance of Coordinate object

        Returns
        -------
        out : Coordinate
            A Coordinate instance with the minimum of the input Coordinates

        Raises
        ------
        TypeError
            Type mismatch between two input coordinates
        RuntimeError
            Input Coordinate not initialized
        TypeError
            Input arguments should be instance of coordinates
        """
        assert self._handle is not None, "Coordinate is not instantiated"
        if isinstance(this, Coordinate) and isinstance(other, Coordinate):
            if this._handle is not None or other._handle is not None:
                raise RuntimeError("input coordinates are not initialized")
            assert self._dtype == this._dtype == other._dtype, "datatype mismatch"
            return Coordinate._from_coordinate(self._handle.minCoordinate(this._handle,
                                                                          other._handle))
        else:
            raise TypeError("Input argument should be instance of Coordinate")

    def centroid(self, this: "Coordinate", other: "Coordinate") -> "Coordinate":
        """Instantiate Coordinate object with the centroid of two input coordinates

        Parameters
        ----------
        this : Coordinate
            An instance of Coordinate object
        other : Coordinate
            An instance of Coordinate object

        Returns
        -------
        out : Coordinate
            A Coordinate instance with the centroid of the input Coordinates

        Raises
        ------
        TypeError
            Type mismatch between two input coordinates
        RuntimeError
            Input Coordinate not initialized
        TypeError
            Input arguments should be instance of coordinates
        """
        assert self._handle is not None, "Coordinate is not instantiated"
        if isinstance(this, Coordinate) and isinstance(other, Coordinate):
            if this._handle is not None or other._handle is not None:
                raise RuntimeError("input coordinates are not initialized")
            assert self._dtype == this._dtype == other._dtype, "datatype mismatch"
            return Coordinate._from_coordinate(
                self._handle.centroid(this._handle, other._handle))
        else:
            raise TypeError("Input argument should be instance of Coordinate")

    def magnitudeSquared(self) -> numbers.Real:
        if self._handle is not None:
            return self._handle.magnitudeSquared()

    def to_wkt(self) -> str:
        """convert a Coordinate object to a wkt string

        Returns
        -------
        str
            a wkt formatted string
        """

        # create a point wkt from Coordinate
        coord_wkt = f"""POINT (({self.p} {self.q}))"""
        return coord_wkt

    @property
    def p(self) -> numbers.Real:
        return self._handle.get_p()

    @p.setter
    def p(self, other: numbers.Real):
        self._handle.set_p(other)

    @property
    def q(self) -> numbers.Real:
        return self._handle.get_q()

    @q.setter
    def q(self, other: numbers.Real):
        self._handle.set_q(other)

    @property
    def r(self) -> numbers.Real:
        return self._handle.get_r()

    @r.setter
    def r(self, other: numbers.Real):
        self._handle.set_r(other)

    @property
    def s(self) -> numbers.Real:
        return self._handle.get_s()

    @s.setter
    def s(self, other: numbers.Real):
        self._handle.set_s(other)

    def to_list(self) -> List:
        return self._handle.to_list()

    def _check_type(self, other):
        if not isinstance(other, Coordinate):
            raise TypeError(
                "input argument should be an instance of Coordinate")
        assert type(self._handle) == type(other._handle), "datatype mismatch"

    def getGeoHash(self) -> str:
        return self._handle.getGeoHash()

    def __eq__(self, other: "Coordinate") -> bool:
        self._check_type(other)
        out = self._handle == other._handle
        return out

    def __ne__(self, other: "Coordinate") -> bool:
        self._check_type(other)
        out = self._handle != other._handle
        return out

    def __add__(self, other: "Coordinate"):
        self._check_type(other)
        out = self._handle + other._handle
        return Coordinate._from_coordinate(out)

    def __iadd__(self, other: "Coordinate"):
        self._check_type(other)
        self._handle = self._handle + other._handle

    def __sub__(self, other: "Coordinate"):
        self._check_type(other)
        out = self._handle - other._handle
        return Coordinate._from_coordinate(out)

    def __isub__(self, other: "Coordinate"):
        self._check_type(other)
        self._handle = self._handle - other._handle

    def __getitem__(self, idx: Union[List, numbers.Integral]) -> Union[List, numbers.Real]:
        if isinstance(idx, int):
            if idx > 3:
                raise IndexError(f"Index {idx} should be in range[0, 3]")
            return self._handle[idx]
        elif isinstance(idx, (list, tuple)):
            return [self._handle[item] for item in filter(lambda s: s < 3 and s >= 0, idx)]
        elif isinstance(idx, slice):
            return self.to_list()[idx]

    def __setitem__(self, idx: numbers.Integral, val: numbers.Real):
        idx_map = {i: prop for i, prop in enumerate(['p', 'q', 'r', 's'])}
        if isinstance(idx, int):
            if idx > 3 or idx < 0:
                raise IndexError(f"Index {idx} should be in range[0, 3]")
            setattr(self, idx_map[idx], val)
        else:
            raise NotImplementedError(
                "set item is only implemented for integer indices")

    def __setstate__(self, ds: Dict) -> None:
        self.__init__(*ds.get('coordinates'),
                      dtype=ds.get('dtype'))

    def __getstate__(self) -> Dict:
        state = {
            'dtype': self._dtype,
            "coordinates": self.to_list()
        }
        return state

    def __repr__(self):
        return "<class 'geostack.vector.%s'>\n    %s>" % (self.__class__.__name__,
                                                          str(self.to_list()))


class BoundingBox:
    """BoundingBox class for cython wrapper to c++ object
    """

    def __init__(self, input_bbox: 'BoundingBox' =None,
                 min_coordinate: 'Coordinate' = None,
                 max_coordinate: 'Coordinate' = None,
                 dtype: np.dtype = core.REAL):
        """BoundingBox constructor.

        Parameters
        ----------
        input_bbox: None/BoundingBox/_BoundingBox_d/_BoundingBox_f/list
            input bounding box, either None for an empty box, an existing
            BoundingBox object or a list of coordinates
        min_coordinate: Coordinate, Optional, default is None
            a Coordinate object with coordinates for lower left corner
        max_coordinate: Coordinate, Optional, default is None
            a Coordinate object with coordinates for upper right corner
        dtype: np.dtype (np.float32/np.float64)
            data type of bounding box.

        Returns
        -------
        out: BoundingBox
            An instance of BoundingBox object.

        Examples
        --------
        >>> # no input argument specified
        >>> bbox = BoundingBox(dtype=np.float32)

        >>> # with coordinates for lower left and upper right corner
        >>> c0 = Coordinate(0.0, 0.0)
        >>> c1 = Coordinate(1.0, 1.0)
        >>> b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)

        >>> # with bounding box
        >>> b2 = BoundingBox(input_bbox=b1)
        """
        if all(map(lambda s: s is None, [input_bbox, min_coordinate, max_coordinate])):
            # Create empty bounding box
            self._handle = None
            self._dtype: np.dtype = None
            if dtype == np.float32:
                self._handle = _BoundingBox_f()
                self._dtype = np.float32
            elif dtype == np.float64:
                self._handle = _BoundingBox_d()
                self._dtype = np.float64
        elif isinstance(input_bbox, (BoundingBox, _BoundingBox_f, _BoundingBox_d)):
            # Create from bounding box
            if isinstance(input_bbox, BoundingBox):
                obj = self.from_bbox(input_bbox)
                self._handle = obj._handle
                self._dtype = obj._dtype
            else:
                if dtype == np.float32:
                    self._handle = _BoundingBox_f(bb=input_bbox)
                elif dtype == np.float64:
                    self._handle = _BoundingBox_d(bb=input_bbox)
                self._dtype = dtype
        elif all(map(lambda s: s is not None, [min_coordinate, max_coordinate])):
            # create from Coordinates
            if all(map(lambda s: isinstance(s, Coordinate), [min_coordinate, max_coordinate])):
                obj = self.from_coordinates(min_coordinate=min_coordinate,
                                            max_coordinate=max_coordinate)
                self._handle = obj._handle
                self._dtype = obj._dtype
            elif all(map(lambda s: isinstance(s, _Coordinate_d) or isinstance(s, _Coordinate_f),
                         [min_coordinate, max_coordinate])):
                if dtype == np.float32:
                    self._handle = _BoundingBox_f(ll=min_coordinate, ur=max_coordinate)
                elif dtype == np.float64:
                    self._handle = _BoundingBox_d(ll=min_coordinate, ur=max_coordinate)
                self._dtype = dtype
        elif isinstance(input_bbox, list):
            # Create from list
            new_bbox = BoundingBox.from_list(input_bbox)
            self._handle = new_bbox._handle
            self._dtype = new_bbox._dtype
        else:
            raise TypeError(
                "input bounding box should be None, a BoundingBox or a list")

    @staticmethod
    def from_coordinates(min_coordinate: "Coordinate",
                         max_coordinate: "Coordinate") -> "BoundingBox":
        """Create a BoundingBox from Coordinates of lower left and upper right corner.

        Parameters
        ----------
        min_coordinate: Coordinate
            an instance of Coordinate for the lower left corner
        max_coordinate: Coordinate
            an instance of Coordinate for the lower left corner

        Returns
        -------
        BoundingBox
            an instance of BoundingBox
        """
        _handle = []
        for obj in [min_coordinate, max_coordinate]:
            if isinstance(obj, Coordinate):
                _handle.append(obj._handle)
                dtype = obj._dtype
            else:
                _handle.append(obj)
                dtype = np.float32 if isinstance(
                    obj, _Coordinate_f) else np.float64
        out = BoundingBox(min_coordinate=_handle[0],
                          max_coordinate=_handle[1], dtype=dtype)
        return out

    @staticmethod
    def from_bbox(input_bbox: "BoundingBox") -> "BoundingBox":
        """Intantiate BoundingBox from cython instance.

        A static method to generate a bounding box from cython instances
        of BoundingBox. It is provided as a convenience function and should
        not be needed for most of purposes.

        Parameters
        ----------
        input_bbox: _BoundingBox_d/_BoundingBox_f
            An instances of boundingbox classes implemented in cython
        """
        if isinstance(input_bbox, BoundingBox):
            _handle = input_bbox._handle
            dtype = input_bbox._dtype
        else:
            _handle = input_bbox
            dtype = np.float32 if isinstance(
                input_bbox, _BoundingBox_f) else np.float64
        out = BoundingBox(input_bbox=_handle, dtype=dtype)
        return out

    @staticmethod
    def from_list(input_bbox: List, dtype: np.dtype = core.REAL) -> "BoundingBox":
        """Instantiate a BoundingBox from a list of list of coordinate bounds.

        A static method to instantiate a bounding box from a list of list
        containing coordinate bounds of a box. This function is provided
        for convenience to generate a C++ instance of bounding box from
        python list.

        For instances, a bounding box can be *[[lower_left_x, lower_left_y],
        [upper_right_x, upper_right_y]]*, where *(lower_left_x, lower_left_y)*
        are the **x** and **y** coordinates of the lower left corner of the
        bounding box while *(upper_right_x, upper_right_y)* are the **x**, **y**
        coordinates of the upper right corner.


        Parameters
        ----------
        input_bbox: list
            input bounding box as a list of list

        dtype: np.dtype (np.float32/np.float64)
            Data type of bounding box
        """
        _input_bbox = deepcopy(input_bbox)
        for item in _input_bbox:
            item.extend([0] * (4 - len(item)))
        if dtype is None or dtype == np.float32:
            out = BoundingBox.from_bbox(_BoundingBox_f.from_list(_input_bbox))
        elif dtype == np.float64:
            out = BoundingBox.from_bbox(_BoundingBox_d.from_list(_input_bbox))
        return out

    def convert(self, dst_proj: Union["core.ProjectionParameters", str],
                src_proj: Union["core.ProjectionParameters", str]) -> "BoundingBox":
        """convert the BoundingBox from src_proj to a dst_proj

        Parameters
        ----------
        dst_proj: ProjectionParameters | str
            a ProjectionParameters object in desired projection

        src_proj: ProjectionParameters | str
            a ProjectionParameters object of the BoundingBox projection

        Returns
        -------
        BoundingBox
            a BoundingBox object after projection

        Raises
        ------
        TypeError
            src_proj should be an instance of ProjectionParameters
        TypeError
            dst_proj should be an instance of ProjectionParameters
        """
        if not isinstance(src_proj, (core.ProjectionParameters, str)):
            raise TypeError(
                "src_proj should be an instance of ProjectionParameters/str")
        if not isinstance(dst_proj, (core.ProjectionParameters, str)):
            raise TypeError(
                "dst_proj should be an instance of ProjectionParameters/str")

        out = BoundingBox(dtype=self._dtype)
        if isinstance(src_proj, str) and isinstance(dst_proj, str):
            out._handle = self._handle.convert_str(dst_proj, src_proj)
        else:
            out._handle = self._handle.convert(dst_proj._handle, src_proj._handle)
        return out

    def area2D(self) -> numbers.Real:
        """Compute 2D area of bounding box.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        out = self._handle.area2D()
        return out

    def centroidDistanceSqr(self, other: "BoundingBox") -> numbers.Real:
        """Compute squared distance between bounding box centroids.

        Parameters
        ----------
        other: BoundingBox
            An instance of BoundingBox class with a same dtype.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        if not isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            raise TypeError(
                "Input bounding box should be an instance of BoundingBox class")
        _other = other._handle if isinstance(other, BoundingBox) else other
        if isinstance(_other, _BoundingBox_d):
            assert isinstance(
                self._handle, _BoundingBox_d), "datatype mismatch"
        elif isinstance(_other, _BoundingBox_f):
            assert isinstance(
                self._handle, _BoundingBox_f), "datatype mismatch"
        out = self._handle.centroidDistanceSqr(_other)
        return out

    def minimumDistanceSqr(self, other: "BoundingBox") -> numbers.Real:
        """Compute minimum squared distance between bounding boxes.

        Parameters
        ----------
        other: BoundingBox
            An instance of BoundingBox class with a same dtype.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        if not isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            raise TypeError(
                "Input bounding box should be an instance of BoundingBox class")
        _other = other._handle if isinstance(other, BoundingBox) else other
        if isinstance(_other, _BoundingBox_d):
            assert isinstance(
                self._handle, _BoundingBox_d), "datatype mismatch"
        elif isinstance(_other, _BoundingBox_f):
            assert isinstance(
                self._handle, _BoundingBox_f), "datatype mismatch"
        out = self._handle.minimumDistanceSqr(_other)
        return out

    def extend2D(self, other: np.float32):
        """Extend the bounding box in 2D using input argument.

        Parameters
        ----------
        other: BoundingBox/float/Coordinate
            Input argument for extending the bounding box.
        """
        if isinstance(other, (Coordinate, _Coordinate_d, _Coordinate_f)):
            _other = other._handle if isinstance(other, Coordinate) else other
            self._handle.extend_with_coordinate_2d(_other)
        elif isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            _other = other._handle if isinstance(other, Coordinate) else other
            self._handle.extend_with_bbox_2d(_other)
        elif np.isscalar(other):
            self._handle.extend2D(core.REAL(other))
        else:
            raise TypeError("unable to deduce data type")

    def extend(self, other: "BoundingBox"):
        """Extend the bounding box using input argument.

        Parameters
        ----------
        other: BoundingBox/float/Coordinate
            Input argument for extending the bounding box.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        if isinstance(other, (Coordinate, _Coordinate_d, _Coordinate_f)):
            _other = other._handle if isinstance(other, Coordinate) else other
            if isinstance(_other, _Coordinate_d):
                assert self._dtype == np.float64, "datatype mismatch"
            elif isinstance(_other, _Coordinate_f):
                assert self._dtype == np.float32, "datatype mismatch"
            self._handle.extend_with_coordinate(_other)
        elif isinstance(other, numbers.Real):
            self._handle.extend_with_value(float(other))
        elif isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            _other = other._handle if isinstance(other, BoundingBox) else other
            if isinstance(_other, _BoundingBox_d):
                assert self._dtype == np.float64, "datatype mismatch"
            elif isinstance(_other, _BoundingBox_f):
                assert self._dtype == np.float32, "datatype mismatch"
            self._handle.extend_with_bbox(_other)
        else:
            raise TypeError(
                "other should be a float or an instance of Coordinate or BoundingBox")

    @property
    def centroid(self) -> "Coordinate":
        """Get the centroid of the bounding box.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        return Coordinate._from_coordinate(self._handle.centroid())

    @property
    def extent(self) -> "Coordinate":
        """Get the extent of the bounding box.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        return Coordinate._from_coordinate(self._handle.extent())

    @property
    def min(self) -> "Coordinate":
        """get the coordinate of lower left corner

        Returns
        -------
        Coordinate
            an instance of Coordinate
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        return Coordinate._from_coordinate(self._handle.min_c)

    @min.setter
    def min(self, other: "Coordinate") -> None:
        """change the minimum coordinate of the bounding box

        Parameters
        ----------
        other : Coordinate
            coordinate of lower left corner

        Raises
        ------
        TypeError
            argument should be an instance of Coordinate
        """
        if not isinstance(other, Coordinate):
            raise TypeError("argument should be an instance of Coordinate")
        self._handle.set_min(other._handle)

    @property
    def max(self) -> "Coordinate":
        """get the coordinate of upper right corner

        Returns
        -------
        Coordinate
            an instance of Coordinate
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        return Coordinate._from_coordinate(self._handle.max_c)

    @max.setter
    def max(self, other: "Coordinate") -> None:
        """change the maximum coordinate of the bounding box

        Parameters
        ----------
        other : Coordinate
            coordinate of upper right corner

        Raises
        ------
        TypeError
            argument should be an instance of Coordinate
        """
        if not isinstance(other, Coordinate):
            raise TypeError("argument should be an instance of Coordinate")
        self._handle.set_max(other._handle)

    def reset(self):
        """Reset the instantiation of the bounding box.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        self._handle.reset()

    def to_list(self) -> List:
        """Convert the bounding box to list of list of coordinates.
        """
        assert self._handle is not None, "BoundingBox is not instantiated"
        return self._handle.to_list()

    def to_wkt(self) -> str:
        """convert a bounding box object to a wkt string

        Returns
        -------
        str
            a wkt formatted string
        """
        return io.vectorItemToGeoWKT(self.toVector(), 0)

    def contains(self, other: 'Coordinate') -> bool:
        """check if Coordinate is within the BoundingBox

        Parameters
        ----------
        other : Coordinate
            a coordinate object

        Returns
        -------
        bool
            True if Coordinate in BoundingBox, False otherwise

        Raises
        ------
        TypeError
            input argument should be a Coordinate
        TypeError
            Type mismatch between BoundingBox and Coordinate
        """
        if not isinstance(other, Coordinate):
            raise TypeError("input argument should be a Coordinate")
        if self._dtype != other._dtype:
            raise TypeError("Type mismatch between BoundingBox and Coordinate")
        return self._handle.contains(other._handle)

    def toVector(self) -> 'Vector':
        """convert a bounding box to a Vector object

        Returns
        -------
        Vector
            a Vector object with a polygon geometry
        """
        return Vector._from_vector(self._handle.toVector())

    @staticmethod
    def boundingBoxIntersects(this: "BoundingBox", other: "BoundingBox") -> bool:
        """check if two bounding box intersect

        Parameters
        ----------
        this : BoundingBox
            first BoundingBox object
        other : BoundingBox
            second BoundingBox object

        Returns
        -------
        bool
            True if the BoundingBox intersect, False otherwise

        Raises
        ------
        TypeError
            input arguments should be a BoundingBox
        """
        if not isinstance(this, BoundingBox) or isinstance(other, BoundingBox):
            raise TypeError("input arguments should be a BoundingBox")
        assert this._dtype == other._dtype, "Type mismatch between input argument"
        if this._dtype == np.float32:
            return _BoundingBox_f.boundingBoxIntersects(this._handle,
                                                        other._handle)
        elif this._dtype == np.float64:
            return _BoundingBox_d.boundingBoxIntersects(this._handle,
                                                        other._handle)

    @staticmethod
    def boundingBoxContains(this: "BoundingBox",
                            other: Union["Coordinate", "BoundingBox"]) -> bool:
        """check if the BoundingBox contains a Coordinate (or BoundingBox) object

        Parameters
        ----------
        this : BoundingBox
            a BoundingBox object to check if it contains Coordinate
        other : Coordinate/ BoundingBox
            a Coordinate (or BoundingBox) object

        Returns
        -------
        bool
            True if the Coordinate (BoundingBox) is in BoundingBox, False otherwise

        Raises
        ------
        TypeError
            first argument should be a BoundingBox
        TypeError
            second argument should be a Coordinate/BoundingBox
        """
        if not isinstance(this, BoundingBox):
            raise TypeError("first argument should be a BoundingBox")
        if not isinstance(other, (Coordinate, BoundingBox)):
            raise TypeError(
                "second argument should be a Coordinate/BoundingBox")
        assert this._dtype == other._dtype, "Type mismatch between input argument"
        if this._dtype == np.float32:
            if isinstance(other, Coordinate):
                return _BoundingBox_f.bbox_contains_coordinate(this._handle,
                                                               other._handle)
            else:
                return _BoundingBox_f.bbox_contains_bbox(this._handle,
                                                         other._handle)
        elif this._dtype == np.float64:
            if isinstance(other, Coordinate):
                return _BoundingBox_d.bbox_contains_coordinate(this._handle,
                                                               other._handle)
            else:
                return _BoundingBox_d.bbox_contains_bbox(this._handle,
                                                         other._handle)

    def intersects(self, other: 'BoundingBox') -> bool:
        """check if the bounding box intersects the other bounding box

        Parameters
        ----------
        other : BoundingBox
            an instance of bounding box objects

        Returns
        -------
        bool
            True if the bounding box intersects, False otherwise
        """
        return self.boundingBoxIntersects(self, other)

    def quadrant(self, other: 'Coordinate') -> int:
        """get the containing quadrant of Coordinate within a BoundingBox.

        Parameters
        ----------
        other : Coordinate
            an instance of a Coordinate

        Returns
        -------
        int
            quadrant of the BoundingBox
        """
        if isinstance(other, Coordinate):
            return self._handle.quadrant(other._handle)
        elif isinstance(other, (_Coordinate_d, _Coordinate_f)):
            return self._handle.quadrant(other)

    def __eq__(self, other: 'BoundingBox') -> bool:
        return self._handle == other._handle

    def __ne__(self, other: 'BoundingBox') -> bool:
        return self._handle != other._handle

    def __contains__(self, other: Union['Coordinate', 'BoundingBox']) -> bool:
        return self.boundingBoxContains(self, other)

    def __getitem__(self, idx: Union[numbers.Integral, int]):
        if idx > 1:
            raise IndexError(f"Index {idx} should be in range [0,1]")
        return Coordinate._from_coordinate(self._handle[idx])

    def __str__(self):
        bounds_string = "    lower bound:   %s\n    upper bound:   %s" % tuple(
            map(str, self.to_list()))
        return bounds_string

    def __setstate__(self, ds: Dict) -> None:
        dispatcher = {
            np.float32: _BoundingBox_f,
            np.float64: _BoundingBox_d
        }
        self.__init__(dispatcher.get(ds.get('dtype'))(ds.get('bounds')),
                      dtype=ds.get('dtype'))

    def __getstate__(self) -> Dict:
        state = {
            'dtype': self._dtype,
            "bounds": self.to_list()
        }
        return state

    def __repr__(self):
        return "<class 'geostack.vector.%s'>\n%s" % (self.__class__.__name__, str(self))


class Vector:
    """Vector class python object around C++ Vector.

    Parameters
    ----------
    dtype : numpy.dtype
        Data type for instantiating Cython Vector object, (np.float32/np.float64).

    Attributes
    ----------
    _dtype : np.dtype
        Data type of Vector class object.

    _handle : Cython object
        Handle to Cython Vector object.

    """

    def __init__(self, input_vector: 'Vector' = None,
                 dtype: np.dtype = core.REAL):
        self._handle: Optional[Union[_Vector_d, _Vector_f]] = None
        self._dtype: Optional[np.dtype] = None
        if input_vector is None:
            if dtype not in [float, np.float32, np.float64]:
                raise TypeError("dtype should be np.float32/ np.float64")
            self._dtype = np.float32 if dtype in [
                float, np.float32] else np.float64
        else:
            assert isinstance(
                input_vector, Vector), "input vector should be a Vector object"
            self._dtype = input_vector._dtype

        if self._dtype == np.float32:
            if input_vector is not None:
                self._handle = _Vector_f(input_vector._handle)
            else:
                self._handle = _Vector_f()
        elif self._dtype == np.float64:
            if input_vector is not None:
                self._handle = _Vector_d(input_vector._handle)
            else:
                self._handle = _Vector_d()

    @staticmethod
    def assign(vec_obj: 'Vector') -> 'Vector':
        """assign an input Vector object to the instance Vector object.

        Parameters
        ----------
        vec_obj: Vector
            an instance of a Vector object.

        Returns
        -------
        Vector
            an instance of a Vector object with the copy of input object.
        """
        out = Vector(dtype=vec_obj._dtype)
        out._handle.assign(vec_obj._handle)
        return out

    @classmethod
    def _from_vector(cls, vec_obj):
        out = cls()
        _vec_obj = vec_obj._handle if isinstance(vec_obj, cls) else vec_obj
        if isinstance(_vec_obj, _Vector_d):
            out._dtype = np.float64
            out._handle = _vec_obj
        elif isinstance(_vec_obj, _Vector_f):
            out._dtype = np.float32
            out._handle = _vec_obj
        else:
            raise TypeError("vector_object can be an instance of Vector")
        return out

    def __copy__(self):
        return Vector(self, dtype=self._dtype)

    def __deepcopy__(self, memo):
        return Vector.assign(self)

    def addGeometry(self, other: "Vector", idx_: numbers.Integral) -> numbers.Integral:
        """add a geometry at a given index from the given vector object

        Parameters
        ----------
        other : Vector
            an instance of the source vector object
        idx_ : numbers.Integral
            index of geometry in the source vector object

        Returns:
        numbers.Integral
            index of the geometry in the destination vector object

        Raises
        ------
        TypeError
            input object should an instance of vector object
        """
        if not isinstance(other, Vector):
            raise TypeError("other should be an instance of Vector object")

        # if isinstance(other, Vector):
        #     geom_type = other.getGeometryType(idx_)

        #     get_method_map = {gs_enums.GeometryType.Point.value: other.getPoint,
        #                       gs_enums.GeometryType.LineString.value: other.getLineString,
        #                       gs_enums.GeometryType.Polygon.value: other.getPolygon}

        # elif isinstance(other, (_Vector_f, _Vector_d)):
        #     geom_type = gs_enums.GeometryType(other.get_geometry_type(idx_))

        # if not self.hasData():
        #     self += get_method_map.get(geom_type.value)(idx_)
        #     out = next(self.getGeometryIndexes())
        # else:
        #     if isinstance(other, Vector):
        #         assert other._dtype == self._dtype, "mismatch in datatype of vector object"
        #         out = self._handle.addGeometry(other._handle, idx_)
        #     else:
        #         out = self._handle.addGeometry(other, idx_)

        geom_type = other.getGeometryType(idx_)

        get_method_map = {gs_enums.GeometryType.Point.value: other.getPoint,
                          gs_enums.GeometryType.LineString.value: other.getLineString,
                          gs_enums.GeometryType.Polygon.value: other.getPolygon}

        self += get_method_map.get(geom_type.value)(idx_)
        out = self.getGeometryIndexes()
        out = out[out.size - 1]
        return out

    def addPoint(self, other: Union[List[numbers.Real], Tuple[numbers.Real], Coordinate]) -> numbers.Integral:
        """add point to a vector object

        Parameters
        ----------
        other : Union[List[numbers.Real], Tuple[numbers.Real], Coordinate]
            the coordinates of the point

        Returns
        -------
        numbers.Integral
            index of the point in the vector object

        Raises
        ------
        RuntimeWarning
            vector class is not yet initialised
        TypeError
            point should be a list/ tuple of maximum length 4
        TypeError
            vales in point should of float type
        TypeError
            point is not of a valid type
        """
        if self._dtype is None or self._handle is None:
            raise RuntimeWarning('Vector class is not yet initialized')
        if isinstance(other, (list, tuple)):
            if len(other) > 4:
                raise TypeError(
                    "point should be a list or tuple of maximum length 4")
            else:
                if not isinstance(other[0], numbers.Real):
                    raise TypeError("values in point should be of float type")
                else:
                    out = self._handle.addPoint(Coordinate.from_list(other,
                                                dtype=self._dtype)._handle)
                    return out
        elif isinstance(other, Coordinate):
            out = self._handle.addPoint(other._handle)
            return out
        else:
            raise TypeError("point is not of a valid type")

    def addPoints(self, other: Union[np.ndarray, List[List[numbers.Real]]]) -> List[numbers.Integral]:
        """add a list of points to the vector object

        Parameters
        ----------
        other : Union[np.ndarray, List[List[numbers.Real]]]
            a ndarray or list of list containing coordinates of points

        Returns
        -------
        List[numbers.Integral]
            a list of indices of the points in the vector object

        Raises
        ------
        TypeError
            input should be a list/ ndarray
        TypeError
            if a numpy array is provided, it should be of shape npoints x 2
        """
        if isinstance(other, np.ndarray):
            points = other.astype(self._dtype)
        elif isinstance(other, list):
            points = np.array(other, dtype=self._dtype)
        else:
            raise TypeError("Input should be list/ np.ndarray")
        if points.ndim == 2 and points.shape[1] >= 2:
            _points = points.copy()
            for _ in range(4 - points.shape[1]):
                _points = np.c_[_points, np.zeros(
                    points.shape[0], dtype=self._dtype)]
        else:
            raise TypeError("If a numpy array is provided, it should be of" +
                            " shape npoints x 2 is expected")
        out = self._handle.addPoints(_points)
        return np.asanyarray(out)

    def addLineString(self, other: Union[np.ndarray, List[List[numbers.Real]]]) -> numbers.Integral:
        """add line string to a vector object

        Parameters
        ----------
        other : Union[np.ndarray, List[List[numbers.Real]]]
            a ndarray or list of list with the coordinates for a line string

        Returns
        -------
        numbers.Integral
            index of linestring in the vector object

        Raises
        ------
        RuntimeWarning
            vector class is not yet initialised
        TypeError
            if a list is provided, it should ba list of list
        TypeError
            if a list is provided, ti should contain points as list of length atleast 2
        TypeError
            if a numpy array is provided, it should be of shape npoints x 2
        """
        if self._dtype is None or self._handle is None:
            raise RuntimeWarning("Vector class is not yet initialized")
        if isinstance(other, list):
            if not isinstance(other[0], (list, tuple)):
                raise TypeError(
                    "If a list is provided, it should be a list of list/ or tuple")
            if len(other[0]) < 2:
                raise TypeError('If a list is provided, it should contain points' +
                                ' as list of length at least 2')
            _other = np.array(other).astype(self._dtype)
            for _ in range(4 - _other.shape[1]):
                _other = np.c_[_other, np.zeros(
                    _other.shape[0], dtype=self._dtype)]
            out = self._handle.addLineString(_other)
        elif isinstance(other, np.ndarray):
            if other.ndim == 2 and other.shape[1] >= 2:
                _other = other.copy().astype(self._dtype)
                for _ in range(4 - other.shape[1]):
                    _other = np.c_[_other, np.zeros(
                        _other.shape[0], dtype=self._dtype)]
                out = self._handle.addLineString(_other)
            else:
                raise TypeError("If a numpy array if provided, it should be of" +
                                " shape npoints x 2 is expected")
        return out

    def addPolygon(self, other: List[Union[List[List[numbers.Real]], np.ndarray]]) -> numbers.Integral:
        """add a polygon to a Vector object

        Parameters
        ----------
        other : List[Union[List[List[numbers.Real]], np.ndarray]]
            a list of lists/ np.ndarray with the coordinates for the polygon boundaries

        Returns
        -------
        numbers.Integral
            index of the polygon geometry in the vector object

        Raises
        ------
        RuntimeWarning
            Vector class is not yet initialized
        TypeError
            Polygon object should be a list of numpy array or list
        TypeError
            Polygon object should be a list of numpy array or list
        TypeError
            if a list of list is provided, the inner list should contain points as list of length atleast 2
        TypeError
            if a list of ndarray is provided, the inner ndarray should be of shape npoints x 2
        """
        if self._dtype is None or self._handle is None:
            raise RuntimeWarning("Vector class is not yet initialized")
        if not isinstance(other, list):
            raise TypeError(
                "Polygon object should be a list of numpy array or list")
        elif not isinstance(other[0], (list, np.ndarray)):
            raise TypeError(
                "Polygon object should be a list of numpy array or list")

        if isinstance(other[0], list):
            if len(other[0]) < 2:
                raise TypeError('If a list is provided, it should contain' +
                                ' points as list of length atleast 2')
        elif isinstance(other[0], np.ndarray):
            if other[0].ndim != 2 and other[0].shape[1] >= 2:
                raise TypeError("If a numpy array if provided, it should be" +
                                " of shape npoints x 2 is expected")

        _poly_item = []
        for item in other:
            if isinstance(item, list):
                _other = np.atleast_2d(item).astype(self._dtype)
                for _ in range(4 - _other.shape[1]):
                    _other = np.c_[_other,
                                   np.zeros(shape=(_other.shape[0], 1),
                                            dtype=self._dtype)]
            elif isinstance(item, np.ndarray):
                _other = item.copy().astype(self._dtype)
                for _ in range(4 - item.shape[1]):
                    _other = np.c_[_other,
                                   np.zeros(shape=(_other.shape[0], 1),
                                            dtype=self._dtype)]
            _poly_item.append(_other)
        out = self._handle.addPolygon(_poly_item)
        return out

    def updatePointIndex(self, index: numbers.Integral):
        self._handle.updatePointIndex(index)

    def updateLineStringIndex(self, index: numbers.Integral):
        self._handle.updateLineStringIndex(index)

    def updatePolygonIndex(self, index: numbers.Integral):
        self._handle.updatePolygonIndex(index)

    def clear(self):
        self._handle.clear()

    def buildTree(self):
        self._handle.buildTree()

    def buildKDTree(self):
        """re(build) a KDTree on the vector geometries
        """
        self._handle.buildKDTree()

    def getVertexSize(self) -> numbers.Integral:
        """get the size of vertices in the vector object

        Returns
        -------
        numbers.Integral
            number of vertices in the vector object
        """
        return self._handle.getVertexSize()

    def getGeometryIndexes(self) -> IndexList:
        """get the indices of geometries in the vector object

        Returns
        -------
        IndexList
            an instance of IndexList object
        """
        return IndexList(self._handle.getGeometryIndexes())

    def getPointIndexes(self) -> IndexList:
        """get the indices of point geometries in the vector object

        Returns
        -------
        IndexList
            an instance of IndexList object
        """
        return IndexList(self._handle.getPointIndexes())

    def getLineStringIndexes(self) -> IndexList:
        """get the indices of line string geometries in the vector object

        Returns
        -------
        IndexList
            an instance of IndexList object
        """
        return IndexList(self._handle.getLineStringIndexes())

    def getPolygonIndexes(self) -> IndexList:
        """get the indices of polygon geometries in the vector object

        Returns
        -------
        IndexList
            an instance of IndexList object
        """
        return IndexList(self._handle.getPolygonIndexes())

    def getPolygonSubIndexes(self, idx: int) -> IndexList:
        """get the sub-indices of polygon geometries in the vector object

        Returns
        -------
        IndexList
            an instance of IndexList object
        """
        return IndexList(self._handle.getPolygonSubIndexes(idx))

    def getCoordinate(self, idx: numbers.Integral, safe=utils.is_ipython()) -> "Coordinate":
        """method to get the coordinates of a vertex

        Parameters
        ----------
        idx : numbers.Integral
            index of a vertex in a vector object
        safe : False, optional
            flag to set the method to safe, by default is_ipython()

        Returns
        -------
        Coordinate
            an instance of Coordinate object with the coordinates of a vertex

        Raises
        ------
        IndexError
            index is not valid
        """
        if safe:
            vertex_size = self.getVertexSize()
            if idx < vertex_size:
                out = self._handle.getCoordinate(int(idx))
                return Coordinate._from_coordinate(out)
            else:
                raise IndexError(f"index {idx} not valid")
        else:
            if self._handle is not None:
                return Coordinate._from_coordinate(self._handle.getCoordinate(int(idx)))

    def getPointCoordinate(self, idx: numbers.Integral, safe: bool = utils.is_ipython()) -> "Coordinate":
        """get the coordinates of a point geometry

        Parameters
        ----------
        idx : numbers.Integral
            index of the point geometry
        safe : bool, optional
            flag to check in the index is valid for a point, by default is_ipython()

        Returns
        -------
        Coordinate
            The coordinates of the point geometry at the given index

        Raises
        ------
        IndexError
            point index is not valid
        """
        if safe:
            point_idx = self.getPointIndexes()
            if idx in point_idx:
                out = self._handle.getPointCoordinate(int(idx))
                return Coordinate._from_coordinate(out)
            else:
                raise IndexError(f"point index {idx} not valid")
        else:
            if self._handle is not None:
                return Coordinate._from_coordinate(self._handle.getPointCoordinate(int(idx)))

    def getLineStringCoordinates(self, idx: numbers.Integral,
                                 safe: bool = utils.is_ipython()) -> np.ndarray:
        """method to get the coordinates of the line string

        Parameters
        ----------
        idx : numbers.Integral
            index of the line string geometry
        safe : bool, optional
            flag to check whether the index is valid for a line string, by default is_ipython()

        Returns
        -------
        np.ndarray
            a ndarray with the coordinates of the line string

        Raises
        ------
        IndexError
            line string index is not valid
        """
        if safe:
            line_str_idx = self.getLineStringIndexes()
            if idx in line_str_idx:
                out = self._handle.getLineStringCoordinates(int(idx))
                return np.asanyarray(out)
            else:
                raise IndexError(f"line string index {idx} not valid")
        else:
            if self._handle is not None:
                out = self._handle.getLineStringCoordinates(int(idx))
                return np.asanyarray(out)

    def getPolygonArea(self, idx: numbers.Integral,
                       safe: bool = utils.is_ipython(),
                       method: 'str' = 'shoelace',
                       remove_holes: bool = False) -> float:
        """compute polygon area using shoelace method

        Parameters
        ----------
        idx : numbers.Integral
            _description_
        safe : bool, optional
            _description_, by default utils.is_ipython()
        remove_holes : bool, optional
            _description_, by default False

        Returns
        -------
        float
            _description_
        """
        def _calc_area(coords, method='shoelace') -> float:
            # shoelace formula
            x_coords = coords[:, 0]
            y_coords = coords[:, 1]
            if method == 'shoelace':
                area1 = x_coords * np.append(y_coords[1:], y_coords[0])
                area2 = y_coords * np.append(x_coords[1:], x_coords[0])
                out = abs(area1.sum() - area2.sum()) * 0.5
            elif method == 'greens':
                out = 0.5 * ((x_coords[1:] + x_coords[:-1]) *
                             (y_coords[1:] - y_coords[:-1])).sum()
            return out

        coords = self.getPolygonCoordinates(idx, safe=safe)
        first_polygon = coords[0]
        poly_area = _calc_area(first_polygon, method=method)

        if remove_holes:
            if len(coords) > 1:
                for i in range(1, len(coords)):
                    poly_area -= _calc_area(coords[i])

        return poly_area

    def getPolygonCoordinates(self, idx: numbers.Integral,
                              safe: bool = utils.is_ipython()) -> List[np.ndarray]:
        """method to get the coordinates of the polygon

        Parameters
        ----------
        idx : numbers.Integral
            index of the polygon geometry
        safe : bool, optional
            flag to check whether the index is valid for a polygon, by default is_ipython()

        Returns
        -------
        List[np.ndarray]
            a list of ndarray with polygon coordinates

        Raises
        ------
        IndexError
            polygon index is not valid
        """
        if safe:
            poly_idx = self.getPolygonIndexes()
            if idx in poly_idx:
                out = np.asanyarray(
                    self._handle.getPolygonCoordinates(int(idx)))
            else:
                raise IndexError(f"polygon index {idx} not valid")
        else:
            if self._handle is not None:
                out = np.asanyarray(
                    self._handle.getPolygonCoordinates(int(idx)))

        # get the sub indices
        sub_idx = self.getPolygonSubIndexes(idx)
        # convert array to list of array
        out = list(map(lambda start, end: out[end - start:end],
                       list(sub_idx), accumulate(sub_idx)))
        return out

    def __delitem__(self, name: Union[str, bytes]):
        self.removeProperty(name)

    def getPropertyType(self, name: Union[str, bytes]) -> Optional[type]:
        """returns type of property in the vector object

        Parameters
        ----------
        name : Union[str, bytes]
            name of the property

        Returns
        -------
        PropertyType
            the type of the property

        Raises
        ------
        TypeError
            property name should be of str/ bytes type
        """
        _prop_type = None
        if not isinstance(name, (str, bytes)):
            raise TypeError("property name should be of str/ bytes type")
        _prop_type = self._handle.getPropertyType(core.str2bytes(name))
        return core.PropertyType.to_pytype(_prop_type)

    def removeProperty(self, name: Union[str, bytes]) -> None:
        """remove a property to the vector object

        Parameters
        ----------
        name : Union[str, bytes]
            name of the property

        Raises
        ------
        TypeError
            property name should be of str/ bytes type
        """
        if not isinstance(name, (str, bytes)):
            raise TypeError("property name should be of str/ bytes type")
        self._handle.removeProperty(core.str2bytes(name))

    def addProperty(self, name: Union[str, bytes]) -> None:
        """add a property to the vector object

        Parameters
        ----------
        name : Union[str, bytes]
            name of the property

        Raises
        ------
        TypeError
            property name should be of str/ bytes type
        """
        if not isinstance(name, (str, bytes)):
            raise TypeError("property name should be of str/ bytes type")

        self._handle.addProperty(core.str2bytes(name))

    def __setitem__(self, name: Union[str, bytes],
                    propValue: Union[Iterable, np.ndarray]) -> None:
        self.setPropertyVector(name, propValue)

    def setPropertyVector(self, name: Union[str, bytes],
                          propValue: Union[Iterable, np.ndarray]) -> None:
        """set all the values of a property in a Vector object

        Parameters
        ----------
        name : Union[str, bytes]
            name of the property defined in a vector object
        propValue : Union[Iterable, np.ndarray]
            the values of the property

        Examples
        --------
        vec = Vector()
        vec.addPoint([1.0, 2.0])
        vec.addPoint([2.0, 2.0])
        vec.addPoint([3.0, 2.0])
        vec.addProperty("dummy")
        vec.setPropertyVector("dummy", [0.0, 0.0, 0.0])
        """

        # create a method map
        method_map = {"int": self._handle.setPropertyVector_int,
                      "str": self._handle.setPropertyVector_str,
                      "uint8": self._handle.setPropertyVector_byt,
                      "uint32": self._handle.setPropertyVector_uint}
        if self._dtype == np.float64:
            method_map.update({'double': self._handle.setPropertyVector_dbl,
                               'float64': self._handle.setPropertyVector_dbl,
                               'float': self._handle.setPropertyVector_dbl})
        elif self._dtype == np.float32:
            method_map.update({'float': self._handle.setPropertyVector_flt,
                               'float64': self._handle.setPropertyVector_flt,
                               'float32': self._handle.setPropertyVector_flt})

        assert isinstance(propValue, (list, tuple)) | isinstance(
            propValue, np.ndarray)

        # get the geometry base count
        geom_base_count = self.getGeometryBaseCount()
        data_type = type(propValue[0])

        if data_type.__name__.startswith('float') or data_type.__name__ == "double":
            data_type = self._dtype

        if data_type.__name__.startswith('int'):
            data_type = int

        # create a map for padding values
        pad_value = {"int": raster.getNullValue(int),
                     "uint8": raster.getNullValue(np.uint8),
                     "uint32": raster.getNullValue(np.uint32),
                     "str": raster.getNullValue(str),
                     "float": raster.getNullValue(float),
                     "float64": raster.getNullValue(float),
                     "float32": raster.getNullValue(float)}

        if self._dtype == np.float64:
            for key in pad_value:
                if key.startswith("float"):
                    pad_value[key] = raster.getNullValue(np.float64)

        # pad values when the input values have a length smaller than
        # the length in the base vector
        diff = geom_base_count - len(propValue)
        if not isinstance(propValue, np.ndarray):
            if diff > 0:
                values = list(chain.from_iterable((propValue,
                                                  repeat(pad_value.get(data_type.__name__), diff))))
            else:
                values = propValue

            if data_type != str:
                values = np.array(list(values), dtype=data_type)
        else:
            if diff > 0:
                values = np.pad(propValue, (0, diff), mode='constant',
                                constant_values=(pad_value.get(data_type.__name__),
                                                 pad_value.get(data_type.__name__)))
            else:
                if data_type == str:
                    values = propValue.tolist()
                else:
                    values = propValue.astype(data_type)

        if data_type.__name__ == "int":
            # work around for python <int> to <numpy.int32>
            values = values.astype(np.int32)

        # set values
        method_map.get(data_type.__name__)(core.str2bytes(name), values)

    def setPropertyValues(self, name: Union[str, bytes],
                          propValue: Union[Iterable, np.ndarray]) -> None:
        # backward compatibility
        return self.setPropertyVector(name, propValue)

    def setProperty(self, idx: int, propName: Union[str, bytes],
                    propValue: Union[str, int, float],
                    propType: type = None) -> None:
        """set a property and value to the vector object.

        Parameters
        ----------
        idx : int
            index of vector geometry in the vector object
        propName : Union[str, bytes]
            name of the property
        propValue : Union[str, int, float]
            value of the property
        propType : type, optional
            data type for the value of the property, by default None

        Raises
        ------
        AssertionError
            Vector class is not yet initialized
        ValueError
            propType is not valid
        """
        assert self._handle is not None, "Vector class is not yet initialized"

        method_map = {"int": self._handle.setProperty_int,
                      "str": self._handle.setProperty_str,
                      "uint8": self._handle.setProperty_byt,
                      "uint32": self._handle.setProperty_uint}
        if self._dtype == np.float64:
            method_map.update({'float64': self._handle.setProperty_dbl,
                               'float32':  self._handle.setProperty_dbl,
                               'float':  self._handle.setProperty_dbl})
        elif self._dtype == np.float32:
            method_map.update({'float': self._handle.setProperty_flt,
                               'float32': self._handle.setProperty_flt,
                               'float64': self._handle.setProperty_flt})

        if propValue is not None:
            if np.isscalar(propValue):
                if propType is None:
                    propType = type(propValue)
            else:
                # work with non-scalar values
                if self._dtype == np.float64:
                    method_map.update({'float64': self._handle.setProperty_dbl_vector,
                                       'float32': self._handle.setProperty_dbl_vector,
                                       'float': self._handle.setProperty_dbl_vector})
                elif self._dtype == np.float32:
                    method_map.update({'float': self._handle.setProperty_flt_vector,
                                       'float32': self._handle.setProperty_flt_vector,
                                       'float64': self._handle.setProperty_flt_vector})

                if propType is None:
                    propType = type(propValue[0])
                    # map integer type to float
                    if propType in [int, np.int32, np.uint32]:
                        propType = self._dtype

            method = method_map.get(propType.__name__)
            if propType.__name__.startswith("int"):
                method = method_map.get("int")

            if method is None:
                raise ValueError(f"propType {propType.__name__} is not valid")

            if propType == str:
                method(np.uint32(idx), core.str2bytes(propName),
                       core.str2bytes(propType(propValue)))
            else:
                if propType == int:
                    propValue = np.int32(propValue)

                # work is vector values
                if np.isscalar(propValue):
                    method(np.uint32(idx), core.str2bytes(propName), propType(propValue))
                else:
                    method(np.uint32(idx), core.str2bytes(propName),
                           core.PropertyType.dtype2vec[propType](propValue))
        else:
            if not self._handle.hasProperty(core.str2bytes(propName)):
                self._handle.addProperty(core.str2bytes(propName))

    def __getitem__(self, name: Union[str, bytes]) -> Union[int, float, str,
                                                            "core.IntegerVector", "core.FloatVector",
                                                            "core.DoubleVector", "core.StringVector",
                                                            "core.IndexVector"]:
        return self.properties[name]

    def getProperty(self, idx: int, propName: Union[str, bytes],
                    propType: type = None,
                    safe: bool = utils.is_ipython()) -> Union[int, float, str]:
        """get the value of a property from the vector object

        Parameters
        ----------
        idx : int
            index of vector geometry in the vector object
        propName : Union[str, bytes]
            name of the property
        propType : type, optional
            data type for the value of property, by default None
        safe : bool, optional
            flag to check if the index is valid for a point, by default is_ipython()

        Returns
        -------
        Union[int, float, str]
            value of the property

        Raises
        ------
        AssertionError
            Vector class is not yet initialized
        ValueError
            propType is not valid
        """
        assert self._handle is not None, "Vector class is not yet initialized"

        if safe:
            geometry_indices = self.getGeometryIndexes()
            if idx not in geometry_indices:
                raise IndexError(f"point index {idx} not valid")

        method_map = {"int": self._handle.getProperty_int,
                      "str": self._handle.getProperty_str,
                      "uint8": self._handle.getProperty_byt,
                      "uint32": self._handle.getProperty_uint,}
        _prop_type = self.getPropertyType(propName)

        if self._dtype == np.float64:
            if _prop_type == np.float64:
                method_map.update({'float64': self._handle.getProperty_dbl})
            elif _prop_type == core.DoubleVector:
                method_map.update({'float64': self._handle.getProperty_dbl_vector,
                                   'DoubleVector': self._handle.getProperty_dbl_vector})
        elif self._dtype == np.float32:
            if _prop_type == np.float32 or _prop_type == float:
                method_map.update({'float': self._handle.getProperty_flt,
                                   'float32': self._handle.getProperty_flt})
            elif _prop_type == core.FloatVector:
                method_map.update({'float': self._handle.getProperty_flt_vector,
                                   'float32': self._handle.getProperty_flt_vector,
                                   'FloatVector': self._handle.getProperty_flt_vector})

        if propType is None:
            if _prop_type is not None:
                _vec_prop_type = self.getPropertyType(propName)
                if _vec_prop_type is None:
                    out = method_map[_prop_type.__name__](
                                    np.uint32(idx), core.str2bytes(propName))
                else:
                    out = _vec_prop_type(method_map[_prop_type.__name__](
                                        np.uint32(idx), core.str2bytes(propName)))
            else:
                out = _prop_type
        else:
            method = method_map.get(propType.__name__)
            if method is None:
                raise ValueError(f"propType {propType.__name__} is not valid")
            _vec_prop_type = self.getPropertyType(propName)
            if _vec_prop_type is None:
                out = method(np.uint32(idx), core.str2bytes(propName))
            else:
                out = _vec_prop_type(method(np.uint32(idx), core.str2bytes(propName)))
        if _prop_type in [core.DoubleVector, core.FloatVector]:
            out = np.asanyarray(out, self.getPropertyType(propName))
        return out

    def __contains__(self, propName: Union[str, bytes]) -> bool:
        return self.hasProperty(propName)

    def isPropertyNumeric(self, propName: Union[str, bytes]) -> bool:
        """check if property value is of numeric type

        Parameters
        ----------
        propName : Union[str, bytes]
            name of the property

        Returns
        -------
        bool
            True if numeric, false otherwise
        """
        if self._handle is not None:
            out = self._handle.isPropertyNumeric(core.str2bytes(propName))
            return out
        else:
            raise RuntimeWarning("Vector class is not yet initialized")

    def hasProperty(self, propName: Union[str, bytes]) -> bool:
        """check if the property is defined for the vector object

        Parameters
        ----------
        propName : Union[str, bytes]
            name of the property

        Returns
        -------
        bool
            True is property is defined, False otherwise

        Raises
        ------
        RuntimeWarning
            Vector class is not yet initialized
        """
        if self._handle is not None:
            out = self._handle.hasProperty(core.str2bytes(propName))
            return out
        else:
            raise RuntimeWarning("Vector class is not yet initialized")

    def convertProperty(self, propName: Union[str, bytes], propType: type) -> None:
        """Convert data type of the property of an object.

        Parameters
        ----------
        propName : Union[str, bytes]
            name of the property
        prop_type: type
            data type to cast the value of property

        Returns
        -------
        None

        Raises
        ------
        RuntimeWarning
            Vector class is not yet initialized
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        method_map = {"int": getattr(self, cy_obj).convertProperty_int,
                      "float": getattr(self, cy_obj).convertProperty_flt,
                      "float64": getattr(self, cy_obj).convertProperty_flt,
                      "str": getattr(self, cy_obj).convertProperty_str,
                      "uint8": getattr(self, cy_obj).convertProperty_byt,
                      "uint32": getattr(self, cy_obj).convertProperty_uint}

        if self._dtype == np.float64:
            method_map.update({'float': getattr(self, cy_obj).convertProperty_dbl,
                               "float64": getattr(self, cy_obj).convertProperty_dbl})

        assert propType.__name__ in method_map, f"propType {propType} is not valid"
        method_map.get(propType.__name__)(core.str2bytes(propName))

    def getGeometry(self, idx: int) -> object:
        assert idx in self.getGeometryIndexes()
        out = self._handle.get_geometry(idx)
        return out

    def getGeometryType(self, idx: int,
                        safe: bool = utils.is_ipython()) -> gs_enums.GeometryType:
        """method to get the geometry type for a given index.

        Parameters
        ----------
        idx : int
            index of a geometry
        safe : bool, optional
            flag to check if the index is valid for a point, by default is_ipython()

        Returns
        -------
        gs_enums.GeometryType
            geometry type for the given index of geometry
        """
        if safe:
            geometry_indices = self.getGeometryIndexes()
            if idx not in geometry_indices:
                raise IndexError(f"point index {idx} not valid")

        geom_type = self._handle.get_geometry_type(idx)
        out = gs_enums.GeometryType(geom_type)
        return out

    def setGlobalProperty(self, propName: Union[str, bytes],
                          propValue: Union[str, int],
                          propType: type = None) -> None:
        """set a global property for the Vector object

        Parameters
        ----------
        propName : Union[str, bytes]
            name of the global property
        propValue : Union[str, int]
            value of the global property
        propType : type, optional
            data type for the value of the property, by default None

        """
        method_map = {"int": self._handle.setGlobalProperty_int,
                      "str": self._handle.setGlobalProperty_str}

        if propType is None:
            propType = type(propValue)

        method = method_map.get(propType.__name__)
        if method is None:
            raise ValueError(f"propType {propType.__name__} is not valid")

        method(core.str2bytes(propName), propValue)

    def getGlobalProperty(self, propName: Union[str, bytes]) -> Union[str, int]:
        """get a global property from the Vector object

        Parameters
        ----------
        propName : Union[str, bytes]
            name of the global property

        Returns
        -------
        propValue: Union[str, int]
            value of the global property
        """
        method_map = {"int": self._handle.getGlobalProperty_int,
                      "str": self._handle.getGlobalProperty_str}

        _prop_type = self.getPropertyType(core.str2bytes(propName))

        method = method_map.get(_prop_type.__name__)
        if method is None:
            raise TypeError('property type is invalid for global property')

        return method(core.str2bytes(propName))

    @property
    def properties(self) -> "core.PropertyMap":
        """return all of the properties

        Returns
        -------
        PropertyMap
            an instance of PropertyMap object
        """
        return self.getProperties()

    def getProperties(self) -> "core.PropertyMap":
        """get all the properties defined for the vector object

        Returns
        -------
        PropertyMap
            an instance of PropertyMap object

        Raises
        ------
        RuntimeWarning
            Vector object is not initialized
        """
        if self._handle is not None:
            obj = core.PropertyMap(other=self._handle.getProperties())
        else:
            raise RuntimeWarning("Vector object is not initialized")
        return obj

    def setProjectionParameters(self, other: Union["core.ProjectionParameters", str]):
        if not isinstance(other, (core.ProjectionParameters, str)):
            raise TypeError(
                "dst_proj should be an instance of ProjectionParameters/str")
        if isinstance(other, str):
            self._handle.setProjectionParameters_str(other)
        else:
            self._handle.setProjectionParameters(other._handle)

    def getProjectionParameters(self) -> "core.ProjectionParameters":
        return core.ProjectionParameters.from_proj_param(
            self._handle.getProjectionParameters())

    def convert(self, other: Union["core.ProjectionParameters",
                                   "gs_enums.GeometryType", int,
                                   str]) -> "Vector":
        """Convert the projection or geometry type of the Vector object.

        Parameters
        ----------
        other: Union["core.ProjectionParameters", "gs_enums.GeometryType", int, str]
            an instance of ProjectionParameters object or GeometryType

        Returns
        -------
        Vector
            a Vector object with the desired projection or GeometryType

        Examples
        --------
        >>> from geostack.vector import Vector
        >>> from geostack.gs_enums import GeometryType
        >>> # GeoJSON string
        >>> geojson = '''{
        ...     "features": [
        ...         {"geometry": {"coordinates": [0, 0.5], "type": "Point"},
        ...             "properties": {"r": 10}, "type": "Feature"},
        ...         {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
        ...             "properties": {"r": 20}, "type": "Feature"},
        ...         {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
        ...             "properties": {"r": 30}, "type": "Feature"},
        ...         {"geometry": {"coordinates": [1, 0.5], "type": "Point"},
        ...             "properties": {"r": 50}, "type": "Feature"}
        ...         ], "type": "FeatureCollection"
        ...     }'''

        >>> # Parse GeoJSON
        >>> v = Vector.from_geojson(geojson, enforceProjection=False)
        >>> print("Number of points :", v.getPointCount())
        Number of points: 2
        >>> print("Number of line string :", v.getLineStringCount())
        Number of line string: 1

        >>> # convert geometries to point
        >>> v2 = v.convert(GeometryType.Point)
        >>> print("Number of points :", v2.getPointCount())
        Number of points: 16
        >>> print("Number of line string :", v2.getLineStringCount())
        Number of line string: 0

        >>> # convert geometries to line string
        >>> v3 = v.convert(GeometryType.LineString)
        >>> print("Number of points :", v3.getPointCount())
        Number of points: 0
        >>> print("Number of line string :", v3.getLineStringCount())
        Number of line string: 4

        >>> # create both points and line strings
        >>> v4 = v.convert(GeometryType.Point | GeometryType.LineString)
        >>> print("Number of points :", v4.getPointCount())
        Number of points: 16
        >>> print("Number of line string :", v4.getLineStringCount())
        Number of line string: 4

        Raises
        ------
        TypeError
            other should be an instance of ProjectionParameters or GeometryType
        """
        if isinstance(other, core.ProjectionParameters):
            return Vector._from_vector(self._handle.convert_projection(other._handle))
        elif isinstance(other, (int, gs_enums.GeometryType)):
            param_value = other if isinstance(other, int) else other.value
            return Vector._from_vector(self._handle.convert_geometry_type(param_value))
        elif isinstance(other, str):
            return Vector._from_vector(self._handle.convert_proj_string(other))
        else:
            raise TypeError(
                "other should be an instance of ProjectionParameters or GeometryType")

    def getPoint(self, idx: numbers.Integral) -> "Vector":
        out = Vector(dtype=self._dtype)
        _idx = out.addPoint(self.getPointCoordinate(idx))
        props = self.getProperties()
        prop_names = filter(lambda prop: props.getPropertyStructure(prop) == gs_enums.PropertyStructure.Vector,
                            props.getPropertyNames())
        for name in prop_names:
            out.setProperty(_idx, name, self.getProperty(idx, name))
        return out

    def getLineString(self, idx: numbers.Integral) -> "Vector":
        out = Vector(dtype=self._dtype)
        _idx = out.addLineString(self.getLineStringCoordinates(idx))
        props = self.getProperties()
        prop_names = filter(lambda prop: props.getPropertyStructure(prop) == gs_enums.PropertyStructure.Vector,
                            props.getPropertyNames())
        for name in prop_names:
            out.setProperty(_idx, name, self.getProperty(idx, name))
        return out

    def getPolygon(self, idx: numbers.Integral) -> "Vector":
        out = Vector(dtype=self._dtype)
        poly_coords = self.getPolygonCoordinates(idx)
        if not isinstance(poly_coords, list):
            poly_coords = [poly_coords]
        _idx = out.addPolygon(poly_coords)
        props = self.getProperties()
        prop_names = filter(lambda prop: props.getPropertyStructure(prop) == gs_enums.PropertyStructure.Vector,
                            props.getPropertyNames())
        for name in prop_names:
            out.setProperty(_idx, name, self.getProperty(idx, name))
        return out

    def region(self, other: "BoundingBox",
               geom_type: Union[numbers.Integral,
                                "gs_enums.GeometryType"] = gs_enums.GeometryType.All) -> "Vector":
        """Return vector geometries within a region.

        Parameters
        ----------
        other : BoundingBox
            input region of type BoundingBox
        geom_type : Union[numbers.Integral, gs_enums.GeometryType]
            type of vector geometry to return

        Returns
        -------
        Vector
            Vector object containing vector geometries within the
            given bounding box.

        Raises
        ------
        TypeError
            input argument should be an instance of BoundingBox
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        """
        if not isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            raise TypeError("other should be an instance of BoundingBox")

        _bbox = other._handle if isinstance(other, BoundingBox) else other
        if isinstance(_bbox, _BoundingBox_d):
            assert self._dtype == np.float64
        else:
            assert self._dtype == np.float32

        if not isinstance(geom_type, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("geom_type should be int/ gs_enums.GeometryType")

        if isinstance(geom_type, gs_enums.GeometryType):
            _geom_type = geom_type.value
        else:
            _geom_type = geom_type
        out = Vector._from_vector(self._handle.region(_bbox, _geom_type))
        return out

    def nearest(self, other: "BoundingBox",
                geom_type: Union[numbers.Integral,
                                 "gs_enums.GeometryType"] = gs_enums.GeometryType.All) -> "Vector":
        """Return vector geometries nearest to a region.

        Parameters
        ----------
        other : BoundingBox
            input region of type BoundingBox
        geom_type : Union[numbers.Integral, gs_enums.GeometryType]
            type of vector geometry to return

        Returns
        -------
        Vector
            Vector object containing vector geometries within the
            given bounding box.

        Raises
        ------
        TypeError
            input argument should be an instance of BoundingBox
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        """
        if not isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            raise TypeError("other should be an instance of BoundingBox")
        _bbox = other._handle if isinstance(other, BoundingBox) else other
        if isinstance(_bbox, _BoundingBox_d):
            assert self._dtype == np.float64
        else:
            assert self._dtype == np.float32

        if not isinstance(geom_type, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("geom_type should be int/ gs_enums.GeometryType")

        if isinstance(geom_type, gs_enums.GeometryType):
            geom_type = geom_type.value
        else:
            geom_type = geom_type

        out = Vector._from_vector(self._handle.nearest(_bbox, geom_type))
        return out

    def nearestGeom(
        self,
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster],
        *,
        search_strategy: gs_enums.SearchStrategy = gs_enums.SearchStrategy.AllVertices,
        idx: numbers.Integral = None,
        idxs: npt.ArrayLike[numbers.Integral] = None,
        proj: core.ProjectionParameters = None
    ) -> np.uint32:
        """find the nearest geometry from this vector

        Parameters
        ----------
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster]
        - Coordinate: the coordinate is directly used in the search. Can
        optionally specify `proj`, otherwise is assumed to adopt this Vector's
        projection
        - Vector: the vertices of the vector geometries are used. Can optionally
        specify `idx` or `idxs` to determine which particular geometry(ies) used
        - BoundingBox: the centroid is used. Can optionally specify `proj`,
        otherwise is assumed to adopt this Vector's projection
        - Raster: the vertices of the footprint are used

        search_strategy: gs_enums.SearchStrategy
            The strategy when searching for the geometries nearest a query vector.
            For gs_enums.SearchStrategy.AllVertices (default), the result will
            be a single geometry that is nearest any vertex of the query vector.
            For gs_enums.SearchStrategy.ByVertex, the result will be a list of geometries,
            each one nearest a Point in the query vector. The LineStrings and Polygons in
            the query vector are ignored.

        idx: numbers.Integeral
            The geom id of the vector geometry

        idxs: npt.ArrayLike[numbers.Integral]
            The geom ids of the vector geometries

        proj: core.ProjectionParameters
            The projection of `obj`.

        Returns
        -------
        np.uint32
            the geometry id of the nearest geometry
        """
        if isinstance(obj, Coordinate):
            if proj is None:
                return self._handle.nearestGeomFromCoord(obj._handle)
            return self._handle.nearestGeomFromCoordProj(obj._handle, proj._handle)
        if isinstance(obj, Vector):
            if idxs is not None:
                return self._handle.nearestGeomFromGeoms(obj._handle, idxs)
            if idx is not None:
                return self._handle.nearestGeomFromGeom(obj._handle, idx)
            return self._handle.nearestGeomFromVec(obj._handle, search_strategy)
        if isinstance(obj, BoundingBox):
            if proj is None:
                return self._handle.nearestGeomFromBBox(obj._handle)
            return self._handle.nearestGeomFromBBoxProj(obj._handle, proj._handle)
        if isinstance(obj, raster.Raster):
            return self._handle.nearestGeomFromRaster(obj._handle)
        raise TypeError(f"Invalid type {type(obj)}")

    def nearestNGeoms(
        self,
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster],
        n: numbers.Integral,
        *,
        idx: numbers.Integral = None,
        idxs: npt.ArrayLike[numbers.Integral] = None,
        proj: core.ProjectionParameters = None
    ) -> npt.NDArray[np.uint32]:
        """find the nearest `n` geometries from this vector

        Parameters
        ----------
        obj: Union[Coordinate, Vector, BoundingBox, raster.Raster]
        - Coordinate: the coordinate is directly used in the search. Can
        optionally specify `proj`, otherwise is assumed to adopt this Vector's
        projection
        - Vector: the vertices of the vector geometries are used. Can optionally
        specify `idx` or `idxs` to determine which particular geometry(ies) used
        - BoundingBox: the centroid is used. Can optionally specify `proj`,
        otherwise is assumed to adopt this Vector's projection
        - Raster: the vertices of the footprint are used

        n: numbers.Integral
            Number of nearest geometries

        idx: numbers.Integeral
            The geom id of the vector geometry

        idxs: npt.ArrayLike[numbers.Integral]
            The geom ids of the vector geometries

        proj: core.ProjectionParameters
            The projection of `obj`

        Returns
        -------
        npt.NDArray[np.uint32]
            an ndarray of geometry ids of the nearest geometries
        """
        out = None
        if isinstance(obj, Coordinate):
            if proj is None:
                out = self._handle.nearestNGeomsFromCoord(obj._handle, n)
            else:
                out = self._handle.nearestNGeomsFromCoordProj(obj._handle, n, proj._handle)
        elif isinstance(obj, Vector):
            if idxs is not None:
                out = self._handle.nearestNGeomsFromGeoms(obj._handle, n, idxs)
            if idx is not None:
                out = self._handle.nearestNGeomsFromGeom(obj._handle, n, idx)
            out = self._handle.nearestNGeomsFromVec(obj._handle, n)
        elif isinstance(obj, BoundingBox):
            if proj is None:
                out = self._handle.nearestNGeomsFromBBox(obj._handle, n)
            else:
                out = self._handle.nearestNGeomsFromBBoxProj(obj._handle, n, proj._handle)
        elif isinstance(obj, raster.Raster):
            out = self._handle.nearestNGeomsFromRaster(obj._handle, n)
        if out is not None:
            return np.asanyarray(out)
        raise TypeError(f"Invalid type {type(obj)}")

    def regionGeometryIndices(self, other: "BoundingBox",
                 geom_type: Union[numbers.Integral, "gs_enums.GeometryType"] = 7) -> np.ndarray:
        """Return vector geometries within the bounding box.

        Parameters
        ----------
        other : BoundingBox
            input region of type BoundingBox
        geom_type : Union[numbers.Integral, gs_enums.GeometryType]
            type of vector geometry to return

        Returns
        -------
        np.ndarray
            a ndarray with geometry id

        Raises
        ------
        TypeError
            inp_coordinate should be of type Coordinate
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        AssertionError
            Datatype mismatch b/w Vector and input coordinate
        """
        if not isinstance(other, (BoundingBox, _BoundingBox_d, _BoundingBox_f)):
            raise TypeError("other should be an instance of BoundingBox")
        _bbox = other._handle if isinstance(other, BoundingBox) else other
        if isinstance(_bbox, _BoundingBox_d):
            assert self._dtype == np.float64
        else:
            assert self._dtype == np.float32

        if isinstance(geom_type, gs_enums.GeometryType):
            _geom_type = geom_type.value
        elif isinstance(geom_type, numbers.Integral):
            _geom_type = geom_type
        else:
            raise TypeError("geom_type should be int/ gs_enums.GeometryType")
        out = self._handle.regionGeometryIndices(_bbox, _geom_type)
        return np.asanyarray(out)

    def attached(self, inp_coordinate: "Coordinate",
                 geom_type: Union[numbers.Integral,
                                  "gs_enums.GeometryType"] = gs_enums.GeometryType.All) -> np.ndarray:
        """Return vector geometries attached to the input coordinate.

        Parameters
        ----------
        inp_coordinate : Coordinate
            Input coordinate to obtain the attached vector geometry
        geom_type : Union[numbers.Integral, gs_enums.GeometryType]
            type of vector geometry to return

        Returns
        -------
        np.ndarray
            a ndarray with geometry id

        Raises
        ------
        TypeError
            inp_coordinate should be of type Coordinate
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        AssertionError
            Datatype mismatch b/w Vector and input coordinate
        """
        if not isinstance(inp_coordinate, Coordinate):
            raise TypeError("inp_coordinate should be Coordinate")
        assert self._dtype == inp_coordinate._dtype, "DataType mismatch"
        if isinstance(geom_type, gs_enums.GeometryType):
            _geom_type = geom_type.value
        elif isinstance(geom_type, numbers.Integral):
            _geom_type = geom_type
        else:
            raise TypeError("geom_type should be int/ gs_enums.GeometryType")
        out = self._handle.attached(inp_coordinate._handle, _geom_type)
        return np.asanyarray(out)

    def deduplicateVertices(self):
        assert self._handle is not None, "Vector is not instantiated"
        self._handle.deduplicateVertices()

    def mapDistance(self, resolution: numbers.Real = None,
                    script: str = "",
                    parameters: Union[numbers.Integral,
                                     "gs_enums.GeometryType"] = gs_enums.GeometryType.All,
                    bounds: Optional['BoundingBox'] = None,
                    inp_raster: Optional[Union['raster.Raster', 'raster.RasterFile']] = None,
                    **kwargs) -> "raster.Raster":
        """Return a distance map for the vector object.

        Parameters
        ----------
        resolution : numbers.Real
            resolution of the output raster
        script : str
            script to use for rasterise operation
        parameters : Union[numbers.Integral, gs_enums.GeometryType]
            type of geometry use for distance map.
        bounds : BoundingBox, optional
            bounding box to subset vector before creating
            distance map, by default None
        inp_raster: raster.Raster, optional
            a raster object to use for creating distance map, by default None

        Returns
        -------
        raster.Raster
            distance map raster

        Raises
        ------
        AssertionError
            Vector is not instantiated
        TypeError
            resolution should be numeric
        TypeError
            bounds should be an instance of boundingbox
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        """
        if inp_raster is None:
            assert self._handle is not None, "Vector is not instantiated"
            if not isinstance(resolution, numbers.Real):
                raise TypeError("resolution should be numeric")
            _resolution = self._dtype(resolution)

            if bounds is None:
                _bounds = BoundingBox()
            else:
                if not isinstance(bounds, BoundingBox):
                    raise TypeError(
                        "bounds should be an instance of boundingbox")
                _bounds = bounds
        else:
            # handle case when a raster is provided
            if not isinstance(inp_raster, (raster.Raster, raster.RasterFile)):
                raise TypeError(
                    "inp_raster should be an instance of Raster/RasterFile")
            if not inp_raster.hasData():
                raise RuntimeError("Input raster cannot be empty")

        parameters = kwargs.get('geom_type', parameters)

        if not isinstance(parameters, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("geom_type should be int/ gs_enums.GeometryType")

        if isinstance(parameters, gs_enums.GeometryType):
            if inp_raster is None:
                _out = self._handle.mapDistanceOnBounds(_resolution,
                                                        script=script,
                                                        parameters=parameters.value,
                                                        bounds=_bounds._handle)
            else:
                if isinstance(inp_raster, raster.Raster):
                    _out = self._handle.mapDistanceOnRaster(inp_raster._handle,
                                                            script=script,
                                                            parameters=parameters.value)
                elif isinstance(inp_raster, raster.RasterFile):
                    _out = self._handle.mapDistanceOnRaster(inp_raster._handle.cy_raster_obj,
                                                            script=script,
                                                            parameters=parameters.value)
        else:
            if inp_raster is None:
                _out = self._handle.mapDistanceOnBounds(_resolution,
                                                        script=script,
                                                        parameters=parameters,
                                                        bounds=_bounds._handle)
            else:
                if isinstance(inp_raster, raster.Raster):
                    _out = self._handle.mapDistanceOnRaster(inp_raster._handle,
                                                            script=script,
                                                            parameters=parameters)
                elif isinstance(inp_raster, raster.RasterFile):
                    _out = self._handle.mapDistanceOnRaster(inp_raster._handle.cy_raster_obj,
                                                            script=script,
                                                            parameters=parameters)
        out = raster.Raster.copy("rasterised", _out)
        out.setProjectionParameters(self.getProjectionParameters())
        return out

    def rasterise(self, resolution: Optional[numbers.Real] = None,
                  script: str = "",
                  parameters: Union[numbers.Integral,
                                    "gs_enums.GeometryType"] = gs_enums.GeometryType.All,
                  bounds: Optional["BoundingBox"] = None,
                  inp_raster: Optional[Union['raster.Raster', 'raster.RasterFile']] = None,
                  output_type: np.dtype = core.REAL,
                  **kwargs) -> "raster.Raster":
        """Return a raster after rasterising the vector object.

        Parameters
        ----------
        resolution : Optional[numbers.Real]
            resolution of the output raster
        script : str
            script to use for rasterise operation
        parameters : Union[numbers.Integral, gs_enums.GeometryType]
            type of geometry use for rasterise operation
        bounds : BoundingBox, optional
            bounding box to subset vector before creating
            distance map, by default None
        inp_raster: raster.Raster, optional
            a raster object to use for creating distance map, by default None

        Returns
        -------
        raster.Raster
            raster generated from rasterise operation.

        Raises
        ------
        AssertionError
            Vector is not instantiated
        TypeError
            bounds should be an instance of boundingbox
        TypeError
            geom_type should be int/ gs_enums.GeometryType
        """
        assert self._handle is not None, "Vector is not instantiated"
        _resolution = self._dtype(resolution)

        if output_type not in [np.uint8, np.uint32]:
            output_type = self._dtype

        if bounds is None:
            _bounds = BoundingBox(dtype=core.REAL)
        else:
            if not isinstance(bounds, BoundingBox):
                raise TypeError("bounds should be an instance of boundingbox")
            _bounds = bounds

        if isinstance(script, (str, bytes)):
            _script = core.str2bytes(script)

        parameters = kwargs.get("geom_type", parameters)

        if not isinstance(parameters, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("parameters should be int/ gs_enums.GeometryType")

        if inp_raster is None:
            method_map = {
                self._dtype: self._handle.rasteriseOnBounds,
                np.uint8: self._handle.rasteriseOnBounds_byt,
                np.uint32: self._handle.rasteriseOnBounds_uint
            }
            dispatcher = partial(method_map[output_type],
                                 _resolution, _script)
        else:
            method_map = {
                self._dtype: self._handle.rasteriseOnRaster,
                np.uint8: self._handle.rasteriseOnRaster_byt,
                np.uint32: self._handle.rasteriseOnRaster_uint
            }

            if isinstance(inp_raster, raster.Raster):
                dispatcher = partial(method_map[output_type],
                                     inp_raster._handle.get_raster_base(), _script)
            elif isinstance(inp_raster, raster.RasterFile):
                dispatcher = partial(method_map[output_type],
                                     inp_raster._handle.cy_raster_obj.get_raster_base(),
                                     _script)

        if isinstance(parameters, gs_enums.GeometryType):
            if inp_raster is None:
                _out = dispatcher(parameters.value, _bounds._handle)
            else:
                _out = dispatcher(parameters.value)
        else:
            if inp_raster is None:
                _out = dispatcher(parameters, _bounds._handle)
            else:
                _out = dispatcher(parameters)

        out = raster.Raster.copy("rasterised", _out)
        out.setProjectionParameters(self.getProjectionParameters())
        return out

    def pointSample(self, other: Union["raster.Raster", "raster.RasterFile"]) -> bool:
        """Sample raster at the location of vector geometries.

        Parameters
        ----------
        other : Union[raster.Raster, raster.RasterFile]
            input raster dataset for sampling.

        Returns
        -------
        bool
            True if raster was sampled False otherwise

        Raises
        ------
        TypeError
            Input argument should be of type Raster
        AssertionError
            Datatype mismatch
        """
        if not isinstance(other, (raster._cyRaster_d,
                                  raster._cyRaster_f,
                                  raster.DataFileHandler_d,
                                  raster.DataFileHandler_f,
                                  raster.Raster,
                                  raster.RasterFile)):
            raise TypeError(
                "Input argument should be an instance of Raster class")
        if isinstance(other, raster.Raster):
            _bbox = other._handle
        elif isinstance(other, raster.RasterFile):
            _bbox = other._handle.cy_raster_obj
        else:
            _bbox = other

        if isinstance(_bbox, raster._cyRaster_d):
            assert self._dtype == np.float64, "Datatype mismatch"
        else:
            assert self._dtype == np.float32, "Datatype mismatch"

        return self._handle.pointSample(_bbox)

    def runScript(self, script: Union[str, bytes]):
        """
        Method to run script on the Vector object.

        Parameters
        ----------
        script: Union[str, bytes]
             Script to run on the Vector object over GPU.

        Returns
        -------
        Nil
        """
        if isinstance(script, (str, bytes)):
            self._handle.runScript(core.str2bytes(script))
        else:
            raise TypeError(
                f"Invalid data type {type(script)} for script, it should be of type str/bytes")

    def getBounds(self) -> "BoundingBox":
        """get the bounds of the Vector object

        Returns
        -------
        BoundingBox
            an instance of BoundingBox object
        """
        if self._handle is not None:
            return BoundingBox.from_bbox(self._handle.getBounds())

    @property
    def bounds(self) -> "BoundingBox":
        return self.getBounds()

    def hasData(self) -> bool:
        """check if the Vector object has data.

        Returns
        -------
        bool
            True if the Vector object has data, False otherwise
        """
        return self._handle.hasData()

    @staticmethod
    def from_geojson(fileName: Union[Dict, str], dtype: np.dtype = core.REAL,
                     **kwargs) -> "Vector":
        """read a geojson to a Vector object

        Parameters
        ----------
        fileName : Union[Dict, str]
            name of the file or a dictionary
        dtype : np.dtype, optional
            data type for the vector object, by default np.float32

        Returns
        -------
        Vector
            a vector object initialized from the geojson
        """
        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        return io.geoJsonToVector(fileName, dtype=dtype, **kwargs)

    @supported_libs.RequireLib("matplotlib")
    def plot(self, ax=None, bounds: Optional[Union[List[List[int]],'BoundingBox']]=None, **kwargs) -> None:
        """convenience method for plotting vector object

        Parameters
        ----------
        ax : Axes, optional
            figure axes, by default None

        Returns
        -------
        Tuple[Figure, Axes]
            a tuple of figure and axes

        Examples
        --------
        >>> import numpy as np
        >>> import matplotlib.pyplot as plt
        >>> import json

        >>> _geo_json = {"features": [
            {"geometry": {"coordinates": [0, 1.5], "type": "Point"},
                "properties": {"A": 1}, "type": "Feature"},
            {"geometry": {"coordinates": [[0, 0], [1, 1], [2, 0], [3, 1]], "type": "LineString"},
                "properties": {"A": 2}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[0.25, 0.25], [0.25, 0.75], [0.75, 0.75], [0.75, 0.25], [0.25, 0.25]]], "type": "Polygon"},
                "properties": {"A": 3}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"A": 4}, "type": "Feature"},
            {"geometry": {"coordinates": [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]], "type": "Polygon"},
                "properties": {"A": 5}, "type": "Feature"}
            ], "type": "FeatureCollection"}

        >>> # create a vector
        >>> test = Vector.from_geojson(json.dumps(_geo_json))

        >>> # plot vector
        >>> fig, ax = test.plot()

        >>> # plot vector and use property to color
        >>> fig, ax = test.plot(values='A')

        >>> # plot within bounds
        >>> bounds = test.getBounds()
        >>> fig, ax = test.plot(values='A', bounds=bounds)

        >>> # with cartopy
        >>> import cartopy.crs as ccrs
        >>> fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        >>> ax.set_extent([2.0, 3.0, 0.0, 1.0])
        >>> fig, ax = test.plot(ax, values='A')

        >>> # for adding colorbar
        >>> fig.colorbar(ax.collections[0], ax=ax)
        """
        def extent_to_bounds(extent: List[float]) -> "BoundingBox":
            # convert geoaxes extent to bounds
            return BoundingBox.from_list([[extent[0], extent[2]],
                                          [extent[1], extent[3]]])

        # geometry type
        geom_type = kwargs.pop("geom_type", None)
        if geom_type is not None:
            assert geom_type in [gs_enums.GeometryType.Point,
                                 gs_enums.GeometryType.Polygon,
                                 gs_enums.GeometryType.LineString], "Geometry type should be Point, LineString or Polygon"

        # set figure size
        figsize = kwargs.pop("figsize", (8, 6))
        # set figure aspect ratio
        aspect = kwargs.pop("aspect", "equal")

        if bounds is not None:
            assert isinstance(bounds, BoundingBox), "bounds should be a BoundingBox object"

        # create plotting axis or get the plotting axis
        if ax is not None:
            fig = ax.get_figure()

            if any([hasattr(ax, 'get_extent'), bounds is not None]):
                if bounds is None:
                    # extract from plot axis
                    bounds = extent_to_bounds(ax.get_extent())
            else:
                bounds = self.getBounds()
        else:
            # import plottling library  (create axes)
            import matplotlib.pyplot as plt

            fig = plt.figure(1, figsize=figsize)
            fig.patch.set_facecolor('white')
            ax = fig.add_subplot(1, 1, 1)
            ax.set_aspect(aspect)

            if bounds is None:
                bounds = self.getBounds()

        from matplotlib.path import Path
        from matplotlib.collections import PathCollection, LineCollection

        # get colors
        color = kwargs.pop("color", None)
        facecolor = kwargs.pop("facecolor", None)
        edgecolor = kwargs.pop("edgecolor", None)

        # get colormap
        values = kwargs.pop("values", None)
        vmin = min_value = kwargs.pop("vmin", None)
        vmax = max_value = kwargs.pop("vmax", None)
        cmap = kwargs.pop("cmap", None)

        # get marker
        marker = kwargs.pop("marker", 'o')
        mfc = kwargs.pop("markerfacecolor", 'r')
        mec = kwargs.pop("markeredgecolor", 'k')

        if values is not None:
            if isinstance(values, str):
                assert self.hasProperty(values), f"property {values} is not in Vector"
                assert self.getProperties().getPropertyStructure(values) != gs_enums.PropertyStructure.Vector, "Only scalar properties are supported"
                assert self.getProperties().getPropertyType(values) != str, "Only numeric properties are supported"
            elif isinstance(values, (list, np.ndarray)):
                geom_size = self.getPointCount() + self.getLineStringCount() + self.getPolygonCount()
                assert geom_size == len(values), "length of values should be equal to geometry count in Vector"

                assert bounds == self.bounds, "Can't use list of values when bounding box is given"

        # work with polygon
        poly_collection = []
        poly_values = []
        if geom_type is None or geom_type == gs_enums.GeometryType.Polygon:
            if bounds == self.getBounds():
                poly_indices = self.getPolygonIndexes()
            else:
                poly_indices = self.regionGeometryIndices(bounds, gs_enums.GeometryType.Polygon)

            for i in poly_indices:
                poly_collection.append(Path.make_compound_path(*map(lambda item: Path(item[:,:2]),
                                                                    self.getPolygonCoordinates(i))))
                if values is not None:
                    if isinstance(values, str):
                        poly_values.append(self.getProperty(i, values))
                    else:
                        poly_values.append(values[i])

        # work with line strings
        line_collection = []
        line_values = []
        if geom_type is None or geom_type == gs_enums.GeometryType.LineString:
            # get the line string indices
            if bounds == self.getBounds():
                line_indices = self.getLineStringIndexes()
            else:
                line_indices = self.regionGeometryIndices(bounds, gs_enums.GeometryType.LineString)

            # now get the line string geometries
            for i in line_indices:
                line_collection.append(self.getLineStringCoordinates(i)[:, :2])
                if values is not None:
                    if isinstance(values, str):
                        line_values.append(self.getProperty(i, values))
                    else:
                        line_values.append(values[i])

        # finally, work with points
        point_collection = []
        point_values = []
        if geom_type is None or geom_type == gs_enums.GeometryType.Point:
            # get the point indices
            if bounds == self.getBounds():
                point_indices = self.getPointIndexes()
            else:
                point_indices = self.regionGeometryIndices(bounds, gs_enums.GeometryType.Point)

            # now get the point geometries
            for i in point_indices:
                point_collection.append(self.getPointCoordinate(i).to_list()[:2])
                if values is not None:
                    if isinstance(values, str):
                        point_values.append(self.getProperty(i, values))
                    else:
                        point_values.append(values[i])

        # update color limits (for polygon)
        if len(poly_collection) > 0:
            # check the color limits for points
            if vmin is None and poly_values:
                min_value = np.nanmin(poly_values)
            else:
                min_value = vmin

            if vmax is None and poly_values:
                max_value = np.nanmax(poly_values)
            else:
                max_value = vmax

        # update color limits (with values for line string)
        if len(line_collection) > 0:
            # check the color limits for line string
            if vmin is None and line_values:
                min_value = min(map(lambda s: s is not None,
                                [np.nanmin(line_values), min_value]))
            else:
                min_value = vmin
            if vmax is None and line_values:
                max_value = max(map(lambda s: s is not None,
                                [np.nanmax(line_values), max_value]))
            else:
                max_value = vmax

        # update color limits (with value for points)
        if len(point_collection) > 0:
            # check the color limits for polygon
            if vmin is None and point_values:
                min_value = min(map(lambda s: s is not None,
                                [np.nanmin(point_values), min_value]))
            else:
                min_value = vmin
            if vmax is None and point_values:
                max_value = max(map(lambda s: s is not None,
                                [np.nanmax(point_values), max_value]))
            else:
                max_value = vmax

        if len(poly_collection) > 0:
            poly_collection = PathCollection(poly_collection, facecolor=facecolor,
                                             edgecolor=edgecolor, cmap=cmap, **kwargs)
            if values is not None:
                poly_collection.set_array(np.array(poly_values))
                poly_collection.set_clim(min_value, max_value)
            ax.add_collection(poly_collection, autolim=True)
            ax.autoscale_view()

        if len(line_collection) > 0:
            c = LineCollection(line_collection, colors=color, cmap=cmap, **kwargs)
            if values is not None:
                c.set_array(np.array(line_values))
                c.set_clim(min_value, max_value)
            ax.add_collection(c, autolim=True)
            ax.autoscale_view()

        if len(point_collection) > 0:
            point_collection = np.array(point_collection)
            if len(point_values) > 0:
                ax.scatter(point_collection[:, 0], point_collection[:, 1],
                           vmin=min_value, vmax=max_value, cmap=cmap, marker=marker,
                           facecolor=mfc, edgecolor=mec, c=point_values, **kwargs)
            else:
                ax.scatter(point_collection[:, 0], point_collection[:, 1],
                           vmin=min_value, vmax=max_value, cmap=cmap, marker=marker,
                           facecolor=mfc, edgecolor=mec, **kwargs)
        return fig, ax

    def to_geojson(self, fileName: Union[str, StringIO] = None,
                   enforceProjection: bool = True,
                   writeNullProperties: bool = True) -> Union[None, str]:
        """get a geojson representation of a Vector object

        Parameters
        ----------
        fileName : Union[str, StringIO], optional
            name and path of the file, by default None
        enforceProjection : bool, optional
            flag to enforce projection of geojson to EPSG:4326, by default True
        writeNullProperties : bool, optional
            flag to write properties as null when the property is not present for a geometry, by default True

        Returns
        -------
        Union[None, str]
            a geojson string or None (when written to a file)
        """
        if fileName is None:
            out = json.loads(io.vectorToGeoJson(self,
                             enforceProjection=enforceProjection,
                             writeNullProperties=writeNullProperties))
            return out
        else:
            if isinstance(fileName, PurePath):
                fileName = str(fileName)

            if isinstance(fileName, str):
                with open(fileName, 'w') as out:
                    out.write(io.vectorToGeoJson(self,
                              enforceProjection=enforceProjection,
                              writeNullProperties=writeNullProperties))
            else:
                fileName.write(io.vectorToGeoJson(self,
                                                  enforceProjection=enforceProjection,
                                                  writeNullProperties=writeNullProperties))

    def to_csv(self, filename: str = None) -> Union[StringIO, None]:
        """write a Vector object to a csv object

        Returns
        -------
        Union[None, StringIO]
            a csv containing the geometeries from the Vector object
        """
        if isinstance(filename, PurePath):
            filename = str(filename)

        return io.vectorToCSV(self, filename=filename)

    def to_geowkt(self) -> str:
        """get a geowkt representation of the Vector object

        Returns
        -------
        str
            a geoWKT containing the geometeries from the Vector object
        """
        return io.vectorToGeoWKT(self)

    @staticmethod
    def from_shapefile(fileName: str,
                       boundingBox: Optional[BoundingBox] = None,
                       boundRegionProj: Optional[core.ProjectionParameters] = None,
                       dtype: np.dtype = core.REAL):
        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        return io.shapefileToVector(fileName, boundingBox=boundingBox,
                                    boundRegionProj = boundRegionProj,
                                    dtype=dtype)

    def to_shapefile(self, fileName: str, geom_type: Optional["gs_enums.GeometryType"] = None):
        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        out = io.vectorToShapefile(self, fileName, geom_type=geom_type)
        return out

    def getPointCount(self) -> numbers.Integral:
        return self._handle.getPointCount()

    def getLineStringCount(self) -> numbers.Integral:
        return self._handle.getLineStringCount()

    def getPolygonCount(self) -> numbers.Integral:
        return self._handle.getPolygonCount()

    def getGeometryBaseCount(self) -> numbers.Integral:
        return self._handle.getGeometryBaseCount()

    @property
    def __geo_interface__(self, enforceProjection: bool = True):
        return io.vectorToGeoJson(self,
                                  enforceProjection=enforceProjection)

    @staticmethod
    def from_geopandas(other: Union[Any, str], dtype: np.dtype = core.REAL):
        obj = readers.vectorReaders.from_geopandas(other, dtype=dtype)
        return obj

    @staticmethod
    def from_fiona(other: Union[Any, str], dtype: np.dtype = core.REAL):
        obj = readers.vectorReaders.from_fiona(other, dtype=dtype)
        return obj

    @staticmethod
    def from_pyshp(other: Union[Any, str], dtype: np.dtype = core.REAL):
        obj = readers.vectorReaders.from_pyshp(other, dtype=dtype)
        return obj

    @staticmethod
    def from_ogr(other: Union[Any, str], dtype: np.dtype = core.REAL, **kwargs):
        obj = readers.vectorReaders.from_ogr(other, dtype=dtype, **kwargs)
        return obj

    def read(self, fileName: str, jsonConfig: Union[Dict, str] = "") -> None:
        """read a vector file and populate Vector object

        Parameters
        ----------
        fileName : str
            path to a vector file
        jsonConfig : Union[Dict, str], optional
            configuration parameters as json string or dictionary, by default ""
        """
        if isinstance(jsonConfig, dict):
            _jsonConfig = core.str2bytes(json.dumps(jsonConfig))
        elif isinstance(jsonConfig, str):
            _jsonConfig = core.str2bytes(jsonConfig)
        else:
            raise TypeError("Unable to deduce type of jsonConfig")

        self._handle.read(fileName, _jsonConfig)

    def write(self, fileName: str,
              writeType: Optional["gs_enums.GeometryType"] = gs_enums.GeometryType.All,
              enforceProjection: bool = True,
              writeNullProperties: bool = True) -> None:
        """write a vector file

        Parameters
        ----------
        fileName : str
            path of vector file to write
        writeType : Optional[gs_enums.GeometryType], optional
            geometry type to write, by default gs_enums.GeometryType.All
        enforceProjection: bool
            convert to EPSG:4326 when writing GeoJSON, by default True
        writeNullProperties: bool
            write null properties in vector output, by defaut True
        """
        if isinstance(writeType, gs_enums.GeometryType):
            _writeType = writeType.value
        else:
            _writeType = gs_enums.GeometryType(writeType).value

        self._handle.write(fileName, _writeType,
                           enforceProjection, writeNullProperties)

    def to_geopandas(self: Union[Any, str], **kwargs):
        obj = writers.vectorWriters.to_geopandas(self, **kwargs)
        return obj

    def clone(self, idx: int) -> int:
        """clone geometry at a given index and return index of new geometry

        Parameters
        ----------
        idx : int
            index of geometry

        Returns
        -------
        int
            index of cloned geometry
        """
        return self._handle.clone(idx)

    def buildRelations(self, geometryType: Union[int, gs_enums.GeometryType],
                      relationType: Optional[Union[int, gs_enums.RelationType]] = 0) -> None:
        """build relations between `geometry` objects in `Vector`

        Parameters
        ----------
        geometryType : Union[int, gs_enums.GeometryType]
            type of geometry objects to use for building relation
        relationType : Optional[Union[int, gs_enums.RelationType]], optional
            type of relation to build, by default 0
        """
        if not isinstance(geometryType, gs_enums.GeometryType):
            geometryType = gs_enums.GeometryType(geometryType)

        if not isinstance(relationType, gs_enums.RelationType):
            relationType = gs_enums.RelationType(relationType)

        self._handle.buildRelations(geometryType.value, relationType.value)

    def getRelationSize(self, geometryId: int) -> int:
        """get size of relation for a given geometry index

        Parameters
        ----------
        geometryId : int
            index of geometry

        Returns
        -------
        int
            relation size
        """
        return self._handle.getRelationSize(geometryId)

    def getRelationData(self, geometryId: int, idx: Optional[int] = None) -> int:
        """get relation data for a given geometry index and relation index

        Parameters
        ----------
        geometryId : int
            index of geometry
        idx : integer
            index of relation

        Returns
        -------
        int
            relation data
        """
        if idx is None:
            return np.asanyarray(self._handle.getRelationDataArray(geometryId))
        else:
            return self._handle.getRelationData(geometryId, idx)

    def __getstate__(self) -> Dict:
        output = {"vector": io.vectorToGeoJson(self, enforceProjection=False),
                  "projection_params": self.getProjectionParameters().to_dict(),
                  "dtype": self._dtype}
        return output

    def __setstate__(self, ds: Dict) -> None:
        self.__init__(io.geoJsonToVector(ds['vector'], dtype=ds['dtype'],
                                         enforceProjection=False),
                    dtype=ds['dtype'])
        self.setProjectionParameters(core.ProjectionParameters.from_dict(
            ds['projection_params']
        ))

    def __iadd__(self, other):
        if isinstance(other, Vector):
            assert self._dtype == other._dtype, "Type mismatch for Vectors"
            self._handle += other._handle
        elif any([supported_libs.HAS_GDAL, supported_libs.HAS_GPD,
                  supported_libs.HAS_FIONA, supported_libs.HAS_PYSHP]):
            obj = None
            if supported_libs.HAS_GDAL:
                if isinstance(other, (ogr.DataSource, ogr.Layer)):
                    obj = Vector.from_ogr(other, dtype=self._dtype)
            elif supported_libs.HAS_FIONA:
                if isinstance(other, fiona.Collection):
                    obj = Vector.from_ogr(other, dtype=self._dtype)
            elif supported_libs.HAS_PYSHP:
                if isinstance(other, shapefile.Reader):
                    obj = Vector.from_shapefile(other, dtype=self._dtype)
            elif supported_libs.HAS_GPD:
                if isinstance(other, (gpd.GeoDataFrame, gpd.GeoSeries)):
                    obj = Vector.from_geopandas(other, dtype=self._dtype)
            if obj is not None:
                if self.getProjectionParameters() == other.getProjectionParameters():
                    self._handle += obj._handle
                else:
                    raise ValueError(
                        "Mismatch in projection parameters of vector objects")
        else:
            raise TypeError("input argument should be a Vector")
        return self

    def __repr__(self):
        bounds_string = "\nBounding Box:\n%s" % str(self.getBounds())
        proj_string = "\nProjection Parameters:\n%s" % str(
            self.getProjectionParameters())
        geom_string = f"\nGeometry:\n    {'Points':10s}:{max(0, self.getPointCount()):4d}\n"
        geom_string += f"    {'LineString':10s}:{max(0, self.getLineStringCount()):4d}\n"
        geom_string += f"    {'Polygon':10s}:{max(0, self.getPolygonCount()):4d}"

        return "<class 'geostack.vector.%s'>%s%s%s" % (self.__class__.__name__,
                                                       geom_string,
                                                       bounds_string,
                                                       proj_string)

class VectorPtrList:
    """A container analogous to python list object.

    VectorPtrList object is a list of shared pointers of a number of Vector objects.
    The VectorPtrList object is used internally by the geostack c++ library to
    hold shared ptr to a number of Vector in a c++ vector.
    """
    def __init__(self: "VectorPtrList", *args, dtype: np.dtype=core.REAL):
        if dtype is not None:
            if dtype in [np.float64, ctypes.c_double]:
                self._handle = _VectorPtrList_d()
                self._dtype = np.float64
            elif dtype in [float, np.float32, ctypes.c_float]:
                self._handle = _VectorPtrList_f()
                self._dtype = np.float32
            else:
                raise TypeError("dtype should be np.float32 or np.float64")
        if args:
            if dtype is None:
                raise ValueError("dtype must be given when instantiating from iterable")
            if len(args) > 1:
                raise ValueError("Only one argument should be provided")
            if not isinstance(args[0], (list, tuple)):
                raise ValueError("Input argument should be a list or tuple")
            else:
                self._from_iterable(args[0])

    @singledispatchmethod
    def from_object(self, arg: "VectorPtrList"):
        raise NotImplementedError(f"Cannot cast {type(arg)} into VectorPtrList")

    @from_object.register(tuple)
    def _(self, arg: Tuple['Vector']) -> None:
        """Instantiate VectorPtrList from tuple of Vector.

        Parameters
        ----------
        arg : tuple
            A tuple of Vector object.

        Returns
        -------
        Nil
        """
        self._from_tuple(arg)

    @from_object.register(list)
    def _(self, arg: List['Vector']) -> None:
        """Instantiate VectorPtrList from list of Vector.

        Parameters
        ----------
        arg : List[Raster]
            A list of Vector objects.

        Returns
        -------
        Nil
        """
        self._from_list(arg)

    @property
    def size(self: "VectorPtrList") -> numbers.Integral:
        """Get size of the VectorPtrList.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : int
            Length of the VectorPtrList.
        """
        return self._size

    def append(self: "VectorPtrList", arg: 'Vector') -> None:
        """Append a Vector object to VectorPtrList.

        Parameters
        ----------
        arg : Vector object.
            A Vector object to append to VectorPtrList.

        Returns
        -------
        Nil
        """
        self._append(arg)

    def add_vector(self: "VectorPtrList", arg: 'Vector') -> None:
        """Add a Vector object to the VectorPtrList.

        Parameters
        ----------
        arg : Vector object
            A Vector object to be added to VectorPtrList.

        Returns
        -------
        Nil
        """
        self._add_vector(arg)

    def get_vector(self, index: int = 0) -> 'Vector':
        """_summary_

        _extended_summary_

        Parameters
        ----------
        index : int, optional
            _description_, by default 0

        Returns
        -------
        Vector
            _description_

        Raises
        ------
        IndexError
            _description_
        """
        if index < 0 or index > self.size:
            raise IndexError("Index is not valid")
        out = Vector()
        out._handle = self._handle.get_vector_from_vec(index)
        return out

    def _from_list(self, other):
        if not isinstance(other, list):
            raise TypeError('Input argument should be a list')
        self._from_iterable(other)

    def _from_tuple(self, other: Tuple["Vector"]):
        if not isinstance(other, tuple):
            raise TypeError('Input argument should be a tuple')
        self._from_iterable(other)

    def _from_iterable(self, other: Tuple["Vector"]):
        n_items = len(other)
        n_vectors = 0

        # count individual vector objects
        for item in other:
            if isinstance(item, Vector):
                n_vectors += 1

        if n_vectors > 0:
            assert n_vectors == n_items, "All element of tuple should be instances of Vector"
            for i, item in enumerate(other, 0):
                assert item._dtype == self._dtype, "Mismatch between Vector datatype and class instance"
                self._add_vector(item)

    def _append(self, other: "Vector"):
        self._add_vector(other)

    def _add_vector(self, other: "Vector"):
        if isinstance(other, Vector):
            if self._dtype != other._dtype:
                raise TypeError(
                    "mismatch between datatype of input Vector and class instance")
            self._add_vector(other._handle)
        elif isinstance(other, _Vector_d):
            if self._dtype != np.float64:
                raise TypeError(
                    "Cannot add input Vector of double type to class instance of single precision")
            self._handle.add_vector(other)

        elif isinstance(other, _Vector_f):
            if self._dtype != np.float32:
                raise TypeError(
                    "Cannot add input vector of single type to class instance of double precision")
            self._handle.add_vector(other)
        else:
            raise TypeError("input argument should be an instance of Raster")

    @property
    def _size(self) -> int:
        if self._handle is not None:
            return self._handle.get_number_of_vectors()

    def __len__(self) -> int:
        if self._handle is not None:
            return self._size

    def __add__(self, other):
        if isinstance(other, Vector):
            self._append(other)
        else:
            self._from_iterable(other)

    def __iadd__(self, other):
        if isinstance(other, Vector):
            self._append(other)
        else:
            self._from_iterable(other)

    def __getitem__(self, other: int):
        if not isinstance(other, numbers.Integral):
            raise TypeError("input argument should an integer")
        return self.get_vector(other)

    def __setitem__(self, other, value):
        raise NotImplementedError(
            "Set item operation is not supported on VectorPtrList")

    def clear(self) -> None:
        """clear vector container
        """
        self._handle.clear()

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % self.__class__.__name__
