# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os.path as pth
from typing import List, Dict
from ._cy_json import _cy_json, _parse, _from_file
from . import str2bytes
import json
from typing import Dict, Union

__all__ = ["Json11"]


class Json11(object):
    def __init__(self):
        self._handle = None

    def is_object(self):
        if self._handle is not None:
            return self._handle.is_object()

    def dump(self):
        if self._handle is None:
            raise RuntimeError("json is not yet initialized")
        out = self._handle.dump()
        if hasattr(out, 'decode'):
            return out.decode()
        else:
            return out

    def dumps(self, out_file_name: str):
        if not isinstance(out_file_name, str):
            raise TypeError("output file name should be string type")
        if not pth.exists(pth.dirname(out_file_name)):
            raise ValueError("Output file path %s does not exist" %
                             pth.dirname(out_file_name))
        if pth.exists(out_file_name):
            raise ValueError(
                "File %s exists, choose a different name or directory" % out_file_name)

        if self._handle is None:
            raise RuntimeError("json is not yet initialized")
        self._handle.dumps(str2bytes(out_file_name))

    @staticmethod
    def parse(other: str):
        if not isinstance(other, (str, bytes)):
            raise TypeError(
                "Only input of string or bytes type can be parsed to json")
        out = Json11()
        if isinstance(other, (str, bytes)):
            out._handle = _parse(str2bytes(other))
        return out

    @staticmethod
    def load(inp_string: str):
        out = Json11.parse(inp_string)
        return out

    @staticmethod
    def loads(inp_file_name: str):
        if not isinstance(inp_file_name, (str, bytes)):
            raise TypeError(
                "input file name should be of string or bytes type")
        if isinstance(inp_file_name, str):
            _inp_file_handle = inp_file_name
        elif isinstance(inp_file_name, bytes):
            _inp_file_handle = inp_file_name.decode()
        if not pth.exists(_inp_file_handle):
            raise ValueError("Input file path %s does not exist" %
                             _inp_file_handle)
        if not pth.isfile(_inp_file_handle):
            raise TypeError("Input argument is not a file")
        out = Json11()
        if isinstance(inp_file_name, (str, bytes)):
            out._handle = _from_file(str2bytes(inp_file_name))
        return out

    def keys(self) -> List[str]:
        if self._handle is not None:
            return self._handle.keys()

    def to_dict(self) -> Dict:
        if self._handle is not None:
            return self._handle.to_dict()

    @staticmethod
    def from_dict(other: Dict):
        if isinstance(other, dict):
            out = Json11()
            out._handle = _cy_json.from_dict(other)
            return out
        else:
            raise TypeError(
                "Input argument should be an instance of python dictionary")

    def __getitem__(self, other: Union[int, str]):
        if not isinstance(other, (int, str)):
            raise TypeError("Only int and string based access is available")
        if isinstance(other, int):
            if self._handle is not None:
                _out = self._handle[other]
                if isinstance(_out, _cy_json):
                    out = Json11()
                    out._handle = _out
                    return out
                else:
                    return _out
            else:
                raise RuntimeError("json is not yet initialized")
        elif isinstance(other, str):
            if self._handle is not None:
                _out = self._handle[str2bytes(other)]
                if isinstance(_out, _cy_json):
                    out = Json11()
                    out._handle = _out
                    return out
                else:
                    return _out
            else:
                raise RuntimeError("json is not yet initialized")

    def is_null(self) -> bool:
        """_summary_

        _extended_summary_

        Returns
        -------
        bool
            _description_
        """
        return self._handle.is_null()

    def __repr__(self):
        return "<class 'geostack.core.%s'>" % self.__class__.__name__


if __name__ == "__main__":
    with open('test.geojson', 'r') as inp:
        temp = json.load(inp)
    print(temp)
    out = Json11.from_dict(temp)
    print(out.to_dict())
