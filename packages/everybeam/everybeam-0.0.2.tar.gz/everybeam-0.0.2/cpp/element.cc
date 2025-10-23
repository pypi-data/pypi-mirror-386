// Copyright (C) 2022 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "element.h"
#include "common/mathutils.h"

#include <complex>
#include <aocommon/matrix2x2.h>

namespace everybeam {

std::shared_ptr<Antenna> Element::Clone() const {
  auto element_clone = std::make_shared<Element>(coordinate_system_, id_);
  element_clone->enabled_[0] = enabled_[0];
  element_clone->enabled_[1] = enabled_[1];
  return element_clone;
}

void Element::LocalResponse(aocommon::MC2x2* result,
                            const ElementResponse& element_response,
                            [[maybe_unused]] double time,
                            const std::span<const double>& freqs,
                            const vector3r_t& direction, size_t id,
                            const Options& options) const {
  vector2r_t thetaphi = cart2thetaphi(direction);
  for (size_t f = 0; f < freqs.size(); f++) {
    result[f] =
        element_response.Response(id, freqs[f], thetaphi[0], thetaphi[1]);

    if (options.rotate) {
      // cross with unit upward pointing vector {0.0, 0.0, 1.0}
      const vector3r_t e_phi = normalize(cross(direction));
      const vector3r_t e_theta = cross(e_phi, direction);
      result[f] *= {dot(e_theta, options.north), dot(e_theta, options.east),
                    dot(e_phi, options.north), dot(e_phi, options.east)};
    }
  }
}
}  // namespace everybeam
