# Copyright (C) 2021 ASTRON (Netherlands Institute for Radio Astronomy)
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import numpy as np
import pytest

from everybeam import OSKAR, GridSettings, load_telescope

DATADIR = os.environ["DATA_DIR"]


@pytest.fixture
def oskar_setup():
    gs = GridSettings()
    gs.width = gs.height = 16
    gs.ra = 0.349066
    gs.dec = -0.523599
    gs.dl = gs.dm = 0.5 * np.pi / 180.0
    gs.l_shift = gs.m_shift = 0.0

    return {
        "filename": "OSKAR_MOCK.ms",
        "time": 4.45353e09,
        # Frequency of channel 4
        "freq": 5.0e07,
        "coordinate_system": gs,
        # Reference cpp solution for station 0, see cpp/test/toskar.cc
        "station_id": 0,
        "cpp_response": np.array(
            [
                [-0.00115441 + 0.00881435j, 6.07546e-05 + 0.0013592j],
                [-0.000379462 + 0.00158725j, 0.000982019 - 0.00856565j],
            ]
        ),
    }


def test_oskar(oskar_setup):
    ms_path = os.path.join(DATADIR, oskar_setup["filename"])
    differential_beam = False
    telescope = load_telescope(
        ms_path,
        use_differential_beam=differential_beam,
        element_response_model="skala40_wave",
    )

    assert type(telescope) is OSKAR
    response = telescope.station_response(
        oskar_setup["time"],
        oskar_setup["station_id"],
        oskar_setup["freq"],
        oskar_setup["coordinate_system"].ra,
        oskar_setup["coordinate_system"].dec,
    )

    # Reference solution same as pixel (8,8) in toskar.cc
    np.testing.assert_allclose(
        response, oskar_setup["cpp_response"], rtol=1e-5
    )
