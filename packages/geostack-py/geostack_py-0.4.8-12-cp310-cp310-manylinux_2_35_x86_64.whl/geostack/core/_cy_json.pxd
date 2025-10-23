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

from cython.operator import dereference as deref
from libcpp.string cimport string
from libcpp import nullptr_t, nullptr
from libcpp cimport bool
from libcpp.map cimport map as cpp_map
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

cdef extern from "utils.h":
    void cy_copy[T](T& a, T& b) nogil

cdef extern from "json11.hpp" namespace "json11":
    ctypedef enum JsonParse:
        STANDARD
        COMMENTS

    ctypedef enum Type:
        NUL
        NUMBER
        BOOL
        STRING
        ARRAY
        OBJECT

    cdef cppclass Json:
        ctypedef vector[Json] json_array "array"
        ctypedef cpp_map[string, Json] json_object "object"

        Json() except +
        Json(nullptr_t) except +
        Json(double value) except +
        Json(int value) except +
        Json(bool value) except +
        Json(const string &value) except +
        Json(const char *value) except +
        Json(const json_array &values) except +
        Json(const json_object &values) except +

        Type type()

        bool is_null()
        bool is_number()
        bool is_bool()
        bool is_string()
        bool is_array()
        bool is_object()

        double number_value()
        int int_value()
        bool bool_value()
        string &string_value()
        json_array &array_items()
        json_object &object_items()

        const Json & operator[](size_t i)
        const Json & operator[](const string &key)
        string dump()
        @staticmethod
        Json parse(char* inp, string& err, JsonParse strategy)
        @staticmethod
        Json parse(string& inp, string& err, JsonParse strategy)


cdef class _cy_json:
    cdef unique_ptr[Json] thisptr
    cdef unique_ptr[Json.json_object] objptr
    cdef void c_copy(self, Json.json_object inp_obj)
    cpdef string dump(self)
    cpdef void dumps(self, string out_file_name)
    cpdef void load(self, string inp_string)
    cpdef void loads(self, string inp_file_name)
    cpdef void object_items(self)
    cpdef void array_items(self)
    cpdef void string_value(self)
    cpdef bool is_null(self)
    cpdef bool is_number(self)
    cpdef bool is_bool(self)
    cpdef bool is_string(self)
    cpdef bool is_array(self)
    cpdef bool is_object(self)
    cpdef double number_value(self)
    cpdef int int_value(self)
    cpdef bool bool_value(self)
    @staticmethod
    cdef list _to_list(Json.json_array inp_arr)
    @staticmethod
    cdef dict _to_dict(Json.json_object inp_obj)
    @staticmethod
    cdef Json.json_array _from_list(list inp_list)
    @staticmethod
    cdef Json.json_object _from_dict(dict inp_dict)

cdef string file_reader_c(char* inp_file_name)
