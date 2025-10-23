# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
#cython: language_level=3

from libcpp.string cimport string
from libcpp.memory cimport shared_ptr, unique_ptr
from libcpp cimport bool
from ..core._cy_projection cimport ProjectionParameters, _ProjectionParameters_d
from ..vector._cy_vector cimport Vector, _Vector_d, _Vector_f, _BoundingBox_f, _BoundingBox_d
from ..vector._cy_vector cimport BoundingBox
from ..raster._cy_raster cimport GeometryType

cdef extern from "gs_shapefile.h" namespace "Geostack":
    cdef cppclass ShapeFile[T]:
        @staticmethod
        Vector[T] shapefileToVector(string shapefileName, string jsonConfig) except *
        @staticmethod
        Vector[T] shapefileToVectorWithBounds(string shapefileName, BoundingBox[T] &bounds,
            ProjectionParameters[double] &boundRegionProj, string jsonConfig) except *
        @staticmethod
        bool vectorToShapefile(Vector[T] &v, string shapefileName, GeometryType) except +

cdef class shapefile_f:
    @staticmethod
    cdef _Vector_f _shapefileToVectorWithBounds(string shapefileName, BoundingBox[float] &bounds,
        ProjectionParameters[double] &boundRegionProj, string jsonConfig)
    @staticmethod
    cdef _Vector_f _shapefileToVector(string shapefileName, string jsonConfig)
    @staticmethod
    cdef bool _vectorToShapefile(_Vector_f v, string shapefileName, GeometryType) except *

cdef class shapefile_d:
    @staticmethod
    cdef _Vector_d _shapefileToVectorWithBounds(string shapefileName, BoundingBox[double] &bounds,
        ProjectionParameters[double] &boundRegionProj, string jsonConfig)
    @staticmethod
    cdef _Vector_d _shapefileToVector(string shapefileName, string jsonConfig)
    @staticmethod
    cdef bool _vectorToShapefile(_Vector_d v, string shapefileName, GeometryType) except *
