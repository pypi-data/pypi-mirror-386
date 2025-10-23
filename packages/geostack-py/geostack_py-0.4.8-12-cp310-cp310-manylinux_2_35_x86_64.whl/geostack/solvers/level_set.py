# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numbers
import json
from typing import Union, Dict, List, Optional, Any
from numbers import Integral, Real
import numpy as np
from ._cy_level_set import cyLevelSet_d, cyLevelSet_f
from ..raster import raster
from ..core import variables, REAL, str2bytes
from ..core import property as gs_property
from ..vector import vector
from ..definitions import _baseEnum, unique

__all__ = ["LevelSet",
           "LevelSetParameters",
           "LevelSetRasterIndex",
           "LevelSetLayers"]


@unique
class LevelSetLayers(_baseEnum):
    Distance: int = 0
    DistanceUpdate: int = 1
    Rate: int = 2
    Speed: int = 3
    Arrival: int = 4
    Advect_x: int = 5
    Advect_y: int = 6
    StartTime: int = 7
    StartTimeUpdate: int = 8
    LevelSetLayers_END: int = 9


try:
    from dataclasses import dataclass

    @dataclass
    class LevelSetParameters:
        time: Union[Integral, Real]
        dt: Union[Integral, Real]
        maxSpeed: Union[Integral, Real]
        area: Union[Integral, Real]
        bandWidth: Union[Integral, Real]
        JulianDate: Union[Integral, Real]

    @dataclass
    class LevelSetRasterIndex:
        i: Integral
        j: Integral
        k: Integral

except ImportError:
    # declare a class if dataclass is not present
    # work around for older python3
    class LevelSetParameters:
        __slots__ = ()
        time: Union[Integral, Real]
        dt: Union[Integral, Real]
        maxSpeed: Union[Integral, Real]
        area: Union[Integral, Real]
        bandWidth: Union[Integral, Real]
        JulianDate: Union[Integral, Real]

    class LevelSetRasterIndex:
        __slots__ = ()
        i: Integral
        j: Integral
        k: Integral


class LevelSet:
    def __init__(self, dtype: np.dtype = REAL):  # type: ignore
        self._handle: Any = None
        self.dtype: np.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyLevelSet_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyLevelSet_d()
            self.dtype = np.float64  # type: ignore

    def init(self,
             jsonConfig: Union[Dict, str],
             startCondition: "vector.Vector",
             inputVariables: "variables.Variables" = None,
             inputLayers: Optional[Union[List[Union['raster.Raster', 'raster.RasterFile']],
                                   'raster.RasterPtrList']] = None,
             outputLayers: Optional['raster.RasterPtrList'] = None) -> bool:
        """Intialise the instance of level set solver

        Parameters
        ----------
        jsonConfig : Union[Dict, str]
            the solver configuration
        startCondition : Vector
            a vector object with the start conditions
        inputVariables : Variables, optional
            a variables object, by default None
        inputLayers : RasterPtrList, optional
            a raster ptr list with input raster layers, by default None
        outputLayers : RasterPtrList, optional
            a raster ptr list with output raster layers, by default None

        Returns
        -------
        bool
            True if solver is initialised, False otherwise

        Raises
        ------
        TypeError
            jsonConfig should be a str or dict
        TypeError
            startConditions should be an instance of Vector
        TypeError
            variables should an instance of Variables
        TypeError
            input layers should be an instance of RasterPtrList
        TypeError
            output layers should be an instance of RasterPtrList
        TypeError
            mistmatch between data type of start conditions and solver instance
        TypeError
            mistmatch between data type of input layers and solver instance
        TypeError
            mistmatch between data type of output layers and solver instance
        TypeError
            mistmatch between data type of input variables and solver instance
        RuntimeError
            unable to initialise the solver instance
        RuntimeError
            solver is not instantiated
        """

        # Check types
        if not isinstance(jsonConfig, (str, dict)):
            raise TypeError("jsonConfig should be str or dict")

        if not isinstance(startCondition, vector.Vector):
            raise TypeError("startCondition should be an instance of Vector")

        if inputVariables is not None:
            if not isinstance(inputVariables, variables.Variables):
                raise TypeError(
                    "variables data should be an instance of Variables")
        else:
            inputVariables = variables.Variables()

        if inputLayers is not None:
            if not isinstance(inputLayers, raster.RasterPtrList):
                raise TypeError(
                    "inputLayers should be an instance of RasterPtrList")
        else:
            inputLayers = raster.RasterPtrList()

        if outputLayers is not None:
            if not isinstance(outputLayers, raster.RasterPtrList):
                raise TypeError(
                    "outputLayers should be an instance of RasterPtrList")
        else:
            outputLayers = raster.RasterPtrList()

        # Check data type
        if self.dtype != startCondition._dtype:
            raise TypeError(
                "Mismatch between datatype of startCondition and LevelSet instance")

        if self.dtype != inputLayers._dtype:
            raise TypeError(
                "Mismatch between datatype of inputLayers and LevelSet instance")

        if self.dtype != outputLayers._dtype:
            raise TypeError(
                "Mismatch between datatype of outputLayers and LevelSet instance")

        if self.dtype != inputVariables._dtype:
            raise TypeError(
                "Mismatch between data type of inputVariables and LevelSet instance")

        # Convert json
        if isinstance(jsonConfig, str):
            _json_config = str2bytes(jsonConfig)
        elif isinstance(jsonConfig, dict):
            _json_config = str2bytes(json.dumps(jsonConfig))

        # Initialise
        if self._handle is not None:
            try:
                rc = self._handle.init(_json_config, startCondition._handle,
                                       inputVariables._handle, inputLayers._handle,
                                       outputLayers._handle)
            except Exception as e:
                raise RuntimeError(f"Unable to initialise solver {str(e)}")
        else:
            raise RuntimeError("LevelSet solver is not initialized")
        return rc

    def step(self) -> bool:
        """step the level set solver.

        Returns
        -------
        bool
            True if successful in forward stepping the solver, False otherwise

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.step()
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def resizeDomain(self, nx: int, ny: int, tox: int, toy: int, activateTiles: bool = False):
        """force the the level set domain to resize.

        Parameters
        ----------
        nx : Integer
            new number of tiles in x-direction
        ny : Integer
            new number of tiles in y-direction
        tox : Integer
            new index of current tile origin in x-direction
        toy : Integer
            new index of current tile origin in y-direction

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.resizeDomain(np.uint32(nx), np.uint32(ny),
                                             np.uint32(tox), np.uint32(toy),
                                             activateTiles = activateTiles)
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def addSource(self, input_source: "vector.Vector"):
        """add source to the solver.

        Parameters
        ----------
        input_source : Vector
            a vector object with the source

        Raises
        ------
        TypeError
            input should should be a vector object
        AssertionError
            Type mismatch for solver and vector
        """
        if not isinstance(input_source, vector.Vector):
            raise TypeError("input source should be a Vector object")
        assert input_source._dtype == self.dtype, "Type mismatch for solver and Vector"
        self._handle.addSource(input_source._handle)

    def getParameters(self) -> Dict:
        """get the level set solver parameters

        Returns
        -------
        dict
            a dictionary with the level set solver parameters

        Raises
        ------
        RuntimeError
            level set solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.getParameters()
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def setParameters(self, param: str, value: numbers.Real):
        """set values of a parameter in LevelSetParameters

        Parameters
        ----------
        param : str
            the parameter in the LevelSetParameters
        value : numbers.Real
            the values for the parameter

        Raises
        ------
        RuntimeError
            level set solver is not instantiated
        """
        if self._handle is not None:
            self._handle.setParameters(
                str2bytes(param), np.float64(value))
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getDistance(self) -> "raster.Raster":
        """get the distance raster

        Returns
        -------
        Raster
            a raster object with the distance values.

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getDistance())
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getArrival(self) -> "raster.Raster":
        """get the fire arrival time.

        Returns
        -------
        Raster
            a raster object with the fire arrival time

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getArrival())
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getClassification(self) -> "raster.Raster":
        """get the land classification

        Returns
        -------
        Raster
            a raster object with the land classification

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getClassification())
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getAdvect_x(self) -> "raster.Raster":
        """get the advection vector in x-direction

        Returns
        -------
        Raster
            a raster object with advection in x-direction

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getAdvect_x())
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getAdvect_y(self) -> "raster.Raster":
        """get the advection in y-direction

        Returns
        -------
        Raster
            a raster object with advection in y-direction

        Raises
        ------
        RuntimeError
            Level set solver is not instantiated
        """
        if self._handle is not None:
            return raster.Raster.copy(None, self._handle.getAdvect_y())
        else:
            raise RuntimeError("LevelSet solver is not initialized")

    def getEpochMilliseconds(self) -> numbers.Real:
        """get the solver time as epoch milliseconds

        Returns
        -------
        numbers.Real
            the solver current time
        """
        out = self._handle.getEpochMilliseconds()
        return out

    def getLevelSetLayer(self, levelSetLayer: LevelSetLayers) -> "raster.Raster":
        """get a level set layer from the LevelSet solver

        Parameters
        ----------
        levelSetLayer : LevelSetLayers
            layer name/ index

        Returns
        -------
        raster.Raster
            a Raster object with level set layer
        """
        return raster.Raster.copy(None, self._handle.getLevelSetLayer(
            LevelSetLayers(levelSetLayer).value))

    def getOutput(self, name: str):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        name : str
            _description_

        Returns
        -------
        _type_
            _description_
        """
        out = raster.RasterBase(self._handle.getOutput(
            gs_property.str2bytes(name)))
        data_type_str = out._handle.getDataTypeString()
        return out

    @property
    def parameters(self) -> LevelSetParameters:
        return LevelSetParameters(**self.getParameters())

    def runInit(self):
        self._handle.runInit()

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
