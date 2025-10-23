# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from __future__ import annotations
from enum import IntEnum, unique, Enum
from typing import Union, Callable
import numbers
import inspect

__all__ = ["GeometryType", "RasterCombinationType",
           "RasterResolutionType", "RasterNullValueType",
           "NeighboursType", "SeriesInterpolationType",
           "RasterInterpolationType", "ReductionType",
           "RasterDebug", "PropertyType", "VectorOrdering",
           "VectorLayerHandling", "RasterSortType", "RelationType",
           "PropertyStructure", "VectorIndexingOptions",
           "SearchStrategy", "RasterDataType"]


def extend_obj_with_enum(inherited_enum: Union[IntEnum, Enum]) -> Callable:
    if not issubclass(inherited_enum, (IntEnum, Enum)):  # type: ignore
        raise TypeError("inherited obj should be an enum")

    def wrapper(obj: object) -> object:
        if not inspect.isclass(obj):
            raise TypeError("object should be a class")
        for item in inherited_enum.__members__:  # type: ignore
            setattr(obj, item, getattr(inherited_enum, item).value)
        return obj
    return wrapper


class _baseEnum(IntEnum):

    def __eq__(self, other: Union[IntEnum, numbers.Integral]) -> bool:  # type: ignore
        if isinstance(other, IntEnum):
            return self.value == other.value
        elif isinstance(other, numbers.Integral):
            return self.value == other
        else:
            raise TypeError("Invalid argument type")

    def __ne__(self, other: Union[IntEnum, numbers.Integral]) -> bool:  # type: ignore
        if isinstance(other, IntEnum):
            return self.value == other.value
        elif isinstance(other, numbers.Integral):
            return self.value != other
        else:
            raise TypeError("Invalid argument type")

    def __and__(self, other: Union[IntEnum, numbers.Integral]) -> int:  # type: ignore
        if isinstance(other, IntEnum):
            return self.value & other.value
        elif isinstance(other, numbers.Integral):
            return self.value & other
        else:
            raise TypeError("Invalid argument type")

    def __or__(self, other: Union[IntEnum, numbers.Integral]) -> int:  # type: ignore
        if isinstance(other, IntEnum):
            return self.value | other.value
        elif isinstance(other, numbers.Integral):
            return self.value | other
        else:
            raise TypeError("Invalid argument type")

    def __xor__(self, other: Union[IntEnum, numbers.Integral]) -> int:  # type: ignore
        if isinstance(other, IntEnum):
            return self.value ^ other.value
        elif isinstance(other, numbers.Integral):
            return self.value ^ other
        else:
            raise TypeError("Invalid argument type")

    def __rand__(self, other: int) -> bool:
        if isinstance(other, numbers.Integral):
            return other & self.value
        else:
            raise TypeError("Invalid argument type")

    def __ror__(self, other: int) -> bool:
        if isinstance(other, numbers.Integral):
            return other | self.value
        else:
            raise TypeError("Invalid argument type")

    def __rxor__(self, other: int) -> bool:
        if isinstance(other, numbers.Integral):
            return other ^ self.value
        else:
            raise TypeError("Invalid argument type")

    def __hash__(self) -> int:
        return self.value.__hash__()


@unique
class GeometryType(_baseEnum):
    NoType: int = 0
    Point: int = 1
    LineString: int = 1 << 1
    Polygon: int = 1 << 2
    All: int = 0x07
    TileType: int = 1 << 3


@unique
class RasterCombinationType(_baseEnum):
    Union: int = 0
    Intersection: int = 1 << 0
    Anchor: int = 2 << 0


@unique
class RasterResolutionType(_baseEnum):
    Minimum: int = 0
    Maximum: int = 1 << 2
    Anchor: int = 2 << 2


@unique
class RasterNullValueType(_baseEnum):
    Null: int = 0
    Zero: int = 1 << 6
    One: int = 2 << 6


@unique
class NeighboursType(_baseEnum):
    NoNeighbours: int = 0  # No neighbours
    N: int = 1 << 0      # North neighbour
    NE: int = 1 << 1      # North-east neighbour
    E: int = 1 << 2      # East neighbour
    SE: int = 1 << 3      # South-east neighbour
    S: int = 1 << 4      # South neighbour
    SW: int = 1 << 5      # South-west neighbour
    W: int = 1 << 6      # West neighbour
    NW: int = 1 << 7      # North-west neighbour
    Rook: int = 0x55      # N, E, S and W neighbours
    Bishop: int = 0xAA    # NE, SW, SW and NW neighbours
    Queen: int = 0xFF     # All neighbours


@unique
class SeriesInterpolationType(_baseEnum):
    Linear: int = 0
    MonotoneCubic: int = 1
    BoundedLinear: int = 2


@unique
class SeriesCappingType(_baseEnum):
    Uncapped: int = 0
    Capped: int = 1


@unique
class RasterInterpolationType(_baseEnum):
    Nearest: int = 0
    Bilinear: int = 1 << 4
    Bicubic: int = 2 << 4


@unique
class ReductionType(_baseEnum):
    NoReduction: int = 0
    Maximum: int = 1 << 8
    Minimum: int = 2 << 8
    Sum: int = 3 << 8
    Count: int = 4 << 8
    Mean: int = 5 << 8
    SumSquares: int = 6 << 8


@unique
class RasterDebug(_baseEnum):
    NoDebug: int = 0 << 12
    Enable: int = 1 << 12


@unique
class RasterSortType(_baseEnum):
    NoSort: int = 0 << 14
    PreScript: int = 1 << 14
    PostScript: int = 2 << 14


@unique
class PropertyType(_baseEnum):
    Undefined: int = 0
    String: int = 1
    Integer: int = 2
    Float: int = 3
    Double: int = 4
    Index: int = 5
    Byte: int = 6
    FloatVector: int = 7
    DoubleVector: int = 8
    Map: int = 9
    StringVector: int = 10
    IntegerVector: int = 11
    IndexVector: int = 12
    ByteVector: int = 13


@unique
class PropertyStructure(_baseEnum):
    Undefined: int = 0
    Scalar: int = 1
    Vector: int = 2


@unique
class VectorOrdering(_baseEnum):
    Ordered: int = 0
    Unordered: int = 1


@unique
class VectorLayerHandling(_baseEnum):
    AllLayers: int = 0
    ByLayer: int = 1 << 1


@unique
class RelationType(_baseEnum):
    NoRelation: int = 0
    Neighbour: int = 1


@unique
class VectorIndexingOptions(_baseEnum):
    All: int = 0
    Interior: int = 1 << 8
    Edges: int = 2 << 8

@unique
class SearchStrategy(_baseEnum):
    AllVertices: int = 0
    ByVertex: int = 1

@unique
class RasterDataType(_baseEnum):
    UInt8 = 0
    UInt32 = 1
    Float = 2
    Double = 3