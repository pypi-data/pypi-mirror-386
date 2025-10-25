#!/usr/bin/env python3

# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

from earthkit.geo import UNIT_SPHERE
from earthkit.geo import haversine_distance
from earthkit.geo import nearest_point_haversine
from earthkit.geo import nearest_point_kdtree


def get_nearest_method(mode):
    if mode == "haversine":
        return nearest_point_haversine
    elif mode == "kdtree":
        return nearest_point_kdtree
    else:
        raise ValueError(f"Invalid mode={mode}")


def test_haversine_distance_single_point():
    p_ref = (48.0, 20)
    d_ref = 5675597.92279149
    p = (0, 0)
    d = haversine_distance(p_ref, p)
    assert np.isclose(d, d_ref)


@pytest.mark.parametrize("dlon_ref", [-720, -360, 0, 360, 720])
@pytest.mark.parametrize("dlon_p", [-720, -360, 0, 360, 720])
@pytest.mark.parametrize(
    "p_ref,d_ref",
    [
        (
            (0, 0),
            [
                0.0,
                10007903.11036912,
                10007903.11036912,
                20015806.22073824,
                10007903.11036912,
                10007903.11036912,
                5675597.92279149,
                5675597.92279149,
                5675597.92279149,
                5675597.92279149,
                np.nan,
            ],
        ),
        (
            (-90, 0),
            [
                10007903.11036912,
                10007903.11036912,
                10007903.11036912,
                10007903.11036912,
                20015806.22073824,
                0.0,
                15345451.43589932,
                15345451.43589932,
                4670354.78483892,
                4670354.78483892,
                np.nan,
            ],
        ),
        (
            (48.0, 20),
            [
                5675597.92279149,
                8536770.52794796,
                11479035.69279028,
                14340208.29794676,
                4670354.78483892,
                15345451.43589932,
                0.0,
                2942265.16484232,
                11351195.84558298,
                10675096.6510604,
                np.nan,
            ],
        ),
    ],
)
def test_haversine_distance(dlon_ref, dlon_p, p_ref, d_ref):
    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0]) + dlon_p
    p_ref = (p_ref[0], p_ref[1] + dlon_ref)
    d_ref = np.array(d_ref)

    d = haversine_distance(p_ref, (lats, lons))
    assert np.allclose(d[:-1], d_ref[:-1]), f"p_ref={p_ref},dlon_ref={dlon_ref},dlon_p={dlon_p}"


def test_haversine_distance_with_radius():
    p = (0, 90)
    p_ref = (48.0, 20)
    d_ref = 1.33989384590445

    d = haversine_distance(p_ref, p, figure=UNIT_SPHERE)
    assert np.allclose(d, d_ref)


# lat is out of range
@pytest.mark.parametrize("p_ref", [((90.00001, 0)), (((-90.00001, 0)))])
def test_haversine_distance_invalid(p_ref):
    p = (-48, 12)
    d = haversine_distance(p_ref, p)
    assert np.isnan(d)


@pytest.mark.parametrize("mode", ["haversine", "kdtree"])
@pytest.mark.parametrize(
    "p_ref,index_ref,dist_ref",
    [
        ((0, 0), 0, 0),
        ((15, 22), 0, 2937383.915942687),
        ((44, 10), 6, 890348.1323086087),
        ((44, -10), 7, 890348.1323086087),
        ((89, -120), 4, 111198.92344854656),
        ((-50, -18), 8, 265965.0757389435),
        ((-50, 18), 9, 265965.0757389435),
    ],
)
def test_nearest_single_ref(mode, p_ref, index_ref, dist_ref):
    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0])

    meth = get_nearest_method(mode)
    index, distance = meth(p_ref, (lats, lons))
    assert np.allclose(index_ref, index)
    assert np.allclose(distance, dist_ref)


@pytest.mark.parametrize("mode", ["haversine", "kdtree"])
@pytest.mark.parametrize(
    "p_ref,index_ref,dist_ref",
    [
        ((0, 0), 0, 0),
        ((15, 22), 0, 0.46103882),
        ((-50, -18), 8, 0.04174471),
    ],
)
def test_nearest_single_ref_with_radius(mode, p_ref, index_ref, dist_ref):
    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0])

    meth = get_nearest_method(mode)
    index, distance = meth(p_ref, (lats, lons), figure=UNIT_SPHERE)
    assert np.allclose(index_ref, index)
    assert np.allclose(distance, dist_ref)


@pytest.mark.parametrize("mode", ["haversine", "kdtree"])
def test_nearest_multi_ref_single_point(mode):
    p_ref = [(15, 44, 44), (22, 10, -10)]

    index_ref = np.array([0, 0, 0])
    dist_ref = np.array([3669564.47380201, 1026629.42232992, 2492883.80828643])

    lats = 48
    lons = 22

    meth = get_nearest_method(mode)
    index, distance = meth(p_ref, (lats, lons))
    assert np.allclose(index, index_ref)
    assert np.allclose(distance, dist_ref)


@pytest.mark.parametrize("mode", ["haversine", "kdtree"])
def test_nearest_multi_ref_multi_points(mode):
    p_ref = [(15, 44, 44), (22, 10, -10)]

    index_ref = np.array([0, 6, 7])
    dist_ref = np.array([2937383.915942687, 890348.1323086087, 890348.1323086087])

    lats = np.array([0.0, 0, 0, 0, 90, -90, 48, 48, -48, -48, np.nan])
    lons = np.array([0, 90, -90, 180, 0, 0, 20, -20, -20, 20, 1.0])

    meth = get_nearest_method(mode)
    index, distance = meth(p_ref, (lats, lons))
    assert np.allclose(index, index_ref)
    assert np.allclose(distance, dist_ref)


@pytest.mark.parametrize("mode", ["haversine", "kdtree"])
def test_nearest_invalid(mode):
    # checks: p_ref must have a (2,) shape
    p_ref = ([15, 21], [22, 7], [44, 12])
    p = ([0.0, 0], [0, 90])

    with pytest.raises(ValueError):
        meth = get_nearest_method(mode)
        meth(p_ref, p)
