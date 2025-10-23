# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#distutils: language=c++
#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: embedsignature=True
# cython: language_level=3

from cpython.pycapsule cimport PyCapsule_New, PyCapsule_GetPointer
from cpython.pycapsule cimport PyCapsule_GetName, PyCapsule_IsValid
from cython.operator import dereference as deref
from libcpp.string cimport string
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libcpp cimport bool, nullptr_t
from libcpp.map cimport map as cpp_map
from libcpp.pair cimport pair
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, make_shared, unique_ptr
from libcpp.memory cimport static_pointer_cast
from libcpp.cast cimport reinterpret_cast
from libcpp.list cimport list as cpp_list
import numpy as np
cimport cython
cimport numpy as np
from ..core._cy_property cimport _PropertyMap, PropertyMap, PropertyType
from ..raster._cy_raster cimport _cyRasterBase_d, _cyRasterBase_f
from ..raster._cy_raster cimport _cyRaster_d, _cyRaster_f, GeometryType
from ..raster._cy_raster cimport _cyRaster_d_i, _cyRaster_f_i
from ..raster._cy_raster cimport _cyRaster_d_byt, _cyRaster_f_byt
from ..core._cy_projection cimport _ProjectionParameters_d

np.import_array()

ctypedef uint8_t cl_uchar
ctypedef uint16_t cl_uint16
ctypedef uint32_t cl_uint
ctypedef uint64_t cl_ulong

cdef extern from "utils.h":
    void cy_copy[T](T& a, T& b)
    void cy_assign[T](T& a, T& b)

cdef extern from "gs_solver.h" namespace "Geostack":
    T getNullValue[T]() nogil

cdef extern from "gs_raster.h" namespace "Geostack":
    cdef cppclass RasterBase[T](PropertyMap):
        pass

    cdef cppclass Raster[R, T](RasterBase[T]):
        pass

cdef extern from "gs_projection.h" namespace "Geostack":
    cdef cppclass ProjectionParameters[C]:
        pass

cdef extern from "gs_vector.h" namespace "Geostack":
    cdef cppclass GeometryBase[T]:
        BoundingBox[T] getBounds() except +
        bool isContainer() except +
        cl_uint getID() except +
        bool isType(size_t type_) except +

cdef extern from "gs_geometry.h" namespace "Geostack":
    cdef cppclass Box[T](GeometryBase[T]):
        Box() except +
        Box(BoundingBox[T]) except +
        BoundingBox[T] getBounds() except +

    cdef cppclass RTreeNode[T](Box[T]):
        RTreeNode() except +
        bool isContainer() except +
        void fitBounds(const BoundingBox[T]&) except +
        void fitBoundsToNodes() except +

    cdef cppclass RTree[T]:
        RTree() except +
        void clear() except +
        void insert(shared_ptr[GeometryBase[T]] gty) except +
        void search(BoundingBox[T] bounds, vector[shared_ptr[GeometryBase[T]]] &searchGeometry,
                    size_t types) except +
        void nearest(BoundingBox[T] bounds, vector[shared_ptr[GeometryBase[T]]] &searchGeometry,
                     size_t types) except +
        BoundingBox[T] getBounds() except +

cdef extern from "gs_vector.h" namespace "Geostack::RelationType":
    cdef enum RelationType "Geostack::RelationType::Type":
        NoRelation "None" = 0
        Neighbour = 1

cdef extern from "gs_kdtree.h" namespace "Geostack":
    cdef cppclass KDTreeNode[T]:
        KDTreeNode() except +
        KDTreeNode(
            const shared_ptr[VectorGeometry[T]] geom,
            const shared_ptr[Coordinate[T]] &coord
        ) except +
        KDTreeNode(
            const shared_ptr[VectorGeometry[T]] geom,
            const shared_ptr[Coordinate[T]] &coord,
            const shared_ptr[KDTreeNode[T]] left,
            const shared_ptr[KDTreeNode[T]] right
        ) except +

    cdef enum class SearchStrategy:
        pass

    cdef cppclass KDTree[T]:
        KDTree() except +
        KDTree(const Vector[T] &vec) except +
        KDTree(const Vector[T] &vec, const vector[cl_uint] &idxs) except +
        void clear() except +
        void build(const Vector[T] &vec) except +
        void build(const Vector[T] &vec, const vector[cl_uint] &idxs) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const Coordinate[T] &coord
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const Coordinate[T] &coord,
            const ProjectionParameters[double] &coordProj
        ) except +
        shared_ptr[Vector[T]] nearest(
            const Vector[T] &vec,
            const SearchStrategy& searchStrategy
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const Vector[T] &vec,
            const cl_uint idx
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const Vector[T] &vec,
            const vector[cl_uint] &idxs
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const BoundingBox[T] &bbox
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const BoundingBox[T] &bbox,
            const ProjectionParameters[double] &bboxProj
        ) except +
        shared_ptr[VectorGeometry[T]] nearest(
            const RasterBase[T] &raster
        ) except +
        void nearestN(
            const Coordinate[T] &coord,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const Coordinate[T] &coord,
            const size_t n,
            const ProjectionParameters[double] &coordProj,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const Vector[T] &vec,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const Vector[T] &vec,
            const size_t n,
            const cl_uint idx,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const Vector[T] &vec,
            const size_t n,
            const vector[cl_uint] &idxs,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const BoundingBox[T] &bbox,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const BoundingBox[T] &bbox,
            const size_t n,
            const ProjectionParameters[double] &bboxProj,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestN(
            const RasterBase[T] &raster,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        size_t getGeomCount() except +
        size_t getNodeCount() except +
        ProjectionParameters[double] getProjectionParameters() except +
        void print() except +
        void print(const size_t indentAmount) except +

cdef extern from "gs_vector.h" namespace "Geostack":
    cdef cppclass Coordinate[T]:
        Coordinate() except +
        Coordinate(T p, T q, T r, T s) except +
        Coordinate(Coordinate[T] &c) except +
        T magnitudeSquared() except +
        Coordinate[T] max_c "max"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] min_c "min"(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T] centroid(Coordinate[T] &a, Coordinate[T] &b) except +
        Coordinate[T]& operator=(Coordinate[T] &c) except +
        T p, q, r, s
        string geoHashEnc32
        string getGeoHash()

    bool operator==[T](Coordinate[T] &a, Coordinate[T] &b) except +
    bool operator!=[T](Coordinate[T] &a, Coordinate[T] &b) except +
    Coordinate[T]& operator+[T](Coordinate[T] &a, Coordinate[T] &b) except +
    Coordinate[T]& operator-[T](Coordinate[T] &a, Coordinate[T] &b) except +

    cdef cppclass BoundingBox[T]:
        BoundingBox() except +
        BoundingBox(BoundingBox[T] &b) except +
        BoundingBox(Coordinate[T], Coordinate[T]) except +
        Coordinate[T] min_c "min"
        Coordinate[T] max_c "max"
        void reset() except +
        void extend2D(T) except +
        void extend2D(Coordinate[T]) except +
        void extend2D(const BoundingBox[T]&) except +
        void extend(Coordinate[T]) except +
        void extend(const BoundingBox[T] &b) except +
        T area2D() except +
        T minimumDistanceSqr(BoundingBox[T] &b) except +
        T centroidDistanceSqr(const BoundingBox[T] &b) except +
        Coordinate[T] centroid() except +
        Coordinate[T] extent() except +
        uint64_t createZIndex(Coordinate[T] c) except +
        BoundingBox[T] convert(ProjectionParameters[double] this, ProjectionParameters[double] other) except +
        BoundingBox[T] convert(string this, string other) except +
        uint64_t quadrant(Coordinate[T] c) except +
        bool contains(const Coordinate[T] c) except +
        @staticmethod
        bool bbox_contains_coordinate "boundingBoxContains"(BoundingBox[T] A, Coordinate[T] c) except +
        @staticmethod
        bool bbox_contains_bbox "boundingBoxContains"(BoundingBox[T] A, BoundingBox[T] B) except +
        @staticmethod
        bool boundingBoxIntersects(BoundingBox[T] A, BoundingBox[T] B) except +
        const BoundingBox[T] geoHashBounds
        Vector[T] toVector() except +

    bool operator==[T](BoundingBox[T] &a, BoundingBox[T] &b) except +
    bool operator!=[T](BoundingBox[T] &a, BoundingBox[T] &b) except +

    cdef cppclass VectorGeometry[T](GeometryBase[T]):
        void addVertex(cl_uint v_) except +
        void setID(cl_uint id_) except +
        VectorGeometry[T]* clone() except +
        void updateVector(Vector[T] &v, cl_uint index) except +
        void updateBounds(const Vector[T] &v) except +
        bool within(const Vector[T] &v, const BoundingBox[T] &b) except +
        bool intercepts(const Vector[T] &v, const BoundingBox[T] &b) except +
        bool encloses(const Vector[T] &v, const BoundingBox[T] &b) except +

    cdef cppclass Point[T](VectorGeometry[T]):
        pass

    cdef cppclass LineString[T](VectorGeometry[T]):
        pass

    cdef cppclass Polygon[T](VectorGeometry[T]):
        vector[cl_uint]& getVertexIndexes() except +
        vector[cl_uint]& getSubIndexes() except +
        vector[BoundingBox[T]]& getSubBounds() except +

    cdef cppclass Vector[T]:
        Vector() except +
        Vector (string name) except +
        Vector(const Vector &v) except +
        bool operator==(Vector &v) except +
        Vector& iadd "operator+=" (Vector &v) except +

        cl_uint addPoint(Coordinate[T] c_) except +
        cl_uint addLineString(vector[Coordinate[T]] cs_) except +
        cl_uint addPolygon(vector[vector[Coordinate[T]]] pcs_) except +
        #cl_uint addGeometry(shared_ptr[VectorGeometry[T]] v) except + nogil

        void updatePointIndex(cl_uint index) except +
        void updateLineStringIndex(cl_uint index) except +
        void updatePolygonIndex(cl_uint index) except +
        void clear() except +
        void buildTree() except +
        void buildKDTree() except +
        size_t getVertexSize() except +

        Coordinate[T]& getCoordinate(cl_uint index) except +
        PropertyMap& getProperties() except +
        cl_uint clone(cl_uint) except +

        vector[cl_uint]& getGeometryIndexes() except +IndexError nogil
        vector[cl_uint]& getPointIndexes() except +IndexError nogil
        vector[cl_uint]& getLineStringIndexes() except +IndexError nogil
        vector[cl_uint]& getPolygonIndexes() except +IndexError nogil
        shared_ptr[VectorGeometry[T]]& getGeometry(cl_uint index) except + nogil

        Coordinate[T] getPointCoordinate(cl_uint index) except +
        vector[Coordinate[T]] getLineStringCoordinates(cl_uint index) except +
        vector[Coordinate[T]] getPolygonCoordinates(cl_uint index) except +
        vector[cl_uint]& getPolygonVertexIndexes(cl_uint index) except +IndexError nogil
        vector[cl_uint]& getPolygonSubIndexes(cl_uint index) except +IndexError nogil
        vector[BoundingBox[T]]& getPolygonSubBounds(cl_uint index) except +IndexError nogil

        bool hasProperty(string name) except +
        void addProperty(string name) except +
        void convertProperty[P](string name) except +
        void removeProperty(string name) except +
        PropertyType getPropertyType(string name) except +
        void setGlobalProperty[P](string name, P v) except +IndexError
        void setProperty[P](cl_uint index, string name, P v) except +IndexError
        void setPropertyVector[P](string name, P v) except +IndexError
        P getGlobalProperty[P](string name) except +IndexError
        P getProperty[P](cl_uint index, string name) except +IndexError
        P& getPropertyVectorRef[P](cl_uint index, string name) except +IndexError
        P& getPropertyVectorsRef[P](string name) except +IndexError
        bool isPropertyNumeric(string name) except +

        void setProjectionParameters(ProjectionParameters[double] proj_) except +
        void setProjectionParameters(string proj_) except +
        ProjectionParameters[double] getProjectionParameters()
        Vector[T] convert(ProjectionParameters[double] proj_to) except +
        Vector[T] convert(size_t geometryType) except +
        Vector[T] convert(string proj_to) except +
        Vector[T] convertProjection(ProjectionParameters[double] proj_to) except +
        Vector[T] convertGeometryType(size_t geometryType) except +

        Vector[T] region(BoundingBox[T] bounds, size_t geometryTypes) except +
        Vector[T] nearest(BoundingBox[T] bounds, size_t geometryTypes) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const Coordinate[T] &coord
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const Coordinate[T] &coord,
            const ProjectionParameters[double] &coordProj
        ) except +
        shared_ptr[Vector[T]] nearestGeom(
            const Vector[T] &vec,
            const SearchStrategy& searchStrategy
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const Vector[T] &vec,
            const cl_uint idx
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const Vector[T] &vec,
            const vector[cl_uint] &idxs
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const BoundingBox[T] &bbox
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const BoundingBox[T] &bbox,
            const ProjectionParameters[double] &bboxProj
        ) except +
        shared_ptr[VectorGeometry[T]] nearestGeom(
            const RasterBase[T] &raster
        ) except +
        void nearestNGeoms(
            const Coordinate[T] &coord,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const Coordinate[T] &coord,
            const size_t n,
            const ProjectionParameters[double] &coordProj,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const Vector[T] &vec,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const Vector[T] &vec,
            const size_t n,
            const cl_uint idx,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const Vector[T] &vec,
            const size_t n,
            const vector[cl_uint] &idxs,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const BoundingBox[T] &bbox,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const BoundingBox[T] &bbox,
            const size_t n,
            const ProjectionParameters[double] &bboxProj,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        void nearestNGeoms(
            const RasterBase[T] &raster,
            const size_t n,
            vector[shared_ptr[VectorGeometry[T]]] &nearestGeoms
        ) except +
        vector[shared_ptr[GeometryBase[T]]] attached(Coordinate[T] coord,
                                                     size_t geometryTypes) except +
        void regionGeometryIndices(BoundingBox[T] bounds, vector[shared_ptr[GeometryBase[T]]]& geomList,
                                   size_t geometryTypes) except +

        void deduplicateVertices()
        Raster[R, T] mapDistanceOnBounds "mapDistance" [R](T resolution,
                                                           string script,
                                                           size_t geometryTypes,
                                                           BoundingBox[T] bounds) except + nogil
        Raster[R, T] mapDistanceOnRaster "mapDistance" [R](RasterBase[T] &rasterBase,
                                                           string script,
                                                           size_t geometryTypes) except + nogil
        Raster[R, T] rasteriseOnBounds  "rasterise"[R](T resolution, string script, size_t geometryTypes,
                                                       BoundingBox[T] bounds) except + nogil
        Raster[uint32_t, T] rasteriseOnBounds_uint  "rasterise"[uint32_t](T resolution, string script, size_t geometryTypes,
                                                                          BoundingBox[T] bounds) except + nogil
        Raster[uint8_t, T] rasteriseOnBounds_byt  "rasterise"[uint8_t](T resolution, string script, size_t geometryTypes,
                                                                       BoundingBox[T] bounds) except + nogil
        Raster[R, T] rasteriseOnRaster "rasterise"[R](RasterBase[T] &rasterBase, string script,
                                                      size_t geometryTypes) except + nogil
        Raster[uint32_t, T] rasteriseOnRaster_uint "rasterise"[uint32_t](RasterBase[T] &rasterBase, string script,
                                                                         size_t geometryTypes) except + nogil
        Raster[uint8_t, T] rasteriseOnRaster_byt "rasterise"[uint8_t](RasterBase[T] &rasterBase, string script,
                                                                      size_t geometryTypes) except + nogil

        void pointSample[R](Raster[R, T] &r) except +
        BoundingBox[T] getBounds() except +
        bool hasData() except +
        size_t getPointCount() except +
        size_t getLineStringCount() except +
        size_t getPolygonCount() except +
        size_t getGeometryBaseCount() except +
        void runScript(string script) except +
        void buildRelations(size_t geometryType, size_t relationType) except +
        size_t getRelationSize(cl_uint gid) except +
        cl_uint getRelationData(cl_uint gid, cl_uint idx) except +
        void read(string fileName, string jsonConfig) except +
        void write(string fileName, size_t writeType,
                   bool enforceProjection, bool writeNullProperties) except +

cdef extern from "pyFileHandler.h" namespace "Geostack::pyGeostack":
    void add_vector_ptr_to_vec[C](vector[shared_ptr[Vector[C]]]&, shared_ptr[Vector[C]]&) except+
    shared_ptr[Vector[C]] get_vector_ptr_from_vec[C](vector[shared_ptr[Vector[C]]]&, size_t i) except+

cdef extern from "<utility>" namespace "std" nogil:
    cdef shared_ptr[Vector[double]] move(shared_ptr[Vector[double]])
    cdef shared_ptr[Vector[float]] move(shared_ptr[Vector[float]])
    cdef shared_ptr[BoundingBox[double]] move(shared_ptr[BoundingBox[double]] bb)
    cdef shared_ptr[BoundingBox[float]] move(shared_ptr[BoundingBox[float]] bb)
    cdef vector[size_t]& move(vector[size_t]&)

ctypedef Coordinate[double] _coordinate_d
ctypedef Coordinate[float] _coordinate_f
ctypedef pair[_coordinate_d, _coordinate_d] _coordinatePair_d
ctypedef pair[_coordinate_f, _coordinate_f] _coordinatePair_f
ctypedef BoundingBox[double] _boundingBox_d
ctypedef BoundingBox[float] _boundingBox_f
ctypedef shared_ptr[_boundingBox_d] _bbox_ptr_d
ctypedef shared_ptr[_boundingBox_f] _bbox_ptr_f
ctypedef vector[_boundingBox_d] _bbox_list_d
ctypedef vector[_boundingBox_f] _bbox_list_f
ctypedef vector[cl_uint] _index_list
ctypedef shared_ptr[GeometryBase[float]] _geometryBase_ptr_f
ctypedef shared_ptr[GeometryBase[double]] _geometryBase_ptr_d
ctypedef shared_ptr[RTreeNode[float]] _rtreeNode_ptr_f
ctypedef shared_ptr[RTreeNode[double]] _rtreeNode_ptr_d
ctypedef shared_ptr[VectorGeometry[float]]* vector_geometry_ptr_f
ctypedef shared_ptr[VectorGeometry[double]]* vector_geometry_ptr_d
ctypedef shared_ptr[Vector[double]] VectorPtr_d
ctypedef shared_ptr[Vector[float]] VectorPtr_f
ctypedef vector[VectorPtr_d] vector_ptr_list_d
ctypedef vector[VectorPtr_f] vector_ptr_list_f


cdef class _RTree_f:
    cdef shared_ptr[RTree[float]] thisptr
    cpdef void insert(self, _Vector_f v, cl_uint idx) except *
    cdef void _insert(self, shared_ptr[VectorGeometry[float]]& v) except *
    cpdef cl_uint[:] search(self, _BoundingBox_f bbox,
                      size_t types) except *
    cdef void _search(self, BoundingBox[float],
                      vector[_geometryBase_ptr_f]&,
                      size_t types) except *
    cpdef cl_uint[:] nearest(self, _BoundingBox_f bbox,
                      size_t types) except *
    cdef void _nearest(self, BoundingBox[float],
                      vector[_geometryBase_ptr_f]&,
                      size_t types) except *
    cpdef _BoundingBox_f getBounds(self)
    cpdef void clear(self) except *

cdef class _RTree_d:
    cdef shared_ptr[RTree[double]] thisptr
    cpdef void insert(self, _Vector_d v, cl_uint idx) except *
    cdef void _insert(self, shared_ptr[VectorGeometry[double]]& v) except *
    cpdef cl_uint[:] search(self, _BoundingBox_d bbox,
                      size_t types) except *
    cdef void _search(self, BoundingBox[double],
                      vector[_geometryBase_ptr_d]&,
                      size_t types) except *
    cpdef cl_uint[:] nearest(self, _BoundingBox_d bbox,
                      size_t types) except *
    cdef void _nearest(self, BoundingBox[double],
                      vector[_geometryBase_ptr_d]&,
                      size_t types) except *
    cpdef _BoundingBox_d getBounds(self)
    cpdef void clear(self) except *

cdef class _KDTree_f:
    cdef shared_ptr[KDTree[float]] thisptr
    cpdef void clear(self) except *
    cpdef void build(self, _Vector_f v) except *
    cpdef void buildWithIndexes(self, _Vector_f v, cl_uint[:] idxs) except *
    cpdef cl_uint nearestFromCoord(self, _Coordinate_f coord) except *
    cpdef cl_uint nearestFromCoordProj(self, _Coordinate_f coord, _ProjectionParameters_d coordProj) except *
    cpdef _Vector_f nearestFromVec(self, _Vector_f v, SearchStrategy searchStrategy)
    cpdef cl_uint nearestFromGeom(self, _Vector_f v, cl_uint idx) except *
    cpdef cl_uint nearestFromGeoms(self, _Vector_f v, cl_uint[:] idxs) except *
    cpdef cl_uint nearestFromBBox(self, _BoundingBox_f bbox) except *
    cpdef cl_uint nearestFromBBoxProj(self, _BoundingBox_f bbox, _ProjectionParameters_d bboxProj) except *
    cpdef cl_uint nearestFromRaster(self, _cyRasterBase_f raster) except *
    cpdef cl_uint[:] nearestNFromCoord(self, _Coordinate_f coord, size_t n) except *
    cpdef cl_uint[:] nearestNFromCoordProj(self, _Coordinate_f coord, size_t n, _ProjectionParameters_d coordProj) except *
    cpdef cl_uint[:] nearestNFromVec(self, _Vector_f v, size_t n) except *
    cpdef cl_uint[:] nearestNFromGeom(self, _Vector_f v, size_t n, cl_uint idx) except *
    cpdef cl_uint[:] nearestNFromGeoms(self, _Vector_f v, size_t n, cl_uint[:] idxs) except *
    cpdef cl_uint[:] nearestNFromBBox(self, _BoundingBox_f bbox, size_t n) except *
    cpdef cl_uint[:] nearestNFromBBoxProj(self, _BoundingBox_f bbox, size_t n, _ProjectionParameters_d bboxProj) except *
    cpdef cl_uint[:] nearestNFromRaster(self, _cyRasterBase_f raster, size_t n) except *
    cpdef size_t getGeomCount(self) except *
    cpdef size_t getNodeCount(self) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef void print(self) except *
    cpdef void printWithIndent(self, size_t indentAmount) except *

cdef class _KDTree_d:
    cdef shared_ptr[KDTree[double]] thisptr
    cpdef void clear(self) except *
    cpdef void build(self, _Vector_d v) except *
    cpdef void buildWithIndexes(self, _Vector_d v, cl_uint[:] idxs) except *
    cpdef cl_uint nearestFromCoord(self, _Coordinate_d coord) except *
    cpdef cl_uint nearestFromCoordProj(self, _Coordinate_d coord, _ProjectionParameters_d coordProj) except *
    cpdef _Vector_d nearestFromVec(self, _Vector_d v, SearchStrategy searchStrategy)
    cpdef cl_uint nearestFromGeom(self, _Vector_d v, cl_uint idx) except *
    cpdef cl_uint nearestFromGeoms(self, _Vector_d v, cl_uint[:] idxs) except *
    cpdef cl_uint nearestFromBBox(self, _BoundingBox_d bbox) except *
    cpdef cl_uint nearestFromBBoxProj(self, _BoundingBox_d bbox, _ProjectionParameters_d bboxProj) except *
    cpdef cl_uint nearestFromRaster(self, _cyRasterBase_d raster) except *
    cpdef cl_uint[:] nearestNFromCoord(self, _Coordinate_d coord, size_t n) except *
    cpdef cl_uint[:] nearestNFromCoordProj(self, _Coordinate_d coord, size_t n, _ProjectionParameters_d coordProj) except *
    cpdef cl_uint[:] nearestNFromVec(self, _Vector_d v, size_t n) except *
    cpdef cl_uint[:] nearestNFromGeom(self, _Vector_d v, size_t n, cl_uint idx) except *
    cpdef cl_uint[:] nearestNFromGeoms(self, _Vector_d v, size_t n, cl_uint[:] idxs) except *
    cpdef cl_uint[:] nearestNFromBBox(self, _BoundingBox_d bbox, size_t n) except *
    cpdef cl_uint[:] nearestNFromBBoxProj(self, _BoundingBox_d bbox, size_t n, _ProjectionParameters_d bboxProj) except *
    cpdef cl_uint[:] nearestNFromRaster(self, _cyRasterBase_d raster, size_t n) except *
    cpdef size_t getGeomCount(self) except *
    cpdef size_t getNodeCount(self) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef void print(self) except *
    cpdef void printWithIndent(self, size_t indentAmount) except *

cdef class IndexList:
    cdef vector[cl_uint] *thisptr
    cdef public int index
    cdef void c_copy(self, _index_list other)
    @staticmethod
    cdef IndexList from_index_list(_index_list this)
    cpdef bool contains(self, size_t index) except *

cdef class _Coordinate_d:
    cdef Coordinate[double] *thisptr
    cdef double p
    cdef double q
    cdef double r
    cdef double s
    cpdef set_p(self, double other)
    cpdef set_q(self, double other)
    cpdef set_r(self, double other)
    cpdef set_s(self, double other)
    cpdef double get_p(self)
    cpdef double get_q(self)
    cpdef double get_r(self)
    cpdef double get_s(self)
    cdef void c_copy(self, Coordinate[double] c)
    cpdef _Coordinate_d maxCoordinate(self, _Coordinate_d this, _Coordinate_d other)
    cpdef _Coordinate_d minCoordinate(self, _Coordinate_d this, _Coordinate_d other)
    cpdef _Coordinate_d centroid(self, _Coordinate_d this, _Coordinate_d other)
    cpdef double magnitudeSquared(self)
    cpdef string getGeoHash(self)


cdef class _Coordinate_f:
    cdef Coordinate[float] *thisptr
    cdef float p
    cdef float q
    cdef float r
    cdef float s
    cpdef set_p(self, float other)
    cpdef set_q(self, float other)
    cpdef set_r(self, float other)
    cpdef set_s(self, float other)
    cpdef float get_p(self)
    cpdef float get_q(self)
    cpdef float get_r(self)
    cpdef float get_s(self)
    cdef void c_copy(self, Coordinate[float] c)
    cpdef _Coordinate_f maxCoordinate(self, _Coordinate_f this, _Coordinate_f other)
    cpdef _Coordinate_f minCoordinate(self, _Coordinate_f this, _Coordinate_f other)
    cpdef _Coordinate_f centroid(self, _Coordinate_f this, _Coordinate_f other)
    cpdef float magnitudeSquared(self)
    cpdef string getGeoHash(self)

cdef class _BoundingBox_d:
    cdef _bbox_ptr_d thisptr
    cdef void c_copy(self, _boundingBox_d other)
    cpdef _Coordinate_d centroid(self)
    cpdef _Coordinate_d extent(self)
    cpdef void extend_with_value(self, double other) except *
    cpdef void extend_with_coordinate_2d(self, _Coordinate_d other) except *
    cpdef void extend_with_bbox_2d(self, _BoundingBox_d other) except *
    cpdef void extend_with_coordinate(self, _Coordinate_d other) except *
    cpdef void extend_with_bbox(self, _BoundingBox_d other) except *
    cpdef double area2D(self) except *
    cpdef double minimumDistanceSqr(self, _BoundingBox_d other) except *
    cpdef double centroidDistanceSqr(self, _BoundingBox_d other) except *
    cpdef void reset(self) except *
    cpdef _BoundingBox_d convert(self, _ProjectionParameters_d this, _ProjectionParameters_d other)
    cpdef _BoundingBox_d convert_str(self, string this, string other)
    cpdef bool contains(self, _Coordinate_d c) except *
    @staticmethod
    cdef bool _bbox_contains_coordinate(BoundingBox[double] A, Coordinate[double] c) except *
    @staticmethod
    cdef bool _bbox_contains_bbox(BoundingBox[double] A, BoundingBox[double] B) except *
    @staticmethod
    cdef bool _boundingBoxIntersects(BoundingBox[double] A, BoundingBox[double] B) except *
    cpdef _Vector_d toVector(self)
    cpdef uint64_t quadrant(self, _Coordinate_d c) except *
    cpdef void set_max(self, _Coordinate_d other) except *
    cpdef void set_min(self, _Coordinate_d other) except *

cdef class _BoundingBox_f:
    cdef _bbox_ptr_f thisptr
    cdef void c_copy(self, _boundingBox_f other)
    cpdef _Coordinate_f centroid(self)
    cpdef _Coordinate_f extent(self)
    cpdef void extend_with_value(self, float other) except *
    cpdef void extend_with_coordinate_2d(self, _Coordinate_f other) except *
    cpdef void extend_with_bbox_2d(self, _BoundingBox_f other) except *
    cpdef void extend_with_coordinate(self, _Coordinate_f other) except *
    cpdef void extend_with_bbox(self, _BoundingBox_f other) except *
    cpdef float area2D(self) except *
    cpdef float minimumDistanceSqr(self, _BoundingBox_f other) except *
    cpdef float centroidDistanceSqr(self, _BoundingBox_f other) except *
    cpdef void reset(self) except *
    cpdef _BoundingBox_f convert(self, _ProjectionParameters_d this, _ProjectionParameters_d other)
    cpdef _BoundingBox_f convert_str(self, string this, string other)
    cpdef bool contains(self, _Coordinate_f c) except *
    @staticmethod
    cdef bool _bbox_contains_coordinate(BoundingBox[float] A, Coordinate[float] c) except *
    @staticmethod
    cdef bool _bbox_contains_bbox(BoundingBox[float] A, BoundingBox[float] B) except *
    @staticmethod
    cdef bool _boundingBoxIntersects(BoundingBox[float] A, BoundingBox[float] B) except *
    cpdef _Vector_f toVector(self)
    cpdef uint64_t quadrant(self, _Coordinate_f c) except *
    cpdef void set_max(self, _Coordinate_f other) except *
    cpdef void set_min(self, _Coordinate_f other) except *

cdef class _Vector_d:
    cdef shared_ptr[Vector[double]] thisptr
    cpdef void assign(self, _Vector_d v) except *
    cdef void c_copy(self, Vector[double] v)
    cdef size_t _add_point(self, Coordinate[double] c_) except *
    cdef size_t _add_line_string(self, vector[Coordinate[double]] cs_) except *
    cdef size_t _add_polygon(self, vector[vector[Coordinate[double]]] pcs_) except *
    cpdef cl_uint clone(self, cl_uint idx) except *
    #cpdef cl_uint addGeometry(self, _Vector_d v, cl_uint idx) except *
    cpdef _Vector_d region(self, _BoundingBox_d other, size_t parameters)
    cpdef _Vector_d nearest(self, _BoundingBox_d other, size_t parameters)
    cpdef cl_uint nearestGeomFromCoord(self, _Coordinate_d coord)
    cpdef cl_uint nearestGeomFromCoordProj(self, _Coordinate_d coord, _ProjectionParameters_d coordProj)
    cpdef _Vector_d nearestGeomFromVec(self, _Vector_d v, SearchStrategy searchStrategy)
    cpdef cl_uint nearestGeomFromGeom(self, _Vector_d v, cl_uint idx)
    cpdef cl_uint nearestGeomFromGeoms(self, _Vector_d v, cl_uint[:] idxs)
    cpdef cl_uint nearestGeomFromBBox(self, _BoundingBox_d bbox)
    cpdef cl_uint nearestGeomFromBBoxProj(self, _BoundingBox_d bbox, _ProjectionParameters_d bboxProj)
    cpdef cl_uint nearestGeomFromRaster(self, _cyRasterBase_d raster)
    cpdef cl_uint[:] nearestNGeomsFromCoord(self, _Coordinate_d coord, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromCoordProj(self, _Coordinate_d coord, size_t n, _ProjectionParameters_d coordProj)
    cpdef cl_uint[:] nearestNGeomsFromVec(self, _Vector_d v, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromGeom(self, _Vector_d v, size_t n, cl_uint idx)
    cpdef cl_uint[:] nearestNGeomsFromGeoms(self, _Vector_d v, size_t n, cl_uint[:] idxs)
    cpdef cl_uint[:] nearestNGeomsFromBBox(self, _BoundingBox_d bbox, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromBBoxProj(self, _BoundingBox_d bbox, size_t n, _ProjectionParameters_d bboxProj)
    cpdef cl_uint[:] nearestNGeomsFromRaster(self, _cyRasterBase_d raster, size_t n)
    cpdef cl_uint[:] attached(self, _Coordinate_d other, size_t parameters) except *
    cpdef cl_uint[:] regionGeometryIndices(self, _BoundingBox_d bounds,
                                           size_t geometryTypes) except *
    cpdef size_t getVertexSize(self) except *
    cpdef _BoundingBox_d getBounds(self)
    cpdef _cyRaster_d mapDistanceOnBounds(self, double resolution, string script,
                                          size_t parameters, _BoundingBox_d bounds)
    cpdef _cyRaster_d mapDistanceOnRaster(self, _cyRasterBase_d r, string script,
                                          size_t parameters)
    cpdef _cyRaster_d rasteriseOnBounds(self, double resolution, string script,
                                        size_t parameters, _BoundingBox_d bounds)
    cpdef _cyRaster_d_i rasteriseOnBounds_uint(self, double resolution, string script,
                                               size_t parameters, _BoundingBox_d bounds)
    cpdef _cyRaster_d_byt rasteriseOnBounds_byt(self, double resolution, string script,
                                                size_t parameters, _BoundingBox_d bounds)
    cpdef _cyRaster_d rasteriseOnRaster(self, _cyRasterBase_d r, string script,
                                        size_t parameters)
    cpdef _cyRaster_d_i rasteriseOnRaster_uint(self, _cyRasterBase_d r, string script,
                                               size_t parameters)
    cpdef _cyRaster_d_byt rasteriseOnRaster_byt(self, _cyRasterBase_d r, string script,
                                                size_t parameters)
    cpdef void pointSample(self, _cyRaster_d r) except *
    cpdef _Vector_d convert_proj_string(self, string other)
    cpdef _Vector_d convert_projection(self, _ProjectionParameters_d other)
    cpdef _Vector_d convert_geometry_type(self, size_t geometryType)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef void updatePointIndex(self, size_t index) except *
    cpdef void updateLineStringIndex(self, size_t index) except *
    cpdef void updatePolygonIndex(self, size_t index) except *
    cpdef void clear(self) except *
    cpdef void buildTree(self) except *
    cpdef void buildKDTree(self) except *
    cpdef void addProperty(self, string name) except *
    cpdef bool hasProperty(self, string name) except *
    cpdef void removeProperty(self, string name) except *
    cpdef PropertyType getPropertyType(self, string name) except *
    cpdef _PropertyMap getProperties(self)
    cpdef IndexList getGeometryIndexes(self)
    cpdef IndexList getPointIndexes(self)
    cpdef IndexList getLineStringIndexes(self)
    cpdef IndexList getPolygonIndexes(self)
    cpdef IndexList getPolygonSubIndexes(self, size_t index)
    cpdef object get_geometry(self, cl_uint idx)
    cpdef size_t get_geometry_type(self, cl_uint idx) except *
    cpdef _Coordinate_d getCoordinate(self, size_t index)
    cpdef _Coordinate_d getPointCoordinate(self, size_t index)
    cpdef double[:, :] getLineStringCoordinates(self, size_t index) except *
    cpdef double[:, :] getPolygonCoordinates(self, size_t index) except *
    cdef _bbox_list_d getPolygonSubBounds(self, size_t index) except *
    cpdef bool hasData(self) except *
    cpdef size_t getPointCount(self) except *
    cpdef size_t getLineStringCount(self) except *
    cpdef size_t getPolygonCount(self) except *
    cpdef size_t getGeometryBaseCount(self) except *
    cpdef void runScript(self, string script) except *
    # method to get property
    cpdef int getProperty_int(self, cl_uint index, string name) except *
    cpdef uint32_t getProperty_uint(self, cl_uint index, string name) except *
    cpdef uint8_t getProperty_byt(self, cl_uint index, string name) except *
    cpdef double getProperty_dbl(self, cl_uint index, string name) except *
    cpdef double[:] getProperty_dbl_vector(self, cl_uint index, string name) except *
    cpdef string getProperty_str(self, cl_uint index, string name) except *
    # set all values of a property
    cdef void _setPropertyVector_str(self, string name, vector[string] v) except *
    cpdef void setPropertyVector_int(self, string name, int[:] v) except *
    cpdef void setPropertyVector_byt(self, string name, uint8_t[:] v) except *
    cpdef void setPropertyVector_uint(self, string name, uint32_t[:] v) except *
    cpdef void setPropertyVector_dbl(self, string name, double[:] v) except *
    # method to set property
    cpdef void setProperty_str(self, cl_uint index, string name, string v) except *
    cpdef void setProperty_int(self, cl_uint index, string name, int v) except *
    cpdef void setProperty_dbl(self, cl_uint index, string name, double v) except *
    cpdef void setProperty_uint(self, cl_uint index, string name, uint32_t v) except *
    cpdef void setProperty_byt(self, cl_uint index, string name, uint8_t v) except *
    cpdef void setProperty_dbl_vector(self, cl_uint index, string name, double[:] v) except *
    # method to convert property
    cpdef void convertProperty_int(self, string name) except *
    cpdef void convertProperty_uint(self, string name) except *
    cpdef void convertProperty_byt(self, string name) except *
    cpdef void convertProperty_dbl(self, string name) except *
    cpdef void convertProperty_str(self, string name) except *
    cpdef bool isPropertyNumeric(self, string name) except *
    # method to get property ref when value is vector
    cdef vector[double]* getPropertyVectorRef_dbl(self, cl_uint idx, string name) except *
    cdef vector[vector[double]]* getPropertyVectorsRef_dbl(self, string name) except *
    # method to get global property
    cpdef int getGlobalProperty_int(self, string name) except *
    cpdef string getGlobalProperty_str(self, string name) except *
    # method to set global property
    cpdef void setGlobalProperty_int(self, string name, int v) except *
    cpdef void setGlobalProperty_str(self, string name, string v) except *
    cpdef void buildRelations(self, size_t geometryType, size_t relationType=?) except *
    cpdef cl_uint getRelationSize(self, size_t geometryType) except *
    cpdef cl_uint getRelationData(self, cl_uint gid, cl_uint idx) except *
    cpdef cl_uint[:] getRelationDataArray(self, cl_uint gid) except *
    # IO methods
    cpdef void read(self, string fileName, string jsonConfig=?) except *
    cpdef void write(self, string fileName, size_t writeType=?,
                     bool enforceProjection=?, bool writeNullProperties=?) except *


cdef class _Vector_f:
    cdef shared_ptr[Vector[float]] thisptr
    cpdef void assign(self, _Vector_f v) except *
    cdef void c_copy(self, Vector[float] v)
    cdef size_t _add_point(self, Coordinate[float] c_) except *
    cdef size_t _add_line_string(self, vector[Coordinate[float]] cs_) except *
    cdef size_t _add_polygon(self, vector[vector[Coordinate[float]]] pcs_) except *
    cpdef cl_uint clone(self, cl_uint idx) except *
    #cpdef cl_uint addGeometry(self, _Vector_f v, cl_uint idx) except *
    cpdef _Vector_f region(self, _BoundingBox_f other, size_t parameters)
    cpdef _Vector_f nearest(self, _BoundingBox_f other, size_t parameters)
    cpdef cl_uint nearestGeomFromCoord(self, _Coordinate_f coord)
    cpdef cl_uint nearestGeomFromCoordProj(self, _Coordinate_f coord, _ProjectionParameters_d coordProj)
    cpdef _Vector_f nearestGeomFromVec(self, _Vector_f v, SearchStrategy searchStrategy)
    cpdef cl_uint nearestGeomFromGeom(self, _Vector_f v, cl_uint idx)
    cpdef cl_uint nearestGeomFromGeoms(self, _Vector_f v, cl_uint[:] idxs)
    cpdef cl_uint nearestGeomFromBBox(self, _BoundingBox_f bbox)
    cpdef cl_uint nearestGeomFromBBoxProj(self, _BoundingBox_f bbox, _ProjectionParameters_d bboxProj)
    cpdef cl_uint nearestGeomFromRaster(self, _cyRasterBase_f raster)
    cpdef cl_uint[:] nearestNGeomsFromCoord(self, _Coordinate_f coord, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromCoordProj(self, _Coordinate_f coord, size_t n, _ProjectionParameters_d coordProj)
    cpdef cl_uint[:] nearestNGeomsFromVec(self, _Vector_f v, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromGeom(self, _Vector_f v, size_t n, cl_uint idx)
    cpdef cl_uint[:] nearestNGeomsFromGeoms(self, _Vector_f v, size_t n, cl_uint[:] idxs)
    cpdef cl_uint[:] nearestNGeomsFromBBox(self, _BoundingBox_f bbox, size_t n)
    cpdef cl_uint[:] nearestNGeomsFromBBoxProj(self, _BoundingBox_f bbox, size_t n, _ProjectionParameters_d bboxProj)
    cpdef cl_uint[:] nearestNGeomsFromRaster(self, _cyRasterBase_f raster, size_t n)
    cpdef cl_uint[:] attached(self, _Coordinate_f other, size_t parameters) except *
    cpdef cl_uint[:] regionGeometryIndices(self, _BoundingBox_f bounds,
                                           size_t geometryTypes) except *
    cpdef size_t getVertexSize(self) except *
    cpdef _BoundingBox_f getBounds(self)
    cpdef _cyRaster_f mapDistanceOnBounds(self, float resolution, string script,
                                          size_t parameters, _BoundingBox_f bounds)
    cpdef _cyRaster_f mapDistanceOnRaster(self, _cyRasterBase_f r, string script,
                                          size_t parameters)
    cpdef _cyRaster_f rasteriseOnBounds(self, float resolution, string script,
                                        size_t parameters, _BoundingBox_f bounds)
    cpdef _cyRaster_f_i rasteriseOnBounds_uint(self, float resolution, string script,
                                               size_t parameters, _BoundingBox_f bounds)
    cpdef _cyRaster_f_byt rasteriseOnBounds_byt(self, float resolution, string script,
                                                size_t parameters, _BoundingBox_f bounds)
    cpdef _cyRaster_f rasteriseOnRaster(self, _cyRasterBase_f r, string script,
                                        size_t parameters)
    cpdef _cyRaster_f_i rasteriseOnRaster_uint(self, _cyRasterBase_f r, string script,
                                               size_t parameters)
    cpdef _cyRaster_f_byt rasteriseOnRaster_byt(self, _cyRasterBase_f r, string script,
                                               size_t parameters)
    cpdef void pointSample(self, _cyRaster_f r) except *
    cpdef _Vector_f convert_proj_string(self, string other)
    cpdef _Vector_f convert_projection(self, _ProjectionParameters_d other)
    cpdef _Vector_f convert_geometry_type(self, size_t geometryType)
    cpdef void setProjectionParameters(self, _ProjectionParameters_d proj_) except *
    cpdef void setProjectionParameters_str(self, string proj_) except *
    cpdef _ProjectionParameters_d getProjectionParameters(self)
    cpdef void updatePointIndex(self, size_t index) except *
    cpdef void updateLineStringIndex(self, size_t index) except *
    cpdef void updatePolygonIndex(self, size_t index) except *
    cpdef void clear(self) except *
    cpdef void buildTree(self) except *
    cpdef void buildKDTree(self) except *
    cpdef void addProperty(self, string name) except *
    cpdef bool hasProperty(self, string name) except *
    cpdef void removeProperty(self, string name) except *
    cpdef PropertyType getPropertyType(self, string name) except *
    cpdef _PropertyMap getProperties(self)
    cpdef IndexList getGeometryIndexes(self)
    cpdef IndexList getPointIndexes(self)
    cpdef IndexList getLineStringIndexes(self)
    cpdef IndexList getPolygonIndexes(self)
    cpdef IndexList getPolygonSubIndexes(self, size_t index)
    cpdef object get_geometry(self, cl_uint idx)
    cpdef size_t get_geometry_type(self, cl_uint idx) except *
    cpdef _Coordinate_f getCoordinate(self, size_t index)
    cpdef _Coordinate_f getPointCoordinate(self, size_t index)
    cpdef float[:, :] getLineStringCoordinates(self, size_t index) except *
    cpdef float[:, :] getPolygonCoordinates(self, size_t index) except *
    cdef _bbox_list_f getPolygonSubBounds(self, size_t index) except *
    cpdef size_t getPointCount(self) except *
    cpdef size_t getLineStringCount(self) except *
    cpdef size_t getPolygonCount(self) except *
    cpdef bool hasData(self) except *
    cpdef size_t getGeometryBaseCount(self) except *
    cpdef void runScript(self, string script) except *
    # method to get property
    cpdef string getProperty_str(self, cl_uint index, string name) except *
    cpdef uint32_t getProperty_uint(self, cl_uint index, string name) except *
    cpdef float getProperty_flt(self, cl_uint index, string name) except *
    cpdef int getProperty_int(self, cl_uint index, string name) except *
    cpdef uint8_t getProperty_byt(self, cl_uint index, string name) except *
    cpdef float[:] getProperty_flt_vector(self, cl_uint index, string name) except *
    # method to convert property
    cpdef void convertProperty_str(self, string name) except *
    cpdef void convertProperty_int(self, string name) except *
    cpdef void convertProperty_flt(self, string name) except *
    cpdef void convertProperty_uint(self, string name) except *
    cpdef void convertProperty_byt(self, string name) except *
    # set all values of a property
    cdef void _setPropertyVector_str(self, string name, vector[string] v) except *
    cpdef void setPropertyVector_int(self, string name, int[:] v) except *
    cpdef void setPropertyVector_flt(self, string name, float[:] v) except *
    cpdef void setPropertyVector_uint(self, string name, uint32_t[:] v) except *
    cpdef void setPropertyVector_byt(self, string name, uint8_t[:] v) except *
    # method to set property
    cpdef void setProperty_str(self, cl_uint index, string name, string v) except *
    cpdef void setProperty_int(self, cl_uint index, string name, int v) except *
    cpdef void setProperty_flt(self, cl_uint index, string name, float v) except *
    cpdef void setProperty_uint(self, cl_uint index, string name, uint32_t v) except *
    cpdef void setProperty_byt(self, cl_uint index, string name, uint8_t v) except *
    cpdef void setProperty_flt_vector(self, cl_uint index, string name, float[:] v) except *
    cpdef bool isPropertyNumeric(self, string name) except *
    # method to get property ref when value is vector
    cdef vector[float]* getPropertyVectorRef_flt(self, cl_uint idx, string name) except *
    cdef vector[vector[float]]* getPropertyVectorsRef_flt(self, string name) except *
    # method to get global property
    cpdef int getGlobalProperty_int(self, string name) except *
    cpdef string getGlobalProperty_str(self, string name) except *
    # method to set global property
    cpdef void setGlobalProperty_int(self, string name, int v) except *
    cpdef void setGlobalProperty_str(self, string name, string v) except *
    cpdef void buildRelations(self, size_t geometryType, size_t relationType=?) except *
    cpdef cl_uint getRelationSize(self, size_t geometryType) except *
    cpdef cl_uint getRelationData(self, cl_uint gid, cl_uint idx) except *
    cpdef cl_uint[:] getRelationDataArray(self, cl_uint gid) except *
    # IO methods
    cpdef void read(self, string fileName, string jsonConfig=?) except *
    cpdef void write(self, string fileName, size_t writeType=?,
                     bool enforceProjection=?, bool writeNullProperties=?) except *

cdef class _CoordinateVector_d:
    cdef vector[Coordinate[double]] *thisptr
    cpdef double[:, :] to_array(self) except *
    cpdef void from_array(self, double[:, :] c) except *

cdef class _CoordinateVector_f:
    cdef vector[Coordinate[float]] *thisptr
    cpdef float[:, :] to_array(self) except *
    cpdef void from_array(self, float[:, :] c) except *

cdef class _VectorPtrList_d:
    cdef vector_ptr_list_d *thisptr
    cdef int n_vector
    cpdef int get_number_of_vectors(self)
    cpdef _Vector_d get_vector_from_vec(self, size_t i)
    cpdef void clear(self)

cdef class _VectorPtrList_f:
    cdef vector_ptr_list_f *thisptr
    cdef int n_vector
    cpdef int get_number_of_vectors(self)
    cpdef _Vector_f get_vector_from_vec(self, size_t i)
    cpdef void clear(self)
