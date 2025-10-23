# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
import numbers
from typing import Union, Dict, Optional, List, AnyStr, Any
import numpy as np
from ._cy_particle import cyParticle_d, cyParticle_f
from ..raster import raster
from ..core import variables, REAL, str2bytes
from ..vector import vector

__all__ = ["Particle"]


class Particle:
    def __init__(self, dtype: np.dtype = REAL):  # type: ignore
        self._handle: Any = None
        self.dtype: np.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyParticle_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyParticle_d()
            self.dtype = np.float64  # type: ignore

    def init(self,
             jsonConfig: Union[Dict, AnyStr],
             particles: "vector.Vector",
             inputVariables: Optional["variables.Variables"] = None,
             inputLayers: Optional[Union['raster.RasterPtrList',
                                   List[Union['raster.Raster', 'raster.RasterFile']]]] = None) -> bool:
        """Initialize the particle solver

        Parameters
        ----------
        jsonConfig : Union[Dict, AnyStr]
            configuration for the solver
        particles : Vector
            a vector object with particles
        inputVariables : Variables, optional
            a variables object, by default None
        inputLayers : RasterPtrList, optional
            a list of input rasters, by default None

        Returns
        -------
        bool
            True is solver is initialised, False otherwise

        Raises
        ------
        TypeError
            jsonConfig should be a list or dict
        TypeError
            particles should be an instance of Vector object
        TypeError
            variables should be an instance of Variables object
        TypeError
            inputlayers should be an instance of RasterPtrList
        TypeError
            mismatch between datatype of input layers and solver instance
        TypeError
            mismatch between datatype of particles and solver instance
        TypeError
            mismatch between datatype of inputVariables and solver instance
        RuntimeError
            unable to initialise solver
        RuntimeError
            solver is not instantiated
        """
        # Check types
        if not isinstance(jsonConfig, (str, bytes, dict)):
            raise TypeError("jsonConfig should be str or dict")

        if not isinstance(particles, vector.Vector):
            raise TypeError("particles should be an instance of Vector")

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

        # Check data type
        if self.dtype != inputLayers._dtype:
            raise TypeError(
                "Mismatch between datatype of inputLayers and Particle instance")

        if self.dtype != particles._dtype:
            raise TypeError(
                "Mismatch between data type of particles and Particle instance")

        if self.dtype != inputVariables._dtype:
            raise TypeError(
                "Mismatch between data type of inputVariables and Particle instance")

        # Convert json
        if isinstance(jsonConfig, (str, bytes)):
            _json_config = str2bytes(jsonConfig)
        elif isinstance(jsonConfig, dict):
            _json_config = str2bytes(json.dumps(jsonConfig))

        # Initialise
        if self._handle is not None:
            try:
                rc = self._handle.init(_json_config,
                                       particles._handle,
                                       inputVariables._handle,
                                       inputLayers._handle)
            except Exception as e:
                raise RuntimeError(f"Unable to initialise solver {str(e)}")
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")
        return rc

    def step(self) -> bool:
        """run a step of the solver

        Returns
        -------
        bool
            True if solver steps forward, False otherwise

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.step()
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")

    def setTimeStep(self, dt: numbers.Real) -> bool:
        """set time step for the solver.

        Parameters
        ----------
        dt : numbers.Real
            the time step size

        Returns
        -------
        bool
            True if sucessful in setting time step, false otherwise

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.setTimeStep(dt)
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not initialized")

    def addParticles(self, particles) -> None:
        """add particles to the solver.

        Parameters
        ----------
        particles : Vector
            a vector object with particles

        Raises
        ------
        TypeError
            particles should be an instance of Vector object
        TypeError
            mismatch between data type of particles and particles instance
        """
        if not isinstance(particles, vector.Vector):
            raise TypeError("particles should be an instance of Vector")

        if self.dtype != particles._dtype:
            raise TypeError(
                "Mismatch between data type of particles and Particle instance")

        if self._handle is not None:
            self._handle.addParticles(particles._handle)

    def getParticles(self) -> "vector.Vector":
        """get the particles from the solver.

        Returns
        -------
        Vector
            a vector object with the particles

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return vector.Vector._from_vector(self._handle.getParticles())
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")

    def getSamplePlaneIndexCount(self) -> int:
        """get the count of particles on or crossing the sample plane from the solver.

        Returns
        -------
        int
            the count of particles on or crossing the sample plane

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.getSamplePlaneIndexCount()
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")

    def getSamplePlaneIndexes(self) -> np.ndarray:
        """get the array of particle indexes crossing the sample plane.

        Returns
        -------
        array
            array of particle indexes crossing the sample plane

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return np.asanyarray(self._handle.getSamplePlaneIndexes())
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")

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
