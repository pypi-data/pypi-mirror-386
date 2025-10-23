# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import numpy as np
from .. import core
from ..definitions import GeometryType
from typing import Dict, Union
from .vector import (Coordinate, Vector, RTree, KDTree,
                     BoundingBox, _BoundingBox_d,
                     _BoundingBox_f, IndexList,
                     triangles_to_indices_d,
                     triangles_to_indices_f,
                     CoordinateVector,
                     VectorPtrList)


def triangles_to_indices(points: Vector, triangles: Vector) -> np.ndarray:
    """Get the Point indices for the coordinates of triangles

    Parameters
    ----------
    points : Vector
        an instance of Vector object with Point geometry
        (used for delaunay triangulation)
    triangles : Vector
        an instance of Vector object with Polygon geometry
        (from delaunay triangulation)

    Returns
    -------
    np.ndarray
        a ndarray with indices of the Point coordinates
    """
    dtype = points._dtype
    if dtype == np.float32:
        method = triangles_to_indices_f
    else:
        method = triangles_to_indices_d
    out = np.asanyarray(method(points._handle, triangles._handle))
    return out


def get_polygon_neighbours(polygon: Vector) -> Dict:
    """get the neighbouring polygon to each polygon geometry

    Parameters
    ----------
    polygon : Vector
        a Vector object with Polgyon geometries

    Returns
    -------
    Dict
        a dictionary with polygon indices and list of indices of neighbours
    """
    segmentToPolygonsArray = {}

    for i in polygon.getPolygonIndexes():
        for coord in polygon.getPolygonCoordinates(i):
            nNodes = len(coord)
            for j in range(nNodes-1): # Note the final node repeats the first
                start = coord[j, :2]
                end = coord[j+1, :2]

                # Order the segment nodes by minimum coordinate x and y.
                if((end[0] < start[0]) or (start[0] == end[0] and start[1] < end[1])):
                    segment = (*end, *start)
                else:
                    # Segment tuple
                    segment = (*start, *end)

                if segment not in segmentToPolygonsArray:
                    segmentToPolygonsArray[segment] = [i]
                else:
                    segmentToPolygonsArray[segment].append(i)

    # A dictionary of polygon indices that maps to an array of connected polygon indices
    polygonsConnected = {}

    max_size = 0
    for segment in segmentToPolygonsArray:
        for p0 in segmentToPolygonsArray[segment]:
            for p1 in segmentToPolygonsArray[segment]:
                if p0 != p1:
                    polygonsConnected.setdefault()
                    if p0 not in polygonsConnected:
                        polygonsConnected[p0] = [p1]
                    elif p1 not in polygonsConnected[p0]:
                        polygonsConnected[p0].append(p1)
                    max_size = max(len(polygonsConnected[p0]), max_size)

    out = np.full((len(polygonsConnected), max_size), -1)
    for id in sorted(polygonsConnected):
        out[id, :len(polygonsConnected[id])] = polygonsConnected[id]

    return out


class Delaunay:
    def __init__(self, points: Union[np.ndarray, Vector],
                 dtype=core.REAL):
        """create a delaunay triangulation from a Vector object

        Parameters
        ----------
        points : Union[np.ndarray, Vector]
            _description_
        dtype : _type_, optional
            _description_, by default np.float32
        """
        if isinstance(points, Vector):
            self._vec = Vector(points)
        else:
            # create a Vector
            self._vec = Vector(dtype=dtype)
            self._vec.addPoints(points)

    @property
    def triangles(self) -> Vector:
        """create delaunay triangulation

        Returns
        -------
        Vector
            a Vector object with delaunay triangulation
        """
        # create a Delaunay Triangulation
        _triang = self._vec.convert(GeometryType.Polygon)
        return _triang

    @property
    def simplices(self) -> np.ndarray:
        """get simplices from a delaunay triangulation

        Returns
        -------
        np.ndarray
            a ndarray with indices of point coordinates
        """
        out = triangles_to_indices(self._vec, self.triangles)
        return out

    @property
    def edges(self) -> Vector:
        """get edges of triangles from a delaunay triangulation

        Returns
        -------
        Vector
            a Vector object with linestrings
        """
        _edges = self._vec.convert(GeometryType.LineString)
        return _edges

    @property
    def hull(self) -> Vector:
        """get hull of a delaunay triangulation

        Returns
        -------
        Vector
            a Vector object with polygon containing the hull of triangulation
        """
        _hull = self.triangles.convert(GeometryType.Polygon)
        return _hull

    @property
    def neighbours(self) -> np.ndarray:
        """get neighbouring polygon of triangles in the delaunay triangulation

        Returns
        -------
        np.ndarray
            a ndarray with indices of neighbouring triangles
        """
        out = get_polygon_neighbours(self.triangles)
        return out

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self):
        return "<class 'geostack.vector.%s'>" % (self.__class__.__name__)
