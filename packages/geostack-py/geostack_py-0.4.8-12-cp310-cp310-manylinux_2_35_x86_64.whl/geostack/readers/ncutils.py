# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import warnings
import os.path as pth
from itertools import chain
from ..dataset import supported_libs

requests, _ = supported_libs.import_or_skip("requests")

if supported_libs.HAS_NCDF:
    import netCDF4 as nc

if supported_libs.HAS_PYDAP:
    from pydap import model as pydap_model

__all__ = ["Pydap2NC"]


class _ncDimension:
    def __init__(self, name: str, size: int, unlimited: bool):
        self._name = name
        self._size = size
        self._unlimited = unlimited

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    @property
    def unlimited(self) -> bool:
        return self._unlimited

    def isUnlimited(self):
        return self.unlimited

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        out = f"<class 'PyDap.{self.__class__.__name__}'>"
        out += f" name = '{self.name}', size = '{self.size}'"
        return out


class _ncVariable:
    def __init__(self, name: str, dimensions, dtype, shape, dataLink):
        self._name = name
        self._dimensions = dimensions
        self._dtype = dtype
        self._shape = shape
        self._dataLink = dataLink
        self._attributes = self._dataLink.attributes
        self._attrs()

    @property
    def ncattrs(self):
        return self._dataLink.attributes.keys()

    @property
    def shape(self):
        return self._shape

    @property
    def ndim(self):
        return len(self._shape)

    @property
    def size(self):
        out = 1
        for item in self.shape:
            out *= item
        return out

    def get_dims(self):
        return self._dimensions

    def __getncattr__(self, other):
        if other in self._dataLink.attributes:
            return self._dataLink.attributes[other]
        else:
            warnings.warn(f"{other} not in the file attributes",
                          category=UserWarning)

    def __hasattr__(self, other):
        if other in self._dataLink.attributes:
            return True
        else:
            return False

    def _attrs(self):
        for item in self._dataLink.attributes:
            if not item.startswith("_"):
                setattr(self, item, self._dataLink.attributes[item])

    @supported_libs.RequireLib('pydap')
    def __getitem__(self, other):
        if isinstance(self._dataLink, pydap_model.GridType):
            return self._dataLink.array[other].data
        elif isinstance(self._dataLink, pydap_model.BaseType):
            return self._dataLink.data[other]

    @property
    def datatype(self):
        return self._dtype

    def __str__(self):
        out_str = f"<class 'PyDap.{self.__class__.__name__}'>\n"
        out_str += f"{self._dtype.name} {self._name}{str(self._dimensions)}\n"
        for item in self._attributes:
            if not item.startswith("_"):
                out_str += f"    {item}: {self._attributes[item]}\n"
        out_str += f"current shape = {str(self._shape)}\n"
        return out_str

    def __repr__(self):
        return self.__str__()


class Pydap2NC:
    @supported_libs.RequireLib("pydap")
    def __init__(self, pydap_dataset):
        self._data_handle = None
        if not isinstance(pydap_dataset, pydap_model.DatasetType):
            warnings.warn("Value of pydap_dataset should be of pydap.model.DatasetType",
                          category=UserWarning)
        else:
            self._data_handle = pydap_dataset
        self._attributes = None
        self._input_dimensions = {}
        self._input_variables = {}
        self._var1D = []
        self._varMulti = []
        self._parse()

    def _parse(self):
        if self._data_handle is not None:
            self._variables()
            self._dimensions()
            self._global_attributes()

    def _check_variables(self):
        if not len(self._var1D) > 0 or not len(self._varMulti) > 0:
            warnings.warn("Dataset variables are not yet mapped",
                          category=RuntimeWarning)
            return False
        else:
            return True

    @property
    def dimensions(self):
        return self._input_dimensions

    @property
    def variables(self):
        return self._input_variables

    @supported_libs.RequireLib('pydap')
    def _dimensions(self):
        if not self._check_variables():
            self._variables()
        if not self._check_variables():
            warnings.warn("no variables are found in the dataset",
                          category=RuntimeWarning)

        if self._attributes is None:
            self._global_attributes()

        ulim_dim_name = None
        if 'DODS_EXTRA' in self._attributes:
            if 'Unlimited_Dimensions' in self._attributes["DODS_EXTRA"]:
                ulim_dim_name = self._attributes["DODS_EXTRA"]['Unlimited_Dimensions']

        for item in self._varMulti:
            for dim in self._data_handle[item].dimensions:
                if dim in self._var1D:
                    if dim not in self._input_dimensions:
                        if ulim_dim_name is None or dim != ulim_dim_name:
                            self._input_dimensions[dim] = _ncDimension(dim,
                                                                       self._data_handle[dim].shape[0],
                                                                       False)
                        elif ulim_dim_name == dim:
                            self._input_dimensions[dim] = _ncDimension(dim,
                                                                       self._data_handle[dim].shape[0],
                                                                       True)

    @supported_libs.RequireLib("pydap")
    def _variables(self):
        if self._data_handle is not None:
            for item in self._data_handle.keys():
                if isinstance(self._data_handle[item], pydap_model.BaseType):
                    self._var1D.append(item)
                elif isinstance(self._data_handle[item], pydap_model.GridType):
                    self._varMulti.append(item)
        else:
            warnings.warn("No Dataset is found", category=RuntimeWarning)

        for item in chain(self._var1D, self._varMulti):
            self._input_variables[item] = _ncVariable(item,
                                                      self._data_handle[item].dimensions,
                                                      self._data_handle[item].dtype,
                                                      self._data_handle[item].shape,
                                                      self._data_handle[item])

    @supported_libs.RequireLib("pydap")
    def _global_attributes(self):
        if self._data_handle is not None:
            if hasattr(self._data_handle, "attributes"):
                if 'NC_GLOBAL' in getattr(self._data_handle, 'attributes'):
                    self._attributes = getattr(self._data_handle, 'attributes')[
                        'NC_GLOBAL']
            for item in self._attributes:
                if not item.startswith("_"):
                    setattr(self, item, self._attributes[item])
        else:
            warnings.warn("No Dataset is found", category=RuntimeWarning)

    def getncattrs(self):
        return self._attributes.keys()

    @supported_libs.RequireLib("netcdf")
    @supported_libs.RequireLib("pydap")
    def to_disk(self, out_file_name, chunk_size=10):
        '''
        write pydap file to local disk at out_file_name path
        '''
        if not isinstance(out_file_name, str):
            raise TypeError("out_file_name should be of string type")
        if pth.exists(out_file_name):
            raise FileExistsError(f"file {out_file_name} exist, check path")
        fileout = nc.Dataset(out_file_name, mode='w')
        for item in self.dimensions:
            if self.dimensions[item].isUnlimited():
                fileout.createDimension(item, size=None)
            else:
                fileout.createDimension(item, size=self.dimensions[item].size)
        var_handle = {}
        for item in self.variables:
            if hasattr(self.variables[item], "_FillValue"):
                var_handle[item] = fileout.createVariable(item,
                                                          self.variables[item]._dtype,
                                                          dimensions=self.variables[item]._dimensions,
                                                          zlib=True, complevel=4,
                                                          fill_value=self.variables[item].getncattr("_FillValue"))
            else:
                var_handle[item] = fileout.createVariable(item,
                                                          self.variables[item]._dtype,
                                                          dimensions=self.variables[item]._dimensions,
                                                          zlib=True, complevel=4)
            for attr in self.variables[item]._attributes:
                if not attr.startswith("_"):
                    var_handle[item].setncattr(attr,
                                               self.variables[item]._attributes[attr])
            if len(self.variables[item]._dimensions) > 2:
                nchunks = self.dimensions['time'].size // chunk_size
                chunk_idx = []
                for i in range(nchunks):
                    chunk_idx.append([i * chunk_size, (i + 1) * chunk_size])
                if chunk_size * nchunks < self.dimensions['time'].size:
                    chunk_idx.append([chunk_idx[-1][1],
                                      self.dimensions['time'].size])
                for idx in chunk_idx:
                    var_handle[item][idx[0]                                     :idx[1], ...] = self.variables[item][idx[0]:idx[1], ...]
            else:
                var_handle[item][...] = self.variables[item][...]
        fileout.setncatts(self._attributes)
        fileout.close()

    def __getattr__(self, other):
        if other in self._attributes:
            return self._attributes[other]

    def __hasattr__(self, other):
        if other in self._attributes:
            return True
        else:
            return False

    def __str__(self):
        return f"<class PyDap.{self.__class__.__name__}>"

    def __repr__(self):
        return self.__str__()
