# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
sys.path.insert(0, os.path.realpath('../../../'))

from geostack.vector import Coordinate, BoundingBox, KDTree, Vector

def test_create_coordinate():
    c0 = Coordinate(0.0, 0.0)
    assert (c0.p == 0.0) & (c0.q == 0.0)

def test_edit_coordinate():
    c0 = Coordinate(0.0, 0.0)
    c0.p = 1.0
    assert (c0.p == 1.0) & (c0.q == 0.0)

def test_coord_equality():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    assert not(c0 == c1)

def test_coord_inequality():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    assert c0 != c1

def test_bbox_from_coords():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)
    assert (b1.min == c0) & (b1.max == c1)

def test_bbox_from_bbox():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)
    b2 = BoundingBox(input_bbox=b1)
    assert (b2.min == c0) & (b2.max == c1)

def test_bbox_equality():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)
    b2 = BoundingBox(input_bbox=b1)
    assert b1 == b2

def test_bbox_inequality():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)
    b2 = BoundingBox(input_bbox=b1)
    assert not(b1 != b2)

def test_change_max_coord_bbox():
    c0 = Coordinate(0.0, 0.0)
    c1 = Coordinate(1.0, 1.0)
    c2 = Coordinate(2.0, 2.0)
    b1 = BoundingBox(min_coordinate=c0, max_coordinate=c1)
    b2 = BoundingBox(input_bbox=b1)
    b2.max = c2
    assert (b2.min == c0) & (b2.max == c2)

def test_kdtree_nearest_point():
    v = Vector()
    v.addPoint([200.0, 100.0])
    v.addPoint([0.0, 0.0])
    v.addPoint([100.0, 0.0])
    expectedGeomID = v.addPoint([100.0, 100.0])
    v.addPoint([200.0, 200.0])

    kdt = KDTree(v)
    nearestGeomID = kdt.nearest(Coordinate(99, 99))
    assert nearestGeomID == expectedGeomID

def test_kdtree_nearestN_points():
    expectedGeomIDs = set()

    v = Vector()
    expectedGeomIDs.add(v.addPoint([100.0, 100.0]))
    v.addPoint([200.0, 200.0])
    v.addPoint([0.0, 0.0])
    expectedGeomIDs.add(v.addPoint([100.0, 0.0]))
    expectedGeomIDs.add(v.addPoint([200.0, 100.0]))

    kdt = KDTree(v)
    nearestGeomIDs = set(kdt.nearestN(Coordinate(99, 99), len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_kdtree_nearest_linestring():
    v = Vector()
    expectedGeomID = v.addLineString(
        [
            [500, 100],
            [100, 100],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    )
    v.addPoint([85, 85])
    v.addLineString(
        [
            [95, 95],
            [105, 105],
            [205, 205],
            [305, 305],
            [405, 405]
        ]
    )
    v.addLineString(
        [
            [190, 190],
            [500, 500],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    )
    v.addPoint([250, 350])
    v.addPoint([350, 450])
    v.addPoint([450, 550])

    kdt = KDTree(v)
    nearestGeomID = kdt.nearest(Coordinate(99, 99))
    assert nearestGeomID == expectedGeomID

def test_kdtree_nearestN_linestrings():
    v = Vector()
    expectedGeomIDs = set()
    expectedGeomIDs.add(v.addLineString(
        [
            [500, 100],
            [100, 100],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    ))
    expectedGeomIDs.add(v.addPoint([85, 85]))
    expectedGeomIDs.add(v.addLineString(
        [
            [95, 95],
            [105, 105],
            [205, 205],
            [305, 305],
            [405, 405]
        ]
    ))
    v.addLineString(
        [
            [190, 190],
            [500, 500],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    )
    v.addPoint([250, 350])
    v.addPoint([350, 450])
    v.addPoint([450, 550])

    kdt = KDTree(v)
    nearestGeomIDs = set(kdt.nearestN(Coordinate(99, 99), len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs

def test_kdtree_nearest_polygon():
    v = Vector()
    expectedGeomID = v.addPolygon(
        [
            [
                [0, 0],
                [100, 0],
                [100, 100],
                [0, 100]
            ]
        ]
    )
    v.addPolygon(
        [
            [
                [-200, -200],
                [-200, 200],
                [200, 200],
                [200, -200]
            ],
            [
                [-100, -100],
                [-100, 100],
                [101, 101],
                [100, -100]
            ]
        ]
    )
    v.addLineString(
        [
            [500, 100],
            [102, 102],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    )
    v.addPolygon(
        [
            [
                [0, 0],
                [300, 0],
                [300, 300],
                [0, 300]
            ]
        ]
    )
    v.addLineString(
        [
            [505, 105],
            [-102, -102],
            [205, 205],
            [305, 305],
            [405, 405]
        ]
    )

    kdt = KDTree(v)
    nearestGeomID = kdt.nearest(Coordinate(99, 99))
    assert nearestGeomID == expectedGeomID

def test_kdtree_nearestN_polygons():
    v = Vector()
    expectedGeomIDs = set()
    expectedGeomIDs.add(v.addPolygon(
        [
            [
                [0, 0],
                [100, 0],
                [100, 100],
                [0, 100]
            ]
        ]
    ))
    expectedGeomIDs.add(v.addPolygon(
        [
            [
                [-200, -200],
                [-200, 200],
                [200, 200],
                [200, -200]
            ],
            [
                [-100, -100],
                [-100, 100],
                [101, 101],
                [100, -100]
            ]
        ]
    ))
    expectedGeomIDs.add(v.addLineString(
        [
            [500, 100],
            [102, 102],
            [200, 200],
            [300, 300],
            [400, 400]
        ]
    ))
    v.addPolygon(
        [
            [
                [0, 0],
                [300, 0],
                [300, 300],
                [0, 300]
            ]
        ]
    )
    v.addLineString(
        [
            [505, 105],
            [-102, -102],
            [205, 205],
            [305, 305],
            [405, 405]
        ]
    )

    kdt = KDTree(v)
    nearestGeomIDs = set(kdt.nearestN(Coordinate(99, 99), len(expectedGeomIDs)))
    assert nearestGeomIDs == expectedGeomIDs
