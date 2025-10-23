// Copyright (C) 2020 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "../telescope/oskar.h"
#include "../oskar/oskarelementresponse.h"
#include "../oskar/skalowelementresponse.h"

#include <complex>
#include <cmath>
#include <iostream>

#include <boost/test/unit_test.hpp>

#include "../load.h"
#include "../beammode.h"
#include "../beamnormalisationmode.h"
#include "../elementresponse.h"
#include "../griddedresponse/phasedarraygrid.h"
#include "../options.h"
#include "../pointresponse/phasedarraypoint.h"
#include "../station.h"

#include "config.h"

using aocommon::CoordinateSystem;
using everybeam::BeamMode;
using everybeam::BeamNormalisationMode;
using everybeam::ElementResponseModel;
using everybeam::Load;
using everybeam::Options;
using everybeam::Station;
using everybeam::griddedresponse::GriddedResponse;
using everybeam::griddedresponse::PhasedArrayGrid;
using everybeam::pointresponse::PhasedArrayPoint;
using everybeam::pointresponse::PointResponse;
using everybeam::telescope::OSKAR;
using everybeam::telescope::Telescope;

BOOST_AUTO_TEST_SUITE(oskar)

BOOST_AUTO_TEST_CASE(load) {
  Options options;
  options.element_response_model = ElementResponseModel::kOSKARSphericalWave;

  casacore::MeasurementSet ms(OSKAR_MOCK_MS);

  // Load OSKAR Telescope
  std::unique_ptr<Telescope> telescope = Load(ms, options);

  // Assert if we indeed have an OSKAR pointer
  BOOST_CHECK(nullptr != dynamic_cast<OSKAR*>(telescope.get()));

  // Assert if correct number of stations
  std::size_t nstations = 30;
  BOOST_CHECK_EQUAL(telescope->GetNrStations(), nstations);

  // Assert if GetStation(stationd_id) behaves properly
  const OSKAR& oskartelescope = static_cast<const OSKAR&>(*telescope.get());
  BOOST_CHECK_EQUAL(oskartelescope.GetStation(0).GetName(), "s0000");

  // Properties extracted from MS
  double time = 4.45353e+09;
  double frequency = 5.0e+07;
  double ra(0.349066), dec(-0.523599);

  // Image properties
  constexpr std::size_t width = 16;
  constexpr std::size_t height = 16;
  double dl(0.5 * M_PI / 180.), dm(0.5 * M_PI / 180.), shift_l(0.), shift_m(0.);

  aocommon::CoordinateSystem coord_system;
  coord_system.width = width;
  coord_system.height = height;
  coord_system.ra = ra;
  coord_system.dec = dec;
  coord_system.dl = dl;
  coord_system.dm = dm;
  coord_system.l_shift = shift_l;
  coord_system.m_shift = shift_m;

  // Get GriddedResponse pointer
  std::unique_ptr<GriddedResponse> grid_response =
      telescope->GetGriddedResponse(coord_system);
  BOOST_CHECK(nullptr != dynamic_cast<PhasedArrayGrid*>(grid_response.get()));

  // Define buffer and get gridded response (all stations)
  std::vector<std::complex<float>> antenna_buffer(
      grid_response->GetStationBufferSize(telescope->GetNrStations()));

  grid_response->ResponseAllStations(BeamMode::kFull, antenna_buffer.data(),
                                     time, frequency, 0);

  BOOST_CHECK_EQUAL(
      antenna_buffer.size(),
      std::size_t(telescope->GetNrStations() * width * height * 2 * 2));

  // Offset for pixels (8, 1), (8, 8), (5, 13) to check
  constexpr size_t offset_p81 = (1 + 8 * width) * 4;
  constexpr size_t offset_p88 = (8 + 8 * width) * 4;
  constexpr size_t offset_p513 = (13 + 5 * width) * 4;

  // Pixel (1, 8), values to be reproduced are
  constexpr std::array<std::complex<float>, 8> oskar_p81(
      {{-0.000770827, 0.00734416},
       {0.000108162, 0.000871187},
       {-0.000259571, 0.00107524},
       {0.000648075, -0.00719359}});
  for (std::size_t i = 0; i < 4; ++i) {
    BOOST_CHECK_LT(std::abs(antenna_buffer[offset_p81 + i] - oskar_p81[i]),
                   1e-6);
  }

  // Pixel (8, 8), values to be reproduced are
  constexpr std::array<std::complex<float>, 8> oskar_p88(
      {{-0.00115441, 0.00881435},
       {6.07546e-05, 0.0013592},
       {-0.000379462, 0.00158725},
       {0.000982019, -0.00856565}});

  // Get PointResponse pointer
  std::unique_ptr<PointResponse> point_response =
      telescope->GetPointResponse(time);
  BOOST_CHECK(nullptr != dynamic_cast<PhasedArrayPoint*>(point_response.get()));

  // Compute results via PointResponse (station 0)
  std::complex<float> point_buffer_single_station[4];
  point_response->Response(BeamMode::kFull, point_buffer_single_station,
                           coord_system.ra, coord_system.dec, frequency, 0, 0);

  for (std::size_t i = 0; i < 4; ++i) {
    BOOST_CHECK(std::abs(antenna_buffer[offset_p88 + i] - oskar_p88[i]) < 1e-6);
    BOOST_CHECK(std::abs(point_buffer_single_station[i] -
                         antenna_buffer[offset_p88 + i]) < 1e-6);
  }

  // Pixel (5, 13), values to be reproduced are
  std::vector<std::complex<float>> oskar_p513 = {{-0.00114459, 0.00757855},
                                                 {-4.72324e-06, 0.00138143},
                                                 {-0.000382852, 0.00158802},
                                                 {0.000975401, -0.00731452}};
  for (std::size_t i = 0; i < 4; ++i) {
    BOOST_CHECK(std::abs(antenna_buffer[offset_p513 + i] - oskar_p513[i]) <
                1e-6);
  }

  // Define buffer and get gridded response (all stations)
  std::vector<std::complex<float>> antenna_buffer_single(
      grid_response->GetStationBufferSize(1));

  // Get full beam response from station 5
  grid_response->Response(everybeam::BeamMode::kFull,
                          antenna_buffer_single.data(), time, frequency, 5, 0);
  // Check that results in antenna_buffer_single matches the relevant part in
  // antenna_buffer
  std::size_t offset_s5 = 5 * width * height * 4;
  for (std::size_t i = 0; i != antenna_buffer_single.size(); ++i) {
    BOOST_CHECK(std::abs(antenna_buffer[offset_s5 + i] -
                         antenna_buffer_single[i]) < 1e-6);
  }
}

/**
 * @brief Check consistency of GriddedReponse with
 * BeamNormalisationMode::kAmplitude against PointResponse with
 * BeamNormalisationMode::kAmplitude
 */
BOOST_AUTO_TEST_CASE(beam_normalisations) {
  Options options;
  options.element_response_model = ElementResponseModel::kOSKARSphericalWave;
  options.beam_normalisation_mode = BeamNormalisationMode::kAmplitude;

  casacore::MeasurementSet ms(OSKAR_MOCK_MS);

  // Load LOFAR Telescope
  std::unique_ptr<Telescope> telescope = Load(ms, options);

  // Properties extracted from MS
  const double time = 4.45353e+09;
  const double frequency = 5.0e+07;
  const double ra(0.349066);
  const double dec(-0.523599);

  // Image properties
  std::size_t width(16), height(16);
  double dl(0.5 * M_PI / 180.), dm(0.5 * M_PI / 180.), shift_l(0.), shift_m(0.);

  CoordinateSystem coord_system;
  coord_system.width = width;
  coord_system.height = height;
  coord_system.ra = ra;
  coord_system.dec = dec;
  coord_system.dl = dl;
  coord_system.dm = dm;
  coord_system.l_shift = shift_l;
  coord_system.m_shift = shift_m;

  // Get GriddedResponse pointer
  std::unique_ptr<GriddedResponse> grid_response =
      telescope->GetGriddedResponse(coord_system);

  // Get PointResponse pointer
  std::unique_ptr<PointResponse> point_response =
      telescope->GetPointResponse(time);

  // Define buffer and get gridded response (all stations)
  std::vector<std::complex<float>> antenna_buffer(
      grid_response->GetStationBufferSize(telescope->GetNrStations()));

  grid_response->ResponseAllStations(BeamMode::kFull, antenna_buffer.data(),
                                     time, frequency, 0);

  BOOST_CHECK_EQUAL(
      antenna_buffer.size(),
      std::size_t(telescope->GetNrStations() * width * height * 2 * 2));

  // Offset for center pixel (8, 8)
  const std::size_t offset_p88 = (8 + 8 * width) * 4;

  // Compute results via PointResponse (station 0)
  std::complex<float> point_buffer_single_station[4];
  point_response->Response(BeamMode::kFull, point_buffer_single_station,
                           coord_system.ra, coord_system.dec, frequency, 0, 0);

  for (std::size_t i = 0; i < 4; ++i) {
    BOOST_CHECK(std::abs(point_buffer_single_station[i] -
                         antenna_buffer[offset_p88 + i]) < 1e-6);
  }
}

BOOST_AUTO_TEST_CASE(element_response_dipole_real) {
  const double kFrequency = 1.0e8;
  const double kTheta = 1.0;
  const double kPhi = 0.5;
  const std::array<double, 4> expected_response_real = {
      -0.41647976019737187, 0.42110486572843914, 0.24931842416298652,
      0.84466475391726659};

  // Generate a response, using kTheta and kPhi.
  const everybeam::OSKARElementResponseDipole element_response;
  aocommon::MC2x2 response =
      element_response.Response(kFrequency, kTheta, kPhi);
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_CLOSE(response.Get(i).real(), expected_response_real[i],
                      1.0e-4);
    BOOST_CHECK(std::abs(response.Get(i).imag()) < 1.0e-9);
  }

  // Check that the response is invertible.
  BOOST_CHECK(response.Invert());
}

BOOST_AUTO_TEST_CASE(ska_low_element_response) {
  const int kSkaLowElement = 0;
  const int kStationId = 0;
  const double kFrequency = 3.15e8;
  const everybeam::vector3r_t kDirection{-0.40241194, 0.79787001, -0.44885196};

  const std::array<double, 4> expected_response_real = {
      -1.2692836587862768, -2.242893427262115, -1.2840197715430925,
      1.2569541572552989};
  const std::array<double, 4> expected_response_imag = {
      -5.7589862751315142, 7.6234040755697237, 7.4872701697930406,
      5.594243471017494};

  Options options;
  options.coeff_path = TEST_DATA_DIR;
  options.element_response_model = ElementResponseModel::kSkaLowFeko;

  casacore::MeasurementSet ms(OSKAR_MOCK_MS);
  // Load OSKAR Telescope
  std::unique_ptr<Telescope> telescope = Load(ms, options);

  const double kTime = 4.45352677e+09;
  std::unique_ptr<everybeam::pointresponse::PointResponse> point_response =
      telescope->GetPointResponse(kTime);

  auto& phased_array_point =
      dynamic_cast<everybeam::pointresponse::PhasedArrayPoint&>(
          *point_response);

  aocommon::MC2x2 response;
  phased_array_point.ElementResponse(&response, kStationId,
                                     std::span(&kFrequency, 1), kDirection,
                                     kSkaLowElement);

  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_CLOSE(response.Get(i).real(), expected_response_real[i],
                      1.0e-4);
    BOOST_CHECK_CLOSE(response.Get(i).imag(), expected_response_imag[i],
                      1.0e-4);
  }

  // Check that the response is invertible.
  BOOST_CHECK(response.Invert());
}

BOOST_AUTO_TEST_CASE(ska_low_element_response_invalid_path) {
  Options options;
  options.coeff_path = "invalid_path";
  options.element_response_model = ElementResponseModel::kSkaLowFeko;

  casacore::MeasurementSet ms(OSKAR_MOCK_MS);
  // Load element coefficient from an invalid path
  BOOST_CHECK_THROW(Load(ms, options), std::invalid_argument);
}

BOOST_AUTO_TEST_SUITE_END()
