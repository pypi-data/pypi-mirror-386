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
from libcpp.vector cimport vector
from cpython.ref cimport Py_INCREF
import numpy as np
cimport cython
cimport numpy as np

np.import_array()

ctypedef unsigned int uint32_t
ctypedef unsigned long long uint64_t
ctypedef signed int int32_t
ctypedef signed long long int64_t
ctypedef double float64_t
ctypedef float float32_t
ctypedef Py_ssize_t intp_t
ctypedef uint32_t cl_uint


cdef extern from *:
    int NPY_LIKELY(int)
    int NPY_UNLIKELY(int)

ctypedef fused vector_typed:
    vector[float64_t]
    vector[float32_t]
    vector[int32_t]
    vector[int64_t]
    vector[uint32_t]
    vector[uint64_t]
    vector[intp_t]

cdef np.ndarray vector_to_nd_array(vector_typed * vect_ptr)
