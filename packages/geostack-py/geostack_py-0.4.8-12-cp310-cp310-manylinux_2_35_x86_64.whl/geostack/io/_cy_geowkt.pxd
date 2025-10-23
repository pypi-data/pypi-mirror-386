# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from libcpp.memory cimport unique_ptr, shared_ptr
from libcpp.string cimport string
from libcpp.vector cimport vector
from libc.stdint cimport uint16_t, uint32_t, int32_t
from ..vector._cy_vector cimport Vector, _Vector_d, _Vector_f, cl_uint
from libcpp cimport bool

cdef extern from "gs_geowkt.h" namespace "Geostack":
    cdef cppclass GeoWKT[T]:
        @staticmethod
        Vector[T] geoWKTToVector(string geoWKTStr) except +
        @staticmethod
        Vector[T] geoWKTFileToVector(string geoWKTFile) except +
        @staticmethod
        string vectorToGeoWKT(Vector[T] &v) except +
        @staticmethod
        string vectorItemToGeoWKT(Vector[T] &v, size_t index)
        @staticmethod
        vector[cl_uint] parseString(Vector[T] &v, string geoWKTStr) except +
        @staticmethod
        vector[cl_uint] parseStrings(Vector[T] &v, vector[string] geoWKTStr) except +

cdef class geoWKT_d:
    @staticmethod
    cdef _Vector_d _geoWKTToVector(string geoJson)
    @staticmethod
    cdef _Vector_d _geoWKTFileToVector(string geoWKTFile)
    @staticmethod
    cdef vector[cl_uint] _parseString(Vector[double]& v, string geoWKTStr) except *
    @staticmethod
    cdef vector[cl_uint] _parseStrings(Vector[double]& v, vector[string] geoWKTStr) except *
    @staticmethod
    cdef string _vectorToGeoWKT(_Vector_d v) except *
    @staticmethod
    cdef string _geometryToGeoWKT(_Vector_d v, size_t index) except *

cdef class geoWKT_f:
    @staticmethod
    cdef _Vector_f _geoWKTToVector(string geoWKTStr)
    @staticmethod
    cdef _Vector_f _geoWKTFileToVector(string geoWKTFile)
    @staticmethod
    cdef vector[cl_uint] _parseString(Vector[float]& v, string geoWKTStr) except *
    @staticmethod
    cdef vector[cl_uint] _parseStrings(Vector[float]& v, vector[string] geoWKTStr) except *
    @staticmethod
    cdef string _vectorToGeoWKT(_Vector_f v) except *
    @staticmethod
    cdef string _geometryToGeoWKT(_Vector_f v, size_t index) except *
