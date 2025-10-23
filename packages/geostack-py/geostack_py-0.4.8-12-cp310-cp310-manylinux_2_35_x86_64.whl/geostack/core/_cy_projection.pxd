# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
#cython: language_level=3

from libcpp.vector cimport vector
from libcpp.string cimport string
from libc.stdint cimport uint32_t, int32_t, uint64_t
from libcpp cimport bool
from ..vector._cy_vector cimport _Coordinate_d, _Coordinate_f
from ..vector._cy_vector cimport _CoordinateVector_d, _CoordinateVector_f

cdef extern from "gs_vector.h" namespace "Geostack":
    cdef cppclass Coordinate[T]:
        Coordinate() except +
        Coordinate(Coordinate[T] &c) except +
        Coordinate(T p, T q, T r, T s) except +
        T magnitudeSquared() except +
        Coordinate[T] max_c "max"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] min_c "min"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] centroid(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T]& operator=(Coordinate[T] &c) except +
        T p, q, r, s
        string geoHashEnc32
        string getGeoHash()

cdef extern from "gs_epsg.h" namespace "Geostack":
    string projParamsFromEPSG(string EPSG) except + nogil

cdef extern from "gs_projection.h" namespace "Geostack":

    cdef cppclass ProjectionParameters[C]:
        uint32_t type   # instance data type
        uint32_t cttype # coordinate transformation type
        C a
        C f
        C x0
        C k0
        C fe
        C fn
        C phi_0
        C phi_1
        C phi_2

    cdef cppclass Projection:

        @staticmethod
        ProjectionParameters[double] parsePROJ4(string PROJ4) except +

        @staticmethod
        ProjectionParameters[double] parseWKT(string PROJ4) except +

        @staticmethod
        string toPROJ4(ProjectionParameters[double] &from_) except +

        @staticmethod
        ProjectionParameters[double] fromEPSG(string EPSG) except +

        @staticmethod
        string toWKT(ProjectionParameters[double] &from_, int crs) except +

        @staticmethod
        void convert "convert"[C](Coordinate[C] &c, ProjectionParameters[double] &to_,
                                  ProjectionParameters[double] &from_) except +

        @staticmethod
        void convert_str "convert"[C](Coordinate[C] &c, string &to_, string &from_) except +

        @staticmethod
        void convertVector "convert"[C](vector[Coordinate[C]] &c, ProjectionParameters[double] &to_,
                                        ProjectionParameters[double] &from_) except +

        @staticmethod
        void convertVector_str "convert"[C](vector[Coordinate[C]] &c, string &to_,
                                            string &from_) except +

        @staticmethod
        ProjectionParameters[double] parseProjString(string projString) except +

    bool operator==[C](ProjectionParameters[C] &l, ProjectionParameters[C] &r)
    bool operator!=[C](ProjectionParameters[C] &l, ProjectionParameters[C] &r)


cdef class _ProjectionParameters_f:
    cdef ProjectionParameters[float] *thisptr
    cdef void c_copy(self, ProjectionParameters[float] inp)

cdef class _ProjectionParameters_d:
    cdef ProjectionParameters[double] *thisptr
    cdef void c_copy(self, ProjectionParameters[double] inp)

cpdef void _convert_f(_Coordinate_f inp, _ProjectionParameters_d proj_to,
                      _ProjectionParameters_d proj_from) except *
cpdef void _convert_d(_Coordinate_d inp, _ProjectionParameters_d proj_to,
                      _ProjectionParameters_d proj_from) except *

cpdef void _convert_f_str(_Coordinate_f inp, string proj_to,
                          string proj_from) except *
cpdef void _convert_d_str(_Coordinate_d inp, string proj_to,
                          string proj_from) except *


cpdef float[:, :] _convert_points_f(float[:, :] inp, _ProjectionParameters_d proj_to,
                                    _ProjectionParameters_d proj_from) except *
cpdef double[:, :] _convert_points_d(double[:, :] inp, _ProjectionParameters_d proj_to,
                                     _ProjectionParameters_d proj_from) except *


cpdef void _convert_pointvector_f(_CoordinateVector_f inp, _ProjectionParameters_d proj_to,
                                  _ProjectionParameters_d proj_from) except *
cpdef void _convert_pointvector_d(_CoordinateVector_d inp, _ProjectionParameters_d proj_to,
                                  _ProjectionParameters_d proj_from) except *

cpdef void _convert_pointvector_f_str(_CoordinateVector_f inp,
                                      string proj_to,
                                      string proj_from) except *
cpdef void _convert_pointvector_d_str(_CoordinateVector_d inp,
                                      string proj_to,
                                      string proj_from) except *

cdef _ProjectionParameters_d _parsePROJ4_d(string proj4)
cdef _ProjectionParameters_d _parseWKT_d(string proj4)
cdef _ProjectionParameters_d _fromEPSG_d(string EPSG)
cpdef string _toPROJ4_d(_ProjectionParameters_d _proj_from) except *
cpdef string _toWKT_d(_ProjectionParameters_d _proj_from, int crs=?) except *
cpdef _ProjectionParameters_d _parseProjString(string projString)