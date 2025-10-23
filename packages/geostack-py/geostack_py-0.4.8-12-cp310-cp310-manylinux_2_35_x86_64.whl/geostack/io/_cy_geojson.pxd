# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp.vector cimport vector
from libcpp cimport bool
from ..vector._cy_vector cimport Vector, _Vector_d, _Vector_f
from ..core._cy_json cimport _cy_json, Json, file_reader_c


cdef extern from "gs_geojson.h" namespace "Geostack":
    cdef cppclass GeoJson[T]:
        @staticmethod
        Vector[T] geoJsonToVector(string geoJSON, bool enforceProjection) except +
        @staticmethod
        Vector[T] geoJsonFileToVector(string geoJsonFile, bool enforceProjection) except +
        @staticmethod
        string vectorToGeoJson(Vector[T] &v, bool enforceProjection, bool writeNullProperties) except +


cdef class geoJson_d:
    @staticmethod
    cdef _Vector_d _geoJsonToVector(string geoJson, bool enforceProjection=?)
    @staticmethod
    cdef _Vector_d _geoJsonFileToVector(string geoJsonFile, bool enforceProjection=?)
    @staticmethod
    cdef string _vectorToGeoJson(_Vector_d v, bool enforceProjection=?,
                                 bool writeNullProperties=?) except *


cdef class geoJson_f:
    @staticmethod
    cdef _Vector_f _geoJsonToVector(string geoJson, bool enforceProjection=?)
    @staticmethod
    cdef _Vector_f _geoJsonFileToVector(string geoJsonFile, bool enforceProjection=?)
    @staticmethod
    cdef string _vectorToGeoJson(_Vector_f v, bool enforceProjection=?,
                                 bool writeNullProperties=?) except *
