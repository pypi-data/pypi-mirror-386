# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
import os
import math
import uuid
import numbers
import warnings
import os.path as pth
from datetime import datetime
from ftplib import FTP, error_perm
from collections import Counter
import numpy as np
from typing import Tuple, Dict, Union, Optional, List
from tempfile import gettempdir
from pathlib import PurePath

from . import DataHandler
from .. import core
from .timeutils import RasterTime
from ..dataset import supported_libs
from ..raster import raster

if supported_libs.HAS_PYGRIB:
    pygrib, HAS_PYGRIB = supported_libs.import_or_skip("pygrib")
elif supported_libs.HAS_CFGRIB:
    cfgrib, HAS_CFGRIB = supported_libs.import_or_skip("cfgrib")

__all__ = ['GRIB_Handler', 'get_ftp_file']


def get_ftp_file(filepath: Optional[str] = None,
                 ftp_server: Optional[str] = None, user: str = "",
                 passwd: str = "", acct: str = "", dest_path: str = "",
                 temp_file=False, file_stat=None) -> str:
    """FTP file download function.

    Parameters
    ----------
    filepath : str, optional
        path of file to download, by default None
    ftp_server : str, optional
        url for ftp server, by default "ftp.bom.gov.au"
    user: str, optional
        username for the ftp server
    passwd: str, optional
        password for the ftp server
    acct: str, optional
        account to use on the ftp server
    dest_path: str, optional
        destination path on local disk to store the downloaded file
    temp_file: bool, optional
        flag to create a temporary file, default False

    Returns
    -------
    out_path: str
        path of the file created after downloading from the ftp server
    """
    assert ftp_server is not None, "ftp server should not be None"
    if filepath is None or not isinstance(filepath, str):
        raise ValueError("filepath should be provided and be of string type")
    if filepath.startswith("ftp"):
        raise ValueError("filepath should not contain ftp server information")

    try:
        ftp = FTP(ftp_server)
    except Exception as e:
        raise RuntimeError(f"Unable to instantiate ftp {str(e)}")

    try:
        rc = ftp.login(user=user, passwd=passwd, acct=acct)
    except Exception as e:
        raise RuntimeError(f"Unable to login to ftp {str(e)}")

    if not rc.startswith("230"):
        raise RuntimeError(f"Unable to login to {ftp_server} server")

    try:
        rc = ftp.cwd(pth.dirname(filepath))
    except error_perm:
        raise ValueError(
            f"{pth.dirname(filepath)} is not a valid file directory")

    if pth.basename(filepath) in ftp.nlst():
        if temp_file:
            # get file modified time
            timestamp = ftp.voidcmd("MDTM " + pth.basename(filepath))[4:].strip()
            timestamp = datetime.strptime(timestamp, "%Y%m%d%H%M%S")

            is_current = False
            if file_stat is not None:
                is_current = (timestamp.timestamp(), timestamp.timestamp()) == (file_stat.st_atime, file_stat.st_mtime)

            if not is_current:
                out_path = pth.join(gettempdir(), f"{uuid.uuid1()}")
                with open(out_path, 'wb') as outfile:
                    rc = ftp.retrbinary(
                        f"RETR {pth.basename(filepath)}", outfile.write)
                # fix file modified time
                os.utime(out_path, (timestamp.timestamp(), timestamp.timestamp()))
            else:
                out_path = None
        else:
            if dest_path != "":
                out_path = pth.join(dest_path, pth.basename(filepath))
            else:
                out_path = pth.basename(filepath)

            is_current = False
            if file_stat is not None:
                is_current = (timestamp.timestamp(), timestamp.timestamp()) == (file_stat.st_atime, file_stat.st_mtime)

            if not is_current:
                with open(out_path, 'wb') as outfile:
                    # get file modified time
                    timestamp = ftp.voidcmd("MDTM " + pth.basename(filepath))[4:].strip()
                    timestamp = datetime.strptime(timestamp, "%Y%m%d%H%M%S")

                    rc = ftp.retrbinary(
                        f"RETR {pth.basename(filepath)}", outfile.write)
                # fix file modified time
                os.utime(out_path, (timestamp.timestamp(), timestamp.timestamp()))
            else:
                out_path = None
    else:
        raise FileNotFoundError(f"{pth.basename(filepath)} not " +
                                f"in {pth.dirname(filepath)} on {ftp_server}")
    ftp.close()
    return out_path


class GRIB_Handler(DataHandler):
    def __init__(self, fileName: Optional[str] = None, base_type: np.dtype = core.REAL,
                 data_type: np.dtype = core.REAL, variable_map: Optional[Dict] = None,
                 raster_name: str = "", **kwargs):

        self.is_thredds = False
        self.use_pydap = False
        self.invert_y = False
        self.data_type = data_type
        self.base_type = base_type
        self._file_handler = None
        self._time_handler = None
        self._variable_map = {}
        self.raster_name = raster_name
        self._file_info: Optional[Dict] = None

        if variable_map is None:
            raise ValueError("Mapping for grib file should be provided")
        self._variable_map = variable_map

        # check if file is of string type
        if fileName is None or not isinstance(fileName, (str, PurePath)):
            raise TypeError("fileName should be of string type")

        # download file from ftp server
        if fileName.startswith("ftp"):
            if not pth.exists(pth.join(os.getcwd(), pth.basename(fileName))):
                split_path = fileName.replace("ftp://", "").split("/")
                ftp_server = split_path[0]
                ftp_file = '/'.join(split_path[1:])
                get_ftp_file(filepath=ftp_file,
                             ftp_server=ftp_server, **kwargs)
            self._file_name = pth.join(os.getcwd(), split_path[-1])
            self._ftp_file = fileName.replace("ftp://", "")
        else:
            self._file_name = fileName
            self._ftp_file = None

        if not pth.exists(self._file_name):
            raise FileNotFoundError(f"file {self._file_name} is not valid")

        self.nullValue = raster.getNullValue(data_type)

    @staticmethod
    def return_proj4(inp_params: Union[str, Dict]) -> str:
        """function to return proj4 string from the input projection parameters.

        Parameters
        ----------
        inp_params : Union[str, Dict]
            input projection parameters

        Returns
        -------
        str
            a proj4 string
        """
        try:
            import pyproj
            if isinstance(inp_params, dict):
                pj = pyproj.Proj(inp_params).definition_string()
            elif isinstance(inp_params, str):
                pj = pyproj.Proj(init=inp_params).definition_string()
            fix_proj_str = []
            for item in pj.split(" "):
                if item.startswith("+"):
                    fix_proj_str.append(item)
                else:
                    fix_proj_str.append(f"+{item}")
            fix_proj_str = " ".join(fix_proj_str)
            return fix_proj_str
        except ImportError:
            return ""

    @staticmethod
    def proj_start_location(x: float, y: float, proj_str: str) -> Tuple[float]:
        """convert location to projection coordinate system.

        Parameters
        ----------
        x : float
            location of x-coordinate in EPSG:4326
        y : float
            location of y-coordinate in EPSG:4326
        proj_str : str
            proj4 string with projection parameters

        Returns
        -------
        Tuple[float]
            coordinate in projection coordinate system
        """
        try:
            import pyproj
            crs_from = pyproj.CRS("EPSG:4326")
            crs_to = pyproj.CRS(proj_str)
            if hasattr(pyproj, "transform"):
                y, x = pyproj.transform(crs_to, crs_from, x, y)
            elif hasattr(pyproj, "Transformer"):
                y, x = pyproj.Transformer(crs_to, crs_from).transform(x, y)
            return x, y
        except ImportError:
            return x, y

    def is_in_file(self, var_map: Dict) -> bool:
        out = False
        common_keys = lambda s: s.keys() & var_map.keys()
        flags = []

        for var_info in self.file_info['variables']:
            inp_item = dict(map(lambda item: (item, var_map.get(item)), common_keys(var_info)))
            file_item = dict(map(lambda item: (item, var_info.get(item)), common_keys(var_info)))
            flags.append(inp_item == file_item)

        if len(flags) > 0:
            out = any(flags)
        return out

    def read_grib_file(self, tidx: numbers.Integral = 0, varname: Optional[str] = None):
        """function to read the data from grib file

        Parameters
        ----------
        tidx : numbers.Integral, optional
            time index to read the grib message, by default 0
        varname : str, optional
            variable to read the grib message from the grib file, by default None

        Raises
        ------
        RuntimeError
            Grib record is not valid
        RuntimeError
            no grib records found
        IndexError
            grib record index is out of bounds
        RuntimeError
            grib file is closed
        ValueError
            invalid mapping for the grib code
        RuntimeError
            no grib map found
        """
        if self._variable_map:
            key_names = []
            if varname is None:
                for item in self._variable_map:
                    if isinstance(self._variable_map[item], dict):
                        if item in self.data_vars:
                            key_names.append(item)
            else:
                if self.is_in_file(self._variable_map.get(varname)):
                    key_names.append(varname)
                else:
                    for var_info in self.file_info['variables']:
                        if var_info['name'] == varname:
                            break

                    # use the default grib name
                    _var_map = {item: var_info[item]
                                for item in ['name', 'shortName', 'typeOfLevel', 'stepType']}
                    # update the variable map
                    self.update_variable_map(_var_map)

                    # add the first name
                    key_names.append(self.data_vars[0])

            assert len(key_names) > 0, "No valid keys in variable_map"

            for item in key_names:
                try:
                    if not self._file_handler.closed:
                        self._file_handler.seek(0)
                        try:
                            # handle case when name is in data_vars
                            _tmp = self._file_handler.select(**self._variable_map[item])
                        except ValueError:
                            raise RuntimeError(
                                f"Grib record {item} is not valid")
                        if not len(_tmp) > 0:
                            raise RuntimeError("No grib records found")
                        if tidx > len(_tmp):
                            raise IndexError(
                                f"Grid record index {tidx} is out of bounds")
                        setattr(self, item, _tmp[tidx])
                        # create a time array and instantiate RasterTime object
                        if len(_tmp) > 1:
                            _time_array = np.array(
                                [msg.validDate for msg in _tmp])
                            self._time_handler = RasterTime(_time_array)
                            self._time_handler.set_time_bounds()
                    else:
                        raise RuntimeError("Grib file is closed")
                except ValueError:
                    raise ValueError("Invalid mapping for grib code")
        else:
            raise RuntimeError("No grib map found")

    @property
    def file_info(self) -> Dict:
        if self._file_info is None:
            self.get_file_info()
        return self._file_info

    @supported_libs.RequireLib("pygrib")
    def get_file_info(self, *args, **kwargs) -> Dict:
        out = {"filename": "", "dimensions": [], "variables": []}
        if self._file_handler is None:
            self.open_file(*args, **kwargs)

        if self._file_handler is not None:
            try:
                out['filename'] = self._file_handler.name
            except Exception:
                pass

            for item in self._file_handler:
                if not hasattr(self, item.name):
                    setattr(self, item.name, item)

                obj = {}
                for attr in ['name', 'shortName', 'typeOfLevel', 'level',
                             'stepType', 'forecastTime', 'validDate', 'analDate',
                             'units']:
                    obj[attr] = getattr(item, attr)
                    if isinstance(obj[attr], datetime):
                        obj[attr] = datetime.strftime(obj[attr], "%Y-%m-%dT%H:%M:%S")
                out['variables'].append(obj)

            if len(out['variables']) > 0:
                _, _, nx, ny, _ = self.get_grid_info(out['variables'][0]['name'])
                out['dimensions'].append({"name": "lon", "size": nx})
                out['dimensions'].append({"name": "lat", "size": ny})
        self._file_info = out
        return out

    @supported_libs.RequireLib("pygrib")
    def open_file(self, *args, **kwargs):
        if supported_libs.HAS_PYGRIB:
            if isinstance(self._file_name, bytes):
                self._file_handler = pygrib.open(self._file_name.decode())
            elif isinstance(self._file_name, str):
                self._file_handler = pygrib.open(self._file_name)
        else:
            warnings.warn("pygrib library is not installed", ImportWarning)
            return None

    @property
    def data_vars(self) -> List[str]:
        return self.get_data_variables()

    @supported_libs.RequireLib("pygrib")
    def get_data_variables(self, *args, **kwargs) -> List[str]:
        out = []
        if len(self.file_info['variables']) > 0:
            out = map(lambda item: item['name'], self.file_info['variables'])
            out = list(Counter(out).keys())
        return out

    @supported_libs.RequireLib("pygrib")
    def get_grid_info(self, varname: str) -> Tuple[np.ndarray, np.ndarray, int, int, str]:
        # use projection information when available in grib file
        projStr = ""

        if self._file_handler is not None:
            if getattr(self, varname)['gridType'] in ['regular_gg', 'regular_ll']:
                try:
                    ny, nx = getattr(self, varname)[
                        'Ny'], getattr(self, varname)['Nx']
                except Exception:
                    ny, nx = getattr(self, varname)[
                        'Nj'], getattr(self, varname)['Ni']
                lon = getattr(self, varname)['distinctLongitudes']
                lat = getattr(self, varname)['distinctLatitudes']
                projStr = GRIB_Handler.return_proj4("EPSG:4326")
            elif getattr(self, varname)['gridType'] in ['reduced_gg', 'reduced_ll']:
                lat, lon = getattr(self, varname).latlons()
                if lat.ndim == 1:
                    ny, nx = len(lat), len(lon)
                elif lat.ndim == 2:
                    ny, nx = lat.shape
                    lon = lon[0, :]
                    lat = lat[:, 0]
                projStr = GRIB_Handler.return_proj4(
                    getattr(self, varname).projparams)
            elif getattr(self, varname)['gridType'] in ["lambert",
                                                        "albers",
                                                        "equatorial_azimuthal_equidistant",
                                                        "lambert_azimuthal_equal_area"]:
                try:
                    ny, nx = getattr(self, varname)[
                        'Ny'], getattr(self, varname)['Nx']
                except Exception:
                    ny, nx = getattr(self, varname)[
                        'Nj'], getattr(self, varname)['Ni']

                lat1 = getattr(self, varname)[
                    'latitudeOfFirstGridPointInDegrees']
                lon1 = getattr(self, varname)[
                    'longitudeOfFirstGridPointInDegrees']

                # get the grid spacing
                if getattr(self, varname)['gridType'] in ["albers",
                                                        "equatorial_azimuthal_equidistant",
                                                        "lambert_azimuthal_equal_area"]:
                    dx = getattr(self, varname)['Dx']
                    dy = getattr(self, varname)['Dy']
                else:
                    dx = getattr(self, varname)['DxInMetres']
                    dy = getattr(self, varname)['DyInMetres']

                # apply scale
                if getattr(self, varname)['gridType'] in ["albers",
                                                        "equatorial_azimuthal_equidistant",
                                                        "lambert_azimuthal_equal_area"]:
                    dx = dx / 1000.0
                    dy = dy / 1000.0
                # get projection string when pyproj is available
                projStr = GRIB_Handler.return_proj4(
                    getattr(self, varname).projparams)
                # project the corner when pyproj library is available
                llcrnrx, llcrnry = GRIB_Handler.proj_start_location(
                    lon1, lat1, projStr)
                if getattr(self, varname)['iScansPositively'] == 0 and dx > 0:
                    dx = -dx
                if getattr(self, varname)['jScansPositively'] == 0 and dy > 0:
                    dy = -dy
                lon = llcrnrx + dx * np.arange(nx)
                lat = llcrnry + dy * np.arange(ny)
            else:
                raise ValueError(
                    f"Grid {getattr(self, varname)['gridType']} is not supported")
            return lon, lat, nx, ny, projStr

    def update_variable_map(self, other: Dict):
        self._variable_map.update(other)

    @supported_libs.RequireLib("pygrib")
    def reader(self, *args, **kwargs) -> Tuple:
        """function to read grib file and instantiate a handler.

        Returns
        -------
        Tuple
            a tuple of parameters used to instantiate a raster object.
            For a grib file, the parameters returned are
            (nx, ny, hx, hy, ox, oy, projStr, time)

        Raises
        ------
        ValueError
            file_name cannot be None
        """

        if self._file_name is None:
            raise ValueError("file_name cannot be None")

        varname = None
        if args:
            if isinstance(args[0], str):
                varname = args[0]
        elif kwargs:
            varname = kwargs.get("varname", self.raster_name)
            if varname is None or varname == "":
                varname = list(self._variable_map.keys())[0]
        else:
            if self._variable_map:
                varname = list(self._variable_map.keys())[0]

        # open file
        self.open_file(*args, **kwargs)

        if not self.is_in_file(self._variable_map.get(varname)) or varname is None:
            warnings.warn(f"Variable {varname} is not valid, using {self.data_vars[0]}")
            varname = self.data_vars[0]
            for var_info in self.file_info['variables']:
                if var_info['name'] == varname:
                    break
            self.update_variable_map({varname: {item: var_info[item]
                                                for item in ['name', 'shortName', 'stepType', 'typeOfLevel']}})

        # read grib file
        self.read_grib_file(tidx=0, varname=varname)

        if self._file_handler is None:
            raise RuntimeError("Unable to open grib file")

        lon, lat, nx, ny, projStr = self.get_grid_info(varname)

        time = self.time(0)
        # compute dimension input for instantiating raster.Raster
        hx = lon[1] - lon[0]
        hy = lat[1] - lat[0]
        nz = 1
        hz = 1.0
        oz = 0.0

        if isinstance(lon[0], np.ma.MaskedArray):
            ox = self.base_type(lon[0].data)
        elif isinstance(lon[0], np.ndarray):
            ox = self.base_type(lon[0])
        elif isinstance(lon[0], numbers.Real):
            ox = self.base_type(lon[0])
        ox -= 0.5 * hx

        if isinstance(lat[0], np.ma.MaskedArray):
            oy = self.base_type(lat[0].data)
        elif isinstance(lat[0], np.ndarray):
            oy = self.base_type(lat[0])
        elif isinstance(lat[0], numbers.Real):
            oy = self.base_type(lat[0])

        if hy < 0:
            self.invert_y = True
            hy = abs(hy)
        oy -= 0.5 * hy

        return nx, ny, nz, hx, hy, hz, ox, oy, oz, core.str2bytes(projStr), time

    def writer(self, *args, **kwargs):
        raise NotImplementedError()

    def setter(self, ti: numbers.Integral, tj: numbers.Integral,
               tx: numbers.Integral, ty: numbers.Integral,
               tidx: numbers.Integral) -> Tuple[np.ndarray, int, int]:
        """function to return data from the grib file for a given geostack raster index.

        Parameters
        ----------
        ti : numbers.Integral
            tile index in x-direction
        tj : numbers.Integral
            tile index in y-direction
        tx : numbers.Integral
            total number of tiles in x-direction
        ty : numbers.Integral
            total numbers of tiles in y-direction
        tidx : numbers.Integral
            time index to return the grib data. This index is
            required when there are multiple values for a grib
            message.

        Returns
        -------
        Tuple
            a tuple containing with the tile data and tile indices
            (buf_arr, ti, tj)

        Raises
        ------
        KeyError
            item is not valid
        """
        # Check handle
        self.check_handler()
        # move grib file to a specific grib message
        self.read_grib_file(tidx=tidx, varname=self.raster_name)

        # Create buffer
        tile_size = raster.TileSpecifications().tileSize
        buf_arr = np.full((1, tile_size, tile_size), self.nullValue,
                          dtype=self.data_type)

        # Get dimensions
        if getattr(self, self.raster_name)['gridType'] == "regular_ll":
            ny, nx = getattr(self, self.raster_name)['Nj'], getattr(self, self.raster_name)['Ni']
        else:
            lat, lon = getattr(self, self.raster_name).latlons()
            if lat.ndim == 1:
                ny, nx = len(lat), len(lon)
            elif lat.ndim == 2:
                ny, nx = lat.shape
                lon = lon[0, :]
                lat = lat[:, 0]

        x_start = ti * tile_size
        x_end = min(min((ti + 1), tx) * tile_size, nx)

        if self.invert_y:
            y_start = ny - min(min((tj + 1), ty) * tile_size, ny)
            y_end = ny - tj * tile_size
        else:
            y_start = tj * tile_size
            y_end = min(min((tj + 1), ty) * tile_size, ny)

        # Get variable name
        if isinstance(self.raster_name, str):
            var_name = self.raster_name
        elif isinstance(self.raster_name, bytes):
            var_name = self.raster_name.decode()

        # Get data
        if hasattr(self, var_name):
            temp = getattr(self, var_name).values[y_start:y_end, x_start:x_end]
            if temp.ndim > 2:
                temp = np.squeeze(temp)

            # Get missing value
            missing_value = None
            if 'missingValue' in getattr(self, var_name).keys():
                missing_value = getattr(self, var_name)['missingValue']

            # Fill missing values
            if isinstance(temp, np.ma.MaskedArray):
                temp = np.ma.filled(temp, fill_value=self.nullValue)
            else:
                if missing_value is not None:
                    if np.can_cast(missing_value, temp.dtype):
                        try:
                            missing_value = temp.dtype.type(missing_value)
                        except Exception as e:
                            print(f"Type Casting Error: {str(e)}")
                    else:
                        missing_value = None
                if missing_value is not None:
                    temp = np.where(temp == missing_value,
                                    self.nullValue, temp)
        else:
            raise KeyError(f"Item {var_name} is not valid")

        # Copy data to buffer
        ysize, xsize = temp.shape
        if self.invert_y:
            buf_arr[0, :ysize, :xsize] = temp[::-1, :].astype(self.data_type)
            return buf_arr, ti, (ty - tj)
        else:
            buf_arr[0, :ysize, :xsize] = temp[:, :].astype(self.data_type)
            return buf_arr, ti, tj

    def time(self, tidx: numbers.Integral) -> numbers.Real:
        """function to get the time from the input index.

        Parameters
        ----------
        index: numbers.Integral
            index for the time dimension in the grib file.

        Returns
        -------
        numbers.Real
            the time for the given index in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        time = 0.0
        if self._time_handler is not None:
            time = self.time_from_index(tidx)
        return time

    def set_time_bounds(self, start_time: Optional[Union[numbers.Real, str]] = None,
                        end_time: Optional[Union[numbers.Real, str]] = None,
                        dt_format: Optional[str] = None):
        """set the time bounds for the grib file

        Parameters
        ----------
        start_time : Union[numbers.Real, str], optional
            lower time bound for the grib file, by default None
        end_time : Union[numbers.Real, str], optional
            upper time bounds for the grib file, by default None
        dt_format : str, optional
            datetime format to parse the input start_time/end_time, by default None

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            self._time_handler.set_time_bounds(start_time=start_time,
                                                end_time=end_time,
                                                dt_format=dt_format)
        else:
            raise RuntimeError("No time handle has been set")

    def time_from_index(self, index: numbers.Integral) -> numbers.Real:
        """function to get the time from the input index.

        Parameters
        ----------
        index: numbers.Integral
            index for the time dimension in the grib file.

        Returns
        -------
        numbers.Real
            the time for the given index in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            return self._time_handler.time_from_index(index)
        else:
            raise RuntimeError("No time handle has been set")

    def index_from_time(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        """function to get the index for the input time stamp.

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            input time stamp to query in the grib file.

        Returns
        -------
        numbers.Integral
            the index for the input time stamp in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            return self._time_handler.get_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_max_time_index(self):
        """function to get the max index in the grib file.

        Returns
        -------
        numbers.Integral
            the maximum time index in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            return self._time_handler.get_max_time_index()
        else:
            raise RuntimeError("No time handle has been set")

    def get_left_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        """function to get the left index of the input time stamp.

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            input time stamp to query in the grib file.

        Returns
        -------
        numbers.Integral
            the left index to the input time stamp in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            return self._time_handler.get_left_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    def get_right_index(self, timestamp: Union[datetime, numbers.Real]) -> numbers.Integral:
        """function to get the right index of the input time stamp.

        Parameters
        ----------
        timestamp : Union[datetime, numbers.Real]
            input time stamp to query in the grib file.

        Returns
        -------
        numbers.Integral
            the right index to the input time stamp in the grib file.

        Raises
        ------
        RuntimeError
            No time handle has been set
        """
        if self._time_handler is not None:
            return self._time_handler.get_right_index(timestamp)
        else:
            raise RuntimeError("No time handle has been set")

    @supported_libs.RequireLib("pygrib")
    def check_handler(self):
        """function to check whether handler is valid.

        Raises
        ------
        TypeError
            Unable to understand the input class instance.
        ValueError
            file_handler cannot be identified
        TypeError
            file_handler is of incorrect type
        ValueError
            mismatch between the file path in the handler to the filename
        """
        if not isinstance(self, GRIB_Handler):
            raise TypeError("Unable to understand the input class instance")

        if self._file_handler is None:
            raise ValueError("file_handler cannot be identified")

        if not isinstance(self._file_handler, pygrib.open):
            raise TypeError("file_handler is of incorrect type")

        if self._file_handler.name != self._file_name:
            raise ValueError("Mismatch between filepath " +
                             f"'{self._file_handler.name}' and filename '{self._file_name}'")

    def close(self):
        """close the grib file.
        """
        if not self._file_handler.closed:
            self._file_handler.close()

        if self._ftp_file is not None:
            if pth.exists(self._file_name):
                os.remove(self._file_name)

    def __exit__(self, *args):
        self.close()


if __name__ == "__main__":
    # get ACCESS-G file
    file_path = "IDY25001.APS3.group1.slv.2019092506.006.surface.grb2"
    if not pth.exists(file_path):
        get_ftp_file(filepath=f"/register/sample/access/grib2/ACCESS-G/single-level/{file_path}",
                     ftp_server="ftp.bom.gov.au")
    else:
        filelist = [file_path]

    variable_map = dict(
        u10=dict(name="10 metre U wind component",
                 typeOfLevel="heightAboveGround",
                 stepType="instant"),
        v10=dict(name="10 metre V wind component",
                 typeOfLevel="heightAboveGround",
                 stepType="instant"),
        t2m=dict(name="Temperature",
                 typeOfLevel="heightAboveGround",
                 stepType="instant"),
        rh=dict(name="Relative humidity",
                typeOfLevel="heightAboveGround",
                stepType="instant")
    )
    tile_size = raster.TileSpecifications().tileSize

    filein = GRIB_Handler(filelist[0], variable_map=variable_map, raster_name="u10")
    params = filein.reader()
    tx = int(math.ceil(params[0] / tile_size))
    ty = int(math.ceil(params[1] / tile_size))
    nx, ny = params[0], params[1]
    test_data, ti, tj = filein.setter(0, 0, tx, ty, 1)
    filein.close()
