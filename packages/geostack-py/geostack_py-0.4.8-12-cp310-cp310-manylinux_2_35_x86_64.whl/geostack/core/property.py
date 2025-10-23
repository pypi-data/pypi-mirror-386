# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import ctypes
import numpy as np
from ._cy_property import _PropertyMap, get_geostack_version
from ._cy_property import get_float_precision as _get_float_precision
from typing import Union, List, Iterable, Set, Dict, Optional
from itertools import starmap, product
import numbers
import json
import warnings
from .. import gs_enums

__all__ = ["PropertyMap", "get_geostack_version", "PropertyType",
           "FloatVector", "DoubleVector", "IntegerVector", 'ByteVector',
           "IndexVector", "StringVector", "str2bytes", "conform_type",
           "bytes2str"]

# define float precision
if _get_float_precision() == 'float':
    REAL: np.dtype = np.float32
elif _get_float_precision() == 'double':
    REAL: np.dtype = np.float64


def conform_type(s, dtype): return dtype(s)


def str2bytes(s): return f"{s}".encode("UTF-8") if isinstance(s, str) else s


def bytes2str(s): return s.decode('UTF-8') if isinstance(s, bytes) else s


class StringVector(list):
    def __init__(self, other):
        if not all(map(lambda s: isinstance(s, (str, bytes)), other)):
            raise TypeError("All items should be string")
        super().__init__(other)
        self._dtype_info = 'str'

    def append(self, other):
        if not isinstance(other, (str, bytes)):
            raise TypeError("argument should be string")
        super().append(other)

    def __iadd__(self, other):
        if not all(map(lambda s: isinstance(s, (str, bytes)), other)):
            raise TypeError("All items should be string")
        super().__iadd__(other)


class ByteVector(np.ndarray):
    def __new__(cls, input_array, dtype=np.uint8):
        obj = np.asarray(input_array, dtype=dtype).view(cls)
        obj._dtype_info = dtype
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._dtype_info = getattr(obj, '_dtype_info', None)


class IndexVector(np.ndarray):
    def __new__(cls, input_array, dtype=np.uint32):
        obj = np.asarray(input_array, dtype=dtype).view(cls)
        obj._dtype_info = dtype
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._dtype_info = getattr(obj, '_dtype_info', None)


class IntegerVector(np.ndarray):
    def __new__(cls, input_array, dtype=np.int32):
        obj = np.asarray(input_array, dtype=dtype).view(cls)
        obj._dtype_info = dtype
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._dtype_info = getattr(obj, '_dtype_info', None)


class FloatVector(np.ndarray):
    def __new__(cls, input_array, dtype=np.float32):
        obj = np.asarray(input_array, dtype=dtype).view(cls)
        obj._dtype_info = dtype
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._dtype_info = getattr(obj, '_dtype_info', None)


class DoubleVector(np.ndarray):
    def __new__(cls, input_array, dtype=np.float64):
        obj = np.asarray(input_array, dtype=dtype).view(cls)
        obj._dtype_info = dtype
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._dtype_info = getattr(obj, '_dtype_info', None)


@gs_enums.extend_obj_with_enum(gs_enums.PropertyType)
class PropertyType:
    __slots__ = ()

    dtype2vec = {int: IntegerVector,
                 np.float32: FloatVector,
                 float: FloatVector,
                 np.float64: DoubleVector,
                 np.uint32: IndexVector,
                 np.int32: IntegerVector,
                 np.uint8: ByteVector,
                 str: StringVector,
                 bytes: StringVector}

    @classmethod
    def to_pytype(cls, other: numbers.Integral) -> Optional[type]:
        """convert PropertyType enum to python data type

        Parameters
        ----------
        other : numbers.Integral
            A PropertyType enum

        Returns
        -------
        Optional[type]
            an equivalent python data type
        """
        type_map = {cls.String: str,
                    cls.Integer: int,
                    cls.Float: float,
                    cls.Double: np.float64,
                    cls.Index: np.uint32,
                    cls.Byte: np.uint8,
                    cls.StringVector: StringVector,
                    cls.ByteVector: ByteVector,
                    cls.IntegerVector: IntegerVector,
                    cls.FloatVector: FloatVector,
                    cls.DoubleVector: DoubleVector,
                    cls.IndexVector: IndexVector}
        if other == cls.Undefined:
            return
        else:
            return type_map.get(other)

    @classmethod
    def from_pytype(cls, other: Union[type, List, None]) -> numbers.Integral:
        """convert a python type to PropertyType

        Parameters
        ----------
        other : Union[type, List, None]
            a python data type

        Returns
        -------
        numbers.Integral
            an equivalent PropertyType
        """
        type_map = {str: cls.String,
                    int: cls.Integer,
                    float: cls.Float,
                    np.float64: cls.Double,
                    np.uint32: cls.Index,
                    np.uint8: cls.Byte,
                    StringVector: cls.StringVector,
                    ByteVector: cls.ByteVector,
                    IntegerVector: cls.IntegerVector,
                    FloatVector: cls.FloatVector,
                    DoubleVector: cls.DoubleVector,
                    IndexVector: cls.IndexVector}
        if other is None:
            return cls.Undefined
        else:
            return type_map.get(other)

    @classmethod
    def from_pyobject(cls, other):
        """get PropertyType from python object.

        Parameters
        ----------
        other : Union[List, numbers.Integral, numbers.Real, str, None]
            a python object

        Returns
        -------
        numbers.Integral
            an equivalent PropertyType
        """
        if other is None:
            return PropertyType.from_pytype(other)

        if np.isscalar(other) or other is None:
            return PropertyType.from_pytype(type(other))
        else:
            return PropertyType.from_pytype(PropertyType.dtype2vec[type(other[0])])


class PropertyMap:
    def __init__(self, other=None):
        if other is None:
            self._handle = _PropertyMap()
        else:
            assert isinstance(
                other, _PropertyMap), "input object should be an instance of _PropertyMap"
            self._handle = other

    @property
    def names(self) -> Set[str]:
        return self.getPropertyNames()

    def getSize(self, name: str) -> int:
        """get the size value array of a given property

        Parameters
        ----------
        name : str
            name of the property

        Returns
        -------
        int
            size of the property value vector
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        return getattr(self, cy_obj).getSize(str2bytes(name))

    def copy(self, name: str, idx_from: int, idx_to: int) -> None:
        """copy value of property from a geometry index to other

        Parameters
        ----------
        name : str
            name of the property
        idx_from : int
            source geometry index
        idx_to : int
            destination geometry index
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")
        if name in self.vectorNames:
            getattr(self, cy_obj).copy_property(
                str2bytes(name), idx_from, idx_to)

    def getPropertyNames(self) -> Set[str]:
        """get the names of property whose values are scalar.

        Returns
        -------
        Set[str]
            a set object with names of properties with scalar values
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        prop_names = getattr(self, cy_obj).getPropertyNames()
        return prop_names

    @property
    def vectorNames(self) -> Set[str]:
        return self.getPropertyVectorNames()

    def getPropertyVectorNames(self) -> Set[str]:
        """get the names of property whose values are std::vectors.

        Returns
        -------
        Set[str]
            a set object with names of properties with std::vector values
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        prop_names = getattr(self, cy_obj).getPropertyVectorNames()
        return prop_names

    def __getitem__(self, prop: str) -> Union[int, float, str,
                                              IntegerVector, FloatVector,
                                              DoubleVector, StringVector,
                                              IndexVector]:
        return self.getProperty(prop)

    def getProperty(self, prop: str, prop_type: type = None) -> Union[int, float, str,
                                                                      IntegerVector, FloatVector,
                                                                      DoubleVector, StringVector,
                                                                      IndexVector]:
        """Get a property of an object.

        Parameters
        ----------
        prop: str
            A property of a Raster or a Vector object.
        prop_type: type
            data type to cast the value of property

        Returns
        -------
        out : int/double/str
            Value of object property.

        Examples
        --------
        >>> testA = Raster(name="testRasterA")
        >>> testA.getProperty("name")
        testRasterA
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        if self.hasProperty(prop):
            prop_names = self.getPropertyNames()
            prop_vector_names = self.getPropertyVectorNames()
            _prop_type = PropertyType.to_pytype(
                getattr(self, cy_obj).getPropertyType(str2bytes(prop)))

            if (prop_names.intersection([prop]) and
                    prop not in prop_vector_names):
                method_map = {"int": getattr(self, cy_obj).getProperty_int,
                              "float": getattr(self, cy_obj).getProperty_flt,
                              "float32": getattr(self, cy_obj).getProperty_flt,
                              "float64": getattr(self, cy_obj).getProperty_dbl,
                              "str": getattr(self, cy_obj).getProperty_str,
                              "uint32": getattr(self, cy_obj).getProperty_idx}

                if prop_type is None:
                    method = method_map.get(_prop_type.__name__)
                    assert method is not None, "property type is not implemented"
                    out = method(str2bytes(prop))
                else:
                    out = method_map.get(prop_type.__name__)(str2bytes(prop))
                return out
            elif prop_vector_names.intersection([prop]):
                method_map = {"IntegerVector": getattr(self, cy_obj).getPropertyVector_int,
                              "IndexVector": getattr(self, cy_obj).getPropertyVector_idx,
                              "FloatVector": getattr(self, cy_obj).getPropertyVector_flt,
                              "DoubleVector": getattr(self, cy_obj).getPropertyVector_dbl,
                              "ByteVector": getattr(self, cy_obj).getPropertyVector_byt,
                              "StringVector": getattr(self, cy_obj).getPropertyVector_str}

                if prop_type is None:
                    _prop_type = PropertyType.to_pytype(
                        getattr(self, cy_obj).getPropertyType(str2bytes(prop)))
                    try:
                        method = method_map.get(
                            PropertyType.dtype2vec[_prop_type].__name__)
                    except Exception as e:
                        method = method_map.get(_prop_type.__name__)
                        if method is None:
                            raise e
                    assert method is not None, "property type is not implemented"
                    return np.asanyarray(method(str2bytes(prop)))
                else:
                    try:
                        return np.asanyarray(method_map.get(
                                             PropertyType.dtype2vec[prop_type].__name__)(str2bytes(prop)))
                    except (RuntimeError, SystemError) as e:
                        raise ValueError("value of prop_type is incorrect")
            else:
                raise KeyError(f"property {prop} doesn't exist")
        else:
            raise KeyError("Property %s is not attached to the object" % prop)

    def __setitem__(self, prop: Union[str, bytes], value: Union[int, float, str, IntegerVector,
                                                                FloatVector, StringVector]):
        self.setProperty(prop, value)

    def setProperty(self, prop: Union[str, bytes], value: Union[int, float, str, IntegerVector,
                                                                FloatVector, StringVector],
                    prop_type: type = None):
        """Set a property of an object.

        Parameters
        ----------
        prop : Union[str, bytes]
            A property to be set for an object.
        value : Union[int, float, str, np.ndarray[int], np.ndarray[float], List[str]]
            A value of the property to be set for an object.
        prop_type : type, optional
            A data type of the property being set for an object., by default None

        Returns
        -------
        Nil

        Raises
        ------
        TypeError
            "property name 'prop' should be of string type"
        AttributeError
            "Raster or Vector has not been created"
        TypeError
            "value of prop_type is not of acceptable type"

        Examples
        --------
        >>> testRasterA = Raster(name="testRasterA")
        >>> testRasterA.setProperty("name", "windSpeed", prop_type=str)
        """

        if not isinstance(prop, str):
            raise TypeError("property name 'prop' should be of string type")
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        if prop_type is not None:
            _prop = str2bytes(prop)

            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                # create a mapping for methods
                method_map = {"IntegerVector": getattr(self, cy_obj).setProperty_int_vector,
                              "FloatVector": getattr(self, cy_obj).setProperty_flt_vector,
                              "DoubleVector": getattr(self, cy_obj).setProperty_dbl_vector,
                              "StringVector": getattr(self, cy_obj).setProperty_str_vector,
                              "ByteVector": getattr(self, cy_obj).setProperty_byt_vector,
                              'IndexVector': getattr(self, cy_obj).setProperty_idx_vector, }

                if any([issubclass(prop_type, ctypes.c_double), issubclass(prop_type, np.float64)]):
                    getattr(self, cy_obj).setProperty_dbl_vector(
                        _prop, DoubleVector(value))
                else:
                    method = method_map.get(
                        PropertyType.dtype2vec[prop_type].__name__)
                    assert method is not None, "value of prop_type is not of acceptable type"
                    if prop_type == str:
                        method(_prop, list(
                            starmap(conform_type, product(value, [prop_type]))))
                    else:
                        method(_prop, PropertyType.dtype2vec[prop_type](value))
            else:
                # create a mapping for methods
                method_map = {"int": getattr(self, cy_obj).setProperty_int,
                              "float": getattr(self, cy_obj).setProperty_flt,
                              "float32": getattr(self, cy_obj).setProperty_flt,
                              "float64": getattr(self, cy_obj).setProperty_flt,
                              "str": getattr(self, cy_obj).setProperty_str,
                              "uint32": getattr(self, cy_obj).setProperty_idx}

                if any([issubclass(prop_type, ctypes.c_double), issubclass(prop_type, np.float64)]):
                    getattr(self, cy_obj).setProperty_dbl(
                        _prop, np.float64(value))
                else:
                    method = method_map.get(prop_type.__name__)
                    assert method is not None, "value of prop_type is not of acceptable type"
                    method(_prop, prop_type(value))
        else:
            if isinstance(value, Iterable):
                prop_type = type(value[0])
            else:
                prop_type = type(value)
            self.setProperty(prop, value, prop_type=prop_type)

    def __contains__(self, other: Union[str, bytes]) -> bool:
        return self.hasProperty(other)

    def hasProperty(self, prop: Union[str, bytes]) -> bool:
        """Check if a property is set for the object.

        Parameters
        ----------
        prop: Union[str, bytes]
            A property to be checked for an object.

        Returns
        -------
        out: bool
            True if property is set, False otherwise.

        Examples
        --------
        >>> testRasterA = Raster(name="testRasterA")
        >>> testRasterA.hasProperty("orientation")
        False
        """
        if not isinstance(prop, str):
            raise TypeError("property name 'prop' should be of string type")
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        return getattr(self, cy_obj).hasProperty(str2bytes(prop))

    def __delitem__(self, prop: Union[str, bytes]) -> None:
        self.removeProperty(prop)

    def removeProperty(self, prop: Union[str, bytes]) -> None:
        """Remove a property from the object.

        Parameters
        ----------
        prop: Union[str, bytes]
            A property to be removed from an object.

        Returns
        -------
        Nil

        Examples
        --------
        >>> testRasterA = Raster(name="testRasterA")
        >>> testRasterA.setProperty("orientation", 1)
        >>> testRasterA.hasProperty("orientation")
        True
        >>> testRasterA.removeProperty("orientation")
        >>> testRasterA.hasProperty("orientation")
        False
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        getattr(self, cy_obj).removeProperty(str2bytes(prop))

    def convertProperty(self, prop: Union[str, bytes], propType: type) -> None:
        """Convert data type of the property of an object.

        Parameters
        ----------
        prop: str
            A property of a Raster or a Vector object.
        prop_type: type
            data type to cast the value of property

        Returns
        -------
        Nil

        Examples
        --------
        >>> testA = Raster(name="testRasterA")
        >>> testA.setProperty("count", 1.0)
        >>> type(testA.getProperty("count"))
        float
        >>> testA.convertProperty("count", str)
        >>> type(testA.getProperty("count"))
        str
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        method_map = {"int": getattr(self, cy_obj).convertProperty_int_vector,
                      "float": getattr(self, cy_obj).convertProperty_flt_vector,
                      "float32": getattr(self, cy_obj).convertProperty_flt_vector,
                      "float64": getattr(self, cy_obj).convertProperty_dbl_vector,
                      "str": getattr(self, cy_obj).convertProperty_str_vector,
                      "uint32": getattr(self, cy_obj).convertProperty_idx_vector}
        assert propType.__name__ in method_map, f"propType {propType} is not valid"
        method_map.get(propType.__name__)(str2bytes(prop))

    def clear(self):
        """clear all the properties from the object

        Raises
        ------
        AttributeError
            Raster or Vector has not been created
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")
        getattr(self, cy_obj).clear()

    def getProperties(self) -> Dict:
        """Get all the properties of an object.

        Returns
        -------
        out: dict
            A dictionary containing properties and values of the properties.

        Examples
        --------
        >>> testRasterA = Raster(name="testRasterA")
        >>> testRasterA.getProperties()
        {"name": "testRasterA"}
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        _properties = getattr(self, cy_obj).getProperties()
        return _properties

    def getPropertyType(self, propName: Union[str, bytes]) -> type:
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")
        _prop_type = getattr(self, cy_obj).getPropertyType(str2bytes(propName))
        return PropertyType.to_pytype(_prop_type)

    def getPropertyStructure(self, propName: Union[str, bytes]) -> "gs_enums.PropertyStructure":
        """get the structure of property.
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")

        _prop_struct = getattr(self, cy_obj).getPropertyStructure(
            str2bytes(propName))
        return gs_enums.PropertyStructure(_prop_struct)

    def toJson(self) -> Dict:
        """get the all the properties of the object as JSON.
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")
        return json.loads(self.toJsonString())

    def toJsonString(self) -> str:
        """get the all the properties of the object as JSON string.
        """
        if hasattr(self, '_handle'):
            cy_obj = "_handle"
        else:
            raise AttributeError("Raster or Vector has not been created")
        return getattr(self, cy_obj).toJsonString()

    def __repr__(self):
        return "<class 'geostack.core.%s'>" % self.__class__.__name__
