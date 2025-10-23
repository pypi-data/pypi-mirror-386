# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
from enum import Enum, unique
import warnings
import numbers
from typing import Union, List, Tuple, Dict, Optional, Set, Generator
from itertools import product
import numpy as np
import numpy.typing as npt
from .. import core
from .. import gs_enums
from .. import io as geostack_io
from . import raster
from ..vector import vector, _cy_vector
from ._cy_raster import (DataFileHandler_f, DataFileHandler_d,
                         DataFileHandler_d_i, DataFileHandler_f_i,
                         DataFileHandler_d_byt, DataFileHandler_f_byt,
                         TileSpecifications)
from ._cy_raster import (_cyRaster_d, _cyRaster_f,
                         _cyRaster_d_i, _cyRaster_f_i,
                         _cyRaster_d_byt, _cyRaster_f_byt)
from ._cy_raster import _cyRasterBase_d, _cyRasterBase_f
from ..runner import runScript, stipple
from pathlib import PurePath
from ..dataset.supported_libs import RequireLib

__all__ = ['RasterKind', "_RasterBase",
           "draw_raster_sample", "_Raster_list"]


@unique
class RasterKind(Enum):
    Raster1D: numbers.Integral = 1
    Raster2D: numbers.Integral = 2
    Raster3D: numbers.Integral = 3

    def __eq__(self, other: Union[numbers.Integral, 'RasterKind']):
        if isinstance(other, numbers.Integral):
            return self.value == other
        else:
            return self == other

    def __req__(self, other: Union[numbers.Integral, 'RasterKind']):
        if isinstance(other, numbers.Integral):
            return other == self.value
        else:
            return other == self


def draw_raster_sample(inpRaster: Union['raster.Raster', 'raster.RasterFile'],
                       sampleSize: int, xy: bool = False,
                       inpVector: Optional['vector.Vector'] = None,
                       na_rm: bool = True) -> Union[npt.NDArray, 'vector.Vector']:
    """sample a Raster object

    Parameters
    ----------
    inpRaster : Union[raster.Raster, raster.RasterFile]
        an instance of a Raster object
    sampleSize: int
        size of random sample
    xy: bool, default is False
        flag to return xy coordinate of sample location
    inpVector: vector.Vector
        an instance of inputVector to make Raster object
    na_rm: bool, default is True
        flag to remove missing values

    Returns
    -------
    Union[npt.NDArray, vector.Vector]
        a ndarary or Vector object with sample values of Raster
    """
    nx = inpRaster.dimensions.nx
    ny = inpRaster.dimensions.ny

    x_size = int(np.ceil(np.sqrt(sampleSize)))
    y_size = sampleSize // x_size
    y_size += sampleSize - (x_size * y_size)

    # create random index
    x_idx = np.random.randint(0, nx, size=2 * x_size)
    y_idx = np.random.randint(0, ny, size=2 * y_size)
    x_idx, y_idx = np.meshgrid(x_idx, y_idx)
    random_idx = np.c_[x_idx.ravel(), y_idx.ravel()]
    z_total = random_idx[:, 0] + random_idx[:, 1] * ny
    random_idx = random_idx[np.isin(z_total, np.unique(z_total))]

    # draws random sample and set values in a Vector
    if xy:
        out_vec = vector.Vector(dtype=inpRaster.data_type)
        out_vec.setProjectionParameters(inpRaster.getProjectionParameters())
    else:
        out_vec = np.empty(shape=(sampleSize), dtype=inpRaster.data_type)

    count = 0

    for item in random_idx:
        if xy:
            # create x, y coordinate when xy = True
            coords = [inpRaster.dimensions.ox + inpRaster.dimensions.hx * item[0],
                      inpRaster.dimensions.oy + inpRaster.dimensions.hy * item[1]]

        # get raster cell value
        propValue = inpRaster.getCellValue(item[0], item[1], 0)

        if na_rm:
            # remove missing value
            if not np.isnan(propValue):
                if xy:
                    pidx = out_vec.addPoint(coords)
                    out_vec.setProperty(pidx, inpRaster.name, propValue)
                else:
                    out_vec[count] = propValue
                count += 1
        else:
            if xy:
                pidx = out_vec.addPoint(coords)
                out_vec.setProperty(pidx, inpRaster.name, propValue)
            else:
                out_vec[count] = propValue
            count += 1

        if count == sampleSize:
            break

    return out_vec


class _RasterBase(core.PropertyMap, np.lib.mixins.NDArrayOperatorsMixin):
    def __init__(self: "_RasterBase", base_type: np.dtype, data_type: np.dtype):
        self._dtype: np.dtype = None
        self._handle = None
        self._has_input_handler = False
        self.tileNum: int = 0
        self.base_type: np.dtype = base_type
        self.data_type: np.dtype = data_type
        self._properties = {}
        self._tmp_script = []
        self._tmp_var_count = None
        self._tmp_var_vector = []

    def sample(self, sampleSize: int, xy: bool = False,
               inpVector: Optional['vector.Vector'] = None,
               na_rm: bool = True) -> Union[npt.NDArray, 'vector.Vector']:
        """sample a Raster object

        Parameters
        ----------
        sampleSize: int
            size of random sample
        xy: bool, default is False
            flag to return xy coordinate of sample location
        inpVector: vector.Vector
            an instance of inputVector to make Raster object
        na_rm: bool, default is True
            flag to remove missing values

        Returns
        -------
        Union[npt.NDArray, vector.Vector]
            a ndarary or Vector object with sample values of Raster
        """

        out = draw_raster_sample(self, sampleSize=sampleSize, xy=xy,
                                 inpVector=inpVector, na_rm=na_rm)
        return out

    def getPropertyNames(self) -> Set[str]:
        """get property names

        _extended_summary_

        Returns
        -------
        Set[str]
            _description_
        """
        if isinstance(self, raster.RasterFile):
            out_names = self._handle.cy_raster_obj.getPropertyNames()
        else:
            out_names = self._handle.getPropertyNames()
        return out_names

    def getVariableNames(self) -> Set[str]:
        """get variables names

        _extended_summary_

        Returns
        -------
        Set[str]
            _description_
        """
        if isinstance(self, raster.RasterFile):
            out_names = self._handle.cy_raster_obj.getVariableNames()
        else:
            out_names = self._handle.getVariableNames()
        return out_names

    def getVariableData(self: "_RasterBase",
                        name: Union[str, bytes, np.uint32],
                        index: Optional[int] = None) -> Union[np.float32, np.float64, np.uint32]:
        """get the value of the variable

        Parameters
        ----------
        name : Union[str, bytes, np.uint32]
            name of the variable
        index: Optional[int], default is None
            array index when value of variable is an array of values

        Returns
        -------
        Union[np.float32,np.float64,np.uint32]
            value of the variable
        """
        # Set variable data
        _name = name
        if isinstance(_name, str):
            _name = core.str2bytes(_name)

        # get the appropriate cython method
        if index is None:
            var_size = self.getVariableSize(_name)
            if var_size <= 1:
                method_name = "getVariableData"
            else:
                method_name = "getVariableDataArray"
        else:
            method_name = "getVariableDataIndex"

        # Get handle
        if isinstance(self, raster.RasterFile):
            if index is not None:
                out = getattr(self._handle.cy_raster_obj, method_name)(_name, index)
            else:
                out = getattr(self._handle.cy_raster_obj, method_name)(_name)
        else:
            if index is not None:
                out = getattr(self._handle, method_name)(_name, index)
            else:
                out = getattr(self._handle, method_name)(_name)

        if not np.isscalar(out):
            out = np.asanyarray(out)
        return out

    def setVariableData(self: "_RasterBase", name: Union[str, bytes, np.uint32],
                        value: Union[np.float32, np.float64, np.uint32, npt.NDArray],
                        index: Optional[int] = None) -> None:
        """set a value for a given variable.

        Parameters
        ----------
        name : Union[str, bytes, np.uint32]
            name of the variable
        value : Union[np.float32, np.float64, np.uint32, npt.NDArray]
            value of the variable
        index: Optional[int], default is None
            array index when value of variable is an array of values

        Returns
        -------
        Nil
        """
        # Set variable data
        _name = name
        if isinstance(_name, str):
            _name = core.str2bytes(_name)

        # get the appropriate cython method
        if index is None:
            if np.isscalar(value):
                value = self.data_type(value)
                method_name = "setVariableData"
            else:
                value = np.array(value, dtype=self.data_type)
                method_name = "setVariableDataArray"
        else:
            value = self.data_type(value)
            method_name = "setVariableDataIndex"

        # Get handle
        if isinstance(self, raster.RasterFile):
            if index is not None:
                getattr(self._handle.cy_raster_obj, method_name)(
                    _name, value, index)
            else:
                getattr(self._handle.cy_raster_obj, method_name)(
                    _name, value)
        else:
            if index is not None:
                getattr(self._handle, method_name)(_name, value, index)
            else:
                getattr(self._handle, method_name)(_name, value)

    def getVariableSize(self, name: Union[str, bytes, np.uint32]) -> int:
        """get size of a given variable.

        Parameters
        ----------
        name : Union[str, bytes, np.uint32]
            name of the variable

        Returns
        -------
        int
        """
        # Set variable data
        _name = name
        if isinstance(_name, str):
            _name = core.str2bytes(_name)

        if isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.getVariableSize(_name)
        else:
            return self._handle.getVariableSize(_name)

    def getVariablesType(self) -> str:
        """get the type of Variables object

        Returns
        -------
        str
            float/ double
        """
        # Get handle
        if isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.getVariablesType()
        else:
            return self._handle.getVariablesType()

    def hasVariables(self) -> bool:
        """check if variables object has data.

        Returns
        -------
        bool
            True if Variables has data else False
        """
        # Get handle
        if isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.hasVariables()
        else:
            return self._handle.hasVariables()

    def deleteVariableData(self) -> None:
        """delete variable data attached to a Raster layer.

        Returns
        -------
        None
        """
        if isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.deleteVariableData()
        else:
            return self._handle.deleteVariableData()

    def saveRandomState(self) -> None:
        """save the random state of raster
        """
        self._handle.saveRandomState()

    def restoreRandomState(self) -> None:
        """restore the random state of raster
        """
        self._handle.restoreRandomState()

    def getVariablesIndexes(self) -> Dict:
        """get the indices of the variable

        Returns
        -------
        Dict
            a dictionary of variable and indices in the Variables object.
        """
        # Get handle
        if isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.getVariablesIndexes()
        else:
            return self._handle.getVariablesIndexes()

    @property
    def name(self) -> str:
        out = self.getProperty('name')
        return out

    @name.setter
    def name(self, other: str) -> None:
        if not core.is_valid_name(other):
            raise ValueError(f"'{other}' is not valid name of Raster")
        self.setProperty("name", other, prop_type=str)

    @property
    def nullValue(self) -> Union[numbers.Integral, numbers.Real]:
        return raster.getNullValue(self.data_type)

    def getPropertyType(self, propName: Union[str, bytes]) -> type:
        return super().getPropertyType(propName)

    def setProjectionParameters(self, other: Union["core.ProjectionParameters", str]) -> None:
        """Set projection parameters for the raster.

        Parameters
        ----------
        other : ProjectionParameters | str
            An instance of projection parameters obtained from a wkt or proj4.

        Returns
        -------
        Nil
        """
        if not isinstance(other, (core.ProjectionParameters, str)):
            raise TypeError(
                "Argument should be an instance of ProjectionParameters or str")
        if isinstance(other, str):
            if isinstance(self, raster.Raster):
                self._handle.setProjectionParameters_str(other)
            elif isinstance(self, raster.RasterFile):
                self._handle.cy_raster_obj.setProjectionParameters_str(other)
        else:
            if isinstance(self, raster.Raster):
                self._handle.setProjectionParameters(other._handle)
            elif isinstance(self, raster.RasterFile):
                self._handle.cy_raster_obj.setProjectionParameters(other._handle)

    def getProjectionParameters(self) -> "core.ProjectionParameters":
        """Get projection parameters from the raster.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : ProjectionParameters
            Returns Raster projection parameters as an instance of ProjectionParameters
        """
        if isinstance(self, raster.Raster):
            out = core.ProjectionParameters.from_proj_param(
                self._handle.getProjectionParameters())
        elif isinstance(self, raster.RasterFile):
            out = core.ProjectionParameters.from_proj_param(
                self._handle.cy_raster_obj.getProjectionParameters())
        return out

    def setInterpolationType(self, interpolation: Union[numbers.Integral,
                                                        gs_enums.RasterInterpolationType]) -> None:
        """Set interpolation type for the raster.

        Parameters
        ----------
        interpolation : Interpolation type
            A RasterInterpolationType enum.

        Returns
        -------
        Nil
        """

        if not isinstance(interpolation, (numbers.Integral,
                                          gs_enums.RasterInterpolationType)):
            raise TypeError("interpolation type should be int / gs_enums")
        elif isinstance(interpolation, numbers.Integral):
            # assign raw value
            _interpolation = interpolation
        else:
            # assign value from enum.Enum
            _interpolation = interpolation.value

        if isinstance(self, raster.Raster):
            self._handle.setInterpolationType(_interpolation)
        elif isinstance(self, raster.RasterFile):
            self._handle.cy_raster_obj.setInterpolationType(_interpolation)

    def getInterpolationType(self) -> Union[numbers.Integral, gs_enums.RasterInterpolationType]:
        """Get interpolation type for the raster.

        Returns
        -------
        RasterInterpolationType
            A RasterInterpolationType enum.
        """
        if isinstance(self, raster.Raster):
            out = self._handle.getInterpolationType()
        elif isinstance(self, raster.RasterFile):
            out = self._handle.cy_raster_obj.getInterpolationType()
        return gs_enums.RasterInterpolationType(out)

    def reproject(self, projParams: "core.ProjectionParameters", **kwargs) -> "raster.Raster":
        """Reproject raster to a given projection parameters.

        Parameters
        ----------
        projParams: ProjectionParameters object
            projection parameters for output raster
        resolution: integer/float, optional
            resolution of output raster
        hx: integer/float, optional
            resolution in x-direction
        hy: integer/float, optional
            resolution in y-direction
        hz: integer/float, optional
            resolution in z-direction
        method: RasterInterpolationType, optional
            method to use for projecting
        bounds: BoundingBox, optional
            destination bounding box
        parameter: integer, optional
            default is 0

        Returns
        -------
        out : Raster object
        """
        # get horizonal and vertical spacing
        hx = kwargs.get("resolution", kwargs.get("hx"))
        hy = kwargs.get("resolution", kwargs.get("hy"))
        hz = kwargs.get("resolution", kwargs.get("hz"))
        if hz is None:
            hz = self.dimensions.hz

        # get interpolation type
        interp_type = kwargs.get("method")

        newBounds: vector.BoundingBox = kwargs.get("bounds")

        # project raster bounds
        if newBounds is None:
            newBounds = self.bounds
            bounds_proj = newBounds.convert(projParams,
                                            self.getProjectionParameters())
        else:
            bounds_proj = newBounds

        if hx is None:
            hx = (bounds_proj.max.p - bounds_proj.min.p) / self.dimensions.nx

        if hy is None:
            hy = (bounds_proj.max.q - bounds_proj.min.q) / self.dimensions.ny

        # create an empty raster
        out = raster.Raster(name="dst", data_type=self.data_type)
        out.init_with_bbox(bounds_proj, hx, hy, hz)
        out.setProjectionParameters(projParams)

        raster_name = self.name
        # change name in src raster
        self.name = "src"

        parameter = kwargs.get("parameter", 0)

        # run script to project raster
        if interp_type is not None:
            prev_interp_type = self.getInterpolationType()
            self.setInterpolationType(interp_type)
        if out.dimensions.nz > 1:
            runScript("dst = src[kpos];", [out, self],
                      parameter=parameter,
                      output_type=None,)
        else:
            runScript("dst = src;", [out, self],
                      parameter=parameter,
                      output_type=None)
        if interp_type is not None:
            self.setInterpolationType(prev_interp_type)

        # update name (or revert to original name)
        self.name = raster_name
        out.name = raster_name

        return out

    def clip(self, other: Union['raster.Raster', 'raster.RasterFile',
                                'vector.Vector', 'vector.BoundingBox'],
             projParams: Optional["core.ProjectionParameters"] = None) -> "raster.Raster":
        """Clip a raster with a vector/ raster object.

        Parameters
        ----------
        other : Raster/RasterFile/BoundingBox,Vector
            a vector or raster object used to clip the raster
        projParams : ProjectionParameters, optional
            projection parameters for use with BoundingBox, by default None

        Returns
        -------
        Raster
            a raster subset with a given vector/ raster object

        Raises
        ------
        ValueError
            ProjectionParameters must be provided for BoundingBox
        TypeError
            projParams should be an instance of ProjectionParameter
        TypeError
            input argument should be an instance of Raster/RasterFile/BoundingBox
        """
        if isinstance(other, (raster.Raster, raster.RasterFile)):
            bbox = other.getBounds()
            if self.getProjectionParameters() != other.getProjectionParameters():
                _bbox = bbox.convert(self.getProjectionParameters(),
                                     other.getProjectionParameters())
            else:
                _bbox = bbox
        elif isinstance(other, vector.BoundingBox):
            if projParams is None:
                raise ValueError(
                    "ProjectionParameters must be provided for BoundingBox")
            if not isinstance(projParams, core.ProjectionParameters):
                raise TypeError(
                    "projParams should be an instance of ProjectionParameters")
            if self.getProjectionParameters() != projParams:
                _bbox = other.convert(
                    self.getProjectionParameters(), projParams)
            else:
                _bbox = other
        elif isinstance(other, vector.Vector):
            bbox = other.getBounds()
            if self.getProjectionParameters() != other.getProjectionParameters():
                _bbox = bbox.convert(self.getProjectionParameters(),
                                     bbox.getProjectionParameters())
            else:
                _bbox = bbox
        else:
            raise TypeError("Argument 'other' should be an instance of" +
                            " Raster/RasterFile/BoundingBox")
        raster_name = self.getProperty("name")

        hx, hy = self.dimensions.hx, self.dimensions.hy

        i, j, k = self.xyz2ijk(_bbox.min.p, _bbox.min.q)
        c0 = self.ijk2xyz(i, j, k)
        x0, y0 = c0.p - 0.5 * hx, c0.q - 0.5 * hy

        i, j, k = self.xyz2ijk(_bbox.max.p, _bbox.max.q)
        c1 = self.ijk2xyz(i, j, k)
        x1, y1 = c1.p + 0.5 * hx, c1.q + 0.5 * hy

        nx = int(np.floor((x1 - x0) / hx))
        ny = int(np.floor((y1 - y0) / hy))
        out = raster.Raster.init_with_raster(raster_name, self,
                                             dims=["x", "y", "z"][:self.ndim],
                                             ox=x0, oy=y0, ex=x1,
                                             ey=y1, nx=nx, ny=ny)
        out.name = raster_name + "_clipped"

        out.setInterpolationType(self.getInterpolationType())
        out.setReductionType(self.getReductionType())

        runScript(f"{raster_name}_clipped = {raster_name};", [out, self],
                  parameter=gs_enums.RasterCombinationType.Intersection)
        out.name = raster_name

        for prop in self.getPropertyNames():
            out.setProperty(prop, self.getProperty(prop))
        return out

    def get_tile_idx_bounds(self, idx: int) -> Tuple[int]:
        tileSize = TileSpecifications().tileSize
        tj, ti = divmod(idx, self.dimensions.tx)
        idx_s = ti * tileSize
        idx_e = min((ti + 1) * tileSize, self.dimensions.nx)
        jdx_s = tj * tileSize
        jdx_e = min((tj + 1) * tileSize, self.dimensions.ny)
        return idx_s, idx_e, jdx_s, jdx_e

    def _slice_to_tiles(self, *args) -> List:
        """internal method to build list of tiles for given slices.
        """
        # handle when slice start or stop is None or -1
        def handle_none(s, r): return r if s is None or s == -1 else s
        # get the tile size used in core library
        tileSize = TileSpecifications().tileSize
        tiles = []

        # start from backwards i.e., (x -> y -> z)
        for i, _slice in enumerate(args[0][::-1]):
            # only return tile index in x and y direction
            if isinstance(_slice, slice) and i < min(len(*args), 2):
                # compute start index for tiles
                start = divmod(handle_none(_slice.start, 0), tileSize)
                # compute end index for tiles
                # also handle cases when stop is larger than number of cells in raster
                if i == 0:
                    end = divmod(min(handle_none(_slice.stop, self.dimensions.nx),
                                     self.dimensions.nx), tileSize)
                elif i == 1:
                    end = divmod(min(handle_none(_slice.stop, self.dimensions.ny),
                                     self.dimensions.ny), tileSize)
                # create a list of tiles
                _tiles = list(
                    range(start[0], end[0] + 1 if end[1] > 0 else end[0], 1))
                # handle case when slice.stop < tileSize
                if not len(_tiles) > 0:
                    _tiles = [0]
                tiles.append(_tiles)
            elif isinstance(_slice, numbers.Integral):
                # handle case when input is a integer
                tiles.append([_slice // tileSize])
        return tiles[::-1]

    def get_full_data(self, *args) -> npt.NDArray:

        tileSize = TileSpecifications().tileSize

        if self._handle is None:
            return
        elif isinstance(self, raster.RasterFile):
            if not self._handle.cy_raster_obj.hasData():
                raise RuntimeError("RasterFile object is not initialized")

        if len(args) > 0:
            data_slice = args[0]
            if isinstance(data_slice, (slice, int)):
                data_slice = (data_slice,)

            # throw an error if input argument is not tuple
            if not isinstance(data_slice, tuple):
                if not self.ndim == 1:
                    raise TypeError("Input argument should be a tuple")

            # check if input argument is a tuple of integer, if so, use the method getCellValue
            # instead of reading whole array
            if all(map(lambda item: not isinstance(item, slice), data_slice)):
                if len(data_slice) != self.ndim:
                    raise ValueError(
                        f"Number of Input arguments should be {self.ndim}")
                return self.getCellValue(*data_slice[::-1])

            # create array to store data
            if self.ndim == RasterKind.Raster1D:
                out_data = np.full((self.dimensions.nx), self.nullValue,
                                   dtype=self.data_type)
            elif self.ndim == RasterKind.Raster2D:
                out_data = np.full((self.dimensions.ny, self.dimensions.nx),
                                   self.nullValue, dtype=self.data_type)
            elif self.ndim == RasterKind.Raster3D:
                out_data = np.full((self.dimensions.nz, self.dimensions.ny,
                                    self.dimensions.nx), self.nullValue,
                                   dtype=self.data_type)

            # read data as tiles
            # get tile indices when
            tile_idx = self._slice_to_tiles(data_slice)

            if len(tile_idx):
                # remove the z-tile index from the slice
                tile_idx = tile_idx[-2:]

            # now build an iterator for tiles and read data
            for tile_idx_tpl in product(*tile_idx):
                if self.ndim > 1:
                    (ti, tj) = tile_idx_tpl
                    idx = tj + ti * self.dimensions.tx
                    idx_s, idx_e, jdx_s, jdx_e = self.get_tile_idx_bounds(idx)
                    tile_ny = jdx_e - jdx_s
                else:
                    (idx,) = tile_idx_tpl
                    idx_s, idx_e, _, _ = self.get_tile_idx_bounds(idx)
                tile_nx = idx_e - idx_s

                if self.ndim == RasterKind.Raster1D:
                    out_data[idx_s:idx_e] = self.get_tile(idx)[:tile_nx]
                elif self.ndim == RasterKind.Raster2D:
                    out_data[jdx_s:jdx_e, idx_s:idx_e] = self.get_tile(idx)[
                        :tile_ny, :tile_nx]
                elif self.ndim == RasterKind.Raster3D:
                    nz = self.dimensions.nz
                    out_data[:, jdx_s:jdx_e, idx_s:idx_e] = self.get_tile(idx)[
                        :, :tile_ny, :tile_nx]
            # slice output array for the given arguments
            out_data = out_data.__getitem__(*args)
        else:
            # read all the data
            if self.ndim == RasterKind.Raster1D:
                data_slice = [slice(self.dimensions.nx)]
                out_data = np.full((self.dimensions.nx), self.nullValue,
                                   dtype=self.data_type)
            elif self.ndim == RasterKind.Raster2D:
                data_slice = [slice(self.dimensions.ny),
                              slice(self.dimensions.nx)]
                out_data = np.full((self.dimensions.ny, self.dimensions.nx),
                                   self.nullValue, dtype=self.data_type)
            elif self.ndim == RasterKind.Raster3D:
                data_slice = [slice(self.dimensions.nz),
                              slice(self.dimensions.ny),
                              slice(self.dimensions.nx)]
                out_data = np.full((self.dimensions.nz, self.dimensions.ny,
                                    self.dimensions.nx), self.nullValue,
                                   dtype=self.data_type)
            else:
                raise NotImplementedError("only upto 3D rasters are handled")

            numTiles = self.dimensions.tx * self.dimensions.ty
            for idx in range(numTiles):
                ny, nx = self.dimensions.ny, self.dimensions.nx
                idx_s, idx_e, jdx_s, jdx_e = self.get_tile_idx_bounds(idx)
                tile_dim = self.get_tile_dimensions(idx)
                nx, ny = tile_dim.nx, tile_dim.ny
                if self.ndim == RasterKind.Raster1D:
                    out_data[idx_s:idx_e, ] = self.get_tile(idx)[:nx]
                elif self.ndim == RasterKind.Raster2D:
                    out_data[jdx_s:jdx_e, idx_s:idx_e, ] = self.get_tile(idx)[
                        :ny, :nx]
                elif self.ndim == RasterKind.Raster3D:
                    nz = self.dimensions.nz
                    out_data[:, jdx_s:jdx_e, idx_s:idx_e] = self.get_tile(idx)[
                        :nz, :ny, :nx]
        return out_data

    def resize2D(self, nx: int, ny: int, tox: int, toy: int) -> "raster.Raster":
        if isinstance(self, raster.Raster):
            out = self._handle.resize2D(np.uint32(nx), np.uint32(ny),
                                        np.uint32(tox), np.uint32(toy))
        elif isinstance(self, raster.RasterFile):
            out = self._handle.cy_raster_obj.resize2D(np.uint32(nx), np.uint32(ny),
                                                      np.uint32(tox), np.uint32(toy))
        return out

    @property
    def tiles(self) -> Generator[npt.NDArray]:
        num_tiles = self.dimensions.tx * self.dimensions.ty
        for tileNum in range(num_tiles):
            yield self.get_tile(tileNum)

    def get_tile(self, tileNum: int) -> npt.NDArray:
        num_tiles = self.dimensions.tx * self.dimensions.ty
        if tileNum > num_tiles or tileNum < 0:
            raise ValueError("Request tile number of out of bounds")
        tj, ti = divmod(tileNum, self.dimensions.tx)

        # for 1D raster, force tj to 0
        if self.ndim == 1:
            tj = 0

        if isinstance(self, (raster.Raster, raster.RasterBase)):
            return self.writeData(ti=ti, tj=tj)
        elif isinstance(self, raster.RasterFile):
            return self.getData(ti=ti, tj=tj)

    def get_tile_dimensions(self, tileNum: int) -> "raster.TileDimensions":
        num_tiles = self.dimensions.tx * self.dimensions.ty
        if tileNum > num_tiles or tileNum < 0:
            raise ValueError("Request tile number of out of bounds")
        tj, ti = divmod(tileNum, self.dimensions.tx)
        if isinstance(self, (raster.Raster, raster.RasterBase)):
            tile_dim = self._handle.getTileDimensions(ti, tj)
        if isinstance(self, raster.RasterFile):
            tile_dim = self._handle.cy_raster_obj.getTileDimensions(ti, tj)
        return raster.TileDimensions.copy(tile_dim)

    def get_tile_bounds(self, tileNum: int) -> "vector.BoundingBox":
        num_tiles = self.dimensions.tx * self.dimensions.ty
        if tileNum > num_tiles or tileNum < 0:
            raise ValueError("Request tile number of out of bounds")
        tj, ti = divmod(tileNum, self.dimensions.tx)
        if isinstance(self, (raster.Raster, raster.RasterBase)):
            tile_bounds = self._handle.getTileBounds(ti, tj)
        if isinstance(self, raster.RasterFile):
            tile_bounds = self._handle.cy_raster_obj.getTileBounds(ti, tj)
        return vector.BoundingBox.from_bbox(tile_bounds)

    def searchTiles(self, bounds: "vector.BoundingBox") -> npt.NDArray:
        if isinstance(self, raster.Raster):
            out = self._handle.searchTiles(bounds._handle)
        elif isinstance(self, raster.RasterFile):
            out = self._handle.cy_raster_obj.searchTiles(bounds._handle)
        return np.asanyarray(out)

    def nearestTiles(self, bounds: "vector.BoundingBox") -> npt.NDArray:
        if isinstance(self, raster.Raster):
            out = self._handle.nearestTiles(bounds._handle)
        elif isinstance(self, raster.RasterFile):
            out = self._handle.cy_raster_obj.nearestTiles(bounds._handle)
        return np.asanyarray(out)

    def getReductionType(self) -> "gs_enums.ReductionType":
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return gs_enums.ReductionType(self._handle.getReductionType())
            elif isinstance(self, raster.RasterFile):
                return gs_enums.ReductionType(self._handle.cy_raster_obj.getReductionType())
        else:
            raise RuntimeError("Raster is not yet initialized")

    def setReductionType(self, other: "gs_enums.ReductionType"):
        if not isinstance(other, gs_enums.ReductionType):
            raise RuntimeError(f"Invalid reduction type '{other}'")
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                self._handle.setReductionType(other.value)
            elif isinstance(self, raster.RasterFile):
                self._handle.cy_raster_obj.setReductionType(other.value)
        else:
            raise RuntimeError("Raster is not yet initialized")

    def getRequiredNeighbours(self) -> "gs_enums.NeighboursType":
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return gs_enums.NeighboursType(self._handle.getRequiredNeighbours())
            elif isinstance(self, raster.RasterFile):
                return gs_enums.NeighboursType(self._handle.cy_raster_obj.getRequiredNeighbours())
        else:
            raise RuntimeError("Raster is not yet initialized")

    def setRequiredNeighbours(self, other: "gs_enums.NeighboursType"):
        if self._handle is not None:
            if not isinstance(other, gs_enums.NeighboursType):
                raise TypeError("input argument should be of NeighboursType")
            if isinstance(self, raster.Raster):
                self._handle.setRequiredNeighbours(other.value)
            elif isinstance(self, raster.RasterFile):
                self._handle.cy_raster_obj.setRequiredNeighbours(other.value)
        else:
            raise RuntimeError("Raster is not yet initialized")

    def max(self) -> Union[int, float]:
        """Get maximum value of the Raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : int/float32/float64
            return the maximum value from the Raster.
        """
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return self._handle.maxVal()
            elif isinstance(self, raster.RasterFile):
                if not self._handle.cy_raster_obj.hasData():
                    raise RuntimeError("RasterFile object is not initialized")
                return self._handle.cy_raster_obj.maxVal()

    def min(self) -> Union[int, float]:
        """Get minimum value of the Raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : int/float32/float64
            return the minimum value from the Raster.
        """
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return self._handle.minVal()
            elif isinstance(self, raster.RasterFile):
                if not self._handle.cy_raster_obj.hasData():
                    raise RuntimeError("RasterFile object is not initialized")
                return self._handle.cy_raster_obj.minVal()

    def getCellValue(self, i: numbers.Integral, j: numbers.Integral = 0,
                     k: numbers.Integral = 0) -> numbers.Real:
        """Get cell value for a location within the Raster.

        Parameters
        ----------
        i : int
            grid cell index along x-axis
        j : int (optional)
            grid cell index along y-axis, default is 0
        k : int (optional)
            grid cell index along z-axis, default is 0

        Returns
        -------
        out : float32/uint32/float64
            Raster value at a given index within the raster.
        """
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return self._handle.getCellValue(i, j=j, k=k)
            elif isinstance(self, raster.RasterFile):
                return self._handle.cy_raster_obj.getCellValue(i, j=j, k=k)
        else:
            raise RuntimeError("Raster is not yet initialized")

    def setOrigin_z(self, oz: numbers.Real) -> None:
        """set raster origin in z-direction

        Parameters
        ----------
        oz : numbers.Real
            origin in z-direction

        Returns
        -------
        Nil

        Raises
        ------
        RuntimeError
            Raster is not yet initialized
        """
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return self._handle.setOrigin_z(oz)
            elif isinstance(self, raster.RasterFile):
                return self._handle.cy_raster_obj.setOrigin_z(oz)
        else:
            raise RuntimeError("Raster is not yet initialized")

    def getNearestValue(self, x: numbers.Real, y: numbers.Real = 0.0,
                        z: numbers.Real = 0.0) -> numbers.Real:
        """Get a nearest value for a location within the spatial extent of Raster.

        Parameters
        ----------
        x : int/float
            Spatial location along x-axis
        y : int/float (optional)
            Spatial location along y-axis
        z : int/float (optional)
            Spatial location along z-axis

        Returns
        -------
        out : float32/uint32/float64
            Raster value a given location within the spatial extent of the raster.
        """
        if self._handle is not None:
            if isinstance(self, raster.Raster):
                return self._handle.getNearestValue(x, y=y, z=z)
            elif isinstance(self, raster.RasterFile):
                return self._handle.cy_raster_obj.getNearestValue(x, y=y, z=z)
            else:
                raise NotImplementedError()
        else:
            raise RuntimeError("Raster is not yet initialized")

    def getBilinearValue(self, x: numbers.Real, y: numbers.Real = 0.0,
                         z: numbers.Real = 0.0) -> numbers.Real:
        """Get a bilinearly interpolated value for a location within the spatial extent of Raster.

        Parameters
        ----------
        x : int/float
            Spatial location along x-axis
        y : int/float (optional)
            Spatial location along y-axis
        z : int/float (optional)
            Spatial location along z-axis

        Returns
        -------
        out : float32/uint32/float64
            Raster value a given location within the spatial extent of the raster.
        """
        if isinstance(self._handle, (_cyRaster_d_i, _cyRaster_f_i,
                                     _cyRaster_d_byt, _cyRaster_f_byt,
                                     DataFileHandler_d_byt, DataFileHandler_f_byt,
                                     DataFileHandler_d_i, DataFileHandler_f_i)):
            raise NotImplementedError("Bilinear value cannot be computed for" +
                                      " Raster of datatype uint32 ")
        else:
            if self._handle is not None:
                if isinstance(self, raster.Raster):
                    return self._handle.getBilinearValue(x, y=y, z=z)
                elif isinstance(self, raster.RasterFile):
                    return self._handle.cy_raster_obj.getBilinearValue(x, y=y, z=z)
                else:
                    raise NotImplementedError()
            else:
                raise RuntimeError("Raster is not yet initialized")

    def getBounds(self) -> "vector.BoundingBox":
        """Get bounding box of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : BoundingBox object
            Return bounding box of the raster object.
        """
        if self._handle is not None:
            if isinstance(self, raster.RasterFile):
                if self._handle.cy_raster_obj.hasData() == False:
                    raise RuntimeError("RasterFile object is not initialized")
                return vector.BoundingBox.from_bbox(self._handle.cy_raster_obj.getBounds())
            elif isinstance(self, raster.Raster):
                return vector.BoundingBox.from_bbox(self._handle.getBounds())
        else:
            return

    def getDimensions(self) -> "raster.RasterDimensions":
        """Get dimensions of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : RasterDimensions object
            Return dimensions of the raster object.
        """
        return self.getRasterDimensions()

    def getRasterDimensions(self) -> "raster.RasterDimensions":
        """Get raster dimensions of the raster object.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : RasterDimensions object
            An instance of RasterDimensions containing dimensions of the Raster object.
        """
        if self._handle is None:
            return

        if isinstance(self, raster.Raster):
            return raster.RasterDimensions.copy(self._handle.getRasterDimensions())
        elif isinstance(self, raster.RasterFile):
            if not self._handle.cy_raster_obj.hasData():
                raise RuntimeError("RasterFile object is not initialized")
            return raster.RasterDimensions.copy(self._handle.cy_raster_obj.getRasterDimensions())

    def cellCentres(self, mapValues: bool = False) -> "vector.Vector":
        """Create a vector of points from Raster cell centres.

        Returns
        -------
        out : Vector object
            Return a vector object containing points.
        mapValues: bool, default is False
            flag to map values to the polygon geometries
        """

        if isinstance(self, raster.Raster):
            _raster_handle = self._handle
        elif isinstance(self, raster.RasterFile):
            _raster_handle = self._handle.cy_raster_obj

        _out = _raster_handle.cellCentres(mapValues=mapValues)

        out = vector.Vector._from_vector(_out)
        return out

    def cellPolygons(self, mapValues: bool = False) -> "vector.Vector":
        """Create a vector of polygons from Raster cell centres.

        Returns
        -------
        out : Vector object
            Return a vector object containing polygons.
        mapValues: bool, default is False
            flag to map values to the polygon geometries
        """

        if isinstance(self, raster.Raster):
            _raster_handle = self._handle
        elif isinstance(self, raster.RasterFile):
            _raster_handle = self._handle.cy_raster_obj

        _out = _raster_handle.cellPolygons(mapValues=mapValues)

        out = vector.Vector._from_vector(_out)
        return out

    def vectorise(self, contourValue: numbers.Real,
                  propertyName: str = "",
                  parameters: int = gs_enums.GeometryType.LineString,
                  noDataValue: Union[int, float] = None) -> "vector.Vector":
        """Get a vector from the Raster object.

        Parameters
        ----------
        contourValue : int/float/list(int/float),npt.NDArray
            A constant value or a list of values to compute contour from the Raster object.
        propertyName: str
            ""
        parameters: int
            gs_enums.GeometryType.LineString
        noDataValue: int/float
            missing value to use


        Returns
        -------
        out : Vector object
            Return a vector object obtained from the raster for a given contour value.
        """

        if (not isinstance(contourValue, (float, list, np.ndarray)) and
                not isinstance(contourValue, numbers.Real)):
            raise TypeError("contourValue should be of numeric type or" +
                            " list/ndarray of numeric types")

        if isinstance(self, raster.Raster):
            _raster_handle = self._handle
        elif isinstance(self, raster.RasterFile):
            _raster_handle = self._handle.cy_raster_obj

        if isinstance(parameters, gs_enums.GeometryType):
            _parameters = parameters.value
        else:
            _parameters = parameters

        _propertyName = core.str2bytes(propertyName)

        if not isinstance(contourValue, np.ndarray):
            if isinstance(contourValue, list):
                _contour_value = contourValue
            else:
                _contour_value = [contourValue]
            _out = _raster_handle.vectorise(np.array(_contour_value,
                                                     dtype=self.data_type),
                                            _propertyName, _parameters,
                                            noDataValue)
        elif isinstance(contourValue, np.ndarray):
            _out = _raster_handle.vectorise(contourValue.astype(self.data_type),
                                            _propertyName,
                                            _parameters,
                                            noDataValue)
        out = vector.Vector._from_vector(_out)
        return out

    def mapVector(self, inp_vector: "vector.Vector",
                  script: str = "",
                  parameters: Union[numbers.Integral,
                                    gs_enums.GeometryType] = gs_enums.GeometryType.All,
                  widthPropertyName: str = "",
                  levelPropertyName: str = "", **kwargs) -> None:
        """Convert an input vector to a raster

        Parameters
        ----------
        inp_vector : vector.Vector
            A vector object to be converted to a raster object
        script : str, optional
            the mapping script
        parameters : Union[numbers.Integral, gs_enums.GeometryType]
            type of the vector geometries
        widthPropertyName : str, optional
            vector property used for width mapping, by default ""
        levelPropertyName: str, optional
            vector property used for level mapping, by default ""

        Returns
        -------
        Nil

        Raises
        ------
        TypeError
            inp_vector should be an instance of Vector class
        TypeError
            geom_type should be int/ GeometryType
        """
        if not isinstance(inp_vector, (vector.Vector,
                                       vector._Vector_d,
                                       vector._Vector_f)):
            raise TypeError("inp_vector should be an instance of Vector class")

        if isinstance(inp_vector, vector.Vector):
            assert self.data_type == inp_vector._dtype
            _inp_vector = inp_vector._handle
        else:
            if isinstance(inp_vector, vector._Vector_d):
                assert self.data_type == np.float64
            elif isinstance(inp_vector, vector._Vector_f):
                assert self.data_type == np.float32
            _inp_vector = inp_vector

        _script = core.str2bytes(script)
        _width = core.str2bytes(widthPropertyName)
        _level = core.str2bytes(levelPropertyName)

        parameters = kwargs.get('geom_type', parameters)

        if not isinstance(parameters, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("parameters should be int/ GeometryType")

        if isinstance(parameters, gs_enums.GeometryType):
            _parameters = parameters.value
        else:
            _parameters = parameters

        self._handle.mapVector(_inp_vector, _script,
                               _parameters, _width, _level)

    def rasterise(self, inp_vector: "vector.Vector", script: str = None,
                  parameters: Union[numbers.Integral, "gs_enums.GeometryType"] = gs_enums.GeometryType.All,
                  levelPropertyName: str = "", **kwargs) -> None:
        """Convert an input vector to a raster.

        Parameters
        ----------
        inp_vector : vector.Vector
            A vector object to be converted to a raster object
        script : str
            script used to assign values to raster cells.
        parameters : Union[numbers.Integral, gs_enums.GeometryType]
            type of the vector geometries
        levelPropertyName: str, optional
            vector property used for level mapping, by default ""

        Returns
        -------
        Nil

        Raises
        ------
        TypeError
            inp_vector should be an instance of Vector class
        AssertionError
            datatype mismatch
        TypeError
            geom_type should be int/ GeometryType
        """
        if not isinstance(inp_vector, (vector.Vector,
                                       vector._Vector_d,
                                       vector._Vector_f)):
            raise TypeError("inp_vector should be an instance of Vector class")

        if isinstance(inp_vector, vector.Vector):
            _inp_vector = inp_vector._handle
        else:
            _inp_vector = inp_vector

        if isinstance(inp_vector, vector._Vector_d):
            assert self.data_type == np.float64, "datatype mismatch"
        elif isinstance(inp_vector, vector._Vector_f):
            assert self.data_type == np.float32, "datatype mismatch"

        if isinstance(script, (str, bytes)):
            _script = core.str2bytes(script)
        else:
            _script = ""

        parameters = kwargs.get('geom_type', parameters)

        if not isinstance(parameters, (numbers.Integral, gs_enums.GeometryType)):
            raise TypeError("parameters should be int/ GeometryType")

        if isinstance(parameters, gs_enums.GeometryType):
            _parameters = parameters.value
        else:
            _parameters = parameters

        _level = core.str2bytes(levelPropertyName)

        self._handle.rasterise(_inp_vector, _script, _parameters, _level)

    def hasData(self) -> bool:
        """Check if raster object has data.

        Parameters
        ----------
        Nil

        Returns
        -------
        out : bool
            Return true if raster object has data else false.
        """
        if isinstance(self, raster.Raster):
            return self._handle.hasData()
        elif isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.hasData()

    def getDataTypeString(self) -> np.dtype:
        """get raster datatype as string

        Returns
        -------
        numpy.dtype
            raster data type as numpy dtype object
        """
        assert self._handle is not None
        dtype = self._handle.getDataTypeString().replace("_t", "")
        if dtype == "float":
            dtype = f"{dtype}32"
        return np.dtype(dtype)

    def write(self, fileName: str,
              jsonConfig: Optional[Union[Dict, str]] = None) -> None:
        """Write raster data to a output file.

        Parameters
        ----------
        fileName : str
            Path of the file to write raster data.
        jsonConfig : Union[str, dict]
            A string or dictionary containing configuration for the output file.

        Returns
        -------
        Nil
        """
        if jsonConfig is None:
            _json_config = core.str2bytes("")
        else:
            if isinstance(jsonConfig, (str, bytes)):
                _json_config = core.str2bytes(jsonConfig)
            elif isinstance(jsonConfig, dict):
                _json_config = core.str2bytes(json.dumps(jsonConfig))

        if isinstance(fileName, PurePath):
            fileName = str(fileName)

        self._handle.write(fileName, _json_config)

    @property
    def dtype(self) -> np.dtype:
        """get raster data type.

        Returns
        -------
        np.dtype
            raster data type as numpy datatype object
        """
        return self.getDataTypeString()

    @staticmethod
    def _check_inputs(inp) -> bool:
        if not isinstance(inp, (raster.Raster, raster.RasterFile)):
            if not isinstance(inp, numbers.Real):
                warnings.warn("Input argument should be numeric",
                              RuntimeWarning)
                return False
            else:
                return True
        if not len(inp.name) >= 1:
            warnings.warn(
                "Length of Input raster name should be greater than 1", RuntimeWarning)
            return False
        else:
            return True

    def setConst(self, isConst: bool) -> None:
        """set const flag for the raster.

        Parameters
        ----------
        isConst : bool
            flag if the raster is const or not
        """
        if isinstance(self, raster.Raster):
            self._handle.setConst(isConst)
        elif isinstance(self, raster.RasterFile):
            self._handle.cy_raster_obj.setConst(isConst)

    def getConst(self) -> bool:
        """get const flag for the raster.

        Returns
        -------
        bool
            get the flag whether ratser is const or not.
        """
        if isinstance(self, raster.Raster):
            return self._handle.getConst()
        elif isinstance(self, raster.RasterFile):
            return self._handle.cy_raster_obj.getConst()

    def xyz2ijk(self, x: float, y: float = 0.0, z: float = 0.0) -> List[int]:
        """map coordinate to raster grid index

        Parameters
        ----------
        x : float
            coordinate in x-direction
        y : float, optional
            coordinate in y-direction, by default 0.0
        z : float, optional
            coordinate in z-direction, by default 0.0

        Returns
        -------
        List[int]
            a list of integer
        """

        if isinstance(self, raster.Raster):
            dispatcher = self._handle.xyz2ijk
        elif isinstance(self, raster.RasterFile):
            dispatcher = self._handle.cy_raster_obj.xyz2ijk

        out = dispatcher(self.base_type(x),
                         self.base_type(y),
                         self.base_type(z))
        return out

    def ijk2xyz(self, i: int, j: int = 0, k: int = 0) -> 'vector.Coordinate':
        """map grid index to raster coordinates

        Parameters
        ----------
        i : int
            index in x direction
        j : int, optional
            index in y direction, by default 0
        k : int, optional
            index in z direction, by default 0

        Returns
        -------
        vector.Coordinate
            a vector coordinate
        """

        if isinstance(self, raster.Raster):
            dispatcher = self._handle.ijk2xyz
        elif isinstance(self, raster.RasterFile):
            dispatcher = self._handle.cy_raster_obj.ijk2xyz

        _out = dispatcher(np.uint32(i),
                          np.uint32(j),
                          np.uint32(k))
        out = vector.Coordinate._from_coordinate(_out)
        return out

    def _check_input_args(self, other):
        assert self.getDimensions() == other.getDimensions(), "Raster size should be same"
        assert self.name != other.name, "Input raster can't have same name"

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != "__call__":
            raise NotImplementedError()
        else:
            inputs = tuple(x.get_full_data()
                           if isinstance(x, (raster.Raster, raster.RasterFile)) else x
                           for x in inputs)
            result = getattr(ufunc, method)(*inputs, **kwargs)
            return result

    def __array__(self, *args, **kwargs) -> npt.NDArray:
        dtype = kwargs.get("dtype", self.data_type)
        return self.get_full_data().astype(dtype)

    def __getitem__(self, val):
        return self.get_full_data(val)

    def indexComponents(self, script: str) -> "raster.Raster":
        """Assign indices to the components

        Parameters
        ----------
        script : str
            script for creating mask

        Returns
        -------
        Raster
            a raster with components and their indices
        """
        if isinstance(self, raster.RasterFile):
            out = raster.Raster.copy(None,
                self._handle.cy_raster_obj.indexComponents(script))
        else:
            out = raster.Raster.copy(None,
                self._handle.indexComponents(script))
        return out

    def indexComponentsVector(self, indexScript: str = '',
                              reduceScript: str = '',
                              reduction_type: gs_enums.ReductionType = gs_enums.ReductionType.NoReduction,
                              overwrite: bool = False) -> "vector.Vector":
        """Index all identified components on the Raster and output as a Vector

        Parameters
        ----------
        indexScript : str
            script for identified and indexing components, default is ""
        reductScript: str
            script for reduction on each component, default is ""
        reduction_type: ReductionType
            type of reduction to perform for each component, default is ReductionType.NoReduction
        overwrite: bool
            flag to overwrite Raster with index value

        Returns
        -------
        Vector
            a vector object with components and their indices
        """
        reduction_type = gs_enums.ReductionType(reduction_type)
        if not isinstance(reduction_type, gs_enums.ReductionType):
            raise RuntimeError(f"Invalid reduction type '{reduction_type}'")

        if isinstance(self, raster.RasterFile):
            out = vector.Vector()._from_vector(
                self._handle.cy_raster_obj.indexComponentsVector(
                    core.str2bytes(indexScript),
                    core.str2bytes(reduceScript),
                    reduction_type.value,
                    overwrite))
        else:
            out = vector.Vector()._from_vector(
                self._handle.indexComponentsVector(core.str2bytes(indexScript),
                                                   core.str2bytes(reduceScript),
                                                   reduction_type.value,
                                                   overwrite))
        return out

    def getRasterFootprint(self) -> 'vector.Vector':
        """_summary_

        _extended_summary_

        Returns
        -------
        vector.Vector
            _description_

        Raises
        ------
        RuntimeError
            _description_
        """

        if isinstance(self, raster.RasterFile):
            out = vector.Vector()._from_vector(
                self._handle.cy_raster_obj.getRasterFootprint())
        else:
            out = vector.Vector()._from_vector(
                self._handle.getRasterFootprint())
        return out

    @property
    def ndim(self) -> int:
        if isinstance(self, raster.RasterFile):
            raster_kind = self._handle.cy_raster_obj.getRasterKind()
        else:
            raster_kind = self._handle.getRasterKind()
        return raster_kind

    @property
    def shape(self) -> Tuple[int]:
        dimensions = self.getDimensions()
        shape = (dimensions.nz, dimensions.ny, dimensions.nx)
        return shape[-1 * (self.ndim):]

    @property
    def grid(self) -> Tuple[npt.NDArray]:
        return self.dimensions.grid

    def rasterAsJson(self, compress: Optional[bool] = True,
               jsonConfig: Optional[Dict] = None) -> Dict:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        compress : Optional[bool], optional
            _description_, by default True
        jsonConfig : Optional[Dict], optional
            _description_, by default {}

        Returns
        -------
        Dict
            _description_
        """
        json_handle = geostack_io.JsonHandler(dtype=self.base_type)
        json_obj = json_handle.toJson(self, compress=compress,
                                      jsonConfig=jsonConfig)
        return json_obj

    @RequireLib("matplotlib")
    def plot(self, ax=None, bounds: Optional["vector.BoundingBox"] = None,
             ti: Optional[int] = None, tj: Optional[int] = None,
             **kwargs) -> None:
        """helper function to plot raster data

        Parameters
        ----------
        bounds : Optional['vector.BoundingBox'], optional
            bounding box, by default None
        ti : Optional[int], optional
            i index of tile, by default None
        tj : Optional[int], optional
            j index of tile, by default None
        ax : _type_, optional
            plot axes, by default None

        Examples
        --------
        >>> import numpy as np
        >>> import matplotlib.pyplot as plt

        >>> # create a raster
        >>> test = Raster(name='test')
        >>> test.init(256, 1.0, ny=256, hy=1.0)
        >>> test.data = np.random.random(test.shape)

        >>> # plot raster
        >>> fig, ax = test.plot()

        >>> # plot raster within a bounding box
        >>> bounds = test.getBounds()
        >>> fig, ax = test.plot(bounds=bounds)

        >>> # with cartopy
        >>> import cartopy.crs as ccrs
        >>> fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        >>> ax.set_extent([10, 40, 10, 40])
        >>> fig, ax = test.plot(ax)

        >>> # for adding colorbar
        >>> fig.colorbar(ax.collections[0], ax=ax)
        """
        def bounds_to_2d(bounds: "vector.BoundingBox") -> "vector.BoundingBox":
            # convert 3d bounds to 2d
            return vector.BoundingBox.from_list([[bounds.min.p, bounds.min.q],
                                                 [bounds.max.p, bounds.max.q]])

        def extent_to_bounds(extent: List[float]) -> "vector.BoundingBox":
            # convert geoaxes extent to bounds
            return vector.BoundingBox.from_list([[extent[0], extent[2]],
                                                 [extent[1], extent[3]]])

        if bounds is not None:
            assert isinstance(bounds, vector.BoundingBox), "bounds should be a BoundingBox object"

        if ax is not None:
            if any([hasattr(ax, 'get_extent'), bounds is not None]):
                if bounds is None:
                    # extract from plot axis
                    bounds = extent_to_bounds(ax.get_extent())
            else:
                bounds = self.getBounds()
            fig = ax.get_figure()
        else:
            # import plottling library  (create axes)
            import matplotlib.pyplot as plt

            fig = plt.figure(1, figsize=(8, 6))
            fig.patch.set_facecolor('white')
            ax = fig.add_subplot(1, 1, 1)

            # use raster bounds
            if bounds is None:
                bounds = self.getBounds()

        # set tile indices in a vector
        if any([ti is not None, tj is not None]):
            tileVec = np.array([[tj, ti]])
        else:
            tileVec = self.searchTiles(bounds_to_2d(bounds))

        assert len(tileVec) > 0, "No tiles found"

        # loop through the tiles and plot
        for tidx in range(len(tileVec)):
            tileNum = self.dimensions.tx * tileVec[tidx][1] + tileVec[tidx][0]
            # get dimension of tile
            tileDims = self.get_tile_dimensions(tileNum)
            # get tile grid
            x, y = tileDims.grid
            nx, ny = len(x), len(y)
            x, y = np.meshgrid(x, y)

            # get tile data
            tileData = self.get_tile(tileNum)

            # get missing value
            miss_val = kwargs.pop("miss_val",
                                  raster.getNullValue(self.data_type))
            # mask data for the given missing value
            tileData = np.ma.masked_where(tileData == miss_val, tileData)
            shading = kwargs.pop("shading", "nearest")
            edgecolors = kwargs.pop("edgecolors", "face")
            rasterized = kwargs.pop("rasterized", True)

            # add to colormesh
            ax.pcolormesh(x, y, tileData[:ny, :nx], **kwargs, shading=shading,
                          edgecolor=edgecolors, rasterized=rasterized)
        return fig, ax

    def closeFile(self) -> None:
        self._handle.closeFile()

    def __str__(self):
        raster_name = f"{self.name} ({self.base_type.__name__}, {self.data_type.__name__})\n"
        proj_str = f"Projection Parameters: \n{str(self.getProjectionParameters())}\n"
        dim_str = str(self.dimensions)
        if self.hasVariables():
            var_data = self.getVariablesIndexes()
            var_str = "Variables:\n"
            var_str += '\n'.join(
                [f"    {item}[{var_data[item]}]:  {self.getVariableData(item)}" for item in var_data])
            raster_name += f"{var_str}\n{proj_str}{dim_str}"
        else:
            raster_name += proj_str + dim_str
        return raster_name

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__


class _Raster_list:
    def __init__(self, dtype: np.dtype, handle=None):
        self._dtype = dtype
        self._handle = handle

    def _from_list(self, other):
        if not isinstance(other, list):
            raise TypeError('Input argument should be a list')
        else:
            self._from_iterable(other)

    def _from_tuple(self, other: Tuple[Union["raster.Raster",
                                             "raster.RasterFile",
                                             "raster.RasterBase"]]):
        if not isinstance(other, tuple):
            raise TypeError('Input argument should be a tuple')
        else:
            self._from_iterable(other)

    def _from_iterable(self, other: Tuple[Union["raster.Raster",
                                                "raster.RasterFile",
                                                "raster.RasterBase"]]):
        n_items = len(other)
        n_rasters = 0
        n_df_handler = 0
        n_raster_base = 0

        # count individual raster objects
        for item in other:
            if isinstance(item, raster.Raster):
                n_rasters += 1
            elif isinstance(item, raster.RasterFile):
                n_df_handler += 1
            elif isinstance(item, raster.RasterBase):
                n_raster_base += 1

        if n_rasters > 0:
            assert n_rasters == n_items, "All element of tuple should be instances of Raster"
            for i, item in enumerate(other, 0):
                assert item.base_type == self._dtype, "Mismatch between Raster datatype and class instance"
                self._add_raster(item)
        elif n_df_handler > 0:
            assert n_df_handler == n_items, "All element of tuple should be instances of DataFileHandler"
            for i, item in enumerate(other, 0):
                assert item._dtype == self._dtype, "Mismatch between RasterFile datatype and class instance"
                self._add_data_handler(item)
        elif n_raster_base > 0:
            assert n_raster_base == n_items, "All element of tuple should be instances of RasterBase"
            for i, item in enumerate(other, 0):
                assert item._dtype == self._dtype, "Mismatch between RasterBase datatype and class instance"
                self._add_raster_base(item)

    def _append(self, other: Union["raster.Raster",
                                   "raster.RasterFile",
                                   "raster.RasterBase"]):
        if isinstance(other, raster.RasterFile):
            self._add_data_handler(other)
        elif isinstance(other, raster.Raster):
            self._add_raster(other)
        elif isinstance(other, raster.RasterBase):
            self._add_raster_base(other)

    def _add_raster(self, other: "raster.Raster"):
        if isinstance(other, raster.Raster):
            if self._dtype != other.base_type:
                raise TypeError(
                    "mismatch between datatype of input raster and class instance")
            self._add_raster(other._handle)
        elif isinstance(other, (_cyRaster_d,
                                _cyRaster_d_i,
                                _cyRaster_d_byt)):
            if self._dtype != np.float64:
                raise TypeError(
                    "Cannot add input raster of double type to class instance of single precision")
            if isinstance(other, _cyRaster_d):
                self._handle.add_dbl_raster(other)
            elif isinstance(other, _cyRaster_d_i):
                self._handle.add_int_raster(other)
            elif isinstance(other, _cyRaster_d_byt):
                self._handle.add_byt_raster(other)
        elif isinstance(other, (_cyRaster_f,
                                _cyRaster_f_i,
                                _cyRaster_f_byt)):
            if self._dtype != np.float32:
                raise TypeError(
                    "Cannot add input raster of single type to class instance of double precision")
            if isinstance(other, _cyRaster_f):
                self._handle.add_flt_raster(other)
            elif isinstance(other, _cyRaster_f_i):
                self._handle.add_int_raster(other)
            elif isinstance(other, _cyRaster_f_byt):
                self._handle.add_byt_raster(other)
        else:
            raise TypeError("input argument should be an instance of Raster")

    def _add_data_handler(self, other: "raster.RasterFile"):
        if isinstance(other, raster.RasterFile):
            if self._dtype != other.base_type:
                raise TypeError(
                    "mismatch between datatype of input RasterFile and class instance")
            self._add_data_handler(other._handle)
        elif isinstance(other, (DataFileHandler_d,
                                DataFileHandler_d_i,
                                DataFileHandler_d_byt)):
            if self._dtype != np.float64:
                raise TypeError(
                    "Cannot add input RasterFile of double type to class instance of single precision")
            if isinstance(other, DataFileHandler_d):
                self._handle.add_dbl_df_handler(other)
            elif isinstance(other, DataFileHandler_d_i):
                self._handle.add_int_df_handler(other)
            elif isinstance(other, DataFileHandler_d_byt):
                self._handle.add_byt_df_handler(other)
        elif isinstance(other, (DataFileHandler_f,
                                DataFileHandler_f_i,
                                DataFileHandler_f_byt)):
            if self._dtype != np.float32:
                raise TypeError(
                    "Cannot add input RasterFile of single type to class instance of double precision")
            if isinstance(other, DataFileHandler_f):
                self._handle.add_flt_df_handler(other)
            elif isinstance(other, DataFileHandler_f_i):
                self._handle.add_int_df_handler(other)
            elif isinstance(other, DataFileHandler_f_byt):
                self._handle.add_byt_df_handler(other)
        else:
            raise TypeError(
                "input argument should be an instance of RasterFile")

    def _add_raster_base(self, other: "raster.RasterBase"):
        if isinstance(other, raster.RasterBase):
            if self._dtype != other.base_type:
                raise TypeError(
                    "mismatch between datatype of input raster base and class instance")
            self._add_raster_base(other._handle)
        elif isinstance(other, _cyRasterBase_d):
            self._handle.add_dbl_raster_base(other)
        elif isinstance(other, _cyRasterBase_f):
            self._handle.add_flt_raster_base(other)

    @property
    def _size(self) -> int:
        if self._handle is not None:
            return self._handle.get_number_of_rasters()

    def __len__(self) -> int:
        if self._handle is not None:
            return self._size

    def __add__(self, other):
        if isinstance(other, (raster.Raster, raster.RasterFile)):
            self._append(other)
        else:
            self._from_iterable(other)

    def __iadd__(self, other):
        if isinstance(other, (raster.Raster, raster.RasterFile)):
            self._append(other)
        else:
            self._from_iterable(other)

    def __getitem__(self, other: int):
        raise NotImplementedError(
            "Get item operation is not supported on RasterBaseList/RasterPtrList")

    def __setitem__(self, other, value):
        raise NotImplementedError(
            "Set item operation is not supported on RasterBaseList/RasterPtrList")

    def clear(self) -> None:
        self._handle.clear()

    def __del__(self) -> None:
        self.clear()
        del self._handle

    def __repr__(self):
        return "<class 'geostack.raster.%s'>" % self.__class__.__name__
