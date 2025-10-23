# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from cython.operator import dereference as deref
from libcpp.string cimport string
from libc.string cimport memcpy
from libcpp cimport bool
from libcpp.map cimport map as cpp_map
from libcpp.set cimport set as cpp_set
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, unique_ptr, make_shared
from libc.stdint cimport uint8_t, uint32_t
from ._cy_json cimport Json, _cy_json
import numpy as np
cimport cython
cimport numpy as np
from .cpp_tools cimport reference_wrapper

np.import_array()

ctypedef uint32_t cl_uint
ctypedef uint8_t cl_uchar

cdef extern from "gs_opencl.h":
    cdef string FLOAT_PRECISION

cdef extern from "gs_version.h":
    cdef string GEOSTACK_VER
    cdef int GEOSTACK_VER_MAJOR
    cdef int GEOSTACK_VER_MINOR
    cdef int GEOSTACK_VER_PATCH

cdef extern from "gs_property.h" namespace "Geostack::PropertyType":
    cdef enum PropertyType "Geostack::PropertyType::Type":
        UndefinedPropType "Undefined" = 0
        String = 1
        Integer = 2
        Float = 3
        Double = 4
        Index = 5
        Byte = 6
        FloatVector = 7
        DoubleVector = 8
        Map = 9

cdef extern from "gs_property.h" namespace "Geostack::PropertyStructure":
    cdef enum PropertyStructure "Geostack::PropertyStructure::Type":
        UndefinedPropStruct "Undefined" = 0
        Scalar = 1
        Vector = 2

cdef extern from "gs_property.h" namespace "Geostack":
    cdef cppclass PropertyBase:
        PropertyBase() except + nogil
        PropertyType getType[P]() except +
        PropertyStructure getStructure[P]() except +
        R convert[P, R](const P) except +

    cdef cppclass PropertyUndefined(PropertyBase):
        PropertyBase* clone() except +

    cdef cppclass Property[P](PropertyBase):
        Property() except + nogil
        Property(P v) except + nogil
        Property(const Property &r) except +
        Property& operator=(const Property &r) except +
        R get[R]() except +
        P& getRef() except +
        void set[R](const R v) except +
        void clear() except +
        PropertyBase* clone() except +

    cdef cppclass PropertyVector[P](PropertyBase):
        PropertyVector() except +
        P& getRef() except +

    cdef cppclass PropertyMap:
        PropertyMap() except + nogil
        PropertyMap(const PropertyMap &r) except + nogil
        PropertyMap& operator=(const PropertyMap &r) except +
        void addProperty(string name) except +
        void setProperty[P](string name, P v) except +
        cpp_map[string, P] getProperties[P]() except +
        cpp_set[string] getUndefinedProperties() except +
        P getProperty[P](string name) except +
        P getPropertyFromVector[P](string name, size_t index) except +
        P& getPropertyRef[P](string name) except +
        void removeProperty(string name) except +
        void clear() except +
        void resize(size_t size) except +
        cpp_set[string] getPropertyNames() except +
        cpp_set[string] getPropertyVectorNames() except +
        cpp_map[string, reference_wrapper[P]] getPropertyRefs[P]() except +
        PropertyType getPropertyType(string name) except +
        PropertyStructure getPropertyStructure(string name) except +
        bool hasProperty(string name) except +
        void convertProperty[P](string name) except +
        Json toJson() except +
        string toJsonString() except +
        size_t getSize(string name) except +
        void copy(string name, size_t, size_t) except +


cdef class _PropertyMap:

    cdef PropertyMap *thisptr
    @staticmethod
    cdef _PropertyMap c_copy(PropertyMap other)
    cpdef void addProperty(self, string name) except *
    cpdef void removeProperty(self, string name) except *
    cpdef void clear(self) except *
    cpdef void resize(self, size_t) except *
    cpdef bool hasProperty(self, string name) except *
    cpdef set getPropertyNames(self)
    cpdef set getPropertyVectorNames(self)
    cpdef set getUndefinedProperties(self)
    cpdef PropertyType getPropertyType(self, string name) except *
    cpdef PropertyStructure getPropertyStructure(self, string name) except *
    cpdef string toJsonString(self) except *
    cpdef size_t getSize(self, string name) except *
    cpdef void copy_property(self, string name, size_t idx_from, size_t idx_to) except *
    # method to converty property vector
    cpdef void convertProperty_int_vector(self, string name) except *
    cpdef void convertProperty_flt_vector(self, string name) except *
    cpdef void convertProperty_dbl_vector(self, string name) except *
    cpdef void convertProperty_idx_vector(self, string name) except *
    cpdef void convertProperty_str_vector(self, string name) except *
    cpdef void convertProperty_byt_vector(self, string name) except *
    # method to set property
    cpdef void setProperty_int(self, string name, int v) except *
    cpdef void setProperty_flt(self, string name, float v) except *
    cpdef void setProperty_dbl(self, string name, double v) except *
    cpdef void setProperty_str(self, string name, string v) except *
    cpdef void setProperty_idx(self, string name, cl_uint v) except *
    cpdef void setProperty_byt(self, string name, cl_uchar v) except *
    # set property where value is a vector
    cdef void _setProperty_int_vector(self, string name, vector[int] v) except *
    cdef void _setProperty_flt_vector(self, string name, vector[float] v) except *
    cdef void _setProperty_dbl_vector(self, string name, vector[double] v) except *
    cdef void _setProperty_str_vector(self, string name, vector[string] v) except *
    cdef void _setProperty_idx_vector(self, string name, vector[cl_uint] v) except *
    cdef void _setProperty_byt_vector(self, string name, vector[cl_uchar] v) except *
    # method to get property
    cpdef int getProperty_int(self, string name) except *
    cpdef float getProperty_flt(self, string name) except *
    cpdef double getProperty_dbl(self, string name) except *
    cpdef string getProperty_str(self, string name) except *
    cpdef cl_uint getProperty_idx(self, string name) except *
    cpdef cl_uchar getProperty_byt(self, string name) except *
    # method to get property from vector
    cpdef int getPropertyFromVector_int(self, string name, size_t index) except *
    cpdef float getPropertyFromVector_flt(self, string name, size_t index) except *
    cpdef double getPropertyFromVector_dbl(self, string name, size_t index) except *
    cpdef string getPropertyFromVector_str(self, string name, size_t index) except *
    cpdef cl_uint getPropertyFromVector_idx(self, string name, size_t index) except *
    cpdef cl_uchar getPropertyFromVector_byt(self, string name, size_t index) except *
    # method to get the properties
    cpdef dict getProperties_int(self)
    cpdef dict getProperties_flt(self)
    cpdef dict getProperties_dbl(self)
    cpdef dict getProperties_str(self)
    cpdef dict getProperties_idx(self)
    cpdef dict getProperties_byt(self)
    # method to get property ref when value is vector
    cdef vector[int] getPropertyRef_int_vector(self, string name) except *
    cdef vector[float] getPropertyRef_flt_vector(self, string name) except *
    cdef vector[double] getPropertyRef_dbl_vector(self, string name) except *
    cdef vector[string] getPropertyRef_str_vector(self, string name) except *
    cdef vector[cl_uint] getPropertyRef_idx_vector(self, string name) except *
    cdef vector[cl_uchar] getPropertyRef_byt_vector(self, string name) except *
