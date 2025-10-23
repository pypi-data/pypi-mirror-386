// Copyright (C) 2023 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "oskar.h"

#include <cassert>

#include <aocommon/banddata.h>
#include <casacore/measures/TableMeasures/ArrayMeasColumn.h>

#include "../common/mathutils.h"
#include "../common/casautils.h"

using casacore::MeasurementSet;
using everybeam::Station;
using everybeam::griddedresponse::GriddedResponse;
using everybeam::pointresponse::PointResponse;
using everybeam::telescope::OSKAR;

namespace everybeam::telescope {

namespace {
Options SetTelescopeOptions(const Options& options) {
  Options new_options = options;
  if (options.element_response_model == ElementResponseModel::kDefault) {
    new_options.element_response_model = ElementResponseModel::kOSKARDipole;
  }

  // OSKAR never uses the subband frequency.
  if (!options.use_channel_frequency) {
    throw std::runtime_error("For OSKAR, use_channel_frequency must be true.");
  }

  return new_options;
}
}  // namespace

OSKAR::OSKAR(const MeasurementSet& ms, const Options& options)
    : PhasedArray(ms, SetTelescopeOptions(options)) {
  SetBand(aocommon::BandData(ms.spectralWindow()));

  casacore::ScalarMeasColumn<casacore::MDirection> delay_dir_col(
      ms.field(),
      casacore::MSField::columnName(casacore::MSFieldEnums::DELAY_DIR));
  SetDelayDirection(delay_dir_col(0));
  // Tile beam direction has dummy values for OSKAR.
  SetTileBeamDirection(delay_dir_col(0));

  PhasedArray::CalculatePreappliedBeamOptions(ms);
}

}  // namespace everybeam::telescope
