// Copyright (C) 2020 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "lofar.h"
#include "../griddedresponse/aartfaacgrid.h"
#include "../pointresponse/aartfaacpoint.h"
#include "../common/mathutils.h"
#include "../common/casautils.h"
#include "../msreadutils.h"
#include "../load.h"

#include <aocommon/banddata.h>
#include <cassert>
#include <casacore/measures/TableMeasures/ArrayMeasColumn.h>

using everybeam::CorrectionMode;
using everybeam::ParseCorrectionMode;
using everybeam::Station;
using everybeam::TelescopeType;
using everybeam::ToString;
using everybeam::griddedresponse::AartfaacGrid;
using everybeam::griddedresponse::GriddedResponse;
using everybeam::pointresponse::AartfaacPoint;
using everybeam::pointresponse::PointResponse;

namespace everybeam::telescope {

namespace {
Options SetTelescopeOptions(const casacore::MeasurementSet& ms,
                            const Options& options) {
  Options new_options = options;

  if (GetTelescopeType(ms) == TelescopeType::kAARTFAAC) {
    switch (options.element_response_model) {
      case ElementResponseModel::kDefault:
      case ElementResponseModel::kHamaker:
        new_options.element_response_model = ElementResponseModel::kHamakerLba;
        break;
      case ElementResponseModel::kHamakerLba:
      case ElementResponseModel::kLOBES:
        break;
      default:
        throw std::runtime_error(
            "Selected element response model not supported for AARTFAAC");
    }
  } else {
    if (options.element_response_model == ElementResponseModel::kDefault) {
      new_options.element_response_model = ElementResponseModel::kHamaker;
    }
  }
  return new_options;
}
}  // namespace

LOFAR::LOFAR(const casacore::MeasurementSet& ms, const Options& options)
    : PhasedArray(ms, SetTelescopeOptions(ms, options)) {
  const TelescopeType telescope_type = GetTelescopeType(ms);
  if (telescope_type == TelescopeType::kAARTFAAC) {
    is_aartfaac_ = true;

    const casacore::ScalarColumn<casacore::String> antenna_type_column(
        ms.observation(), everybeam::kAartfaacAntennaTypeName);
    const std::string antenna_type = antenna_type_column(0);

    if (antenna_type != "LBA") {
      throw std::runtime_error(
          "Currently, AARTFAAC is only supported for LBA observations");
    }
  }

  // Following is ms.field() related, first check whether field complies with
  // LOFAR field
  if (ms.field().nrow() != 1) {
    throw std::runtime_error("LOFAR MeasurementSet has multiple fields");
  }

  if (!is_aartfaac_) {
    if (!ms.field().tableDesc().isColumn("LOFAR_TILE_BEAM_DIR")) {
      throw std::runtime_error("LOFAR_TILE_BEAM_DIR column not found");
    }
  }

  // Set PhasedArray properties.
  SetBand(aocommon::BandData(ms.spectralWindow()));

  casacore::ScalarMeasColumn<casacore::MDirection> delay_dir_col(
      ms.field(),
      casacore::MSField::columnName(casacore::MSFieldEnums::DELAY_DIR));
  SetDelayDirection(delay_dir_col(0));

  CalculatePreappliedBeamOptions(ms);

  if (is_aartfaac_) {
    // Just fill with arbitrary value for AARTFAAC
    casacore::ScalarMeasColumn<casacore::MDirection> reference_dir_col(
        ms.field(),
        casacore::MSField::columnName(casacore::MSFieldEnums::REFERENCE_DIR));
    SetTileBeamDirection(reference_dir_col(0));
  } else {
    casacore::ArrayMeasColumn<casacore::MDirection> tile_beam_dir_col(
        ms.field(), "LOFAR_TILE_BEAM_DIR");
    SetTileBeamDirection(*(tile_beam_dir_col(0).data()));
  }
}

std::unique_ptr<GriddedResponse> LOFAR::GetGriddedResponse(
    const aocommon::CoordinateSystem& coordinate_system) const {
  if (is_aartfaac_) {
    return std::make_unique<AartfaacGrid>(*this, coordinate_system);
  } else {
    return PhasedArray::GetGriddedResponse(coordinate_system);
  }
}

std::unique_ptr<PointResponse> LOFAR::GetPointResponse(double time) const {
  if (is_aartfaac_) {
    return std::make_unique<AartfaacPoint>(*this, time);
  } else {
    return PhasedArray::GetPointResponse(time);
  }
}

}  // namespace everybeam::telescope
