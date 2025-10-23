// phasedarray.h: Base class for computing the response for phased array
// telescopes (e.g. LOFAR, SKA-LOW)
//
// Copyright (C) 2020 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#ifndef EVERYBEAM_TELESCOPE_PHASEDARRAY_H_
#define EVERYBEAM_TELESCOPE_PHASEDARRAY_H_

#include <memory>
#include <vector>

#include <aocommon/banddata.h>

#include <casacore/measures/Measures/MDirection.h>
#include <casacore/ms/MeasurementSets/MeasurementSet.h>

#include "telescope.h"

#include "../correctionmode.h"
#include "../msreadutils.h"
#include "../station.h"

namespace everybeam {
namespace telescope {

//! PhasedArray telescope class, is parent to OSKAR and LOFAR
class [[gnu::visibility("default")]] PhasedArray : public Telescope {
 public:
  /**
   * @brief Constructs a PhasedArray object.
   *
   * @param ms MeasurementSet, containing station names and positions.
   * @param options Telescope configuration options.
   */
  PhasedArray(const casacore::MeasurementSet& ms, const Options& options)
      : Telescope(ms.antenna().nrow(), options),
        stations_(ReadAllStations(ms, GetOptions())) {}

  /**
   * @brief Constructs a PhasedArray object with specified station positions.
   *
   * @param station_positions Positions in ITRF format: (x, y, z) in meters.
   * @param options Telescope configuration options.
   */
  PhasedArray(const std::vector<vector3r_t>& station_positions,
              const Options& options);

  std::unique_ptr<griddedresponse::GriddedResponse> GetGriddedResponse(
      const aocommon::CoordinateSystem& coordinate_system) const override;

  std::unique_ptr<pointresponse::PointResponse> GetPointResponse(double time)
      const override;

  /**
   * @brief Get station by index
   * @param station_id Station index to retrieve.
   * @return The station with the given index.
   */
  const Station& GetStation(std::size_t station_idx) const {
    assert(station_idx < GetNrStations());
    return *stations_[station_idx];
  }

  casacore::MDirection GetDelayDirection() const { return delay_direction_; }

  virtual casacore::MDirection GetTileBeamDirection() const {
    return tile_beam_direction_;
  };

  CorrectionMode GetPreappliedCorrectionMode() const {
    return preapplied_correction_mode_;
  };

  virtual casacore::MDirection GetPreappliedBeamDirection() const {
    return preapplied_beam_direction_;
  };

  double GetSubbandFrequency() const { return subband_frequency_; };

  size_t GetNrChannels() const { return channel_frequencies_.size(); };

  double GetChannelFrequency(size_t idx) const {
    assert(idx < channel_frequencies_.size());
    return channel_frequencies_[idx];
  };

 protected:
  void ProcessTimeChange(double time) final;
  void CalculatePreappliedBeamOptions(const casacore::MeasurementSet& ms);
  void SetBand(const aocommon::BandData& band);
  void SetDelayDirection(casacore::MDirection direction) {
    delay_direction_ = std::move(direction);
  }
  void SetTileBeamDirection(casacore::MDirection direction) {
    tile_beam_direction_ = std::move(direction);
  }

 private:
  std::vector<std::unique_ptr<Station>> stations_;
  double subband_frequency_;
  std::vector<double> channel_frequencies_;
  casacore::MDirection delay_direction_;
  casacore::MDirection tile_beam_direction_;

  CorrectionMode preapplied_correction_mode_ = CorrectionMode::kNone;
  casacore::MDirection preapplied_beam_direction_;
};
}  // namespace telescope
}  // namespace everybeam
#endif  // EVERYBEAM_TELESCOPE_PHASEDARRAY_H_
