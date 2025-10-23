# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import json
from typing import Union, Dict, Any, AnyStr
import numpy as np
from ._cy_network_flow import cyNetworkFlowSolver_d, cyNetworkFlowSolver_f
from .. import core
from ..vector import vector

__all__ = ["NetworkFlowSolver"]


class NetworkFlowSolver:
    def __init__(self, dtype: np.dtype = core.REAL):  # type: ignore
        self._handle: Any = None
        self.dtype: np.dtype = dtype  # type: ignore
        if dtype is None or dtype == np.float32:
            self._handle = cyNetworkFlowSolver_f()
            self.dtype = np.float32  # type: ignore
        elif dtype == np.float64:
            self._handle = cyNetworkFlowSolver_d()
            self.dtype = np.float64  # type: ignore

    def init(self,
             input_vector: "vector.Vector",
             jsonConfig: Union[Dict, AnyStr]) -> bool:
        """initialise the network flow solver.

        Parameters
        ----------
        input_vector : Vector
            a vector object
        jsonConfig : Union[Dict, str, bytes]
            solver configuration

        Returns
        -------
        bool
            True if successfully initialised the solver, False otherwise

        Raises
        ------
        TypeError
            input vector should be an instance of vector object
        TypeError
            json config should be string/ bytes or dict
        TypeError
            mismatch between type of network flow solver and input vector
        """
        if not isinstance(input_vector, vector.Vector):
            raise TypeError(
                "input_vector should be an instance of vector class")
        if not isinstance(jsonConfig, (str, bytes, dict)):
            raise TypeError("jsonConfig should be string/ bytes or dict")

        if input_vector._dtype != self.dtype:
            raise TypeError(
                "Mismatch between type of network flow solver and input vector")

        if isinstance(jsonConfig, (str, bytes)):
            rc = self._handle.init_solver(
                input_vector._handle, core.str2bytes(jsonConfig))
        elif isinstance(jsonConfig, dict):
            rc = self._handle.init_solver(
                input_vector._handle, core.str2bytes(json.dumps(jsonConfig)))

        # if not rc:
        #    raise RuntimeError("Unable to initialise network flow solver")
        return rc

    def run(self) -> bool:
        """run the network flow solver

        Returns
        -------
        bool
            True if successfully ran the solver, False otherwise
        """
        out = self._handle.run()
        return out

    def getNetwork(self) -> "vector.Vector":
        """get the network after running the network flow solver.

        Returns
        -------
        Vector
            a vector object with the resulting network.
        """
        out = self._handle.getNetwork()
        return vector.Vector._from_vector(out)

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
