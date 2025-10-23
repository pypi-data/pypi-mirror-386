# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
from ._cy_solver import cySolver
from ..utils import enable_geostack_logging
from numbers import Integral
import numpy as np
import numbers
from typing import Union

from ._cy_solver import (isValid_flt, isValid_dbl, isValid_u32,
                         isValid_u64, isValid_i32, isValid_i64,
                         isValid_str)
from ._cy_solver import (isInvalid_flt, isInvalid_dbl, isInvalid_u32,
                         isInvalid_u64, isInvalid_i32, isInvalid_i64,
                         isInvalid_str)

__all__ = ["Solver", 'isValid', 'isInvalid']


def isValid(other: Union[str, numbers.Number]) -> bool:
    """check if the input is a valid value

    Parameters
    ----------
    other : Union[str, numbers.Number]
        a value

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    method_map = {
        np.uint32: isValid_u32,
        np.uint64: isValid_u64,
        np.int32: isValid_i32,
        int: isValid_i64,
        np.int64: isValid_i64,
        np.float32: isValid_flt,
        np.float64: isValid_dbl,
        float: isValid_dbl,
        str: isValid_str
    }
    out = method_map[type(other)](other)
    return out


def isInvalid(other: Union[str, numbers.Number]) -> bool:
    """check if the input is an invalid value

    Parameters
    ----------
    other : Union[str, numbers.Number]
        a value

    Returns
    -------
    bool
        True if invalid, False otherwise
    """
    method_map = {
        np.uint32: isInvalid_u32,
        np.uint64: isInvalid_u64,
        np.int32: isInvalid_i32,
        np.int64: isInvalid_i64,
        int: isInvalid_i64,
        np.float32: isInvalid_flt,
        np.float64: isInvalid_dbl,
        float: isInvalid_dbl,
        str: isInvalid_str,
    }
    out = method_map[type(other)](other)
    return out


class Solver:
    def __init__(self):
        self._handle = cySolver()
        enable_geostack_logging(self._handle.getVerboseLevel())

    def setVerbose(self, verbose: bool):
        """set verbose flag for logger

        Parameters
        ----------
        verbose : bool
            True to set solver to verbose, false otherwise

        Raises
        ------
        TypeError
            input argument should be a bool
        """
        if not isinstance(verbose, bool):
            raise TypeError("input argument should be bool")
        self._handle.setVerbose(verbose)

        # update python logger
        if verbose:
            enable_geostack_logging(self._handle.getVerboseLevel())

    def setVerboseLevel(self, verbose: Integral):
        """set verbosity level of the solver

        Parameters
        ----------
        verbose : Integral
            verbosity level to control logging and verbosity

        Raises
        ------
        TypeError
            verbose level should be an integer
        """
        if not isinstance(verbose, Integral):
            raise TypeError("input argument should be an integer")
        self._handle.setVerboseLevel(verbose)
        # update python logger
        enable_geostack_logging(self._handle.getVerboseLevel())

    def getVerboseLevel(self) -> Integral:
        """get the verbosity level of the solver (logger)

        Returns
        -------
        Integral
            the verbosity level of the logger (solver)
        """
        return self._handle.getVerboseLevel()

    def setHostMemoryLimit(self, hostMemoryLimit_: Integral):
        """set host memory limit in bytes

        Parameters
        ----------
        hostMemoryLimit: Integral
            host memory limit in bytes
        """

        self._handle.setHostMemoryLimit(np.uint64(hostMemoryLimit_))

    def getHostMemoryLimit(self) -> Integral:
        """get host memory limit in bytes

        Returns
        -------
        Integral
            get host memory limit in bytes
        """

        return self._handle.getHostMemoryLimit()

    def setDeviceMemoryLimit(self, deviceMemoryLimit_: Integral):
        """set device memory limit in bytes

        Parameters
        ----------
        deviceMemoryLimit: Integral
            set device memory limit in bytes
        """

        self._handle.setDeviceMemoryLimit(np.uint64(deviceMemoryLimit_))

    def getDeviceMemoryLimit(self) -> Integral:
        """get device memory limit in bytes

        Returns
        -------
        Integral
            get device memory limit in bytes
        """

        return self._handle.getDeviceMemoryLimit()

    @staticmethod
    def get_verbose_level() -> Integral:
        """get verbose level from the solve instance.

        Returns
        -------
        Integral
            the verbosity level from the solver instance
        """
        obj = Solver()
        return obj.getVerboseLevel()

    @staticmethod
    def set_verbose(verbose: bool):
        """set verbosity of the solver.

        Parameters
        ----------
        verbose : bool
            True to enable verbosity, False otherwise.
        """
        obj = Solver()
        obj.setVerbose(verbose)

    @staticmethod
    def set_verbose_level(verbose: Integral):
        """set verbosity level for the solver

        Parameters
        ----------
        verbose : Integral
            the level of verbosity for the solver.
        """
        obj = Solver()
        obj.setVerboseLevel(verbose)

    @staticmethod
    def set_host_memory_limit(hostMemoryLimit_: Integral):
        """set host memory limit

        Parameters
        ----------
        hostMemoryLimit: Integral
            set host memory limit in bytes
        """
        obj = Solver()
        obj.setHostMemoryLimit(hostMemoryLimit_)

    @staticmethod
    def get_host_memory_limit() -> Integral:
        """get host memory limit in bytes

        Returns
        -------
        Integral
            get host memory limit
        """
        obj = Solver()
        return obj.getHostMemoryLimit()

    @staticmethod
    def set_device_memory_limit(deviceMemoryLimit_: Integral):
        """set device memory limit in bytes

        Parameters
        ----------
        deviceMemoryLimit: Integral
            set device memory limit
        """
        obj = Solver()
        obj.setDeviceMemoryLimit(deviceMemoryLimit_)

    @staticmethod
    def get_device_memory_limit() -> Integral:
        """get device memory limit in bytes

        Returns
        -------
        Integral
            get device memory limit
        """
        obj = Solver()
        return obj.getDeviceMemoryLimit()

    def openCLInitialised(self) -> bool:
        return self._handle.openCLInitialised()

    def initOpenCL(self) -> bool:
        return self._handle.initOpenCL()

    def __repr__(self):
        return self.__repr__()

    def __str__(self):
        return "<class 'geostack.core.%s'>" % self.__class__.__name__
