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
from libcpp.pair cimport pair as cpp_pair
from libcpp.vector cimport vector
from libc.stdint cimport uint32_t, int32_t, uint64_t, int64_t
from libcpp.iterator cimport iterator
import numpy as np
cimport cython
cimport numpy as np
from libcpp.memory cimport shared_ptr, unique_ptr, make_shared

np.import_array()

ctypedef cython.floating floating
ctypedef cython.integral integral

cdef extern from "gs_series.h" namespace "Geostack::SeriesInterpolation":
    cdef enum SeriesInterpolationType "Geostack::SeriesInterpolation::Type":
        Linear = 0
        MonotoneCubic = 1
        BoundedLinear = 2

cdef extern from "gs_series.h" namespace "Geostack::SeriesCapping":
    cdef enum SeriesCappingType "Geostack::SeriesCapping::Type":
        Uncapped = 0
        Capped = 1

cdef extern from "gs_series.h" namespace "Geostack":
    cdef cppclass SeriesItem[XTYPE, YTYPE]:
        XTYPE x
        YTYPE y

    cdef cppclass Series[X, Y]:
        Series() except +
        Series(string fileName) except +
        Series(Series &) except +
        Series& operator=(Series &) except +
        void clear() except +
        void addValue(string xval, Y yval, bool isSorted) except +
        void addValue(X xval, Y yval, bool isSorted) except +
        void addValues(vector[SeriesItem[X, Y]] newValues) except +
        void addValues(vector[cpp_pair[string, Y]] newValues) except +
        void update(bool isSorted) except +
        void updateLimits() except +
        void setBounds(Y lowerLimit, Y upperLimit) except +
        Y mean() except +
        Y total "sum"() except +
        bool isSorted() except +

        Y get_value"operator()"(X) except +
        vector[Y] get_values"operator()"(vector[X]) except +

        vector[Y] getOrdinates() except +
        vector[X] getAbscissas() except +

        X get_xMax() except +
        X get_xMin() except +
        Y get_yMax() except +
        Y get_yMin() except +

        bool inRange(X) except +
        void setName(string &name) except +
        string getName() except +
        bool isInitialised() except +
        bool isConstant() except +
        void setInterpolation(SeriesInterpolationType interp_type) except +
        void setCapping(SeriesCappingType capping_type) except +
        SeriesCappingType getCapping() except +
        SeriesInterpolationType getInterpolation() except +
        size_t getSize() except +

cdef class Series_dbl_flt:
    cdef shared_ptr[Series[double, float]] thisptr
    cdef void c_copy(self, Series[double, float]&) except *
    cpdef void clear(self)
    cpdef double[:] getAbscissas(self)
    cpdef double get_xMax(self)
    cpdef double get_xMin(self)
    cpdef float[:] getOrdinates(self)
    cpdef float get_yMax(self)
    cpdef float get_yMin(self)
    cpdef bool isInitialised(self)
    cpdef bool isConstant(self)
    cpdef string getName(self)
    cpdef void setName(self, string name)
    cpdef bool inRange(self, double x)
    cpdef void update(self, bool isSorted=?)
    cpdef void updateLimits(self)
    cpdef void setBounds(self, float lowerLimit, float upperLimit)
    cdef float get_value(self, double x)
    cdef float[:] get_values(self, double[:] x)
    cpdef void from_series(self, Series_dbl_flt other)
    cpdef void from_file(self, string filename) except *
    cpdef void setInterpolation(self, int interp_type)
    cpdef void setCapping(self, int capping_type)
    cpdef int getInterpolation(self)
    cpdef int getCapping(self)
    cpdef void add_string_value(self, string xval, float yval, bool isSorted=?)
    cpdef void add_value(self, double xval, float yval, bool isSorted=?)
    cpdef void add_values(self, double[:] xvals, float[:] yvals, bool isSorted=?)
    cpdef size_t getSize(self)
    cpdef bool isSorted(self) except *
    cpdef float total(self) except *
    cpdef float mean(self) except *

cdef class Series_dbl_dbl:
    cdef shared_ptr[Series[double, double]] thisptr
    cdef void c_copy(self, Series[double, double]&) except *
    cpdef void clear(self)
    cpdef double[:] getAbscissas(self)
    cpdef double get_xMax(self)
    cpdef double get_xMin(self)
    cpdef double[:] getOrdinates(self)
    cpdef double get_yMax(self)
    cpdef double get_yMin(self)
    cpdef bool isInitialised(self)
    cpdef bool isConstant(self)
    cpdef string getName(self)
    cpdef void setName(self, string name)
    cpdef bool inRange(self, double x)
    cpdef void update(self, bool isSorted=?)
    cpdef void updateLimits(self)
    cpdef void setBounds(self, double lowerLimit, double upperLimit)
    cdef double get_value(self, double x)
    cdef double[:] get_values(self, double[:] x)
    cpdef void from_series(self, Series_dbl_dbl other)
    cpdef void from_file(self, string filename) except *
    cpdef void setInterpolation(self, int interp_type)
    cpdef void setCapping(self, int capping_type)
    cpdef int getInterpolation(self)
    cpdef int getCapping(self)
    cpdef void add_string_value(self, string xval, double yval, bool isSorted=?)
    cpdef void add_value(self, double xval, double yval, bool isSorted=?)
    cpdef void add_values(self, double[:] xvals, double[:] yvals, bool isSorted=?)
    cpdef size_t getSize(self)
    cpdef bool isSorted(self) except *
    cpdef double total(self) except *
    cpdef double mean(self) except *

cdef class Series_int_dbl:
    cdef shared_ptr[Series[int64_t, double]] thisptr
    cdef void c_copy(self, Series[int64_t, double]&) except *
    cpdef void clear(self)
    cpdef int64_t[:] getAbscissas(self)
    cpdef int64_t get_xMax(self)
    cpdef int64_t get_xMin(self)
    cpdef double[:] getOrdinates(self)
    cpdef double get_yMax(self)
    cpdef double get_yMin(self)
    cpdef bool isInitialised(self)
    cpdef bool isConstant(self)
    cpdef string getName(self)
    cpdef void setName(self, string name)
    cpdef bool inRange(self, int64_t x)
    cpdef void update(self, bool isSorted=?)
    cpdef void updateLimits(self)
    cpdef void setBounds(self, double lowerLimit, double upperLimit)
    cdef double get_value(self, int64_t x)
    cdef double[:] get_values(self, int64_t[:] x)
    cpdef void from_series(self, Series_int_dbl other)
    cpdef void from_file(self, string filename) except *
    cpdef void setInterpolation(self, int interp_type)
    cpdef void setCapping(self, int capping_type)
    cpdef int getInterpolation(self)
    cpdef int getCapping(self)
    cpdef void add_string_value(self, string xval, double yval, bool isSorted=?)
    cpdef void add_value(self, int64_t xval, double yval, bool isSorted=?)
    cpdef void add_values(self, int64_t[:] xvals, double[:] yvals, bool isSorted=?)
    cpdef size_t getSize(self)
    cpdef bool isSorted(self) except *
    cpdef double total(self) except *
    cpdef double mean(self) except *

cdef class Series_int_flt:
    cdef shared_ptr[Series[int64_t, float]] thisptr
    cdef void c_copy(self, Series[int64_t, float]&) except *
    cpdef void clear(self)
    cpdef int64_t[:] getAbscissas(self)
    cpdef int64_t get_xMax(self)
    cpdef int64_t get_xMin(self)
    cpdef float[:] getOrdinates(self)
    cpdef float get_yMax(self)
    cpdef float get_yMin(self)
    cpdef bool isInitialised(self)
    cpdef bool isConstant(self)
    cpdef string getName(self)
    cpdef void setName(self, string name)
    cpdef bool inRange(self, int64_t x)
    cpdef void update(self, bool isSorted=?)
    cpdef void updateLimits(self)
    cpdef void setBounds(self, float lowerLimit, float upperLimit)
    cdef float get_value(self, int64_t x)
    cdef float[:] get_values(self, int64_t[:] x)
    cpdef void from_series(self, Series_int_flt other)
    cpdef void from_file(self, string filename) except *
    cpdef void setInterpolation(self, int interp_type)
    cpdef void setCapping(self, int capping_type)
    cpdef int getInterpolation(self)
    cpdef int getCapping(self)
    cpdef void add_string_value(self, string xval, float yval, bool isSorted=?)
    cpdef void add_value(self, int64_t xval, float yval, bool isSorted=?)
    cpdef void add_values(self, int64_t[:] xvals, float[:] yvals, bool isSorted=?)
    cpdef size_t getSize(self)
    cpdef bool isSorted(self) except *
    cpdef float total(self) except *
    cpdef float mean(self) except *

ctypedef SeriesItem[double, floating] series_dbl
ctypedef SeriesItem[int64_t, floating] series_int

cdef vector[cpp_pair[string, floating]] vec_of_pair(self, char[:, :] xval, floating[:] yval)
cdef vector[series_dbl] vec_of_series_dbl(self, double[:] xval, floating[:] yval)
cdef vector[series_int] vec_of_series_int(self, int64_t[:] xval, floating[:] yval)
cdef series_dbl get_series_item_dbl(double x, floating y)
cdef series_int get_series_item_int(int64_t x, floating y)
