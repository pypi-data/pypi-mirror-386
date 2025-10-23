# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
import numbers
from typing import Union, Dict, Optional, AnyStr, Any
import numpy as np
from ._cy_ode import cyODE_d, cyODE_f
from ..series import Series
from ..core import variables, REAL, str2bytes

__all__ = ["ODE"]


class ODE:
    def __init__(self, dtype: np.dtype = REAL) -> None:
        self._handle: Any = None
        self.dtype: np.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyODE_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyODE_d()
            self.dtype = np.float64  # type: ignore

    def init(self, jsonConfig: Union[Dict, AnyStr],
             inputVariables: Optional["variables.Variables"] = None) -> bool:
        """Initialize the ODE solver

        Parameters
        ----------
        jsonConfig : Union[Dict, AnyStr]
            configuration for the solver
        inputVariables : Variables, optional
            a variables object, by default None

        Returns
        -------
        bool
            True is solver is initialised, False otherwise

        Raises
        ------
        TypeError
            jsonConfig should be a list or dict
        TypeError
            variables should be an instance of Variables object
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

        if inputVariables is not None:
            if not isinstance(inputVariables, variables.Variables):
                raise TypeError(
                    "variables data should be an instance of Variables")
        else:
            inputVariables = variables.Variables()

        if self.dtype != inputVariables._dtype:
            raise TypeError(
                "Mismatch between data type of inputVariables and ODE instance")

        # Convert json
        if isinstance(jsonConfig, (str, bytes)):
            _json_config = str2bytes(jsonConfig)
        elif isinstance(jsonConfig, dict):
            _json_config = str2bytes(json.dumps(jsonConfig))

        # Initialise
        if self._handle is not None:
            try:
                rc = self._handle.init(_json_config,
                                       inputVariables._handle)
            except Exception as e:
                raise RuntimeError(f"Unable to initialise solver {str(e)}")
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")
        return rc

    def setTime(self, t: numbers.Real) -> None:
        """set time for the solver.

        Parameters
        ----------
        d : numbers.Real
            solver time

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            self._handle.setTime(self.dtype(t))
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not initialized")

    def setTimeStep(self, dt: numbers.Real) -> None:
        """set time step for the solver.

        Parameters
        ----------
        dt : numbers.Real
            the time step size

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            self._handle.setTimeStep(self.dtype(dt))
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not initialized")

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

    def get(self, var2_name: str, var1_name: str, var1: numbers.Real,
            index: Optional[int] = 0) -> numbers.Real:
        """returns a value in an internal result series specified as var2(var1)

        Parameters
        ----------
        var2_name : str
            The dependent variable name
        var1_name : str
            The independent variable name
        var1 : numbers.Real
            The independent variable value
        index : int
            The index of the ODE series

        Returns
        -------
        numbers.Real
            the interpolated value from the series, no-data if outside range

        Raises
        ------
        RuntimeError
            solver is not instantiated
        """
        if self._handle is not None:
            return self._handle.get(var2_name, var1_name, var1, index)
        else:
            raise RuntimeError(
                f"{self.__class__.__name__} solver is not instantiated")

    def getSeries(self, var2_name: str, var1_name: str,
                  index: Optional[int] = 0) -> 'Series':
        _out = self._handle.getSeries(var2_name, var1_name, index=index)
        out = Series.c_copy(_out)
        return out

    def isInitialised(self) -> bool:
        """check if solver is initialised

        Returns
        -------
        bool
            True if solver is initialised, False otherwise
        """
        return self._handle.isInitialised()

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
