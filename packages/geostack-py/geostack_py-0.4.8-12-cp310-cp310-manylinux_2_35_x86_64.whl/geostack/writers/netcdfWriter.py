# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import numbers
import logging
import numpy as np
from ..dataset import supported_libs
from .. import core
from .. import raster
from ..utils import proj4_to_wkt
from typing import Dict, Union, Optional
from pathlib import Path

if supported_libs.HAS_NCDF:
    import netCDF4 as nc

logger = logging.getLogger("geostack")

__all__ = ["write_to_netcdf", "get_netcdf_crs"]


def get_netcdf_crs(projection_params: "core.ProjectionParameters") -> Dict:
    """convert ProjectionParameters to NC Conventions crs variables

    Parameters
    ----------
    projection_params : ProjectionParameters
        an instance of projection parameters object

    Returns
    -------
    dict
        a dictionary with attributes for crs variable

    Raises
    ------
    ValueError
        "projection_params should be an instance of Projection Parameters"
    """
    if not isinstance(projection_params, core.ProjectionParameters):
        raise ValueError(
            "projection_params should be an instance of Projection Parameters")
    out = {}
    if projection_params.type == 1:
        if projection_params.cttype == 1:
            out["grid_mapping_name"] = "transverse_mercator"
            out['scale_factor_at_central_meridian'] = projection_params.k0
            out['latitude_of_projection_origin'] = projection_params.phi_0
            out['semi_major_axis'] = projection_params.a
        elif projection_params.cttype == 7:
            out["grid_mapping_name"] = "mercator"
            out['standard_parallel'] = projection_params.phi_1
        elif projection_params.cttype == 8:
            out["grid_mapping_name"] = "lambert_conformal_cubic"
            out['standard_parallel_1'] = projection_params.phi_1
            out['standard_parallel_2'] = projection_params.phi_2
            out['latitude_of_projection_origin'] = projection_params.phi_0
        elif projection_params.cttype == 11:
            out["grid_mapping_name"] = "albers_conical_equal_area"
            out['standard_parallel_1'] = projection_params.phi_1
            out['standard_parallel_2'] = projection_params.phi_2
            out['latitude_of_projection_origin'] = projection_params.phi_0
        out['longitude_of_central_meridian'] = projection_params.x0
        out['false_easting'] = projection_params.fe
        out['false_northing'] = projection_params.fn
        out['unit'] = "metre"
    elif projection_params.type == 2:
        out["grid_mapping_name"] = "latitude_longitude"
        out['latitude_of_prime_meridian'] = 0.0
        out['semi_major_axis'] = projection_params.a
    if projection_params.f != 0.0:
        out['inverse_flattening'] = 1.0 / projection_params.f
    else:
        out['inverse_flattening'] = projection_params.f
    if supported_libs.HAS_GDAL:
        out['crs_wkt'] = proj4_to_wkt(projection_params.to_proj4())
        if not out['crs_wkt']:
            out.pop("crs_wkt")
    return out


@supported_libs.RequireLib("netcdf")
def write_to_netcdf(inp_raster: Union['raster.Raster', 'raster.RasterFile'],
                    out_file_name: str,
                    group: Optional[str] = None,
                    mode: str = 'w',
                    missing_value: Optional[numbers.Real] = None,
                    data_model: str = "NETCDF4"):
    """write a raster object to a netcdf file

    Parameters
    ----------
    inp_raster : Union[raster.Raster, raster.RasterFile]
        a Raster/ RasterFile object
    out_file_name : str
        name and path of netcdf file
    group : str, optional
        name of group in netcdf file, by default None
    mode : str, optional
        access mode for netcdf file, by default 'w'

        w means write; a new file is created,
        an existing file with the same name is deleted.
        a and r+ mean append
    missing_value : numbers.Real, optional
        a missing value for netcdf variable, by default None
    data_model : str, optional
        data_model describes the netCDF data model version, by default "NETCDF4"

    Examples
    --------
    >>> import json
    >>> from geostack.utils import get_epsg
    >>> from geostack.vector import Vector

    >>> map_geojson = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[144.76,-37.9],[147.6,-37.9],[147.6,-36.3],[144.8,-36.3],[144.8,-37.9]]]}}]}

    >>> vec = Vector.from_geojson(json.dumps(map_geojson))
    >>> raster = vec.mapDistance(0.1)
    >>> netcdf_writer.write_to_netcdf(raster, "test2.nc", group="cyl", mode='w')

    >>> vec_p = vec.convert(get_epsg(28355))
    >>> raster_p = vec_p.mapDistance(112.9 * 100)
    >>> netcdf_writer.write_to_netcdf(raster_p, "test2.nc", group="tm", mode='r+')
    """

    logger.debug(f"Working on {inp_raster.name}")

    if not isinstance(inp_raster, (raster.Raster, raster.RasterFile)):
        raise TypeError("input raster should be an instance Raster/RasterFile")
    # create coordinates
    x_dim = np.linspace(inp_raster.dimensions.ox,
                        inp_raster.dimensions.ex,
                        inp_raster.dimensions.nx + 1)
    x_dim = 0.5 * (x_dim[1:] + x_dim[:-1])
    if inp_raster.ndim > 1:
        y_dim = np.linspace(inp_raster.dimensions.oy,
                            inp_raster.dimensions.ey,
                            inp_raster.dimensions.ny + 1)
        y_dim = 0.5 * (y_dim[1:] + y_dim[:-1])
    if inp_raster.ndim > 2:
        z_dim = np.linspace(inp_raster.dimensions.oz,
                            inp_raster.dimensions.ez,
                            inp_raster.dimensions.nz + 1)
        z_dim = 0.5 * (z_dim[1:] + z_dim[:-1])

    if mode not in ["w", "r+", "a"]:
        raise ValueError(f"invalid mode '{mode}' for netcdf writer")

    raster_projection = inp_raster.getProjectionParameters()
    nc_crs = get_netcdf_crs(raster_projection)
    if raster_projection.type == 1:
        xdim_name = "x"
        ydim_name = "y"
    elif raster_projection.type == 2:
        xdim_name = "longitude"
        ydim_name = "latitude"

    # open netcdf file
    if mode == "w":
        out_file = nc.Dataset(out_file_name, mode=mode, data_model=data_model)
    else:
        if not Path(out_file_name).is_file():
            raise FileNotFoundError(f"File {out_file_name} is not valid")

        out_file = nc.Dataset(out_file_name, mode=mode)

    var_handle = {}

    if mode == 'w':
        # create dimensions when writing file
        if group is None:
            # when groups are not used
            out_file.createDimension(xdim_name, size=x_dim.size)
            var_handle['x'] = out_file.createVariable(xdim_name, inp_raster.base_type,
                                                      dimensions=(xdim_name,),
                                                      zlib=True)
            if inp_raster.ndim > 1:
                out_file.createDimension(ydim_name, size=y_dim.size)
                var_handle['y'] = out_file.createVariable(ydim_name, inp_raster.base_type,
                                                          dimensions=(
                                                              ydim_name,),
                                                          zlib=True)
            if inp_raster.ndim > 2:
                out_file.createDimension("height", size=z_dim.size)
                var_handle['z'] = out_file.createVariable("height", inp_raster.base_type,
                                                          dimensions=(
                                                              "height",),
                                                          zlib=True)
        else:
            # when groups are used
            out_grp = out_file.createGroup(group)
            out_grp.createDimension(xdim_name, size=x_dim.size)
            var_handle['x'] = out_grp.createVariable(xdim_name, inp_raster.base_type,
                                                     dimensions=(xdim_name,),
                                                     zlib=True)
            if inp_raster.ndim > 1:
                out_grp.createDimension(ydim_name, size=y_dim.size)
                var_handle['y'] = out_grp.createVariable(ydim_name, inp_raster.base_type,
                                                         dimensions=(
                                                             ydim_name,),
                                                         zlib=True)
            if inp_raster.ndim > 2:
                out_grp.createDimension("height", size=z_dim.size)
                var_handle['z'] = out_grp.createVariable("height", inp_raster.base_type,
                                                         dimensions=(
                                                             "height",),
                                                         zlib=True)
    else:
        # when appending or updating an existing file
        if group is None:
            # when groups are not used
            if xdim_name not in out_file.dimensions:
                raise RuntimeError(
                    f"dimension '{xdim_name}' not in file {out_file_name}")
            if inp_raster.ndim > 1:
                if ydim_name not in out_file.dimensions:
                    raise RuntimeError(
                        f"dimension {ydim_name} not in file {out_file_name}")
            if inp_raster.ndim > 2:
                if 'height' not in out_file.dimensions:
                    raise RuntimeError(
                        f"dimension 'height' not in file {out_file_name}")
        else:
            # when groups are used
            if group not in out_file.groups:
                # when group doesn't exist in the file
                out_grp = out_file.createGroup(group)
                out_grp.createDimension(xdim_name, size=x_dim.size)
                var_handle['x'] = out_grp.createVariable(xdim_name, inp_raster.base_type,
                                                         dimensions=(xdim_name,))
                if inp_raster.ndim > 1:
                    out_grp.createDimension(ydim_name, size=y_dim.size)
                    var_handle['y'] = out_grp.createVariable(ydim_name, inp_raster.base_type,
                                                             dimensions=(ydim_name,))
                if inp_raster.ndim > 2:
                    out_grp.createDimension("height", size=z_dim.size)
                    var_handle['z'] = out_grp.createVariable("height", inp_raster.base_type,
                                                             dimensions=("height",))
            else:
                # when group exist in the file
                out_grp = out_file.groups[group]
                if xdim_name not in out_grp.dimensions:
                    raise RuntimeError(
                        f"dimension '{xdim_name}' not in group {group}")
                if inp_raster.ndim > 1:
                    if ydim_name not in out_grp.dimensions:
                        raise RuntimeError(
                            f"dimension '{ydim_name}' not in group {group}")
                if inp_raster.ndim > 2:
                    if 'height' not in out_grp.dimensions:
                        raise RuntimeError(
                            f"dimension 'height' not in group {group}")

    map_dtype = {np.uint32: 'u4',
                 np.uint8: 'u1',
                 np.float32: 'f4',
                 np.float64: 'f8'}

    # handle nullValue (or used defined missing value)
    if not missing_value:
        fill_value = inp_raster.nullValue
    else:
        fill_value = missing_value

    if group is None:
        # create variable when groups are not used
        if inp_raster.name in out_file.variables:
            raise RuntimeError(
                f"variable {inp_raster.name} exist in the file {out_file_name}")
        if inp_raster.ndim == 1:
            var_handle[inp_raster.name] = out_file.createVariable(inp_raster.name,
                                                                  map_dtype[inp_raster.data_type],
                                                                  dimensions=(
                                                                      xdim_name,),
                                                                  fill_value=fill_value,
                                                                  zlib=True,)
        elif inp_raster.ndim == 2:
            var_handle[inp_raster.name] = out_file.createVariable(inp_raster.name,
                                                                  map_dtype[inp_raster.data_type],
                                                                  dimensions=(
                                                                      ydim_name, xdim_name,),
                                                                  fill_value=fill_value,
                                                                  zlib=True)
        elif inp_raster.ndim == 3:
            var_handle[inp_raster.name] = out_file.createVariable(inp_raster.name,
                                                                  map_dtype[inp_raster.data_type],
                                                                  dimensions=(
                                                                      'height', ydim_name, xdim_name,),
                                                                  fill_value=fill_value,
                                                                  zlib=True)
        if 'crs' not in out_file.variables:
            var_handle['crs'] = out_file.createVariable(
                "crs", "i4", dimensions=())
            for item in nc_crs:
                setattr(var_handle['crs'], item, nc_crs.get(item))
        out_file.setncattr('proj4text', raster_projection.to_proj4())
    else:
        # create variable within a group
        if inp_raster.name in out_grp.variables:
            raise RuntimeError(
                f"variable {inp_raster.name} exist in group {group}")
        if inp_raster.ndim == 1:
            var_handle[inp_raster.name] = out_grp.createVariable(inp_raster.name,
                                                                 map_dtype[inp_raster.data_type],
                                                                 dimensions=(
                                                                     xdim_name,),
                                                                 fill_value=fill_value,
                                                                 zlib=True)
        elif inp_raster.ndim == 2:
            var_handle[inp_raster.name] = out_grp.createVariable(inp_raster.name,
                                                                 map_dtype[inp_raster.data_type],
                                                                 dimensions=(
                                                                     ydim_name, xdim_name,),
                                                                 fill_value=fill_value,
                                                                 zlib=True)
        elif inp_raster.ndim == 3:
            var_handle[inp_raster.name] = out_grp.createVariable(inp_raster.name,
                                                                 map_dtype[inp_raster.data_type],
                                                                 dimensions=(
                                                                     'height', ydim_name, xdim_name,),
                                                                 fill_value=fill_value,
                                                                 zlib=True)

        if 'crs' not in out_grp.variables:
            var_handle['crs'] = out_grp.createVariable(
                "crs", "i4", dimensions=())
            for item in nc_crs:
                setattr(var_handle['crs'], item, nc_crs.get(item))
        out_grp.setncattr('proj4text', raster_projection.to_proj4())

    # write data for coordinate variable
    if 'x' in var_handle:
        var_handle['x'][:] = x_dim[:]
        if raster_projection.type == 1:
            setattr(var_handle['x'], "standard_name",
                    "projection_x_coordinate")
            setattr(var_handle['x'], "long_name", "x coordinate of projection")
            setattr(var_handle['x'], "units", "meters")
        elif raster_projection.type == 2:
            setattr(var_handle['x'], "standard_name", "longitude")
            setattr(var_handle['x'], "long_name", "longitude coordinate")
            setattr(var_handle['x'], "units", "degrees_east")
    if 'y' in var_handle:
        var_handle['y'][:] = y_dim[:]
        if raster_projection.type == 1:
            setattr(var_handle['y'], "standard_name",
                    "projection_y_coordinate")
            setattr(var_handle['y'], "long_name", "y coordinate of projection")
            setattr(var_handle['y'], "units", "meters")
        elif raster_projection.type == 2:
            setattr(var_handle['y'], "standard_name", "latitude")
            setattr(var_handle['y'], "long_name", "latitude coordinate")
            setattr(var_handle['y'], "units", "degrees_north")
    if 'z' in var_handle:
        var_handle['z'][:] = z_dim[:]
        setattr(var_handle['z'], "standard_name", "height")
        setattr(var_handle['z'], "long_name", "height above ground")

    # write data for raster
    if inp_raster.ndim > 1:
        num_tiles = inp_raster.dimensions.tx * inp_raster.dimensions.ty
        for i in range(num_tiles):
            idx_s, idx_e, jdx_s, jdx_e = inp_raster.get_tile_idx_bounds(i)
            tile_ny = jdx_e - jdx_s
            tile_nx = idx_e - idx_s
            out_data = inp_raster.get_tile(i)
            # change missing value
            if missing_value:
                out_data[out_data == inp_raster.nullValue] = inp_raster.data_type(
                    fill_value)
                setattr(var_handle[inp_raster.name],
                        "missing_value", fill_value)
            else:
                setattr(var_handle[inp_raster.name],
                        "missing_value", inp_raster.nullValue)
            out_data = np.ma.masked_where(out_data == inp_raster.data_type(fill_value),
                                          out_data)
            # write data to netcdf file
            if inp_raster.ndim == 2:
                var_handle[inp_raster.name][jdx_s:jdx_e,
                                            idx_s:idx_e] = out_data[:tile_ny, :tile_nx]
            elif inp_raster.ndim == 3:
                var_handle[inp_raster.name][:, jdx_s:jdx_e,
                                            idx_s:idx_e] = out_data[:, :tile_ny, :tile_nx]

            if i > 0 and i % 100 == 0:
                out_file.sync()
    else:
        out_data = inp_raster.data
        if missing_value:
            out_data = np.where(
                out_data == inp_raster.nullValue, fill_value, out_data)
            setattr(var_handle[inp_raster.name], "missing_value", fill_value)
        else:
            setattr(var_handle[inp_raster.name],
                    "missing_value", inp_raster.nullValue)
        var_handle[inp_raster.name][:] = out_data[:]
    out_file.close()
