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
from libc.stdint cimport uint8_t, uint16_t, uint32_t, int32_t
from libcpp cimport bool
from ..raster._cy_raster cimport _cyRaster_d, _cyRaster_f
from ..raster._cy_raster cimport _cyRaster_d_i, _cyRaster_f_i
from ..raster._cy_raster cimport _cyRaster_d_byt, _cyRaster_f_byt

cdef extern from "gs_raster.h" namespace "Geostack":
   cdef cppclass RasterFileHandler[R, C]:
        pass
   cdef cppclass Raster[R, C]:
        void setFileInputHandler(shared_ptr[RasterFileHandler[R, C]] fileHandlerIn_) except +

cdef extern from "gs_geotiff.h" namespace "Geostack::GeoTIFFDataTypes":
    cdef enum GeoTIFFDataTypes "Type":
        Byte = 1
        Ascii = 2
        Short = 3
        Long = 4
        Rational = 5
        SByte = 6
        Undefined = 7
        SShort = 8
        SLong = 9
        SRational = 10
        FFloat "Float" = 11
        Double = 12

cdef extern from "gs_geotiff.h" namespace "Geostack::GeoTIFFCompressionTypes":
    cdef enum GeoTIFFCompressionTypes "Type":
        Uncompressed = 1
        CCITT_1D = 2
        Group_3_Fax = 3
        Group_4_Fax = 4
        LZW = 5
        OldJPEG = 6
        NewJPEG = 7
        Deflate = 8
        PackBits = 32773

cdef extern from "gs_geotiff.h" namespace "Geostack::GeoTIFFPredictorTypes":
    cdef enum GeoTIFFPredictorTypes "Type":
        None = 1
        HorizontalDifferencing = 2
        FloatingPoint = 3

cdef extern from "gs_geotiff.h" namespace "Geostack::GeoTIFFSampleTypes":
    cdef enum GeoTIFFSampleTypes "Type":
        UnsignedInt = 1
        SignedInt = 2
        Float = 3

cdef extern from "gs_geotiff.h" namespace "Geostack":
    cdef cppclass GeoTIFFDirectory:
        GeoTIFFDirectory() except +
        GeoTIFFDirectory(GeoTIFFDataTypes dtype, uint32_t length, uint32_t value) except +
        uint16_t getType() except +
        uint32_t getSize() except +
        uint32_t getLength() except +
        vector[uint32_t] GeoTIFFDataSizes

    cdef cppclass GeoTIFFHandler[R, C](RasterFileHandler[R, C]):
        GeoTIFFHandler() except +
        void read(string fileName, Raster[R, C] &r, string jsonConfig) except +
        void write(string fileName, Raster[R, C] &r, string jsonConfig) except +

cdef class cyGeoTIFF_d_d:
    cdef shared_ptr[GeoTIFFHandler[double, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[double, double] &r,
            shared_ptr[RasterFileHandler[double, double]] rf) except *

cdef class cyGeoTIFF_f_f:
    cdef shared_ptr[GeoTIFFHandler[float, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[float, float] &r,
            shared_ptr[RasterFileHandler[float, float]] rf) except *

cdef class cyGeoTIFF_d_i:
    cdef shared_ptr[GeoTIFFHandler[uint32_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_i r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint32_t, double] &r,
            shared_ptr[RasterFileHandler[uint32_t, double]] rf) except *

cdef class cyGeoTIFF_f_i:
    cdef shared_ptr[GeoTIFFHandler[uint32_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_i r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint32_t, float] &r,
            shared_ptr[RasterFileHandler[uint32_t, float]] rf) except *

cdef class cyGeoTIFF_d_byt:
    cdef shared_ptr[GeoTIFFHandler[uint8_t, double]] thisptr
    cpdef void read(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_d_byt r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint8_t, double] &r,
            shared_ptr[RasterFileHandler[uint8_t, double]] rf) except *

cdef class cyGeoTIFF_f_byt:
    cdef shared_ptr[GeoTIFFHandler[uint8_t, float]] thisptr
    cpdef void read(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
    cpdef void write(self, string fileName, _cyRaster_f_byt r, string jsonConfig) except *
    cdef void setFileInputHandler(self, Raster[uint8_t, float] &r,
            shared_ptr[RasterFileHandler[uint8_t, float]] rf) except *
