# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
#cython: language_level=3

from cython.operator cimport dereference as deref
from cython.operator cimport preincrement as preinc
from libcpp.string cimport string
from libcpp cimport bool
from libcpp.map cimport map as cpp_map
from libcpp.set cimport set as cpp_set
from libcpp.set cimport pair as cpp_pair
from libcpp.list cimport list as cpp_list
from libcpp.vector cimport vector
from libc.stdint cimport uint8_t, uint32_t, int32_t, uint64_t, int64_t, uint16_t
from libc.stdio cimport printf
from libcpp.functional cimport function
from libcpp.iterator cimport iterator
from cpython.pycapsule cimport PyCapsule_IsValid, PyCapsule_GetPointer, PyCapsule_New
import numpy as np
cimport cython
cimport numpy as np
from numpy cimport npy_intp, PyArray_SimpleNewFromData
from libcpp.memory cimport shared_ptr, unique_ptr, make_shared, default_delete
from ..core._cy_property cimport (PropertyType, PropertyStructure,
                                  PropertyMap, _PropertyMap)
from ..core.cpp_tools cimport reference_wrapper, fstream, ifstream, ios_out
from ..vector._cy_vector cimport (_Vector_d, _Vector_f,
                                  _BoundingBox_d, _BoundingBox_f,
                                  _Coordinate_f, _Coordinate_d)
from ..core._cy_projection cimport _ProjectionParameters_d

np.import_array()

ctypedef uint32_t cl_uint

ctypedef fused float_t:
    double
    float

ctypedef fused int_t:
    int32_t
    int

cdef extern from "utils.h":
    void cy_copy[T](T& a, T& b) nogil

cdef extern from "gs_projection.h" namespace "Geostack":
    cdef cppclass ProjectionParameters[T]:
        pass

cdef extern from "gs_solver.h" namespace "Geostack":
    T getNullValue[T]() nogil

cdef extern from "gs_vector.h" namespace "Geostack":
    cdef cppclass Vector[T]:
        pass

    cdef cppclass Coordinate[T]:
        Coordinate() except +
        Coordinate(Coordinate[T] &c) except +
        Coordinate(T p, T q) except +
        T magnitudeSquared() except +
        Coordinate[T] max_c "max"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] min_c "min"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] centroid(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T]& operator=(Coordinate[T] &c) except +
        T p, q, r, s

    bool operator==[T](Coordinate[T] &a, Coordinate[T] &b) except +
    bool operator!=[T](Coordinate[T] &a, Coordinate[T] &b) except +
    Coordinate[T]& operator+[T](Coordinate[T] &a, Coordinate[T] &b) except +
    Coordinate[T]& operator-[T](Coordinate[T] &a, Coordinate[T] &b) except +

    cdef cppclass BoundingBox[T]:
        BoundingBox() except +
        BoundingBox(Coordinate[T], Coordinate[T]) except +
        Coordinate[T] min_c "min"
        Coordinate[T] max_c "max"
        void reset()
        void extend2D(T)
        void extend(Coordinate[T])
        void extent(const BoundingBox[T] &b)
        T area()
        T diameterSqr()
        T centroidDistanceSqr(const BoundingBox[T] &b)
        Coordinate[T] centroid()
        Coordinate[T] extent()
        uint64_t createZIndex(Coordinate[T] c)

    cdef cppclass GeometryBase[T]:
        BoundingBox[T] getBounds()
        bool isContainer()
        cl_uint getID() except +
        bool isType(size_t type_) except +

    cdef cppclass VectorGeometry[T](GeometryBase[T]):
        pass

cdef extern from "gs_tile.h" namespace "Geostack":
    cdef cppclass Dimensions[C]:
        uint32_t nx
        uint32_t ny
        uint32_t nz
        C hx
        C hy
        C hz
        C ox
        C oy
        C oz
        uint32_t mx
        uint32_t my

    cdef cppclass TileDimensions[C]:
        Dimensions[C] d
        C ex
        C ey
        C ez
        uint32_t ti
        uint32_t tj

    cdef cppclass RasterDimensions[C]:
        Dimensions[C] d
        C ex
        C ey
        C ez
        uint32_t tx
        uint32_t ty

    bool operator==[R, C](const Tile[R, C] &l, const Tile[R, C] &r) except +
    bool operator!=[R, C](const Tile[R, C] &l, const Tile[R, C] &r) except +
    bool equalSpatialMetrics[T](const Dimensions[T] l, const Dimensions[T] r) except +
    bool equalSpatialMetrics2D[T](const Dimensions[T] l, const Dimensions[T] r) except +

cdef extern from "gs_tile.h" namespace "Geostack":
    cdef cppclass Tile[R, C](GeometryBase[C]):
        Tile() except + nogil
        Tile(const Tile &r) except + nogil
        bool init(int32_t ti_, int32_t tj_, RasterDimensions[C] rdim_)
        Dimensions[C] getDimensions() except +
        TileDimensions[C] getTileDimensions() except +
        BoundingBox[C] getBounds() except +
        Coordinate[C] getCentroid() except +
        bool isType(size_t typeMask) except +
        bool operator==[R, C](const Tile[R, C] &l, const Tile[R, C] &r) except +
        bool operator!=[R, C](const Tile[R, C] &l, const Tile[R, C] &r) except +
        R& operator[](uint32_t i, uint32_t j, uint32_t k) except +
        bool hasData() except +
        void setAllCellValues(R val) except +
        R max() except + nogil
        R min() except + nogil

cdef extern from "pyFileHandler.h" namespace "Geostack::pyGeostack":
    cdef cppclass IntRaster[C]:
        pass

cdef extern from "gs_raster.h" namespace "Geostack":
    cdef cppclass dataHandlerFunction[R, C]:
        pass

    cdef cppclass RasterFileHandler[R, C]:
        RasterFileHandler() except + nogil
        RasterFileHandler(RasterFileHandler &) except + nogil
        void read(string fileName, Raster[R, C] &r, string jsonConfig) except +
        void write(string fileName, Raster[R, C] &r, string jsonConfig) except +
        const dataHandlerFunction[R, C]& getDataHandler()
        Raster[R, C] &r
        shared_ptr[fstream] fileStream

    cdef cppclass RasterBase[C](PropertyMap):
        RasterBase() except + nogil
        RasterBase(const RasterBase &Rb) except + nogil
        RasterDimensions[C] getRasterDimensions() except +
        BoundingBox[C] getBounds() except +
        bool hasData() except +
        void deleteRasterData() except + nogil
        void setProjectionParameters(ProjectionParameters[double] proj_)
        void setProjectionParameters(string proj_)
        void setInterpolationType(size_t interpolation_) except +
        size_t getInterpolationType() except +
        ProjectionParameters[double] getProjectionParameters()
        cpp_set[string] getVariableNames() except +
        R getVariableData[R](string name) except +
        R getVariableDataIndex "getVariableData" [R](string name, size_t index) except +
        void setVariableData[R](string name, R value) except +
        void setVariableDataIndex "setVariableData" [R](string name, R value, size_t index) except +
        cpp_map[string, size_t]& getVariablesIndexes() except +
        size_t getVariableSize(string name) except +
        string getVariablesType() except +
        bool hasVariables() except +
        string getDataTypeString() except +
        void setConst(bool isConst_) except +
        bool getConst() except +
        void read(string fileName, string jsonConfig) except +
        void write(string fileName, string jsonConfig) except +
        IntRaster[C] indexComponents(string) except + nogil
        Vector[C] indexComponentsVector(string, string, size_t, bool) except + nogil
        Vector[C] getRasterFootprint() except +
        void saveRandomState() except +
        void restoreRandomState() except +
        TileDimensions[C] getTileDimensions(uint32_t i, uint32_t j) except + nogil
        BoundingBox[C] getTileBounds(uint32_t i, uint32_t j) except + nogil
        void closeFile() except + nogil
        void deleteVariableData() except + nogil

ctypedef pyException (*data_reader_d) (void*, TileDimensions[double], vector[double]&) noexcept
ctypedef pyException (*data_reader_f) (void*, TileDimensions[float], vector[float]&) noexcept
ctypedef pyException (*data_reader_f_i) (void*, TileDimensions[float], vector[uint32_t]&) noexcept
ctypedef pyException (*data_reader_d_i) (void*, TileDimensions[double], vector[uint32_t]&) noexcept
ctypedef pyException (*data_reader_f_byt) (void*, TileDimensions[float], vector[uint8_t]&) noexcept
ctypedef pyException (*data_reader_d_byt) (void*, TileDimensions[double], vector[uint8_t]&) noexcept

cdef extern from "pyFileHandler.h" namespace "Geostack::pyGeostack":

    ctypedef struct pyException:
        int rc
        string errMessage

    cdef cppclass pyFileHandler[R, C]:
        ctypedef pyException (*data_reader_d) (void*, TileDimensions[double], vector[double]&)
        ctypedef pyException (*data_reader_f) (void*, TileDimensions[float], vector[float]&)
        ctypedef pyException (*data_reader_f_i) (void*, TileDimensions[float], vector[uint32_t]&)
        ctypedef pyException (*data_reader_d_i) (void*, TileDimensions[double], vector[uint32_t]&)
        ctypedef pyException (*data_reader_f_byt) (void*, TileDimensions[float], vector[uint8_t]&)
        ctypedef pyException (*data_reader_d_byt) (void*, TileDimensions[double], vector[uint8_t]&)

        pyFileHandler(data_reader_f py_f, void* py_class, string filename) except + nogil
        pyFileHandler(data_reader_d py_f, void* py_class, string filename) except + nogil
        pyFileHandler(data_reader_f_i py_f, void* py_class, string filename) except + nogil
        pyFileHandler(data_reader_d_i py_f, void* py_class, string filename) except + nogil
        pyFileHandler(data_reader_f_byt py_f, void* py_class, string filename) except + nogil
        pyFileHandler(data_reader_d_byt py_f, void* py_class, string filename) except + nogil
        void dataFunction(TileDimensions[C] tdim, vector[R] &v) except + nogil
        string getFileName() except + nogil

    void add_ref_to_vec[T](vector[reference_wrapper[RasterBase[T]]]&,
                           RasterBase[T]&) except +
    RasterBase[T]& get_raster_ref_from_vec[T](vector[reference_wrapper[RasterBase[T]]]&, size_t i) except +
    void add_raster_ptr_to_vec[R, C](vector[shared_ptr[RasterBase[C]]]&,
                                     shared_ptr[Raster[R, C]]&) except +
    shared_ptr[RasterBase[C]] get_raster_ptr_from_vec[C](vector[shared_ptr[RasterBase[C]]]&, size_t i) except +

cdef extern from "gs_raster.h" namespace "Geostack::RasterCombination":
    cdef enum RasterCombinationType "Geostack::RasterCombination::Type":
        Union = 0
        Intersection = 1 << 0

cdef extern from "gs_raster.h" namespace "Geostack::RasterResolution":
    cdef enum RasterResolutionType "Geostack::RasterResolution::Type":
        Resolution_MIN "Minimum" = 0
        Resolution_MAX "Maximum" = 1 << 2

cdef extern from "gs_raster.h" namespace "Geostack::RasterInterpolation":
    cdef enum RasterInterpolationType "Geostack::RasterInterpolation::Type":
        Nearest = 0
        Bilinear = 1 << 4
        Bicubic = 2 << 4

cdef extern from "gs_raster.h" namespace "Geostack::RasterNullValue":
    cdef enum RasterNullValueType "Geostack::RasterNullValue::Type":
        Null = 0
        Zero = 1 << 6
        One = 2 << 6

cdef extern from "gs_tile.h" namespace "Geostack::Reduction":
    cdef enum ReductionType "Geostack::Reduction::Type":
        NoReduction "None" = 0
        Reduction_MAX "Maximum" = 1 << 8
        Reduction_MIN "Minimum" = 2 << 8
        Reduction_SUM "Sum" = 3 << 8
        Reduction_COUNT "Count" = 4 << 8
        Reduction_MEAN "Mean" = 5 << 8
        Reduction_SumSquares "SumSquares" = 6 << 8

cdef extern from "gs_tile.h" namespace "Geostack":
    cdef cppclass RasterIndex[T]:
        uint32_t id
        uint16_t i
        uint16_t j
        T w

cdef extern from "gs_raster.h" namespace "Geostack::RasterDebug":
    cdef enum RasterDebugType "Geostack::RasterDebug::Type":
        NoDebug "Geostack::RasterDebug::Type::None" = 0 << 12
        Enable = 1 << 12

cdef extern from "gs_raster.h" namespace "Geostack::RasterSort":
    cdef enum RasterSortType "Geostack::RasterSort::Type":
        NoSort = 0
        PreScript = 1 << 6
        PostScript = 2 << 6

cdef extern from "gs_raster.h" namespace "Geostack::GeometryType":
    cdef enum GeometryType "Geostack::GeometryType::Type":
        NoType "Geostack::GeometryType::Type::None" = 0
        Point = 1
        LineString = 1 << 1
        Polygon = 1 << 2
        All = 0x07
        TileType "Geostack::GeometryType::Type::Tile" = 1 << 3

cdef extern from "gs_raster.h" namespace "Geostack::Neighbours":
    cdef enum NeighboursType "Geostack::Neighbours::Type":
        NoNeighbour "None" = 0x00
        N  = 1 << 0
        NE = 1 << 1
        E  = 1 << 2
        S =  1 << 4
        SW = 1 << 5
        W =  1 << 6
        NW = 1 << 7
        Rook = 0x01
        Bishop = 0x02
        Queen = 0x03

ctypedef cpp_set[cpp_pair[uint32_t, uint32_t]] tileIndexSet

cdef extern from "gs_raster.h" namespace "Geostack":
    cdef cppclass Raster[R, C](RasterBase[C]):
        Raster() except + nogil
        Raster(string) except + nogil
        Raster(const Raster &r) except + nogil
        Raster& operator=(const Raster &r)
        bool init(Dimensions[C] &dim) except +
        bool init(BoundingBox[C] bounds, C hx, C hy, C hz) except +
        bool init2D(uint32_t nx_, uint32_t ny_, C hx_, C hy_,
                    C ox_, C oy_) except + nogil
        bool init(uint32_t nx_, uint32_t ny_, uint32_t nz_,
                  C hx_, C hy_, C hz_, C ox_, C oy_, C oz_) except + nogil
        bool resize2D(uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except + nogil
        tileIndexSet resize2DIndexes(uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except + nogil
        R max() nogil
        R min() nogil
        void setOrigin_z(C oz) except +
        R reduce() except + nogil
        R getCellValue(uint32_t i, uint32_t j, uint32_t k) except + nogil
        R getNearestValue(C x, C y, C z) except + nogil
        R getBilinearValue(C x, C y, C z) except + nogil
        void setAllCellValues(R c) except + nogil
        void setCellValue(R v, uint32_t i, uint32_t j, uint32_t k) except + nogil
        void setTileData(uint32_t ti, uint32_t tj, vector[R] &data) except + nogil
        void getTileData(uint32_t ti, uint32_t tj, vector[R] &data) except + nogil
        void mapVector(Vector[C] &v, string script, size_t parameters,
                       string widthPropertyName, string levelPropertyName) except + nogil
        void rasterise(Vector[C] &v, string script, size_t parameters,
                       string levelPropertyName) except + nogil
        Vector[C] cellCentres(bool mapValues) except + nogil
        Vector[C] cellPolygons(bool mapValues) except + nogil
        Vector[C] vectorise(vector[R] contourValue, string propertyName,
                            size_t parameter, R noDataValue) except + nogil
        bool operator==[R, C](Raster[R, C] &l, Raster[R, C] &r) except +
        uint8_t getRequiredNeighbours()
        void setRequiredNeighbours(uint8_t requiredNeighbours)
        ReductionType getReductionType()
        void setReductionType(ReductionType requiredReduction)
        bool getNeedsStatus()
        void setNeedsStatus(bool needsStatus_)
        bool getNeedsWrite()
        void setNeedsWrite(bool needsWrite_)
        void setFileInputHandler(shared_ptr[pyFileHandler[R, C]]) except +
        void setFileOutputHandler(shared_ptr[pyFileHandler[R, C]]) except +
        Coordinate[C] ijk2xyz(uint32_t i, uint32_t j, uint32_t z) except +
        cpp_list[uint32_t] xyz2ijk(C x, C y, C z) except +
        void searchTiles(BoundingBox[C] bounds, vector[shared_ptr[GeometryBase[C]]] &searchGeometry) except +
        void nearestTiles(BoundingBox[C] bounds, vector[shared_ptr[GeometryBase[C]]] &searchGeometry) except +

    bool operator==[R, C](const Raster[R, C] &l, const Raster[R, C] &r) except +
    void sortColumns[R](RasterBase[R] &r) except + nogil

cdef extern from "gs_tile.h" namespace "Geostack::TileMetrics":
    cdef uint32_t tileSizePower
    cdef uint32_t tileSize
    cdef uint32_t tileSizeSquared
    cdef uint32_t tileSizeMask
    cdef uint32_t workgroupSizePower
    cdef uint32_t workgroupSize
    cdef uint32_t reductionMultiple

ctypedef enum RasterKind:
    Raster1D = 1
    Raster2D = 2
    Raster3D = 3

cdef extern from "<utility>" namespace "std" nogil:
    cdef shared_ptr[Raster[float, float]] move(shared_ptr[Raster[float, float]])
    cdef shared_ptr[Raster[uint8_t, float]] move(shared_ptr[Raster[uint8_t, float]])
    cdef shared_ptr[Raster[uint32_t, float]] move(shared_ptr[Raster[uint32_t, float]])
    cdef shared_ptr[Raster[double, double]] move(shared_ptr[Raster[double, double]])
    cdef shared_ptr[Raster[uint8_t, double]] move(shared_ptr[Raster[uint8_t, double]])
    cdef shared_ptr[Raster[uint32_t, double]] move(shared_ptr[Raster[uint32_t, double]])

ctypedef reference_wrapper[RasterBase[double]] RasterBaseRef_d
ctypedef reference_wrapper[RasterBase[float]] RasterBaseRef_f
ctypedef shared_ptr[RasterBase[double]] RasterBasePtr_d
ctypedef shared_ptr[RasterBase[float]] RasterBasePtr_f
ctypedef vector[RasterBaseRef_d] raster_base_list_d
ctypedef vector[RasterBaseRef_f] raster_base_list_f
ctypedef vector[RasterBasePtr_d] raster_ptr_list_d
ctypedef vector[RasterBasePtr_f] raster_ptr_list_f
ctypedef RasterDimensions[double] raster_dimensions_d
ctypedef RasterDimensions[float] raster_dimensions_f
ctypedef TileDimensions[double] tile_dimensions_d
ctypedef TileDimensions[float] tile_dimensions_f

cpdef double getNullValue_dbl()
cpdef float getNullValue_flt()
cpdef uint8_t getNullValue_uint8()
cpdef uint32_t getNullValue_uint32()
cpdef uint64_t getNullValue_uint64()
cpdef int32_t getNullValue_int32()
cpdef int64_t getNullValue_int64()
cpdef string getNullValue_str()


cdef class _Dimensions_d:
    cdef Dimensions[double] *thisptr
    cdef void c_copy(self, Dimensions[double] inp_dims)


cdef class _Dimensions_f:
    cdef Dimensions[float] *thisptr
    cdef void c_copy(self, Dimensions[float] inp_dims)


cdef class _RasterDimensions_d:
    cdef raster_dimensions_d *thisptr
    cdef void c_copy(self, raster_dimensions_d inp_dims)


cdef class _RasterDimensions_f:
    cdef raster_dimensions_f *thisptr
    cdef void c_copy(self, raster_dimensions_f inp_dims)


cdef class _TileDimensions_d:
    cdef tile_dimensions_d *thisptr
    cdef uint32_t n, nz, lnx, lny
    cdef uint32_t ti, tj
    cdef double hx, hy, hz, ox, oy, oz, ex, ey, ez
    cdef void c_copy(self, tile_dimensions_d inp_dims)


cdef class _TileDimensions_f:
    cdef tile_dimensions_f *thisptr
    cdef uint32_t n, nz, lnx, lny
    cdef uint32_t ti, tj
    cdef float hx, hy, hz, ox, oy, oz, ex, ey, ez
    cdef void c_copy(self, tile_dimensions_f inp_dims)


cdef class _cyRasterBase_d(_PropertyMap):
    cdef bool ptr_owner
    cdef RasterBase[double] *baseptr
    cpdef _BoundingBox_d getBounds(self)
    cpdef _RasterDimensions_d getRasterDimensions(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_) except *
    cpdef size_t getInterpolationType(self) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef int getRasterKind(self)
    cpdef double getVariableData(self, string name) except *
    cpdef void setVariableData(self, string name, double value) except *
    cpdef double[:] getVariableDataArray(self, string name) except *
    cpdef void setVariableDataArray(self, string name, double[:] value) except *
    cpdef double getVariableDataIndex(self, string name, size_t index) except *
    cpdef void setVariableDataIndex(self, string name, double value, size_t index) except *
    cpdef dict getVariablesIndexes(self)
    cpdef string getVariablesType(self) except *
    cpdef size_t getVariableSize(self, string name) except *
    cpdef bool hasVariables(self) except *
    cpdef void deleteVariableData(self) except *
    cpdef void deleteRasterData(self) except *
    cpdef string getDataTypeString(self) except *
    cpdef void setConst(self, bool isConst_) except *
    cpdef bool getConst(self) except *
    cpdef void read(self, string fileName, string jsonConfig) except *
    cpdef void write(self, string fileName, string jsonConfig) except *
    cpdef bool hasData(self) except *
    cpdef _Vector_d getRasterFootprint(self)
    cpdef _cyRaster_d_i indexComponents(self, string)
    cpdef _Vector_d indexComponentsVector(self, string, string, ReductionType, bool)
    cpdef cpp_set[string] getVariableNames(self) except *
    @staticmethod
    cdef _cyRasterBase_d from_ptr(object capsule)
    cpdef void saveRandomState(self) except *
    cpdef void restoreRandomState(self) except *
    cpdef _TileDimensions_d getTileDimensions(self, uint32_t ti=?, uint32_t tj=?)
    cpdef _BoundingBox_d getTileBounds(self, uint32_t ti=?, uint32_t tj=?)
    cpdef void closeFile(self) except *


cdef class _cyRasterBase_f(_PropertyMap):
    cdef RasterBase[float] *baseptr
    cdef bool ptr_owner
    cpdef _BoundingBox_f getBounds(self)
    cpdef _RasterDimensions_f getRasterDimensions(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_) except *
    cpdef size_t getInterpolationType(self) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef int getRasterKind(self)
    cpdef float getVariableData(self, string name) except *
    cpdef void setVariableData(self, string name, float value) except *
    cpdef float[:] getVariableDataArray(self, string name) except *
    cpdef void setVariableDataArray(self, string name, float[:] value) except *
    cpdef float getVariableDataIndex(self, string name, size_t index) except *
    cpdef void setVariableDataIndex(self, string name, float value, size_t index) except *
    cpdef dict getVariablesIndexes(self)
    cpdef string getVariablesType(self) except *
    cpdef size_t getVariableSize(self, string name) except *
    cpdef bool hasVariables(self) except *
    cpdef void deleteVariableData(self) except *
    cpdef void deleteRasterData(self) except *
    cpdef string getDataTypeString(self) except *
    cpdef void setConst(self, bool isConst_) except *
    cpdef bool getConst(self) except *
    cpdef void read(self, string fileName, string jsonConfig) except *
    cpdef void write(self, string fileName, string jsonConfig) except *
    cpdef bool hasData(self) except *
    cpdef _cyRaster_f_i indexComponents(self, string)
    cpdef _Vector_f indexComponentsVector(self, string, string, ReductionType, bool)
    cpdef _Vector_f getRasterFootprint(self)
    cpdef cpp_set[string] getVariableNames(self) except *
    @staticmethod
    cdef _cyRasterBase_f from_ptr(object capsule)
    cpdef void saveRandomState(self) except *
    cpdef void restoreRandomState(self) except *
    cpdef _TileDimensions_f getTileDimensions(self, uint32_t ti=?, uint32_t tj=?)
    cpdef _BoundingBox_f getTileBounds(self, uint32_t ti=?, uint32_t tj=?)
    cpdef void closeFile(self) except *


cdef class _cyRaster_f(_cyRasterBase_f):
    cdef shared_ptr[Raster[float, float]] sh_ptr
    cdef float[:] data1D
    cdef float[:, :] data2D
    cdef float[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef float hx_, hy_, hz_
    cdef float ox_, oy_, oz_
    cdef void init_with_raster_dimensions(self, _RasterDimensions_f d)  except *
    cdef void init_with_bbox(self, _BoundingBox_f b, float hx, float hy, float hz)  except *
    cpdef void init1D(self, uint32_t nx_, float hx_, float ox_=?)  except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, float hx_, float hy_,
                      float ox_=?, float oy_=?)  except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_,
                      float hx_, float hy_, float hz_, float ox_=?, float oy_=?,
                      float oz_=?)  except *
    cdef void c_rastercopy(self, Raster[float, float] &other) except *
    cpdef float getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef float getNearestValue(self, float x, float y=?, float z=?) except *
    cpdef float getBilinearValue(self, float x, float y=?, float z=?) except *
    cpdef void setCellValue(self, float value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, float c) except *
    cpdef void set1D(self, float[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, float[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, float[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef float[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef float[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef float[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[float]& vec) except *
    cpdef float maxVal(self) except *
    cpdef float minVal(self) except *
    cpdef float reduceVal(self) except *
    cpdef void mapVector(self, _Vector_f v, string script, size_t parameters,
        string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_f v, string script, size_t parameters,
        string levelPropertyName) except *
    cpdef _Vector_f cellCentres(self, bool mapValues=?)
    cpdef _Vector_f cellPolygons(self, bool mapValues=?)
    cpdef _Vector_f vectorise(self, float[:] contourValue,
                              string proprtyName,
                              size_t parameters,
                              object noDataValue=?)
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, float oz) except *
    cpdef _Coordinate_f ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, float x, float y=?, float z=?)
    cpdef _cyRasterBase_f get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_f bbox) except *
    cdef void _searchTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_f bbox) except *
    cdef void _nearestTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *


cdef class _cyRaster_f_byt(_cyRasterBase_f):
    cdef shared_ptr[Raster[uint8_t, float]] sh_ptr
    cdef uint8_t[:] data1D
    cdef uint8_t[:, :] data2D
    cdef uint8_t[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef float hx_, hy_, hz_
    cdef float ox_, oy_, oz_
    cdef void init_with_raster_dimensions(self, _RasterDimensions_f d)  except *
    cdef void init_with_bbox(self, _BoundingBox_f b, float hx, float hy, float hz)  except *
    cpdef void init1D(self, uint32_t nx_, float hx_, float ox_=?)  except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, float hx_, float hy_,
                      float ox_=?, float oy_=?)  except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_, float hx_,
                      float hy_, float hz_, float ox_=?, float oy_=?, float oz_=?)  except *
    cdef void c_rastercopy(self, Raster[uint8_t, float] &other) except *
    cpdef uint8_t maxVal(self) except *
    cpdef uint8_t minVal(self) except *
    cpdef uint8_t reduceVal(self) except *
    cpdef void set1D(self, uint8_t[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, uint8_t[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, uint8_t[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef uint8_t[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint8_t[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint8_t[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[uint8_t]& vec) except *
    cpdef void mapVector(self, _Vector_f v, string script, size_t parameters,
                         string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_f v, string script, size_t parameters,
                         string levelPropertyName) except *
    cpdef _Vector_f cellCentres(self, bool mapValues=?)
    cpdef _Vector_f cellPolygons(self, bool mapValues=?)
    cpdef _Vector_f vectorise(self, uint8_t[:] contourValue,
                              string proprtyName,
                              size_t parameters,
                              object noDataValue=?)
    cpdef uint8_t getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef uint8_t getNearestValue(self, float x, float y=?, float z=?) except *
    # cpdef uint32_t getBilinearValue(self, float x, float y=?, float z=?)
    cpdef void setCellValue(self, uint8_t value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, uint8_t c) except *
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, float oz) except *
    cpdef _Coordinate_f ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, float x, float y=?, float z=?)
    cpdef _cyRasterBase_f get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_f bbox) except *
    cdef void _searchTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_f bbox) except *
    cdef void _nearestTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *


cdef class _cyRaster_f_i(_cyRasterBase_f):
    cdef shared_ptr[Raster[uint32_t, float]] sh_ptr
    cdef uint32_t[:] data1D
    cdef uint32_t[:, :] data2D
    cdef uint32_t[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef float hx_, hy_, hz_
    cdef float ox_, oy_, oz_
    cdef void init_with_raster_dimensions(self, _RasterDimensions_f d)  except *
    cdef void init_with_bbox(self, _BoundingBox_f b, float hx, float hy, float hz)  except *
    cpdef void init1D(self, uint32_t nx_, float hx_, float ox_=?)  except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, float hx_, float hy_,
                      float ox_=?, float oy_=?)  except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_, float hx_,
                      float hy_, float hz_, float ox_=?, float oy_=?, float oz_=?)  except *
    cdef void c_rastercopy(self, Raster[uint32_t, float] &other) except *
    cpdef uint32_t maxVal(self) except *
    cpdef uint32_t minVal(self) except *
    cpdef uint32_t reduceVal(self) except *
    cpdef void set1D(self, uint32_t[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, uint32_t[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, uint32_t[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef uint32_t[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint32_t[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint32_t[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[uint32_t]& vec) except *
    cpdef void mapVector(self, _Vector_f v, string script, size_t parameters,
        string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_f v, string script, size_t parameters,
        string levelPropertyName) except *
    cpdef _Vector_f cellCentres(self, bool mapValues=?)
    cpdef _Vector_f cellPolygons(self, bool mapValues=?)
    cpdef _Vector_f vectorise(self, uint32_t[:] contourValue,
                              string proprtyName,
                              size_t parameters, object noDataValue=?)
    cpdef uint32_t getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef uint32_t getNearestValue(self, float x, float y=?, float z=?) except *
    # cpdef uint32_t getBilinearValue(self, float x, float y=?, float z=?)
    cpdef void setCellValue(self, uint32_t value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, uint32_t c) except *
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, float oz) except *
    cpdef _Coordinate_f ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, float x, float y=?, float z=?)
    cpdef _cyRasterBase_f get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_f bbox) except *
    cdef void _searchTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_f bbox) except *
    cdef void _nearestTiles(self, BoundingBox[float], vector[shared_ptr[GeometryBase[float]]]&) except *


cdef class _cyRaster_d(_cyRasterBase_d):
    cdef shared_ptr[Raster[double, double]] sh_ptr
    cdef double[:] data1D
    cdef double[:, :] data2D
    cdef double[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef double hx_, hy_, hz_
    cdef double ox_, oy_, oz_
    cdef void init_with_raster_dimensions(self, _RasterDimensions_d d)  except *
    cdef void init_with_bbox(self, _BoundingBox_d b, double hx, double hy, double hz)  except *
    cpdef void init1D(self, uint32_t nx_, double hx_, double ox_=?)  except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, double hx_, double hy_,
                      double ox_=?, double oy_=?)  except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_, double hx_,
                      double hy_, double hz_, double ox_=?, double oy_=?,
                      double oz_=?)  except *
    cdef void c_rastercopy(self, Raster[double, double] &other) except *
    cpdef double getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef double getNearestValue(self, double x, double y=?, double z=?) except *
    cpdef double getBilinearValue(self, double x, double y=?, double z=?) except *
    cpdef void setCellValue(self, double value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, double c) except *
    cpdef void set1D(self, double[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, double[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, double[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef double[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef double[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef double[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[double]& vec) except *
    cpdef double maxVal(self) except *
    cpdef double minVal(self) except *
    cpdef double reduceVal(self) except *
    cpdef void mapVector(self, _Vector_d v, string script, size_t parameters,
        string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_d v, string script, size_t parameters,
        string levelPropertyName) except *
    cpdef _Vector_d cellCentres(self, bool mapValues=?)
    cpdef _Vector_d cellPolygons(self, bool mapValues=?)
    cpdef _Vector_d vectorise(self, double[:] contourValue,
                              string proprtyName,
                              size_t parameters, object noDataValue=?)
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, double oz) except *
    cpdef _Coordinate_d ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, double x, double y=?, double z=?)
    cpdef _cyRasterBase_d get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_d bbox) except *
    cdef void _searchTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_d bbox) except *
    cdef void _nearestTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *


cdef class _cyRaster_d_i(_cyRasterBase_d):
    cdef shared_ptr[Raster[uint32_t, double]] sh_ptr
    cdef uint32_t[:] data1D
    cdef uint32_t[:, :] data2D
    cdef uint32_t[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef double hx_, hy_, hz_
    cdef double ox_, oy_, oz_
    cdef void c_rastercopy(self, Raster[uint32_t, double] &other) except *
    cdef void init_with_raster_dimensions(self, _RasterDimensions_d d) except *
    cdef void init_with_bbox(self, _BoundingBox_d b, double hx, double hy, double hz) except *
    cpdef void init1D(self, uint32_t nx_, double hx_, double ox_=?) except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, double hx_, double hy_,
                      double ox_=?, double oy_=?) except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_, double hx_,
                      double hy_, double hz_, double ox_=?, double oy_=?,
                      double oz_=?) except *
    cpdef uint32_t maxVal(self) except *
    cpdef uint32_t minVal(self) except *
    cpdef uint32_t reduceVal(self) except *
    cpdef void set1D(self, uint32_t[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, uint32_t[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, uint32_t[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef uint32_t[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint32_t[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint32_t[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[uint32_t]& vec) except *
    cpdef void mapVector(self, _Vector_d v, string script, size_t parameters,
        string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_d v, string script, size_t parameters,
        string levelPropertyName) except *
    cpdef _Vector_d cellCentres(self, bool mapValues=?)
    cpdef _Vector_d cellPolygons(self, bool mapValues=?)
    cpdef _Vector_d vectorise(self, uint32_t[:] contourValue,
                              string proprtyName,
                              size_t parameters, object noDataValue=?)
    cpdef uint32_t getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef uint32_t getNearestValue(self, double x, double y=?, double z=?) except *
    # cpdef uint32_t getBilinearValue(self, double x, double y=?, double z=?)
    cpdef void setCellValue(self, uint32_t value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, uint32_t c) except *
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, double oz) except *
    cpdef _Coordinate_d ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, double x, double y=?, double z=?)
    cpdef _cyRasterBase_d get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_d bbox) except *
    cdef void _searchTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_d bbox) except *
    cdef void _nearestTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *


cdef class _cyRaster_d_byt(_cyRasterBase_d):
    cdef shared_ptr[Raster[uint8_t, double]] sh_ptr
    cdef uint8_t[:] data1D
    cdef uint8_t[:, :] data2D
    cdef uint8_t[:, :, :] data3D
    cdef uint32_t nx_, ny_, nz_
    cdef double hx_, hy_, hz_
    cdef double ox_, oy_, oz_
    cdef void c_rastercopy(self, Raster[uint8_t, double] &other) except *
    cdef void init_with_raster_dimensions(self, _RasterDimensions_d d) except *
    cdef void init_with_bbox(self, _BoundingBox_d b, double hx, double hy, double hz) except *
    cpdef void init1D(self, uint32_t nx_, double hx_, double ox_=?) except *
    cpdef void init2D(self, uint32_t nx_, uint32_t ny_, double hx_, double hy_,
                      double ox_=?, double oy_=?) except *
    cpdef void init3D(self, uint32_t nx_, uint32_t ny_, uint32_t nz_, double hx_,
                      double hy_, double hz_, double ox_=?, double oy_=?,
                      double oz_=?) except *
    cpdef uint8_t maxVal(self) except *
    cpdef uint8_t minVal(self) except *
    cpdef uint8_t reduceVal(self) except *
    cpdef void set1D(self, uint8_t[:] inp, int ti=?, int tj=?) except *
    cpdef void set2D(self, uint8_t[:, :] inp, int ti=?, int tj=?) except *
    cpdef void set3D(self, uint8_t[:, :, :] inp, int ti=?, int tj=?) except *
    cpdef uint8_t[:] get_data_1d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint8_t[:, :] get_data_2d(self, uint32_t ti=?, uint32_t tj=?) except *
    cpdef uint8_t[:, :, :] get_data_3d(self, uint32_t ti=?, uint32_t tj=?) except *
    cdef void get_tile_data(self, uint32_t ti, uint32_t tj, vector[uint8_t]& vec) except *
    cpdef void mapVector(self, _Vector_d v, string script, size_t parameters,
                         string widthPropertyName, string levelPropertyName) except *
    cpdef void rasterise(self, _Vector_d v, string script, size_t parameters,
        string levelPropertyName) except *
    cpdef _Vector_d cellCentres(self, bool mapValues=?)
    cpdef _Vector_d cellPolygons(self, bool mapValues=?)
    cpdef _Vector_d vectorise(self, uint8_t[:] contourValue,
                              string proprtyName,
                              size_t parameters, object noDataValue=?)
    cpdef uint8_t getCellValue(self, uint32_t i, uint32_t j=?, uint32_t k=?) except *
    cpdef uint8_t getNearestValue(self, double x, double y=?, double z=?) except *
    # cpdef uint32_t getBilinearValue(self, double x, double y=?, double z=?)
    cpdef void setCellValue(self, uint8_t value, uint32_t i, uint32_t j=?,
                            uint32_t k=?) except *
    cpdef void setAllCellValues(self, uint8_t c) except *
    cpdef uint8_t getRequiredNeighbours(self) except *
    cpdef void setRequiredNeighbours(self, uint8_t requiredNeighbours) except *
    cpdef ReductionType getReductionType(self) except *
    cpdef void setReductionType(self, ReductionType other) except *
    cpdef bool getNeedsStatus(self) except *
    cpdef void setNeedsStatus(self, bool other) except *
    cpdef bool getNeedsWrite(self) except *
    cpdef void setNeedsWrite(self, bool other) except *
    cpdef bool resize2D(self, uint32_t nx, uint32_t ny, uint32_t tox, uint32_t toy) except *
    cpdef void setOrigin_z(self, double oz) except *
    cpdef _Coordinate_d ijk2xyz(self, uint32_t i, uint32_t j=?, uint32_t k=?)
    cpdef list xyz2ijk(self, double x, double y=?, double z=?)
    cpdef _cyRasterBase_d get_raster_base(self)
    cpdef cl_uint[:, :] searchTiles(self, _BoundingBox_d bbox) except *
    cdef void _searchTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *
    cpdef cl_uint[:, :] nearestTiles(self, _BoundingBox_d bbox) except *
    cdef void _nearestTiles(self, BoundingBox[double], vector[shared_ptr[GeometryBase[double]]]&) except *


cdef class _RasterPtrList_d:

    cdef raster_ptr_list_d *thisptr
    cdef int n_raster
    cpdef int get_number_of_rasters(self)
    cpdef _cyRasterBase_d get_raster_from_vec(self, size_t i)
    cpdef void clear(self)


cdef class _RasterPtrList_f:

    cdef raster_ptr_list_f *thisptr
    cdef int n_raster
    cpdef int get_number_of_rasters(self)
    cpdef _cyRasterBase_f get_raster_from_vec(self, size_t i)
    cpdef void clear(self)


cdef class _RasterBaseList_d:

    cdef raster_base_list_d *thisptr
    cdef int n_raster
    cpdef int get_number_of_rasters(self)
    cdef void _add_raster(self, RasterBase[double]* other)
    cdef void _add_df_handler(self, RasterBase[double]* other)
    cpdef _cyRasterBase_d get_raster_from_vec(self, size_t i)
    cpdef void clear(self)


cdef class _RasterBaseList_f:

    cdef raster_base_list_f *thisptr
    cdef int n_raster
    cpdef int get_number_of_rasters(self)
    cdef void _add_raster(self, RasterBase[float]* other)
    cdef void _add_df_handler(self, RasterBase[float]* other)
    cpdef _cyRasterBase_f get_raster_from_vec(self, size_t i)
    cpdef void clear(self)


cdef class DataFileHandler_f:

    cdef public _cyRaster_f cy_raster_obj
    cdef shared_ptr[pyFileHandler[float, float]] thisptr
    cdef float[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[float] tdim,
        vector[float] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)


cdef class DataFileHandler_f_i:

    cdef public _cyRaster_f_i cy_raster_obj
    cdef shared_ptr[pyFileHandler[uint32_t, float]] thisptr
    cdef uint32_t[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[float] tdim,
                                     vector[uint32_t] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)


cdef class DataFileHandler_f_byt:

    cdef public _cyRaster_f_byt cy_raster_obj
    cdef shared_ptr[pyFileHandler[uint8_t, float]] thisptr
    cdef uint8_t[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[float] tdim,
                                     vector[uint8_t] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)


cdef class DataFileHandler_d:

    cdef public _cyRaster_d cy_raster_obj
    cdef shared_ptr[pyFileHandler[double, double]] thisptr
    cdef double[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[double] tdim,
                                     vector[double] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)


cdef class DataFileHandler_d_i:

    cdef public _cyRaster_d_i cy_raster_obj
    cdef shared_ptr[pyFileHandler[uint32_t, double]] thisptr
    cdef uint32_t[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[double] tdim,
                                     vector[uint32_t] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)


cdef class DataFileHandler_d_byt:

    cdef public _cyRaster_d_byt cy_raster_obj
    cdef shared_ptr[pyFileHandler[uint8_t, double]] thisptr
    cdef uint8_t[:, :, :] buf_arr
    cdef int tidx
    cdef double time
    cdef public object class_obj, _file_handler_obj, _file_name
    cdef object cls_capsule, func_capsule
    cpdef void read(self, bool thredds=?, bool use_pydap=?,
                    str modelProjection=?, bool read_projection=?,
                    object layers=?, object dims=?) except *
    cpdef void write(self, object fileName, string jsonConfig)
    cpdef void update_time(self, int tidx)
    cpdef double time_from_index(self, int tidx)
    cpdef void set_time_bounds(self, object start_time=?, object end_time=?,
                               object dt_str=?)
    cpdef int index_from_time(self, double timestamp)
    cpdef int get_left_index(self, double timestamp)
    cpdef int get_right_index(self, double timestamp)
    cpdef double get_time(self)
    cpdef int get_time_index(self)
    cpdef int get_max_time_index(self)
    cdef pyException setDataFunction(self, TileDimensions[double] tdim,
                                     vector[uint8_t] &v) except * with gil
    cpdef void setFileInputHandler(self)
    cpdef void setFileOutputHandler(self)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef void setInterpolationType(self, size_t interpolation_)
    cpdef _ProjectionParameters_d getProjectionParameters(self)

cpdef bool equalSpatialMetrics_d(_Dimensions_d l, _Dimensions_d r) except *
cpdef bool equalSpatialMetrics_f(_Dimensions_f l, _Dimensions_f r) except *
cpdef bool equalSpatialMetrics2D_d(_Dimensions_d l, _Dimensions_d r) except *
cpdef bool equalSpatialMetrics2D_f(_Dimensions_f l, _Dimensions_f r) except *
cpdef void sortColumns_d(_cyRaster_d r) except *
cpdef void sortColumns_f(_cyRaster_f r) except *
cpdef void sortColumns_d_i(_cyRaster_d_i r) except *
cpdef void sortColumns_f_i(_cyRaster_f_i r) except *
cpdef void sortColumns_d_byt(_cyRaster_d_byt r) except *
cpdef void sortColumns_f_byt(_cyRaster_f_byt r) except *
