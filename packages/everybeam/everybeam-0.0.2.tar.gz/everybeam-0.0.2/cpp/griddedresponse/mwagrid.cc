// Copyright (C) 2020 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "mwagrid.h"

#include <aocommon/imagecoordinates.h>

#include <casacore/measures/Measures/MCDirection.h>
#include <casacore/measures/Measures/MCPosition.h>
#include <casacore/measures/Measures/MDirection.h>
#include <casacore/measures/Measures/MEpoch.h>

#include "../telescope/mwa.h"

using everybeam::mwabeam::TileBeam2016;

namespace everybeam {
namespace griddedresponse {
void MWAGrid::Response(BeamMode /* beam_mode */, std::complex<float>* buffer,
                       double time, double frequency, size_t /* station_idx */,
                       size_t /* field_id */) {
  const telescope::MWA& mwatelescope =
      static_cast<const telescope::MWA&>(*telescope_);

  casacore::MEpoch time_epoch(casacore::Quantity(time, "s"));
  casacore::MeasFrame frame(mwatelescope.GetArrayPosition(), time_epoch);

  const casacore::MDirection::Ref hadec_ref(casacore::MDirection::HADEC, frame);
  const casacore::MDirection::Ref azelgeo_ref(casacore::MDirection::AZELGEO,
                                              frame);
  const casacore::MDirection::Ref j2000_ref(casacore::MDirection::J2000, frame);
  casacore::MDirection::Convert j2000_to_hadecref(j2000_ref, hadec_ref),
      j2000_to_azelgeoref(j2000_ref, azelgeo_ref);
  casacore::MPosition wgs = casacore::MPosition::Convert(
      mwatelescope.GetArrayPosition(), casacore::MPosition::WGS84)();
  const double arr_latitude = wgs.getValue().getLat();

  if (!tile_beam_) {
    tile_beam_.reset(
        new TileBeam2016(mwatelescope.GetDelays().data(),
                         mwatelescope.GetOptions().frequency_interpolation,
                         mwatelescope.GetOptions().coeff_path));
  }
  std::complex<float>* buffer_ptr = buffer;
  for (size_t y = 0; y != height_; ++y) {
    for (size_t x = 0; x != width_; ++x) {
      double l, m, ra, dec;
      aocommon::ImageCoordinates::XYToLM(x, y, dl_, dm_, width_, height_, l, m);
      l += l_shift_;
      m += m_shift_;
      aocommon::ImageCoordinates::LMToRaDec(l, m, ra_, dec_, ra, dec);

      aocommon::MC2x2 gain;
      tile_beam_->ArrayResponse(ra, dec, j2000_ref, j2000_to_hadecref,
                                j2000_to_azelgeoref, arr_latitude, frequency,
                                gain);
      gain.AssignTo(buffer_ptr);
      buffer_ptr += 4;  // An aocommon::MC2x2 has 4 complex doubles.
    }
  }
}

void MWAGrid::MakeIntegratedCorrectionSnapshot(
    BeamMode beam_mode, std::vector<aocommon::HMC4x4>& matrices, double time,
    double frequency, size_t field_id, const double* baseline_weights_interval,
    bool square_mueller) {
  const size_t n_stations = telescope_->GetNrStations();
  aocommon::UVector<std::complex<float>> buffer_undersampled(
      GetStationBufferSize(n_stations));
  ResponseAllStations(beam_mode, buffer_undersampled.data(), time, frequency,
                      field_id);

  // For MWA, we can simply weight a (time) snapshot with the accumulated
  // baseline weights
  const size_t n_baselines = n_stations * (n_stations + 1) / 2;
  double snapshot_weight = 0.;
  for (size_t index = 0; index != n_baselines; ++index) {
    snapshot_weight += baseline_weights_interval[index];
  }

  for (size_t y = 0; y != height_; ++y) {
    for (size_t x = 0; x != width_; ++x) {
      size_t offset = (y * width_ + x) * 4;
      const aocommon::MC2x2 A(&buffer_undersampled[offset]);

      // Mueller matrix constant for all baselines, so just compute once for
      // each individual pixel
      if (square_mueller) {
        matrices[y * width_ + x] =
            aocommon::HMC4x4::KroneckerProduct(A.HermTranspose().Transpose(), A)
                .Square() *
            snapshot_weight;
      } else {
        matrices[y * width_ + x] = aocommon::HMC4x4::KroneckerProduct(
                                       A.HermTranspose().Transpose(), A) *
                                   snapshot_weight;
      }
    }
  }
}
}  // namespace griddedresponse
}  // namespace everybeam
