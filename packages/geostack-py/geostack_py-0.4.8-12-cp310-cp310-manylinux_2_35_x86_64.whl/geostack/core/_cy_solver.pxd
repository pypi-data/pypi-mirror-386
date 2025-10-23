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
from libcpp.memory cimport shared_ptr, unique_ptr
from libc.stdint cimport uint8_t, uint32_t, uint64_t, int32_t, int64_t
from libcpp import nullptr_t, nullptr
from libcpp.string cimport string
from libcpp cimport bool

cdef extern from "utils.h":
    void cy_copy[T](T& a, T& b) nogil

cdef extern from "gs_solver.h" namespace "Geostack":
    cdef enum VerbosityType "Geostack::Verbosity::Type":
        NotSet = 0
        Debug = 10
        Info = 20
        Warning = 30
        Error = 40
        Critical = 50

cdef extern from "gs_solver.h" namespace "Geostack":
    bool isValid[T](T a) except + nogil
    bool isInvalid[T](T a) except + nogil

cdef extern from "gs_solver.h" namespace "Geostack":
    cdef cppclass Solver:
        Solver() except + nogil
        void setVerbose(bool verbose_) except + nogil
        void setVerboseLevel(uint8_t verbose_) except + nogil
        uint8_t getVerboseLevel() except + nogil

        @staticmethod
        Solver& getSolver() except + nogil
        string getError() except + nogil
        bool openCLInitialised() except + nogil
        size_t buildProgram(string uid, string clProgram) except +
        int getMaxWorkGroupSize(string) except + nogil
        int getAlignMemorySize(string) except + nogil
        void resetTimers() except +
        bool initOpenCL() except + nogil

        void switchTimers(string, string) except +
        void incrementTimers(string, string, double) except +
        void displayTimers() except +
        string currentTimer(string) except +
        void setHostMemoryLimit(uint64_t hostMemoryLimit_) except + nogil
        uint64_t getHostMemoryLimit() except + nogil
        void setDeviceMemoryLimit(uint64_t deviceMemoryLimit_) except + nogil
        uint64_t getDeviceMemoryLimit() except + nogil

        @staticmethod
        string processScript(string script) except + nogil
        @staticmethod
        size_t getNullHash() except + nogil
        @staticmethod
        string getTypeString[R]() except +
        @staticmethod
        string getOpenCLTypeString[R]() except +

cdef class cySolver:
    cdef Solver* thisptr
    cpdef void setVerbose(self, bool verbose_) except *
    cpdef void setVerboseLevel(self, uint8_t verbose_) except *
    cpdef uint8_t getVerboseLevel(self) except *
    cpdef void setHostMemoryLimit(self, uint64_t hostMemoryLimit_) except *
    cpdef uint64_t getHostMemoryLimit(self) except *
    cpdef void setDeviceMemoryLimit(self, uint64_t deviceMemoryLimit_) except *
    cpdef uint64_t getDeviceMemoryLimit(self) except *
    cpdef string getError(self) except *
    cpdef string processScript(self, string script) except *
    cpdef size_t getNullHash(self) except *
    cpdef bool openCLInitialised(self) except *
    cpdef bool initOpenCL(self) except *

cpdef bool isValid_flt(float a) except *
cpdef bool isValid_dbl(double a) except *
cpdef bool isValid_u32(uint32_t a) except *
cpdef bool isValid_u64(uint64_t a) except *
cpdef bool isValid_i32(int32_t a) except *
cpdef bool isValid_i64(int64_t a) except *
cpdef bool isValid_str(string a) except *

cpdef bool isInvalid_flt(float a) except *
cpdef bool isInvalid_dbl(double a) except *
cpdef bool isInvalid_u32(uint32_t a) except *
cpdef bool isInvalid_u64(uint64_t a) except *
cpdef bool isInvalid_i32(int32_t a) except *
cpdef bool isInvalid_i64(int64_t a) except *
cpdef bool isInvalid_str(string a) except *
