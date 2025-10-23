# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
#cython: language_level=3
#cython: emit_linenums=True

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.memory cimport shared_ptr
from libcpp cimport bool
from ._cy_json cimport Json, _cy_json
from ..raster._cy_raster cimport RasterBase
from ..vector._cy_vector cimport Vector
from ..raster._cy_raster cimport _RasterPtrList_d, _RasterPtrList_f
from ..vector._cy_vector cimport _VectorPtrList_d, _VectorPtrList_f

cdef extern from "gs_operation.h" namespace "Geostack":
    cdef Json readYaml(string configFile) except +

    cdef cppclass Operation[T]:
        @staticmethod
        void runFromConfigFile(string configFileName) except +

        @staticmethod
        void run(string jsonConfig, vector[shared_ptr[RasterBase[T]]]&, vector[shared_ptr[Vector[T]]]&) except +

cdef class Operation_d:
    @staticmethod
    cdef void _runFromConfigFile(string configFileName) except *

    @staticmethod
    cdef void _run(string jsonConfig, vector[shared_ptr[RasterBase[double]]] &rasters,
                  vector[shared_ptr[Vector[double]]] &vectors) except *

cdef class Operation_f:
    @staticmethod
    cdef void _runFromConfigFile(string configFileName) except *

    @staticmethod
    cdef void _run(string jsonConfig, vector[shared_ptr[RasterBase[float]]] &rasters,
                  vector[shared_ptr[Vector[float]]] &vectors) except *

cpdef _cy_json cy_readYaml(string configFile)
