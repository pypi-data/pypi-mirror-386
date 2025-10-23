// Copyright (C) 2021 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include <casacore/measures/TableMeasures/ArrayMeasColumn.h>

#include "phasedarray.h"
#include "../common/casautils.h"
#include "../griddedresponse/phasedarraygrid.h"
#include "../pointresponse/phasedarraypoint.h"

namespace everybeam {
namespace telescope {

PhasedArray::PhasedArray(const std::vector<vector3r_t>& station_positions,
                         const Options& options)
    : Telescope(station_positions.size(), options) {
  stations_.reserve(station_positions.size());
  for (std::size_t i = 0; i < station_positions.size(); ++i) {
    const std::string station_name = "station" + std::to_string(i);
    stations_.push_back(
        std::make_unique<Station>(station_name, station_positions[i], options));
  }
}

std::unique_ptr<griddedresponse::GriddedResponse>
PhasedArray::GetGriddedResponse(
    const aocommon::CoordinateSystem& coordinate_system) const {
  return std::make_unique<griddedresponse::PhasedArrayGrid>(*this,
                                                            coordinate_system);
}

std::unique_ptr<pointresponse::PointResponse> PhasedArray::GetPointResponse(
    double time) const {
  return std::make_unique<pointresponse::PhasedArrayPoint>(*this, time);
}

void PhasedArray::ProcessTimeChange(double time) {
  for (const std::unique_ptr<Station>& station : stations_) {
    station->UpdateTime(time);
  }
}

void PhasedArray::CalculatePreappliedBeamOptions(
    const casacore::MeasurementSet& ms) {
  casacore::ScalarMeasColumn<casacore::MDirection> referenceDirColumn(
      ms.field(),
      casacore::MSField::columnName(casacore::MSFieldEnums::REFERENCE_DIR));
  preapplied_beam_direction_ = referenceDirColumn(0);

  // Read beam keywords of input datacolumn
  // NOTE: it is somewhat confusing that "LOFAR" is explicitly mentioned
  // in the keyword names. The keywords, however, naturally extend to the
  // OSKAR telescope as well.
  casacore::ArrayColumn<std::complex<float>> data_column(
      ms, GetOptions().data_column_name);
  if (data_column.keywordSet().isDefined("LOFAR_APPLIED_BEAM_MODE")) {
    preapplied_correction_mode_ = ParseCorrectionMode(
        data_column.keywordSet().asString("LOFAR_APPLIED_BEAM_MODE"));
    switch (preapplied_correction_mode_) {
      case CorrectionMode::kNone:
        break;
      case CorrectionMode::kElement:
      case CorrectionMode::kArrayFactor:
      case CorrectionMode::kFull:
        casacore::String error;
        casacore::MeasureHolder mHolder;
        if (!mHolder.fromRecord(error, data_column.keywordSet().asRecord(
                                           "LOFAR_APPLIED_BEAM_DIR"))) {
          throw std::runtime_error(
              "Error while reading LOFAR_APPLIED_BEAM_DIR keyword: " + error);
        }
        preapplied_beam_direction_ = mHolder.asMDirection();
        break;
    }
  } else {
    preapplied_correction_mode_ = CorrectionMode::kNone;
  }
}

void PhasedArray::SetBand(const aocommon::BandData& band) {
  if (GetOptions().use_channel_frequency) {
    subband_frequency_ = 0.0;
  } else {
    subband_frequency_ = band.ReferenceFrequency();
  }
  channel_frequencies_ = std::vector<double>(band.begin(), band.end());
}

}  // namespace telescope
}  // namespace everybeam
