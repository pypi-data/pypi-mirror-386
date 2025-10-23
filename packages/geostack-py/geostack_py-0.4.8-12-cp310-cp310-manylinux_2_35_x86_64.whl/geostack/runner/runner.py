# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import numbers
from typing import List, Union, Tuple, Optional
import numpy as np
from ..raster import raster
from .. import gs_enums
from .. import core
from ..runner._cy_runner import (RasterScript_d, RasterScript_f,
                                 VectorScript_d, VectorScript_f)
from ..vector import vector, _cy_vector


__all__ = ["runScript", "runAreaScript",
           "runVectorScript", "stipple"]


def runScript(script: str, inputRasters: Union[List[Union['raster.Raster',
                                                          'raster.RasterFile',
                                                          'raster.RasterBase']],
                                               Tuple[Union['raster.Raster',
                                                           'raster.RasterFile',
                                                           'raster.RasterBase']],
                                               'raster.RasterBaseList'],
              parameter: Union[numbers.Integral,
                               gs_enums.RasterCombinationType,
                               gs_enums.RasterResolutionType,
                               gs_enums.RasterNullValueType,
                               gs_enums.RasterInterpolationType,
                               gs_enums.ReductionType,
                               gs_enums.RasterDebug,
                               gs_enums.RasterSortType] = 0,
              output_type=core.REAL) -> 'raster.Raster':
    '''Run script on a list of input raster over GPU.

    Parameters
    ----------
    script : str
        Script to build kernel for running on GPU.
    inputRasters : list/tuple/RasterBaseList/RasterPtrList
        A list of input rasters
    parameter : Union[numbers.Integral,
                      gs_enums.RasterCombinationType,
                      gs_enums.RasterResolutionType,
                      gs_enums.RasterNullValueType,
                      gs_enums.RasterInterpolationType,
                      gs_enums.RasterDebug,
                      gs_enums.RasterSortType]

        parameter for controlling script processing, default 0
    output_type : np.float32/np.float64/np.uint32
        Data type for the output raster object from runScript

    Returns
    -------
    out : Raster object
        Raster output from the runScript

    Examples
    --------
    >>> out = runScript("out = 100 * testRasterA;", [testRasterA])
    '''

    # Check script and encode as necessary
    if isinstance(script, (str, bytes)):
        _script = core.str2bytes(script)
    else:
        raise TypeError("script can be only string or bytes")

    # check parameter
    if not isinstance(parameter, (numbers.Integral,
                                  gs_enums.RasterCombinationType,
                                  gs_enums.RasterResolutionType,
                                  gs_enums.RasterNullValueType,
                                  gs_enums.RasterInterpolationType,
                                  gs_enums.ReductionType,
                                  gs_enums.RasterDebug,
                                  gs_enums.RasterSortType)):
        raise TypeError("parameter should be int/ gs_enums")
    if isinstance(parameter, numbers.Integral):
        # assign raw parameter
        _parameter = parameter
    else:
        # assign value from enum.Enum
        _parameter = parameter.value

    # Run script for list of rasters
    if isinstance(inputRasters, list):
        # Ensure list has entries
        if not len(inputRasters) > 0:
            raise RuntimeError(
                "length of inputRasters should be greater than 0")

        # Ensure list entires are Rasters or DataFileHandlers
        for i, item in enumerate(inputRasters, 0):
            if not isinstance(item, (raster.Raster, raster.RasterFile, raster.RasterBase)):
                raise TypeError(
                    "item at %d in inputRasters is not of Raster/RasterFile type" % i)

        # Set base type to first raster type
        base_type = inputRasters[0].base_type

        # Check all raster types are the same as the base type
        for i, item in enumerate(inputRasters, 0):
            if item.base_type != base_type:
                raise TypeError(f"Basetype of input raster at {i} is different." +
                                " All the raster in list should be of same basetype")

        # Create vector of raster bases
        vec = raster.RasterBaseList(dtype=base_type)
        for item in inputRasters:
            vec.append(item)

        if output_type is None or parameter == gs_enums.RasterDebug.Enable:
            # Create script function based on types
            if base_type == np.float32:
                run_script_function = RasterScript_f.run_script_noout
            elif base_type == np.float64:
                run_script_function = RasterScript_d._run_script_noout

            # Run script
            run_script_function(_script, vec._handle, _parameter)
            del vec
            # Return first raster
            return inputRasters[0]
        else:
            # Check for valid types
            if output_type not in [np.uint8, np.uint32, np.float32, np.float64]:
                raise ValueError(
                    "Output type should np.float32/np.float64/np.uint32")

            # Create script function based on types
            if base_type == np.float32:
                if output_type == np.float32:
                    run_script_function = RasterScript_f.run_script
                elif output_type == np.uint32:
                    run_script_function = RasterScript_f.run_script_i
                elif output_type == np.uint8:
                    run_script_function = RasterScript_f.run_script_byt
            elif base_type == np.float64:
                if output_type == np.float64:
                    run_script_function = RasterScript_d.run_script
                elif output_type == np.uint32:
                    run_script_function = RasterScript_d.run_script_i
                elif output_type == np.uint8:
                    run_script_function = RasterScript_d.run_script_byt

            # Run script
            try:
                _out = run_script_function(_script, vec._handle, _parameter)
            except Exception as e:
                print(_script)
                raise e

            # Convert from Cython to Python Raster
            out = raster.Raster.copy("output", _out)
            del vec

            # Return output raster
            return out

    # Run script for list of raster bases
    elif isinstance(inputRasters, raster.RasterBaseList):
        if output_type is None:
            # Create script function based on types
            if inputRasters._dtype == np.float32:
                run_script_function = RasterScript_f.run_script_noout
            elif inputRasters._dtype == np.float64:
                run_script_function = RasterScript_d.run_script_noout

            # Run script
            run_script_function(_script, inputRasters._handle, _parameter)
        else:
            # Create script function based on types
            if inputRasters._dtype == np.float32:
                if output_type == np.uint32:
                    run_script_function = RasterScript_f.run_script_i
                elif output_type == np.uint8:
                    run_script_function = RasterScript_f.run_script_byt
                else:
                    run_script_function = RasterScript_f.run_script
            elif inputRasters._dtype == np.float64:
                if output_type == np.uint32:
                    run_script_function = RasterScript_d.run_script_i
                elif output_type == np.uint8:
                    run_script_function = RasterScript_d.run_script_byt
                else:
                    run_script_function = RasterScript_d.run_script

            # Run script
            _out = run_script_function(
                _script, inputRasters._handle, _parameter)

            # Convert from Cython to Python Raster
            out = raster.Raster.copy("output", _out)
            del inputRasters

            # Return output raster
            return out

    else:

        # Throw exception if input is not a valid list
        raise TypeError("inputRasters should be of type list")


def runAreaScript(script: str, inputRaster: Union['raster.Raster',
                                                  'raster.RasterFile',
                                                  "raster.RasterBase"],
                  width: numbers.Integral = 1,
                  output_type=core.REAL) -> 'raster.Raster':
    '''Run areascript on an input raster over GPU.

    Parameters
    ----------
    script : str
        Script to build kernel for running on GPU.
    inputRasters : Raster/DataFileHandler
        An input raster.RasterFile object
    width : integer
        The width of the area window in cells, default 1
    output_type : np.float32/np.float64/np.uint32
        Data type for the output raster object from runScript

    Returns
    -------
    out : Raster object
        Raster output from the runScript

    Examples
    --------
    >>> from geostack import raster
    >>> script = """// Average
    ... if (isValid_REAL(testRasterA)) {
    ... output += testRasterA;
    ... sum++;
    ... };
    ... """
    >>> testRasterA = Raster(name="testRasterA", base_type=np.float32,
    ... data_type=np.float32)
    >>> testRasterA.init(21, 1.0, ny=21, hy=1.0)
    >>> testRasterA.setAllCellValues(0.0)
    >>> testRasterA.setCellValue(99.9, 10, 10)
    >>> out = runAreaScript(script, testRasterA, 3)
    '''

    # Check for valid types
    if output_type is None:
        raise ValueError("Output type should be provided")
    if output_type not in [np.uint32, np.float32, np.float64]:
        raise ValueError("Output type should np.float32/np.float64/np.uint32")

    # Check script and encode as necessary
    if isinstance(script, (str, bytes)):
        _script = core.str2bytes(script)
    else:
        raise TypeError("script can be only string or bytes")

    if isinstance(width, numbers.Integral):
        _width = width
    else:
        raise TypeError("width should be integer")

    # Run script for list of rasters
    if isinstance(inputRaster, (raster.Raster, raster.RasterFile, raster.RasterBase)):
        # Set base type
        base_type = inputRaster.base_type

        # Check base type
        if base_type == np.float32:

            # Create script function based on types
            if output_type == np.float32:
                run_script_function = RasterScript_f.run_areascript
            elif output_type == np.uint32:
                run_script_function = RasterScript_f.run_areascript_i
            elif output_type == np.uint8:
                run_script_function = RasterScript_f.run_areascript_byt
            # Run script
            if isinstance(inputRaster, (raster.Raster, raster.RasterBase)):
                _out = run_script_function(
                    _script, inputRaster._handle, _width)
            elif isinstance(inputRaster, raster.RasterFile):
                _out = run_script_function(
                    _script, inputRaster._handle.cy_raster_obj, _width)

        elif base_type == np.float64:
            # Create script function based on types
            if output_type == np.float64:
                run_script_function = RasterScript_d.run_areascript
            elif output_type == np.uint32:
                run_script_function = RasterScript_d.run_areascript_i
            elif output_type == np.uint8:
                run_script_function = RasterScript_d.run_areascript_byt

            # Run script
            if isinstance(inputRaster, (raster.Raster, raster.RasterBase)):
                _out = run_script_function(
                    _script, inputRaster._handle, _width)
            elif isinstance(inputRaster, raster.RasterFile):
                _out = run_script_function(
                    _script, inputRaster._handle.cy_raster_obj, _width)

    # Convert from Cython to Python Raster
    out = raster.Raster.copy("output", _out)
    del _out

    # Return output raster
    return out


def runVectorScript(script: str,
                    inputVector: "vector.Vector",
                    inputRasters: Optional[List[Union['raster.Raster',
                                                      'raster.RasterFile',
                                                      'raster.RasterBase']]] = None,
                    reductionType: "gs_enums.ReductionType" = 0,
                    parameter: Union[numbers.Integral,
                                     gs_enums.VectorOrdering,
                                     gs_enums.VectorLayerHandling,
                                     gs_enums.VectorIndexingOptions] = 0,
                    output_type: Optional[np.dtype] = None) -> "vector.Vector":
    '''Run script on a Vector and a list of input rasters.

    Parameters
    ----------
    script : str
        Script to build kernel for running on GPU.
    inputVector: Vector
        a vector object
    inputRasters : Optional, list/tuple/RasterBaseList/RasterPtrList, default is None
        A list of input rasters
    reductionType : gs_enums.ReductionType
        parameter for reduction operation on the input raster, default 0
    parameter : Union[numbers.Integral,
                      gs_enums.VectorOrdering,
                      gs_enums.VectorLayerHandling,
                      gs_enums.VectorIndexingOptions]

        parameter for controlling script processing, default 0
    output_type : None

    Returns
    -------
    out : Vector object
        a modified instance of vector object

    Examples
    --------
    >>> from geostack.raster import Raster
    >>> from geostack.vector import Vector
    >>> from geostack.utils import get_epsg
    >>> from geostack.runner import runVectorScript, runScript
    >>> from geostack.gs_enums import ReductionType
    >>> # create a raster
    >>> r = Raster(name="r")
    >>> r.init(10, 1.0, ny=10, hy=1.0, ox=-5.0, oy=-5.0)
    >>> r.setProjectionParameters(get_epsg(4326))
    >>> # fill raster values by running a script
    >>> runScript("r = hypot((REAL)x, (REAL)y);", [r])
    >>> r.getCellValue(9,1)
    5.7008771896362305
    >>> # get the cell centers
    >>> v = r.cellCentres()
    >>> v.setProperty(0, "vx", 0.0)
    >>> v.setProperty(0, "vy", 0.0)
    >>> # run vector script
    >>> v = runVectorScript("REALVEC2 g = grad(r); vx = g.x; vy = g.y;", v, [r], ReductionType.Mean)
    >>> # get properties for point index 11
    >>> v.getProperty(11, 'vx', float), v.getProperty(11, 'vy', float)
    (-0.703481912612915, 0.703481912612915)
    '''

    # Check script and encode as necessary
    if isinstance(script, (str, bytes)):
        _script = core.str2bytes(script)
    else:
        raise TypeError("script can be only string or bytes")

    # check reductionType
    if not isinstance(reductionType, (numbers.Integral,
                                      gs_enums.ReductionType)):
        raise TypeError("reductionType should be int/ gs_enums.ReductionType")
    if isinstance(reductionType, numbers.Integral):
        # assign raw reduction type
        _reduction_type = reductionType
    else:
        # assign value from enum.Enum
        _reduction_type = reductionType.value

    # check parameter
    if not isinstance(parameter, (numbers.Integral,
                                  gs_enums.VectorOrdering,
                                  gs_enums.VectorLayerHandling,
                                  gs_enums.VectorIndexingOptions)):
        raise TypeError("parameter should be int/ gs_enums")
    if isinstance(parameter, numbers.Integral):
        # assign raw parameter
        _parameter = parameter
    else:
        # assign value from enum.Enum
        _parameter = parameter.value

    if isinstance(inputVector, vector.Vector):
        # python wrapper
        _input_vector = inputVector._handle
        # Set base type to first raster type
        base_type = inputVector._dtype
    elif isinstance(inputVector, (_cy_vector._Vector_d, _cy_vector._Vector_f)):
        # cython wrapper
        _input_vector = inputVector
        if isinstance(inputVector, _cy_vector._Vector_f):
            base_type = np.float32
        elif isinstance(inputVector, _cy_vector._Vector_f):
            base_type = np.float64

    if not inputRasters:
        # when no raster is specified
        if base_type == np.float32:
            run_script_function = _input_vector.runScript
        elif base_type == np.float64:
            run_script_function = _input_vector.runScript
    else:
        # when a raster is specified (call c++ runVectorScript method)
        if base_type == np.float32:
            run_script_function = VectorScript_f.run_script_noout
        elif base_type == np.float64:
            run_script_function = VectorScript_d.run_script_noout

    # Run script for list of rasters
    if isinstance(inputRasters, list):
        # Ensure list has entries
        if not len(inputRasters) > 0:
            raise RuntimeError(
                "length of inputRasters should be greater than 0")

        # Ensure list entires are Rasters or DataFileHandlers
        for i, item in enumerate(inputRasters, 0):
            if not isinstance(item, (raster.Raster, raster.RasterFile, raster.RasterBase)):
                raise TypeError(
                    f"item at {i} in inputRasters is not of Raster/RasterFile type")

        # Check all raster types are the same as the base type
        for i, item in enumerate(inputRasters, 0):
            if item.base_type != base_type:
                raise TypeError(f"Basetype of input raster at {i} is different." +
                                " All the raster in list should be of same basetype")
        # Create vector of raster bases
        raster_list = raster.RasterBaseList(dtype=base_type)
        for item in inputRasters:
            raster_list.append(item)
    # Run script for list of raster bases
    elif isinstance(inputRasters, raster.RasterBaseList):
        raster_list = inputRasters
    elif not inputRasters:
        raster_list = None

    if not output_type:
        if not raster_list:
            # Run script with no raster input
            run_script_function(_script)
        else:
            # Run script with raster input
            run_script_function(_script,
                                _input_vector,
                                raster_list._handle,
                                _reduction_type,
                                _parameter)

        return inputVector
    else:
        raise NotImplementedError("")


def stipple(script: str, inputRasters: Union[List[Union['raster.Raster',
                                                        'raster.RasterFile',
                                                        "raster.RasterBase"]],
                                             Tuple[Union['raster.Raster',
                                                         'raster.RasterFile',
                                                         "raster.RasterBase"]],
                                             "raster.RasterBaseList"],
            fields: List[str] = [],
            nPerCell: numbers.Integral = 1,
            output_type=core.REAL) -> "vector.Vector":
    '''Create Vector object from stippling on a list of input raster over GPU.

    Parameters
    ----------
    script : str
        Script to build kernel for running on GPU.
    inputRasters : list/tuple/RasterBaseList/RasterPtrList
        A list of input rasters
    fields: list[str]
        A list of strings
    nPerCell : numbers.Integral
        parameter for controlling script processing, default 0
    output_type : core.REAL/np.float64/np.uint32
        Data type for the output raster object from runScript

    Returns
    -------
    out : Vector object
        Vector object obtained from stippling on a list of rasters

    Examples
    --------
    >>> out = stipple("create = true;", [testRasterA])
    '''

    # Check script and encode as necessary
    if isinstance(script, (str, bytes)):
        _script = core.str2bytes(script)
    else:
        raise TypeError("script can be only string or bytes")

    # create a list of bytes for fields
    if not isinstance(fields, list):
        raise TypeError("fields should be a list")
    _fields = []
    if len(fields) > 0:
        for item in fields:
            if not isinstance(item, (bytes, str)):
                raise TypeError(f"field {item} should be of type bytes/ str")
            _fields.append(core.str2bytes(item))

    # Run script for list of rasters
    if isinstance(inputRasters, list):
        # Ensure list has entries
        if not len(inputRasters) > 0:
            raise RuntimeError(
                "length of inputRasters should be greater than 0")

        # Ensure list entires are Rasters or DataFileHandlers
        for i, item in enumerate(inputRasters, 0):
            if not isinstance(item, (raster.Raster, raster.RasterFile, raster.RasterBase)):
                raise TypeError(
                    "item at %d in inputRasters is not of Raster/RasterFile type" % i)

        # Set base type to first raster type
        base_type = inputRasters[0].base_type

        # Check all raster types are the same as the base type
        for i, item in enumerate(inputRasters, 0):
            if item.base_type != base_type:
                raise TypeError(f"Basetype of input raster at {i} is different." +
                                " All the raster in list should be of same basetype")

        # Create vector of raster bases
        vec = raster.RasterBaseList(dtype=base_type)
        for item in inputRasters:
            vec.append(item)

        if base_type == output_type == np.float32:
            stipple_function = RasterScript_f._stipple
        elif base_type == output_type == np.float64:
            stipple_function = RasterScript_d._stipple
        else:
            raise ValueError(
                "Mismatch between raster base type and output type")

        # Run script
        _out = stipple_function(_script, vec._handle, _fields, nPerCell)

        # Convert from Cython to Python Raster
        out = vector.Vector._from_vector(_out)
        #del _out, vec

    # Run script for list of raster bases
    elif isinstance(inputRasters, raster.RasterBaseList):

        if inputRasters._dtype == output_type == np.float32:
            stipple_function = RasterScript_f._stipple
        elif inputRasters._dtype == output_type == np.float64:
            stipple_function = RasterScript_d._stipple
        else:
            raise ValueError(
                "Mismatch between raster base type and output type")

        # Run script
        _out = stipple_function(
            _script, inputRasters._handle, _fields, nPerCell)

        # Convert from Cython to Python Raster
        out = vector.Vector._from_vector(_out)
        #del _out

    # Return output vector
    return out
