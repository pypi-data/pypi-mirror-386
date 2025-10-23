# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
from typing import Union, Dict, Any, AnyStr, List, Optional
import numpy as np
from ._cy_shallow_water import cyShallowWater_d, cyShallowWater_f
from ..raster import raster
from ..core import REAL, str2bytes
from ..definitions import _baseEnum, unique

__all__ = ["ShallowWater", "ShallowWaterLayers"]


@unique
class ShallowWaterLayers(_baseEnum):
    d: int = 0
    b: int = 1
    uh: int = 2
    vh: int = 3
    fi: int = 4
    fe: int = 5
    ft: int = 6
    ShallowWaterLayers_END: int = 7

class ShallowWater:
    def __init__(self, dtype: np.dtype = REAL):  # type: ignore
        self._handle: Any = None
        self.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyShallowWater_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyShallowWater_d()
            self.dtype = np.float64  # type: ignore

    def init(self,
             jsonConfig: Union[Dict, AnyStr],
             inputLayers: Optional[Union[List[Union['raster.Raster', 'raster.RasterFile']],
                                   'raster.RasterPtrList']] = None,) -> bool:
        """initialise the solver instance.

        Parameters
        ----------
        jsonConfig : Union[Dict, str]
            a configuration for the solver
        inputLayers : RasterPtrList, optional
            a raster ptr list with input raster layers, by default None

        Returns
        -------
        bool
            True if solver is initialised, False otherwise

        Raises
        ------
        TypeError
            jsonConfig should be a str or dict
        TypeError
            input layers should be an instance of RasterPtrList
        RuntimeError
            unable to initialise the solver
        RuntimeError
            ShallowWater solver is not instantiated
        """
        # Check types
        if not isinstance(jsonConfig, (str, bytes, dict)):
            raise TypeError("jsonConfig should be str or dict")

        if inputLayers is not None:
            if not isinstance(inputLayers, raster.RasterPtrList):
                raise TypeError(
                    "inputLayers should be an instance of RasterPtrList")
        else:
            inputLayers = raster.RasterPtrList()

        if self.dtype != inputLayers._dtype:
            raise TypeError(
                "Mismatch between datatype of inputLayers and ShallowWater instance")

        # Convert json
        if isinstance(jsonConfig, (str, bytes)):
            _json_config = str2bytes(jsonConfig)
        elif isinstance(jsonConfig, dict):
            _json_config = str2bytes(json.dumps(jsonConfig))

        # Initialise
        if self._handle is not None:
            try:
                rc = self._handle.init(_json_config,
                                       inputLayers._handle)
            except Exception as e:
                raise RuntimeError(f"Unable to initialise solver {str(e)}")
        else:
            raise RuntimeError("ShallowWater solver is not initialized")
        return rc

    def step(self) -> bool:
        """forward step the solver.

        Returns
        -------
        bool
            True is successful in forward stepping solver, False otherwise

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.step()
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getHeight(self) -> "raster.Raster":
        """get the height raster from flood solver.

        Returns
        -------
        Raster
            a raster object with the height

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getHeight())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getBase(self) -> "raster.Raster":
        """get the base raster from flood solver.

        Returns
        -------
        Raster
            a raster object with the base

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getBase())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getUnitDischarge_x(self) -> "raster.Raster":
        """get the unit discharge in x direction from flood solver.

        Returns
        -------
        Raster
            a raster object with the base

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getUnitDischarge_x())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getUnitDischarge_y(self) -> "raster.Raster":
        """get the unit discharge in y direction from flood solver.

        Returns
        -------
        Raster
            a raster object with the base

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getUnitDischarge_y())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getU(self) -> "raster.Raster":
        """get the velocity component in x direction from flood solver.

        Returns
        -------
        Raster
            a raster object with the base

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getU())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def getV(self) -> "raster.Raster":
        """get the velocity component in y direction from flood solver.

        Returns
        -------
        Raster
            a raster object with the base

        Raises
        ------
        RuntimeError
            Shallow water solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getV())
        else:
            raise RuntimeError("ShallowWater solver is not initialized")

    def __del__(self):
        if self._handle is not None:
            del self._handle
            self._handle = None

    def __exit__(self, *args, **kwargs):
        self.__del__()

    def __setstate__(self, ds: Dict) -> None:
        self.__init__(dtype=ds.get('dtype'))

    def __getstate__(self) -> Dict:
        output = {"dtype": self.dtype}
        return output

    def __repr__(self):
        return "<class 'geostack.solvers.%s'>" % self.__class__.__name__
