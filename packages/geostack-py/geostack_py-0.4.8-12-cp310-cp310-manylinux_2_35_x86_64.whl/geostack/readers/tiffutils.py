import uuid
import array
import struct
from typing import Dict, Tuple, Any
from ..dataset import supported_libs
if supported_libs.HAS_GDAL:
    from osgeo import gdal


TIFF_BYTE = 1        # 8-bit unsigned integer
TIFF_ASCII = 2       # 8-bit bytes w/ last byte null
TIFF_SHORT = 3       # 16-bit unsigned integer
TIFF_LONG = 4        # 32-bit unsigned integer
TIFF_RATIONAL = 5    # 64-bit unsigned fraction
TIFF_SBYTE = 6       # 8-bit signed integer
TIFF_UNDEFINED = 7   # 8-bit untyped data
TIFF_SSHORT = 8      # 16-bit signed integer
TIFF_SLONG = 9       # 32-bit signed integer
TIFF_SRATIONAL = 10  # 64-bit signed fraction
TIFF_FLOAT = 11      # 2-bit IEEE floating point
TIFF_DOUBLE = 12     # 64-bit IEEE floating point
TIFF_IFD = 13        # 32-bit unsigned integer (offset)
TIFF_LONG8 = 16      # BigTIFF 64-bit unsigned integer
TIFF_SLONG8 = 17     # BigTIFF 64-bit signed integer
TIFF_IFD8 = 18       # BigTIFF 64-bit unsigned integer (offset)

datatypesize = {}
datatypesize[TIFF_ASCII] = 1
datatypesize[TIFF_SHORT] = 2
datatypesize[TIFF_DOUBLE] = 8

TIFFTAG_GEOPIXELSCALE = 33550
TIFFTAG_GEOTIEPOINTS = 33922
TIFFTAG_GEOTRANSMATRIX = 34264
TIFFTAG_GEOKEYDIRECTORY = 34735
TIFFTAG_GEODOUBLEPARAMS = 34736
TIFFTAG_GEOASCIIPARAMS = 34737
geotiff_tagids = [TIFFTAG_GEOPIXELSCALE,
                  TIFFTAG_GEOTIEPOINTS,
                  TIFFTAG_GEOTRANSMATRIX,
                  TIFFTAG_GEOKEYDIRECTORY,
                  TIFFTAG_GEODOUBLEPARAMS,
                  TIFFTAG_GEOASCIIPARAMS]


@supported_libs.RequireLib("gdal")
def get_geotiff_tags(ds: "gdal.Dataset") -> Dict[int, Tuple]:
    """extract geotiff tags

    Reference
    ---------
    https://github.com/rouault/cogserver/blob/master/cogserver.py


    Parameters
    ----------
    ds : gdal.Dataset
        input dataset to extract geotiff tags

    Returns
    -------
    List[Tuple]
        a list of tuples with geotiff tags
    """
    close_file_at_end = False

    if isinstance(ds, str):
        ds = gdal.Open(ds)
        close_file_at_end = True

    tmpfilename = '/vsimem/' + str(uuid.uuid1()) + '.tif'
    tmp_ds = gdal.GetDriverByName('GTiff').Create(tmpfilename, 1, 1)

    gcps = ds.GetGCPs()
    if gcps:
        tmp_ds.SetGCPS(gcps, ds.GetGCPProjection())
    else:
        tmp_ds.SetSpatialRef(ds.GetSpatialRef())
        gt = ds.GetGeoTransform(can_return_null=True)
        if gt:
            tmp_ds.SetGeoTransform(gt)
    tmp_ds = None

    f = gdal.VSIFOpenL(tmpfilename, 'rb')
    maxsize = 100 * 1000

    data = gdal.VSIFReadL(1, maxsize, f)
    gdal.VSIFCloseL(f)
    gdal.Unlink(tmpfilename)
    assert len(data) < maxsize

    assert data[0:4] == b'\x49\x49\x2A\x00'
    assert data[4:8] == b'\x08\x00\x00\x00'
    num_tags = struct.unpack('H', data[8:10])[0]
    offset = 10

    geotifftags = {}
    for i in range(num_tags):
        tagid = struct.unpack('H', data[offset:offset+2])[0]
        if tagid in geotiff_tagids:
            tagtype = struct.unpack('H', data[offset+2:offset+4])[0]
            valrepeat = struct.unpack('I', data[offset+4:offset+8])[0]
            valoroffset = struct.unpack('I', data[offset+8:offset+12])[0]
            assert valoroffset >= 10 + num_tags * 12

            tag_value = data[valoroffset:valoroffset + valrepeat * datatypesize[tagtype]]

            if tagid == TIFFTAG_GEOTRANSMATRIX:
                tag_value = list(array.array('d', tag_value))
            elif tagid == TIFFTAG_GEOTIEPOINTS:
                tag_value = list(array.array('d', tag_value))
            elif tagid == TIFFTAG_GEOPIXELSCALE:
                tag_value = list(array.array('d', tag_value))
            elif tagid == TIFFTAG_GEOKEYDIRECTORY:
                tag_value = list(array.array('H', tag_value))
            elif tagid == TIFFTAG_GEOASCIIPARAMS:
                tag_value = tag_value.decode()

            geotifftags[tagid] = (tagtype, valrepeat, tag_value)
            num_tags += 1
        offset += 12

    if close_file_at_end:
        ds = None

    return geotifftags
