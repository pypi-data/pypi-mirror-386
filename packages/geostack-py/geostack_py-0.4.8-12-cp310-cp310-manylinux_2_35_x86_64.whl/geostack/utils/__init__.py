# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import os.path as pth
import re
import sys
import platform
import ctypes
import numbers
import logging
from typing import Union, Dict, List, Callable
from functools import partial
import numpy as np
from .get_projection import (get_epsg,
                             get_wkt_for_epsg_code,
                             proj4_from_wkt,
                             proj4_to_wkt,
                             have_internet)
from ._cy_utilities import c_quantile, c_percentile
from .. import core
from .. import vector
from .. import raster
from .. import gs_enums
from .. import runner


def is_ipython():
    """check if using ipython kernel

    Returns
    -------
    bool
        True if running ipython kernel, False otherwise
    """
    try:
        from IPython import get_ipython
        rc = get_ipython()
        if rc:
            return True
        else:
            return False
    except ImportError:
        return False


def is_jupyter_notebook() -> bool:
    """check if using jupyter notebook

    Returns
    -------
    bool
        True if running notebook, False otherwise
    """
    rc = False
    if is_ipython():
        out = os.environ.get("_", None)
        if out:
            if os.path.basename(out) != 'jupyter-console':
                rc = True
    return rc


def enable_geostack_logging(level: int = logging.INFO):
    """enable logging from geostack.

    Parameters
    ----------
    level : int, optional
        logging level, by default logging.INFO

    Returns
    -------
    None
    """
    class Filter(logging.Filter):
        def filter(self, message):
            return message.levelno < logging.WARNING

    if is_jupyter_notebook():
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        logger.propagate = False

        if logger.hasHandlers():
            for handle in logger.handlers:
                logger.removeHandler(handle)

        stdout = logging.StreamHandler(sys.stdout)
        stdout.setLevel(level)
        stdout.addFilter(Filter())
        logger.addHandler(stdout)

        stderr = logging.StreamHandler(sys.stderr)
        stderr.setLevel(logging.WARNING)
        logger.addHandler(stderr)
    else:
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        logger.propagate = False

        if logger.hasHandlers():
            for handle in logger.handlers:
                logger.removeHandler(handle)

        logger.setLevel(level)


def percentile(inp_array: np.ndarray, p: Union[numbers.Real, np.ndarray],
               is_sorted: bool = True) -> Union[numbers.Real, np.ndarray]:
    """an optimized implementation of percentile calculator

    Parameters
    ----------
    inp_array : np.ndarray
        input 1d array
    p : Union[numbers.Real, np.ndarray]
        desired percentile
    is_sorted : bool, optional
        flag to skip sorting if input data is sorted, by default True

    Returns
    -------
    Union[numbers.Real, np.ndarray]
        a float value or ndarray with percentile values
    """
    if np.isscalar(p):
        return c_percentile(inp_array, p, is_sorted)
    else:
        out = map(lambda s: c_percentile(inp_array, s, is_sorted), p)
        return np.fromiter(out, dtype='f', count=len(p))


def quantile(inp_array: np.ndarray, q: Union[numbers.Real, np.ndarray],
             is_sorted: bool = True) -> Union[numbers.Real, np.ndarray]:
    """an optimized implementation of quantile calculator

    Parameters
    ----------
    inp_array : np.ndarray
        input 1d array
    q : Union[numbers.Real, np.ndarray]
        desired quantile
    is_sorted : bool, optional
        flag to skip sorting if input data is sorted, by default True

    Returns
    -------
    Union[numbers.Real, np.ndarray]
        a float value or ndarray with quantile values
    """
    if np.isscalar(q):
        return c_quantile(inp_array, q, is_sorted)
    else:
        out = map(lambda s: c_quantile(inp_array, s, is_sorted), q)
        return np.fromiter(out, dtype='f', count=len(q))


def zonal_stats(inpVector: "vector.Vector", inpRaster: "raster.Raster",
                stats: Union[List, str, Callable] = None,
                add_stats: Dict = None, inplace: bool = False) -> Union[Dict, "vector.Vector"]:
    """Compute zonal statistics from a Raster object for a given Vector object.

    The default statistics computed by this method are:
    * min: minimum of the raster values
    * max: maximum of the raster values
    * mean: mean of the raster values
    * count: count of the raster values

    The other statistics available are:
    * sum: sum of the raster values
    * range: range (max - min) of the raster values
    * median: median of the raster values
    * std: standard deviation of the raster values
    * var: variance of the raster values

    For raster with integer values, it is also possible to compute the following statistics:
    * majority: most frequent value of the raster values
    * minority: least frequent value of the raster values
    * variety: number of unique values in the raster values

    Parameters
    ----------
    inpVector : Vector
        an instance of Vector object
    inpRaster : Raster/RasterFile
        an instance of Raster/RasterFile object
    stats : Union[List, str]
        a list or string describing stats to be computed, default is None
    add_stats: Dict
        a dictionary with user defined method for computing stats
    inplace: bool
        flag to update the Vector in place, if True, update in place,
        else return a dictionary with properties

    Returns
    -------
    Union[Dict, Any]
        a dictionary or an instance of Vector object
    """
    default_stats = ["min", "max", "mean", "count"]
    valid_stats = default_stats + ["sum", "range", "median", "std", "var"]

    def unique_method(s): return np.unique(s, return_counts=True)
    def majority_method(s): return s[0][np.argmax(s[1])]
    def minority_method(s): return s[0][np.argmin(s[1])]

    int_stats = dict(variety=lambda s: len(unique_method(s)[0]),
                     majority=lambda s: majority_method(unique_method(s)),
                     minority=lambda s: minority_method(unique_method(s)))

    # list of non-numpy stats
    non_npy_stats = ['count', 'range']

    nullValue = raster.getNullValue(inpRaster.data_type)

    # define methods for non-numpy stats
    def range_method(s): return s.max() - s.min() if len(s) > 0 else nullValue

    # user defined stats
    defined_stats = {}
    if add_stats is not None:
        defined_stats.update(add_stats)

    if not isinstance(inpVector, vector.Vector):
        raise TypeError("input vector should be an instance of Vector object")

    if not isinstance(inpRaster, (raster.Raster, raster.RasterFile)):
        raise TypeError(
            "input raster should be an instance of Raster/RasterFile object")

    assert inpRaster.base_type == inpVector._dtype, "Input raster and vector should have same data type"

    # add stats that are only valid for integer values
    if inpRaster.data_type in [np.uint32, np.int32]:
        non_npy_stats += [item for item in int_stats]

    methods = {}
    if stats is None:
        inp_stats = [*default_stats]
        defined_stats.update({"count": lambda s: len(s) if len(s) > 0 else 0})
    else:
        if isinstance(stats, (list, str)):
            if isinstance(stats, str):
                inp_stats = stats.strip().split(" ")
            elif isinstance(stats, list):
                inp_stats = [item.strip() for item in stats]

            # filter user stats
            def stats_filter(s): return (s in valid_stats) | s.startswith(
                "percentile") | (s in non_npy_stats)
            inp_stats = list(filter(lambda s: stats_filter(s), inp_stats))

            # add percentile method (or non numpy methods) if needed
            for stat in inp_stats:
                if stat.startswith("percentile"):
                    p_value = eval(f'{stat.replace("percentile_")}')
                    if p_value < 0 | p_value > 100:
                        raise ValueError(f"stat {stat} is invalid")
                    methods[stat] = partial(percentile, p=p_value)
                elif stat == "range":
                    defined_stats.update({f"{stat}": range_method})
                elif stat == "count":
                    defined_stats.update(
                        {"count": lambda s: len(s) if len(s) > 0 else 0})
                elif inpRaster.data_type in [np.uint32, np.int32] and stat in int_stats:
                    defined_stats[stat] = int_stats[stat]
        else:
            raise TypeError(
                "stats should be either a string or list of string")

    # get the methods from numpy
    for stat in inp_stats:
        if not (stat.startswith("percentile") | (stat in non_npy_stats)):
            methods[stat] = getattr(np, stat)

    # now create a list of new properties
    new_props = {}
    for stat in inp_stats:
        if stat.startswith("percentile"):
            new_props[stat] = f"{inpRaster.name}_{stat.replace('percentile', 'p')}"
        else:
            new_props[stat] = f"{inpRaster.name}_{stat}"

    # add user defined stats
    new_props.update(
        {stat: f"{inpRaster.name}_{stat}" for stat in defined_stats})
    methods.update(defined_stats)

    if not inplace:
        out_stats = {new_props[prop]: [] for prop in new_props}
    else:
        for prop in new_props:
            if not inpVector.hasProperty(new_props[prop]):
                inpVector.addProperty(new_props[prop])

    inpVector.addProperty("raster_values")

    # get the raster cells attached to each vector geometry
    runner.runVectorScript(f"raster_values = {inpRaster.name};",
                           inpVector, [inpRaster],
                           reductionType=gs_enums.ReductionType.NoReduction)

    # now compute stats for each geometry
    for idx in inpVector.getGeometryIndexes():
        raster_values = inpVector.getProperty(idx, "raster_values")
        for prop in methods:
            if inplace:
                if len(raster_values) > 0:
                    value = methods[prop](raster_values)
                    if not np.isscalar(value):
                        if len(value) > 1 and prop in add_stats:
                            raise ValueError(
                                f"invalid method for used defined stat {prop}")
                else:
                    value = nullValue if prop != 'count' else 0
                inpVector.setProperty(idx, new_props[prop], value)
            else:
                if len(raster_values) > 0:
                    try:
                        value = methods[prop](raster_values)
                        if isinstance(value, (core.FloatVector,
                                              core.DoubleVector,
                                              core.IntegerVector)):
                            if len(value.shape) < 1:
                                value = value[0]
                    except Exception as e:
                        if isinstance(raster_values, (core.FloatVector,
                                                      core.DoubleVector,
                                                      core.IntegerVector)):
                            value = methods[prop](np.asarray(raster_values[:],
                                                             dtype=raster_values._dtype_info))

                    if np.isscalar(value):
                        value = [value]
                else:
                    value = [nullValue] if prop != 'count' else [0]

                if len(value) > 1 and prop in add_stats:
                    raise ValueError(
                        f"invalid method for used defined stat {prop}")
                if isinstance(value, np.ndarray):
                    out_stats[new_props[prop]] += value.tolist()
                else:
                    out_stats[new_props[prop]] += value

    inpVector.removeProperty("raster_values")

    if inplace:
        return inpVector
    else:
        return out_stats


class DiskUsage:
    def __init__(self, path):

        path = os.path.realpath(path)
        self.path = path

        if platform.system() == "Windows":
            avail = ctypes.c_ulonglong()
            total = ctypes.c_ulonglong()
            free = ctypes.c_ulonglong()

            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                ctypes.pointer(avail),
                ctypes.pointer(total),
                ctypes.pointer(free),
            )
            self.avail = avail.value
            self.total = total.value
            self.free = free.value
        else:
            st = os.statvfs(path)
            self.free = st.f_bfree * st.f_frsize
            self.total = st.f_blocks * st.f_frsize
            self.avail = st.f_bavail * st.f_frsize

        self.percent = int(
            float(self.total - self.avail) / float(self.total) * 100 + 0.5
        )

    def __repr__(self):
        return (
            f"DiskUsage(total={self.total},free={self.free},"
            f"avail={self.avail},percent={self.percent},path={self.path})"
        )


def disk_usage(path):
    return DiskUsage(path)


def is_remote_uri(path: str) -> bool:
    """Finds URLs of the form protocol:// or protocol::
    This also matches for http[s]://, which were the only remote URLs
    supported in <=v0.16.2.

    It now also supports /vsicurl/protocol://
    """
    return bool(re.search(r"^[a-z\/]*[a-z][a-z0-9]*(\://|\:\:)", path))


def is_file_on_disk(path: str) -> bool:
    """check if file is on disk

    Parameters
    ----------
    path : str
        path of a file

    Returns
    -------
    bool
        True if file or soft link to file exists on disk, False otherwise
    """
    if not is_remote_uri(path):
        return pth.isfile(path) | pth.islink(path)
    else:
        return True


class rpartial(partial):
    #reference: https://stackoverflow.com/a/11831662
    def __call__(self, *args, **kwargs):
        kw = self.keywords.copy()
        kw.update(kwargs)
        return self.func(*(args + self.args), **kw)
