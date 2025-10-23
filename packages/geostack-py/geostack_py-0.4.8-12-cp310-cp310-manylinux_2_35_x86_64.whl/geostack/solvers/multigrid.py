# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
from typing import Union, Dict, Optional, Any, AnyStr
import numpy as np
from ._cy_multigrid import cyMultigrid_d, cyMultigrid_f
from .. import core
from ..raster import raster

__all__ = ["Multigrid"]


class Multigrid:
    def __init__(self, dtype: np.dtype = core.REAL):  # type: ignore
        self._handle: Any = None
        self.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyMultigrid_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyMultigrid_d()
            self.dtype = np.float64  # type: ignore

    def init(self,
             jsonConfig: Union[Dict, AnyStr],
             inputLayers: Optional['raster.RasterPtrList'] = None) -> bool:
        """initialise the solver instance.

        Parameters
        ----------
        jsonConfig : Union[Dict, str]
            a configuration for the solver
        inputLayers : RasterPtrList, optional
            a raster ptr list containing input raster layers, by default None

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
            multigrid solver is not instantiated
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

        # Convert json
        if isinstance(jsonConfig, (str, bytes)):
            _json_config = core.str2bytes(jsonConfig)
        elif isinstance(jsonConfig, dict):
            _json_config = core.str2bytes(json.dumps(jsonConfig))

        # Initialise
        if self._handle is not None:
            try:
                rc = self._handle.init(_json_config,
                                       inputLayers._handle)
            except Exception as e:
                raise RuntimeError(f"Unable to initialise solver {str(e)}")
        else:
            raise RuntimeError("Multigrid solver is not initialized")
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
            raise RuntimeError("Multigrid solver is not initialized")

    def getForcing(self) -> "raster.Raster":
        """get the forcing raster object.

        Returns
        -------
        Raster
            a raster object with the solver forcing

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy("", self._handle.getForcing())
        else:
            raise RuntimeError("Multigrid solver is not initialized")

    def getForcingLevel(self, level: int) -> "raster.Raster":
        """get the forcing raster object for a given level.

        Parameters
        ----------
        level: int
            forcing level

        Returns
        -------
        Raster
            a raster object with the solver forcing

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy("", self._handle.getForcingLevel(level))
        else:
            raise RuntimeError("Multigrid solver is not initialized")

    def getSolution(self) -> "raster.Raster":
        """get the solution of the multigrid solver

        Returns
        -------
        Raster
            a raster object with the solution from the solver.

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy("", self._handle.getSolution())
        else:
            raise RuntimeError("Multigrid solver is not initialized")

    def pyramids(self) -> bool:
        """generate pyramids

        Returns
        -------
        bool
            True if pyramids are created, False otherwise
        """
        return self._handle.pyramids()

    def __del__(self):
        if self._handle is not None:
            del self._handle
            self._handle = None

    def __exit__(self):
        self.__del__()

    def __setstate__(self, ds: Dict) -> None:
        self.__init__(dtype=ds.get('dtype'))

    def __getstate__(self) -> Dict:
        output = {"dtype": self.dtype}
        return output

    def __repr__(self):
        return "<class 'geostack.solvers.%s'>" % self.__class__.__name__
