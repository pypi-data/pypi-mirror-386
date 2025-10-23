# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
#cython: language_level=3

from cython.operator import dereference as deref
from libcpp.string cimport string
from libcpp cimport bool
from libcpp.map cimport map as cpp_map
from libcpp.set cimport set as cpp_set
from libcpp.set cimport pair as cpp_pair
from libcpp.vector cimport vector
from libc.stdint cimport uint8_t, uint16_t, uint32_t, int32_t, uint64_t
from libcpp.functional cimport function
from libcpp.iterator cimport iterator
from libc.string cimport memset
import numpy as np
cimport cython
cimport numpy as np
from libcpp.memory cimport shared_ptr, unique_ptr, make_shared

np.import_array()

ctypedef uint8_t cl_uchar
ctypedef uint16_t cl_uint16
ctypedef uint32_t cl_uint

cdef extern from "gs_variables.h" namespace "Geostack":

    cdef cppclass VariablesBase[C]:
        pass

    cdef cppclass Variables[R, C](VariablesBase[C]):
        Variables() except + nogil
        C set(C key, R value) except + nogil
        C set_index "set" (C key, R value, size_t index) except +
        R get(C key) except + nogil
        R get_index "get" (C key, size_t index) except +
        cpp_map[C, size_t]& getIndexes() except + nogil
        bool hasData() except + nogil
        size_t getSize(C key) except +
        bool hasVariable(C key) except +
        void clear() except +
        void runScript(string script, string var) except +

    cdef cppclass VariablesVector[R]:
        VariablesVector() except + nogil
        vector[R]& getData() except +
        void clear() except + nogil
        size_t size() except + nogil
        VariablesVector[R]* clone() except + nogil

cdef class _Variables_f:
    cdef shared_ptr[Variables[float, string]] thisptr
    cpdef float get(self, string name) except *
    cpdef void set(self, string name, float value) except *
    cpdef float get_index(self, string name, size_t index) except *
    cpdef void set_index(self, string name, float value, size_t index) except *
    cpdef float[:] get_array(self, string name, size_t) except *
    cpdef void set_array(self, string name, float[:] value) except *
    cpdef size_t getSize(self, string name) except *
    cpdef dict getIndexes(self)
    cpdef bool hasData(self) except *
    cpdef bool hasVariable(self, string name) except *
    cpdef void clear(self) except *
    cpdef void runScript(self, string, string) except *

cdef class _Variables_d:
    cdef shared_ptr[Variables[double, string]] thisptr
    cpdef double get(self, string name) except *
    cpdef void set(self, string name, double value) except *
    cpdef double get_index(self, string name, size_t index) except *
    cpdef void set_index(self, string name, double value, size_t index) except *
    cpdef double[:] get_array(self, string name, size_t) except *
    cpdef void set_array(self, string name, double[:] value) except *
    cpdef size_t getSize(self, string name) except *
    cpdef dict getIndexes(self)
    cpdef bool hasData(self) except *
    cpdef bool hasVariable(self, string name) except *
    cpdef void clear(self) except *
    cpdef void runScript(self, string, string) except *

cdef class _Variables_byt:
    cdef shared_ptr[Variables[cl_uchar, uint32_t]] thisptr
    cpdef cl_uchar get(self, uint32_t name) except *
    cpdef void set(self, uint32_t name, cl_uchar value) except *
    cpdef cl_uchar get_index(self, uint32_t name, size_t index) except *
    cpdef void set_index(self, uint32_t name, cl_uchar value, size_t index) except *
    cpdef cl_uchar[:] get_array(self, uint32_t name, size_t) except *
    cpdef void set_array(self, uint32_t name, cl_uchar[:] value) except *
    cpdef size_t getSize(self, uint32_t name) except *
    cpdef dict getIndexes(self)
    cpdef bool hasData(self) except *
    cpdef bool hasVariable(self, uint32_t name) except *
    cpdef void clear(self) except *
    cpdef void runScript(self, string, string) except *

cdef class _Variables_i:
    cdef shared_ptr[Variables[cl_uint, uint32_t]] thisptr
    cpdef cl_uint get(self, uint32_t name) except *
    cpdef void set(self, uint32_t name, cl_uint value) except *
    cpdef cl_uint get_index(self, uint32_t name, size_t index) except *
    cpdef void set_index(self, uint32_t name, cl_uint value, size_t index) except *
    cpdef cl_uint[:] get_array(self, uint32_t name, size_t) except *
    cpdef void set_array(self, uint32_t name, cl_uint[:] value) except *
    cpdef size_t getSize(self, uint32_t name) except *
    cpdef dict getIndexes(self)
    cpdef bool hasData(self) except *
    cpdef bool hasVariable(self, uint32_t name) except *
    cpdef void clear(self) except *
    cpdef void runScript(self, string, string) except *

cdef class _VariablesVector_f:
    cdef shared_ptr[VariablesVector[float]] thisptr
    cpdef float[:] getData(self) except *
    cpdef size_t size(self) except *
    cpdef void clear(self) except *

cdef class _VariablesVector_d:
    cdef shared_ptr[VariablesVector[double]] thisptr
    cpdef double[:] getData(self) except *
    cpdef size_t size(self) except *
    cpdef void clear(self) except *

cdef class _VariablesVector_i:
    cdef shared_ptr[VariablesVector[cl_uint]] thisptr
    cpdef uint32_t[:] getData(self) except *
    cpdef size_t size(self) except *
    cpdef void clear(self) except *
