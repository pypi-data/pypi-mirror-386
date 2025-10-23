// Copyright (C) 2020 ASTRON (Netherlands Institute for Radio Astronomy)
// SPDX-License-Identifier: GPL-3.0-or-later

#include "voltagepattern.h"

#include <aocommon/imagecoordinates.h>

#include <cmath>

using aocommon::ImageCoordinates;
using aocommon::UVector;
using everybeam::circularsymmetric::VoltagePattern;

namespace {
double LmMaxSquared(double frequency_hz, double maximum_radius_arc_min) {
  const double factor =
      (180.0 / M_PI) * 60.0 * frequency_hz * 1e-9;  // arcminutes * GHz
  const double rmax = maximum_radius_arc_min / factor;
  return rmax * rmax;
}
}  // namespace

void VoltagePattern::EvaluatePolynomial(const UVector<double>& coefficients,
                                        double reference_frequency,
                                        bool invert) {
  // This comes from casa's: void PBMath1DIPoly::fillPBArray(), wideband case
  constexpr size_t nsamples = 10000;
  const size_t nfreq = frequencies_.size();
  const size_t ncoef = coefficients.size() / nfreq;
  values_.resize(nsamples * nfreq);
  inverse_increment_radius_ = double(nsamples - 1) / maximum_radius_arc_min_;
  double* output = values_.data();
  const double referenced_increment =
      std::sqrt(reference_frequency / 1e9) / inverse_increment_radius_;
  for (size_t n = 0; n != nfreq; n++) {
    const double* freq_coefficients = &coefficients[n * ncoef];
    for (size_t i = 0; i < nsamples; i++) {
      double taper = 0.0;
      double x2 = double(i) * referenced_increment;
      x2 = x2 * x2;
      double y = 1.0;

      for (size_t j = 0; j < ncoef; j++) {
        taper += y * freq_coefficients[j];
        y *= x2;
      }
      if (taper >= 0.0) {
        if (invert && taper != 0.0) {
          taper = 1.0 / std::sqrt(taper);
        } else {
          taper = std::sqrt(taper);
        }
      } else {
        taper = 0.0;
      }
      *output = taper;
      ++output;
    }
  }
}

void VoltagePattern::EvaluateAiryDisk(double dish_diameter_in_m,
                                      double blocked_diameter_in_m) {
  // Number of evaluated grid points in the 1D radial function
  constexpr size_t n_samples = 10000;
  values_.resize(n_samples);

  inverse_increment_radius_ = double(n_samples - 1) / maximum_radius_arc_min_;

  // This scales the maximum radius from arcminutes on the sky at
  // 1 GHz for a 24.5 m unblocked aperture to the J1 Bessel function
  // coordinates (7.016 at the 2nd null).
  const double dimensionless_max_in_rad = maximum_radius_arc_min_ * 7.016 /
                                          (1.566 * 60.) * dish_diameter_in_m /
                                          24.5;
  const double dimensionless_inverse_in_rad =
      static_cast<double>(n_samples - 1) / dimensionless_max_in_rad;
  if (blocked_diameter_in_m == 0.0) {
    values_[0] = 1.0;
    for (size_t i = 1; i < n_samples; i++) {
      const double x = static_cast<double>(i) / dimensionless_inverse_in_rad;
      values_[i] = 2.0 * std::cyl_bessel_j(1, x) / x;
    }
  } else {
    const double length_ratio = dish_diameter_in_m / blocked_diameter_in_m;
    const double area_ratio = length_ratio * length_ratio;
    const double area_norm = area_ratio - 1.0;
    values_[0] = 1.0;
    for (size_t i = 1; i < n_samples; i++) {
      const double x = static_cast<double>(i) / dimensionless_inverse_in_rad;
      values_[i] =
          (area_ratio * 2.0 * std::cyl_bessel_j(1, x) / x -
           2.0 * std::cyl_bessel_j(1, x * length_ratio) / (x * length_ratio)) /
          area_norm;
    }
  }
}

UVector<double> VoltagePattern::InterpolateValues(double freq) const {
  UVector<double> result;
  size_t ifit = 0;
  size_t nfreq = frequencies_.size();
  for (ifit = 0; ifit != nfreq; ifit++) {
    if (freq <= frequencies_[ifit]) break;
  }
  if (ifit == 0) {
    result.assign(values_.begin(), values_.begin() + NSamples());
  } else if (ifit == nfreq) {
    result.assign(values_.begin() + (nfreq - 1) * NSamples(), values_.end());
  } else {
    size_t n = NSamples();
    double l = (freq - frequencies_[ifit - 1]) /
               (frequencies_[ifit] - frequencies_[ifit - 1]);
    const double* vpA = FreqIndexValues(ifit - 1);
    const double* vpB = FreqIndexValues(ifit);
    result.resize(n);
    for (size_t i = 0; i != n; ++i) {
      result[i] = vpA[i] * (1.0 - l) + vpB[i] * l;
    }
  }
  return result;
}

const double* VoltagePattern::InterpolateValues(
    double frequency_hz, UVector<double>& interpolated_values) const {
  if (frequencies_.size() > 1) {
    interpolated_values = InterpolateValues(frequency_hz);
    return interpolated_values.data();
  } else {
    return FreqIndexValues(0);
  }
}

void VoltagePattern::Render(std::complex<float>* aterm, size_t width,
                            size_t height, double pixel_scale_x,
                            double pixel_scale_y, double phase_centre_ra,
                            double phase_centre_dec, double pointing_ra,
                            double pointing_dec, double phase_centre_dl,
                            double phase_centre_dm, double frequency_hz) const {
  const double lm_max_sq = LmMaxSquared(frequency_hz, maximum_radius_arc_min_);

  UVector<double> interpolated_values;
  const double* vp = InterpolateValues(frequency_hz, interpolated_values);

  const double factor =
      (180.0 / M_PI) * 60.0 * frequency_hz * 1e-9;  // arcminutes * GHz
  double l0, m0;
  ImageCoordinates::RaDecToLM(pointing_ra, pointing_dec, phase_centre_ra,
                              phase_centre_dec, l0, m0);
  l0 += phase_centre_dl;
  m0 += phase_centre_dm;
  for (size_t iy = 0; iy != height; ++iy) {
    std::complex<float>* row = aterm + iy * width * 4;
    for (size_t ix = 0; ix != width; ++ix) {
      double l, m, ra, dec;
      ImageCoordinates::XYToLM(ix, iy, pixel_scale_x, pixel_scale_y, width,
                               height, l, m);
      l += l0;
      m += m0;
      ImageCoordinates::LMToRaDec(l, m, phase_centre_ra, phase_centre_dec, ra,
                                  dec);
      ImageCoordinates::RaDecToLM(ra, dec, pointing_ra, pointing_dec, l, m);
      l -= l0;
      m -= m0;
      double r2 = l * l + m * m;
      double out;
      if (r2 > lm_max_sq || !std::isfinite(r2)) {
        out = 1e-4;
      } else {
        double r = std::sqrt(r2) * factor;
        int indx = int(r * inverse_increment_radius_);
        out = vp[indx] * (1.0 - 1e-4) + 1e-4;
      }

      std::complex<float>* ptr = row + ix * 4;
      ptr[0] = out;
      ptr[1] = 0.0;
      ptr[2] = 0.0;
      ptr[3] = out;
    }
  }
}

void VoltagePattern::Render(std::complex<float>* aterm, double phase_centre_ra,
                            double phase_centre_dec, double pointing_ra,
                            double pointing_dec, double frequency_hz) const {
  const double lm_max_sq = LmMaxSquared(frequency_hz, maximum_radius_arc_min_);

  UVector<double> interpolated_values;
  const double* vp = InterpolateValues(frequency_hz, interpolated_values);

  const double factor =
      (180.0 / M_PI) * 60.0 * frequency_hz * 1e-9;  // arcminutes * GHz

  // TODO: probably not all conversions needed?
  double l0, m0;
  ImageCoordinates::RaDecToLM(pointing_ra, pointing_dec, phase_centre_ra,
                              phase_centre_dec, l0, m0);
  double l = l0;
  double m = m0;
  double ra, dec;
  ImageCoordinates::LMToRaDec(l, m, phase_centre_ra, phase_centre_dec, ra, dec);
  ImageCoordinates::RaDecToLM(ra, dec, pointing_ra, pointing_dec, l, m);
  l -= l0;
  m -= m0;
  const double r2 = l * l + m * m;
  double out;
  if (r2 > lm_max_sq) {
    out = 1e-4;
  } else {
    const double r = std::sqrt(r2) * factor;
    const int indx = int(r * inverse_increment_radius_);
    out = vp[indx] * (1.0 - 1e-4) + 1e-4;
  }

  aterm[0] = out;
  aterm[1] = 0.0;
  aterm[2] = 0.0;
  aterm[3] = out;
}
