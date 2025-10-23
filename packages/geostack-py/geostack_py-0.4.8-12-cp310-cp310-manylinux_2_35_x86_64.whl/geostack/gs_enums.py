# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Re-implemented as definitions, gs_enums kept for backwards compatibility

from .definitions import extend_obj_with_enum
from .definitions import _baseEnum
from .definitions import (GeometryType, RasterCombinationType,
                          RasterResolutionType, RasterNullValueType,
                          NeighboursType, SeriesInterpolationType, SeriesCappingType,
                          RasterInterpolationType, ReductionType,
                          RasterDebug, PropertyType, VectorOrdering,
                          VectorLayerHandling, RasterSortType, RelationType,
                          PropertyStructure, VectorIndexingOptions,SearchStrategy,
                          RasterDataType)
