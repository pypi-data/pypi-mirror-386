# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from libcpp.memory cimport unique_ptr
from libcpp.string cimport string
from libcpp cimport bool
from ..raster._cy_raster cimport _cyRaster_f, _cyRaster_d
from ..raster._cy_raster cimport _cyRaster_d_i, _cyRaster_f_i
from ..raster._cy_raster cimport _cyRaster_d_byt, _cyRaster_f_byt
from libc.stdint cimport uint8_t, uint32_t

cdef extern from "gs_raster.h" namespace "Geostack":
    cdef cppclass Raster[R, C]:
        pass

    cdef cppclass RasterFileHandler[R, C]:
        pass

cdef extern from "gs_flt.h" namespace "Geostack":
    cdef cppclass FltHandler[R, C](RasterFileHandler[R, C]):
        FltHandler() except +
        void read(string fileName, Raster[R, C] &r, string jsonConfig) except +
        void write(string fileName, Raster[R, C] &r, string jsonConfig) except +

cdef class cyFlt_d_d:
    cdef unique_ptr[FltHandler[double, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d r, string jsonConfig) except *

cdef class cyFlt_f_f:
    cdef unique_ptr[FltHandler[float, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f r, string jsonConfig) except *

cdef class cyFlt_d_i:
    cdef unique_ptr[FltHandler[uint32_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *

cdef class cyFlt_f_i:
    cdef unique_ptr[FltHandler[uint32_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *

cdef class cyFlt_d_byt:
    cdef unique_ptr[FltHandler[uint8_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *

cdef class cyFlt_f_byt:
    cdef unique_ptr[FltHandler[uint8_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
