// Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "../telescope/phasedarray.h"

#include <boost/test/unit_test.hpp>

using everybeam::telescope::PhasedArray;

namespace {
const std::vector<everybeam::vector3r_t> kStationPositions{{1.0, 2.0, 3.0},
                                                           {4.0, 5.0, 6.0}};
const everybeam::Options kOptions{
    .element_response_model = everybeam::ElementResponseModel::kOSKARDipole,
};
}  // namespace

BOOST_AUTO_TEST_SUITE(phased_array)

BOOST_AUTO_TEST_CASE(constructor_station_positions) {
  PhasedArray phased_array(kStationPositions, kOptions);

  BOOST_REQUIRE_EQUAL(phased_array.GetNrStations(), kStationPositions.size());
  BOOST_CHECK_EQUAL(phased_array.GetStation(0).GetName(), "station0");
  BOOST_CHECK_EQUAL(phased_array.GetStation(1).GetName(), "station1");
  BOOST_CHECK(phased_array.GetStation(0).GetPosition() == kStationPositions[0]);
  BOOST_CHECK(phased_array.GetStation(1).GetPosition() == kStationPositions[1]);
}

BOOST_AUTO_TEST_CASE(process_time_change) {
  /** PhasedArray subclass which exposes ProcessTimeChange for testing. */
  class TestPhasedArray : public PhasedArray {
   public:
    using PhasedArray::PhasedArray;
    using PhasedArray::ProcessTimeChange;
  };

  const std::vector<everybeam::vector3r_t> kStationPositions{{1.0, 2.0, 3.0},
                                                             {4.0, 5.0, 6.0}};

  TestPhasedArray phased_array(kStationPositions, kOptions);
  for (std::size_t i = 0; i < kStationPositions.size(); ++i) {
    BOOST_CHECK_LT(phased_array.GetStation(i).GetTime(), 0.0);
  }

  const double kTime = 42.0;
  phased_array.ProcessTimeChange(kTime);
  for (std::size_t i = 0; i < kStationPositions.size(); ++i) {
    BOOST_CHECK_EQUAL(phased_array.GetStation(i).GetTime(), kTime);
  }
}

BOOST_AUTO_TEST_SUITE_END()
