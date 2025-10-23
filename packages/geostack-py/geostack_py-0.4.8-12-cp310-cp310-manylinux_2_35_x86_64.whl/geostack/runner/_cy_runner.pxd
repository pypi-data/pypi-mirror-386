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
from libcpp.vector cimport vector
from ..core.cpp_tools cimport reference_wrapper
from ..raster._cy_raster cimport (_RasterBaseList_d, _RasterBaseList_f,
                                  _cyRaster_d, _cyRaster_f,
                                  _cyRaster_d_i, _cyRaster_f_i,
                                  _cyRaster_d_byt, _cyRaster_f_byt)
from ..raster._cy_raster cimport _cyRasterBase_d, _cyRasterBase_f
from ..vector._cy_vector cimport Vector, _Vector_d, _Vector_f
from ..raster._cy_raster cimport Raster, RasterBase, ReductionType, RasterDebugType, RasterSortType
from libc.stdint cimport uint8_t, uint32_t
from libcpp cimport bool
cimport cython

cdef extern from "utils.h":
    void cy_copy[T](T& a, T& b) nogil

cdef extern from "gs_raster.h" namespace "Geostack":
    void runScriptNoOut[C](string script,
                           vector[reference_wrapper[RasterBase[C]]] inputRasters,
                           size_t parameters) except + nogil

    Raster[R, C] runScript[R, C](string script,
                                 vector[reference_wrapper[RasterBase[C]]] inputRasters,
                                 size_t parameters) except + nogil

    Raster[R, C] runAreaScript[R, C](string script, RasterBase[C] inputRaster,
                                     int width) except + nogil

    Vector[C] stipple[C](string script, vector[reference_wrapper[RasterBase[C]]] inputRasters,
                         vector[string] fields, uint32_t nPerCell) except + nogil

cdef extern from "gs_vector.h" namespace "Geostack":
    void runVectorScript[C](string script, Vector[C] &v,
                            vector[reference_wrapper[RasterBase[C]]] inputRasters,
                            ReductionType r, size_t parameters) except + nogil

ctypedef reference_wrapper[RasterBase[double]] RasterBaseRef_d
ctypedef reference_wrapper[RasterBase[float]] RasterBaseRef_f

ctypedef fused FusedRaster_d:
    _cyRaster_d
    _cyRasterBase_d

ctypedef fused FusedRaster_f:
    _cyRaster_f
    _cyRasterBase_f

cdef class RasterScript_d:
    @staticmethod
    cdef void _run_script_noout(bytes script,
                                _RasterBaseList_d input_rasters,
                                size_t parameters) except *
    @staticmethod
    cdef _cyRaster_d _run_script(bytes script,
                                 _RasterBaseList_d input_rasters,
                                 size_t parameters)
    @staticmethod
    cdef _cyRaster_d _run_areascript(bytes script,
                                     RasterBase[double]& input_raster,
                                     int width)

    @staticmethod
    cdef _Vector_d c_stipple(bytes script, _RasterBaseList_d input_rasters,
                             vector[string] fields, uint32_t nPerCell)

    @staticmethod
    cdef _cyRaster_d_i _run_script_i(bytes script,
                                     _RasterBaseList_d input_rasters,
                                     size_t parameters)
    @staticmethod
    cdef _cyRaster_d_i _run_areascript_i(bytes script,
                                         _cyRaster_d_i input_raster,
                                         int width)

    @staticmethod
    cdef _cyRaster_d_byt _run_script_byt(bytes script,
                                         _RasterBaseList_d input_rasters,
                                         size_t parameters)
    @staticmethod
    cdef _cyRaster_d_byt _run_areascript_byt(bytes script,
                                             _cyRaster_d_byt input_raster,
                                             int width)

cdef class RasterScript_f:
    @staticmethod
    cdef void _run_script_noout(bytes script,
                                _RasterBaseList_f input_rasters,
                                size_t parameters) except *
    @staticmethod
    cdef _cyRaster_f _run_script(bytes script,
                                 _RasterBaseList_f input_rasters,
                                 size_t parameters)
    @staticmethod
    cdef _cyRaster_f _run_areascript(bytes script,
                                     RasterBase[float]& input_raster,
                                     int width)

    @staticmethod
    cdef _Vector_f c_stipple(bytes script, _RasterBaseList_f input_rasters,
                             vector[string] fields, uint32_t nPerCell)

    @staticmethod
    cdef _cyRaster_f_i _run_script_i(bytes script,
                                     _RasterBaseList_f input_rasters,
                                     size_t parameters)
    @staticmethod
    cdef _cyRaster_f_i _run_areascript_i(bytes script,
                                         _cyRaster_f_i input_raster,
                                         int width)

    @staticmethod
    cdef _cyRaster_f_byt _run_script_byt(bytes script,
                                         _RasterBaseList_f input_rasters,
                                         size_t parameters)
    @staticmethod
    cdef _cyRaster_f_byt _run_areascript_byt(bytes script,
                                             _cyRaster_f_byt input_raster,
                                             int width)

cdef class VectorScript_d:
    @staticmethod
    cdef void _run_script_noout(bytes script,
                                _Vector_d v,
                                _RasterBaseList_d input_rasters,
                                ReductionType r,
                                size_t parameters) except *

cdef class VectorScript_f:
    @staticmethod
    cdef void _run_script_noout(bytes script,
                                _Vector_f v,
                                _RasterBaseList_f input_rasters,
                                ReductionType r,
                                size_t parameters) except *
