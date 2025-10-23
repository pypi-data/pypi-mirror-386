# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import os.path as pth
import warnings
import numbers
from typing import Tuple, Union, Optional
from itertools import product
import numpy as np

from ..dataset.supported_libs import HAS_GDAL, HAS_XARRAY, HAS_DASK  # type: ignore
from ..dataset.supported_libs import RequireLib
from ..dataset.dataset import gdal_dtype_to_numpy, numpy_to_gdal_dtype

if HAS_GDAL:
    from osgeo import gdal, gdalconst
    os.environ['GDAL_CACHEMAX'] = "100"

if HAS_XARRAY:
    import xarray as xr

if HAS_DASK:
    import dask
    import dask.array as da_arr

from ..raster import raster
from .. import readers
from .netcdfWriter import proj4_to_wkt

__all__ = ["create_output_file_gdal",
           "write_data_to_gdal_buffer",
           "writeRaster", "to_xarray", "to_zarr"]


def create_grid_from_corner(ulx: numbers.Real, uly: numbers.Real,
                            delx: numbers.Real, dely: numbers.Real,
                            nx: numbers.Integral, ny: numbers.Integral) -> Tuple:
    '''
    generate grid for the raster using the values of the corners
    '''
    xcoords = np.linspace(0, nx, nx + 1) * delx + ulx
    ycoords = np.linspace(0, ny, ny + 1) * dely + uly
    return xcoords, ycoords


def grid_vertices_to_centers(lonInp: np.ndarray, latInp: np.ndarray) -> Tuple:
    '''
    convert grid vertices to an array of corners of cells
    '''
    if lonInp.ndim == 1 and latInp.ndim == 1:
        lon_centers = (lonInp[1:] + lonInp[:-1]) * 0.5
        lat_centers = (latInp[1:] + latInp[:-1]) * 0.5
        return lon_centers, lat_centers
    else:
        raise TypeError("only 1D numpy array should be used")


@RequireLib("gdal")
def create_output_file_gdal(file_path: str,
                            inputRaster: Union["raster.Raster", 'raster.RasterFile'],
                            bands_count: numbers.Integral = 1,
                            compress: bool = True,
                            out_driver: str = "GTiff",
                            missing_value: Optional[numbers.Real] = None,
                            force: bool = False,
                            dtype: Optional[np.dtype] = None):
    """Create output file for GDAL IO using inputRaster.
    """
    if not isinstance(inputRaster, (raster.Raster, raster.RasterFile)):
        raise TypeError("input raster should be an instance of Raster")

    if not isinstance(file_path, str):
        raise TypeError(
            "Path of output file 'file_path' should be of string type")

    if pth.exists(file_path):
        if not force:
            raise FileExistsError(
                f"file {file_path} exist, choose different name")
        else:
            os.remove(file_path)

    _file_dir = pth.dirname(file_path).strip()
    if len(_file_dir) > 0:
        if not pth.isdir(_file_dir):
            raise NotADirectoryError(f"Path {_file_dir} is invalid")

    _, file_ext = pth.splitext(file_path)

    if 'tif' in file_ext.lower():
        _out_driver = "GTiff"
    else:
        _out_driver = out_driver

    raster_dimensions = inputRaster.getDimensions()
    raster_projection = inputRaster.getProjectionParameters()
    nx = raster_dimensions.nx
    ny = raster_dimensions.ny

    if dtype is None:
        out_type = numpy_to_gdal_dtype(inputRaster.data_type)
    else:
        out_type = numpy_to_gdal_dtype(dtype)

    out_geotransform = readers.rasterReaders.get_gdal_geotransform(
        raster_dimensions)
    nbands = max(1, bands_count)

    if out_driver == "GTiff":
        create_options = ["TILED=YES"]
        if compress:
            create_options.append("COMPRESS=DEFLATE")
    else:
        create_options = []

    driver = gdal.GetDriverByName(_out_driver)
    metadata = driver.GetMetadata()
    if not metadata.get(gdal.DCAP_CREATE) == "YES":
        # driver = gdal.GetDriverByName("GTiff")
        # file_path = pth.splitext(file_path)[0] + '.tif'
        driver = gdal.GetDriverByName("MEM")
        file_path = ""

    if driver is not None:
        if compress:
            out_file = driver.Create(file_path, xsize=nx,
                                     ysize=ny, bands=nbands,
                                     eType=out_type,
                                     options=create_options)
        else:
            out_file = driver.Create(file_path, xsize=nx,
                                     ysize=ny, bands=nbands,
                                     eType=out_type,
                                     options=create_options)
    else:
        raise ValueError(f"Driver {_out_driver} is not a valid gdal driver")

    out_file.SetGeoTransform(out_geotransform)
    wkt_string = proj4_to_wkt(raster_projection.to_proj4(), pretty=False)
    if wkt_string:
        out_file.SetProjection(wkt_string)

    return out_file


def write_tile(tile_index_x: int, tile_index_y: int,
               inputRaster: Union['raster.Raster', 'raster.RasterFile'],
               missing_value: numbers.Real,
               raster_dims: 'raster.RasterDimensions',
               invert_y: bool,
               out_band: 'gdal.Band',
               out_type: np.dtype,
               band_idx: Optional[int] = None):

    tile_index = tile_index_y + tile_index_x * inputRaster.dimensions.tx
    idx_s, idx_e, jdx_s, jdx_e = inputRaster.get_tile_idx_bounds(tile_index)

    try:
        out_data = inputRaster.writeData(tile_index_x, tile_index_y)
    except AttributeError as e:
        out_data = inputRaster.getData(tile_index_x, tile_index_y)

    tile_ny = jdx_e - jdx_s
    tile_nx = idx_e - idx_s

    if band_idx is None or out_data.ndim == 2:
        data_slice = (slice(None, tile_ny), slice(None, tile_nx),)
    else:
        data_slice = (band_idx, slice(None, tile_ny), slice(None, tile_nx),)

    if missing_value is not None:
        out_data = np.where(out_data == inputRaster.nullValue,
                            missing_value, out_data)
    if invert_y:
        out_band.WriteArray(out_data[data_slice][::-1, :].astype(out_type),
                            xoff=idx_s, yoff=raster_dims.ny - jdx_e)
    else:
        out_band.WriteArray(out_data[data_slice][:, :].astype(out_type),
                            xoff=idx_s, yoff=raster_dims.ny - jdx_e)


@RequireLib("gdal")
def write_data_to_gdal_buffer(fileHandle,
                              inputRaster: Union["raster.Raster", 'raster.RasterFile'],
                              raster_band: numbers.Integral = 1,
                              invert_y: bool = True,
                              missing_value: Optional[numbers.Real] = None,
                              dtype: Optional[np.dtype] = None):
    """Write raster data from inputRaster to fileHandle.
    """
    if not isinstance(inputRaster, (raster.Raster, raster.RasterFile)):
        raise TypeError("input raster should be an instance of Raster")
    if not isinstance(fileHandle, (gdal.Dataset, str)):
        raise TypeError(
            "fileHandle should an instance of gdal.Dataset or file name")

    if raster_band > fileHandle.RasterCount:
        raise ValueError("raster band is more than available bands in file")
    if raster_band == 0:
        raise ValueError("raster band should be greater than 0")

    raster_dims = inputRaster.getDimensions()
    num_tiles = raster_dims.tx * raster_dims.ty
    if dtype is None:
        out_type = inputRaster.data_type
    else:
        out_type = dtype

    # set missing value for a raster band
    if missing_value is not None:
        _missing_value = missing_value
    else:
        _missing_value = inputRaster.nullValue

    for j in range(raster_band):
        out_band = fileHandle.GetRasterBand(j + 1)
        for tx, ty in product(range(raster_dims.tx), range(raster_dims.ty)):
            write_tile(tx, ty, inputRaster, missing_value, raster_dims,
                       invert_y, out_band, out_type, band_idx=j)
        out_band.SetNoDataValue(_missing_value)
        out_band.FlushCache()


@RequireLib("gdal")
def writeRaster(out_file_name: str,
                inputRaster: Union["raster.Raster", 'raster.RasterFile'],
                bands_count: numbers.Integral = 1,
                compress: bool = True,
                build_overview: bool = False,
                missing_value: Optional[numbers.Real] = None,
                out_driver: str = "GTiff",
                force: bool = False,
                invert_y: bool = True,
                dtype: Optional[np.dtype] = None):
    '''
    write output raster using the structure of the input satellite image with the
    number of bands specified using num_bands
    '''

    if not HAS_GDAL:
        raise RuntimeError(
            "GDAL is not installed in current python environment")

    if build_overview:
        gdal.SetConfigOption('TIFF_USE_OVR', 'YES')

    out_file_handle = create_output_file_gdal(out_file_name,
                                              inputRaster,
                                              bands_count=bands_count,
                                              compress=compress,
                                              out_driver=out_driver,
                                              missing_value=missing_value,
                                              force=force,
                                              dtype=dtype)

    write_data_to_gdal_buffer(out_file_handle,
                              inputRaster,
                              raster_band=bands_count,
                              invert_y=invert_y,
                              missing_value=missing_value,
                              dtype=dtype)

    driver = gdal.GetDriverByName(out_driver)
    metadata = driver.GetMetadata()
    if not metadata.get(gdal.DCAP_CREATE) == "YES":
        # make a copy from the MEM raster
        driver.CreateCopy(out_file_name, out_file_handle, strict=0)

        del out_file_handle, driver
    else:
        out_file_handle = None
        del out_file_handle


@RequireLib("xarray")
def to_xarray(inputRaster: Union['raster.Raster', 'raster.RasterFile'], **kwargs):
    """Convert geostack raster to Xarray DataArray

    Parameters
    ----------
    inputRaster : raster.Raster
        input raster object
    name : str, Optional
        name of the xarray DataArray, default inputRaster.name
    chunks: str/tuple, Optional
        chunks for dask chunks, use when dask is installed
        default, (tileSize, tileSize)

    Returns
    -------
    xr.DataArray
        a xarray DataArray
    """
    dims = inputRaster.dimensions
    if inputRaster.ndim >= 1:
        x = np.arange(dims.ox, dims.ex, dims.hx)
        xr_dims = ['x']
        coords = {"x": (['x'], x)}
    if inputRaster.ndim >= 2:
        y = np.arange(dims.oy, dims.ey, dims.hy)
        xr_dims.append("y")
        coords["y"] = (['y'], x)
    if inputRaster.ndim == 3:
        layers = np.arange(dims.oz, dims.ez, dims.hz)
        xr_dims.append("layers")
        coords['layers'] = (['layers'], layers)

    attrs = {}
    if inputRaster.hasVariables():
        for item in inputRaster.getVariablesIndexes():
            attrs[item] = inputRaster.getVariableData(item)

    if HAS_DASK:
        tx = ty = raster.TileSpecifications().tileSize
        chunks = kwargs.get("chunks")
        if chunks is None or chunks == "auto":
            chunks = (ty, tx)
        raster_name = inputRaster.name if inputRaster.name != "" else None
        inp_dataset = da_arr.from_array(inputRaster.data,
                                        name=raster_name,
                                        chunks=chunks,
                                        asarray=False)
    else:
        inp_dataset = inputRaster.data

    da = xr.DataArray(data=inp_dataset, name=kwargs.get("name", inputRaster.name),
                      dims=xr_dims, coords=coords, attrs=attrs,)
    return da

@RequireLib("zarr")
@RequireLib("xarray")
def to_zarr(inp_raster: Union['raster.Raster', 'raster.RasterFile'],
            zarr_path: Optional[str] = None) -> str:
    """write a Raster/ RasterFile to zarr store

    Parameters
    ----------
    inp_raster : Union[Raster, RasterFile]
        an instance of Raster/RasterFile object
    zarr_path : Optional[str]
        path to write zarr object

    Returns
    -------
    zarr_path: str
        path where zarr object was stored
    """
    da = to_xarray(inp_raster)
    ds = da.to_dataset()
    if zarr_path is None:
        zarr_path = f'{inp_raster.name}.zarr'
    zrr = ds.to_zarr(zarr_path, mode='w')
    zrr.set_attributes(
        {'proj4': inp_raster.getProjectionParameters().to_proj4()})
    zrr.close()
    return zarr_path
