# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numpy as np
try:
    import numpy.typing as npt
    ArrayLike = npt.ArrayLike
except ImportError:
    ArrayLike = np.ndarray
import warnings
from .. import core
from ._cy_variables import _Variables_f, _Variables_d
from ._cy_variables import _Variables_i, _Variables_byt
from typing import Union, Dict, Optional
from ..utils import rpartial
from .tools import is_valid_name
from .property import REAL
from . import str2bytes

__all__ = ["Variables"]


class Variables:
    def __init__(self, dtype: Union[np.float32, np.float64,
                                    np.uint32, np.uint8] = REAL):
        self._handle = None
        if dtype == np.float32:
            self._handle = _Variables_f()
            self._dtype = np.float32
        elif dtype == np.float64:
            self._handle = _Variables_d()
            self._dtype = dtype
        elif dtype == np.uint32:
            self._handle = _Variables_i()
            self._dtype = dtype
        elif dtype == np.uint8:
            self._handle = _Variables_byt()
            self._dtype = dtype

    def set(self, var_name: Union[str, bytes, np.uint32],
            var_value: Union[float, np.float64, np.uint8, np.uint32, ArrayLike],
            index: Optional[int] = None) -> None:
        """set a value for a given variable.

        Parameters
        ----------
        var_name : Union[str, bytes, np.uint32]
            name of the variable
        var_value : Union[float, np.float64, np.uint8, np.uint32, npt.ArrayLike]
            value of the variable
        index: Optional[int], None by default
            index of array when value of variable is an array
        Returns
        -------
        Nil
        """
        assert self._handle is not None, "Variables object is not initialized"

        if not is_valid_name(var_name):
            raise ValueError(f"'{var_name}' is not a valid name for Variables")

        # create a method map
        if index is not None:
            var_value = self._dtype(var_value)
            method = rpartial(self._handle.set_index, index)
        else:
            if not np.isscalar(var_value):
                # ensure var_value is array and of correct dtype
                var_value = np.array(var_value, dtype=self._dtype)
                method = self._handle.set_array
            else:
                var_value = self._dtype(var_value)
                method = self._handle.set

        if self._dtype == np.uint32:
            assert type(var_name) in [np.uint32, int]
            method(var_name, var_value)
        elif self._dtype == np.uint8:
            assert type(var_name) in [np.uint32, int]
            method(var_name, var_value)
        else:
            if isinstance(var_name, (str, bytes)):
                method(core.str2bytes(var_name), var_value)
            else:
                raise TypeError("var_name is not of correct type")

    def get(self, var_name: Union[str, bytes, np.uint32],
            index: int = None) -> Union[np.float32, np.float64,
                                        np.uint32, np.uint8,
                                        ArrayLike]:
        """get the value of the variable

        Parameters
        ----------
        var_name : Union[str, bytes, np.uint32]
            name of the variable
        index: Optional[int], None by default
            index of array when value of variable is an array

        Returns
        -------
        Union[np.float32,np.float64,np.uint32,np.uint8,npt.ArrayLike]
            value of the variable
        """
        assert self._handle is not None, "Variables object is not initialized"

        # create a method map
        if index is not None:
            out = self._handle.get_index(var_name, index)
        else:
            var_size = self.getSize(var_name)

            if self._dtype in [np.uint32, np.uint8]:
                assert type(var_name) in [np.uint32, int]

            if var_size > 1:
                out = np.asanyarray(self._handle.get_array(var_name, var_size))
            else:
                out = self._handle.get(var_name)

        return out

    def getSize(self, var_name: Union[str, bytes, np.uint32]) -> int:
        """get size of variable

        Parameters
        ----------
        var_name : Union[str, bytes, np.uint32]
            variable name

        Returns
        -------
        int
            size of variable
        """
        if self._dtype == np.uint32:
            assert type(var_name) in [np.uint32, int]
            out = self._handle.getSize(var_name)
        elif self._dtype == np.uint8:
            assert type(var_name) in [np.uint32, int]
            out = self._handle.getSize(var_name)
        else:
            if isinstance(var_name, (str, bytes)):
                out = self._handle.getSize(core.str2bytes(var_name))
        return out

    def getIndexes(self) -> Dict:
        """get the indices of the variable

        Returns
        -------
        Dict
            a dictionary of variable and indices in the Variables object.
        """
        assert self._handle is not None, "Variable object is not initialised"
        return self._handle.getIndexes()

    @property
    def hasData(self) -> bool:
        """check if variables object has data.

        Returns
        -------
        bool
            True if Variables has data else False
        """
        assert self._handle is not None, "Variable object is not initialised"
        return self._handle.hasData()

    @staticmethod
    def from_dict(other, **kwargs):
        if not isinstance(other, dict):
            raise TypeError("input argument should be a dictionary")
        dtype = kwargs.get("dtype", REAL)
        obj = Variables(dtype=dtype)
        for item in other:
            obj[item] = other[item]
        return obj

    def update(self, other):
        if isinstance(other, dict):
            for item in other:
                self[item] = other[item]
        elif isinstance(other, Variables):
            assert other._dtype == self._dtype, "data type mismatch between the input and current object"
            idx = other.getIndexes()
            for item in idx:
                self[item] = other[item]

    def hasVariable(self, var_name: Union[str, bytes, np.uint32]) -> bool:
        """check if variable exists

        Parameters
        ----------
        var_name : Union[str, bytes, np.uint32]
            name of variables

        Returns
        -------
        bool
            True if exists, False otherwise
        """
        return self._handle.hasVariable(var_name)

    def runScript(self, script: str, var: Optional[str] = None) -> None:
        """method to compute or amend variables

        Parameters
        ----------
        script : str
            script for computing or amending variables
        var : Optional[str]
            optional variable to use as anchor

        Examples
        --------
        >>> vars = Variables()

        >>> # define vector variables
        >>> vars.set("a", list(range(10)))
        >>> vars.set("b", list(map(lambda i: i * 2, range(10))))

        >>> # define scalar variables
        >>> vars.set("c", 3.0)

        >>> # call runScript
        >>> vars.runScript("a = b * c;")
        """
        if var is None:
            var = ""
        self._handle.runScript(script, var)

    @property
    def indexes(self):
        return self.getIndexes()

    def clear(self) -> None:
        self._handle.clear()

    def __iter__(self):
        for item in self.indexes:
            yield item

    def __setitem__(self, var_name: Union[str, bytes, np.uint32],
                    var_value):
        self.set(var_name, var_value)

    def __getitem__(self, var_name: Union[str, bytes, np.uint32]):
        return self.get(var_name)

    def __contains__(self, var_name: Union[str, bytes, np.uint32]) -> bool:
        return self._handle.hasVariable(var_name)

    def __repr__(self):
        return self.__str__()

    def __getstate__(self):
        _state = {
            'dtype': self._dtype
        }
        var_data = self.getIndexes()
        for item in var_data:
            _state[item] = self.get(item)
        return _state

    def __setstate__(self, ds):
        self.__init__(ds['dtype'])
        for item in ds:
            if item != 'dtype':
                self[item] = ds[item]

    def __str__(self) -> str:
        var_data = self.getIndexes()
        var_string = []
        for item in var_data:
            if self.getSize(item) <= 1:
                var_string.append(f"    {item}:  {self.get(item)}")
            else:
                var_string.append(f"    {item}[{self.getSize(item)}]:  {self.get(item, 0)} ... {self.get(item, self.getSize(item)-1)}")
        var_string = '\n'.join(var_string)
        return "<class 'geostack.core.%s'>\n%s" % (self.__class__.__name__, var_string)
