# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

from earthkit.geo.coord import _normalise_lon

LOG = logging.getLogger(__name__)

_ROOT_DIR = os.path.dirname(__file__)

if not os.path.exists(os.path.join(_ROOT_DIR, "data")):
    _ROOT_DIR = "./"


def earthkit_test_data_file(*args):
    return os.path.join(_ROOT_DIR, "data", *args)


def normalise_lon(lon):
    if isinstance(lon, (int, float)):
        return _normalise_lon(lon, -180)
    else:
        import numpy as np

        lon = np.asarray(lon)
        return np.array([_normalise_lon(x, -180) for x in lon])
