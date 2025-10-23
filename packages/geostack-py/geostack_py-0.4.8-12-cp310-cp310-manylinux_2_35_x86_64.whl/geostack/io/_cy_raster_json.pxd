# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from libcpp.memory cimport unique_ptr, shared_ptr, make_shared
from libcpp.string cimport string
from libcpp cimport bool
from ..raster._cy_raster cimport _cyRaster_d, _cyRaster_f
from ..raster._cy_raster cimport _cyRaster_d_i, _cyRaster_f_i
from ..raster._cy_raster cimport _cyRaster_d_byt, _cyRaster_f_byt
from libc.stdint cimport uint8_t, uint32_t

cdef extern from "gs_raster.h" namespace "Geostack":
    cdef cppclass RasterFileHandler[R, C]:
        pass

    cdef cppclass Raster[R, C]:
        void setFileInputHandler(shared_ptr[RasterFileHandler[R, C]] fileHandlerIn_) except +


cdef extern from "gs_raster_json.h" namespace "Geostack":
    cdef cppclass JsonHandler[R, C](RasterFileHandler[R, C]):
        JsonHandler() except +
        string toJson(Raster[R, C] &r, bool compress, string jsonConfig) except +
        void read(string fileName, Raster[R, C] &r, string jsonConfig) except +
        void write(string fileName, Raster[R, C] &r, string jsonConfig) except +

cdef class cyJson_d_d:
    cdef shared_ptr[JsonHandler[double, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_d r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[double, double] &r,
            shared_ptr[RasterFileHandler[double, double]] rf) except *

cdef class cyJson_f_f:
    cdef shared_ptr[JsonHandler[float, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_f r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[float, float] &r,
            shared_ptr[RasterFileHandler[float, float]] rf) except *

cdef class cyJson_d_i:
    cdef shared_ptr[JsonHandler[uint32_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_d_i r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint32_t, double] &r,
            shared_ptr[RasterFileHandler[uint32_t, double]] rf) except *

cdef class cyJson_f_i:
    cdef shared_ptr[JsonHandler[uint32_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_f_i r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint32_t, float] &r,
            shared_ptr[RasterFileHandler[uint32_t, float]] rf) except *

cdef class cyJson_d_byt:
    cdef shared_ptr[JsonHandler[uint8_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_d_byt r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint8_t, double] &r,
            shared_ptr[RasterFileHandler[uint8_t, double]] rf) except *

cdef class cyJson_f_byt:
    cdef shared_ptr[JsonHandler[uint8_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
    cpdef void toJson(self, _cyRaster_f_byt r, bool compress, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint8_t, float] &r,
            shared_ptr[RasterFileHandler[uint8_t, float]] rf) except *
