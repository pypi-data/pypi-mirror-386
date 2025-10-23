/* -== file: vm.hpp ==- */
/*******************************************************************************
* Copyright (C) 2019 Intel Corporation
*
* This software and the related documents are Intel copyrighted  materials,  and
* your use of  them is  governed by the  express license  under which  they were
* provided to you (License).  Unless the License provides otherwise, you may not
* use, modify, copy, publish, distribute,  disclose or transmit this software or
* the related documents without Intel's prior written permission.
*
* This software and the related documents  are provided as  is,  with no express
* or implied  warranties,  other  than those  that are  expressly stated  in the
* License.
*******************************************************************************/


#ifndef ONEAPI_MKL_VM_DEVICE_VM_HPP
#define ONEAPI_MKL_VM_DEVICE_VM_HPP 1


#include "oneapi/mkl/vm/device/detail/api.hpp"

namespace oneapi::mkl::vm::device {

namespace mode {

using detail::mode::ep;
using detail::mode::la;
using detail::mode::ha;
using detail::mode::not_defined;

} // mode

// === compile-time dispatch ===
using oneapi::mkl::vm::device::detail::abs;
using oneapi::mkl::vm::device::detail::acos;
using oneapi::mkl::vm::device::detail::acosh;
using oneapi::mkl::vm::device::detail::acospi;
using oneapi::mkl::vm::device::detail::add;
using oneapi::mkl::vm::device::detail::arg;
using oneapi::mkl::vm::device::detail::asin;
using oneapi::mkl::vm::device::detail::asinh;
using oneapi::mkl::vm::device::detail::asinpi;
using oneapi::mkl::vm::device::detail::atan;
using oneapi::mkl::vm::device::detail::atan2;
using oneapi::mkl::vm::device::detail::atan2pi;
using oneapi::mkl::vm::device::detail::atanh;
using oneapi::mkl::vm::device::detail::atanpi;
using oneapi::mkl::vm::device::detail::cbrt;
using oneapi::mkl::vm::device::detail::cdfnorm;
using oneapi::mkl::vm::device::detail::cdfnorminv;
using oneapi::mkl::vm::device::detail::ceil;
using oneapi::mkl::vm::device::detail::cis;
using oneapi::mkl::vm::device::detail::conj;
using oneapi::mkl::vm::device::detail::copysign;
using oneapi::mkl::vm::device::detail::cos;
using oneapi::mkl::vm::device::detail::cosd;
using oneapi::mkl::vm::device::detail::cosh;
using oneapi::mkl::vm::device::detail::cospi;
using oneapi::mkl::vm::device::detail::div;
using oneapi::mkl::vm::device::detail::erf;
using oneapi::mkl::vm::device::detail::erfc;
using oneapi::mkl::vm::device::detail::erfcinv;
using oneapi::mkl::vm::device::detail::erfcx;
using oneapi::mkl::vm::device::detail::erfinv;
using oneapi::mkl::vm::device::detail::exp;
using oneapi::mkl::vm::device::detail::exp10;
using oneapi::mkl::vm::device::detail::exp2;
using oneapi::mkl::vm::device::detail::expint1;
using oneapi::mkl::vm::device::detail::expm1;
using oneapi::mkl::vm::device::detail::fdim;
using oneapi::mkl::vm::device::detail::floor;
using oneapi::mkl::vm::device::detail::fmax;
using oneapi::mkl::vm::device::detail::fmin;
using oneapi::mkl::vm::device::detail::fmod;
using oneapi::mkl::vm::device::detail::frac;
using oneapi::mkl::vm::device::detail::hypot;
using oneapi::mkl::vm::device::detail::i0;
using oneapi::mkl::vm::device::detail::i1;
using oneapi::mkl::vm::device::detail::inv;
using oneapi::mkl::vm::device::detail::invcbrt;
using oneapi::mkl::vm::device::detail::invsqrt;
using oneapi::mkl::vm::device::detail::j0;
using oneapi::mkl::vm::device::detail::j1;
using oneapi::mkl::vm::device::detail::jn;
using oneapi::mkl::vm::device::detail::lgamma;
using oneapi::mkl::vm::device::detail::linearfrac;
using oneapi::mkl::vm::device::detail::ln;
using oneapi::mkl::vm::device::detail::log10;
using oneapi::mkl::vm::device::detail::log1p;
using oneapi::mkl::vm::device::detail::log2;
using oneapi::mkl::vm::device::detail::logb;
using oneapi::mkl::vm::device::detail::maxmag;
using oneapi::mkl::vm::device::detail::minmag;
using oneapi::mkl::vm::device::detail::modf;
using oneapi::mkl::vm::device::detail::mul;
using oneapi::mkl::vm::device::detail::mulbyconj;
using oneapi::mkl::vm::device::detail::nearbyint;
using oneapi::mkl::vm::device::detail::nextafter;
using oneapi::mkl::vm::device::detail::pow;
using oneapi::mkl::vm::device::detail::pow2o3;
using oneapi::mkl::vm::device::detail::pow3o2;
using oneapi::mkl::vm::device::detail::powr;
using oneapi::mkl::vm::device::detail::powx;
using oneapi::mkl::vm::device::detail::remainder;
using oneapi::mkl::vm::device::detail::rint;
using oneapi::mkl::vm::device::detail::round;
using oneapi::mkl::vm::device::detail::sin;
using oneapi::mkl::vm::device::detail::sincos;
using oneapi::mkl::vm::device::detail::sincospi;
using oneapi::mkl::vm::device::detail::sind;
using oneapi::mkl::vm::device::detail::sinh;
using oneapi::mkl::vm::device::detail::sinpi;
using oneapi::mkl::vm::device::detail::sqr;
using oneapi::mkl::vm::device::detail::sqrt;
using oneapi::mkl::vm::device::detail::sub;
using oneapi::mkl::vm::device::detail::tan;
using oneapi::mkl::vm::device::detail::tand;
using oneapi::mkl::vm::device::detail::tanh;
using oneapi::mkl::vm::device::detail::tanpi;
using oneapi::mkl::vm::device::detail::tgamma;
using oneapi::mkl::vm::device::detail::trunc;
using oneapi::mkl::vm::device::detail::y0;
using oneapi::mkl::vm::device::detail::y1;
using oneapi::mkl::vm::device::detail::yn;

// === explicit accuracy NOT_DEFINED ===
namespace ep {

using oneapi::mkl::vm::device::detail::ep::abs;
using oneapi::mkl::vm::device::detail::ep::acos;
using oneapi::mkl::vm::device::detail::ep::acosh;
using oneapi::mkl::vm::device::detail::ep::acospi;
using oneapi::mkl::vm::device::detail::ep::add;
using oneapi::mkl::vm::device::detail::ep::arg;
using oneapi::mkl::vm::device::detail::ep::asin;
using oneapi::mkl::vm::device::detail::ep::asinh;
using oneapi::mkl::vm::device::detail::ep::asinpi;
using oneapi::mkl::vm::device::detail::ep::atan;
using oneapi::mkl::vm::device::detail::ep::atan2;
using oneapi::mkl::vm::device::detail::ep::atan2pi;
using oneapi::mkl::vm::device::detail::ep::atanh;
using oneapi::mkl::vm::device::detail::ep::atanpi;
using oneapi::mkl::vm::device::detail::ep::cbrt;
using oneapi::mkl::vm::device::detail::ep::cdfnorm;
using oneapi::mkl::vm::device::detail::ep::cdfnorminv;
using oneapi::mkl::vm::device::detail::ep::ceil;
using oneapi::mkl::vm::device::detail::ep::cis;
using oneapi::mkl::vm::device::detail::ep::conj;
using oneapi::mkl::vm::device::detail::ep::copysign;
using oneapi::mkl::vm::device::detail::ep::cos;
using oneapi::mkl::vm::device::detail::ep::cosd;
using oneapi::mkl::vm::device::detail::ep::cosh;
using oneapi::mkl::vm::device::detail::ep::cospi;
using oneapi::mkl::vm::device::detail::ep::div;
using oneapi::mkl::vm::device::detail::ep::erf;
using oneapi::mkl::vm::device::detail::ep::erfc;
using oneapi::mkl::vm::device::detail::ep::erfcinv;
using oneapi::mkl::vm::device::detail::ep::erfcx;
using oneapi::mkl::vm::device::detail::ep::erfinv;
using oneapi::mkl::vm::device::detail::ep::exp;
using oneapi::mkl::vm::device::detail::ep::exp10;
using oneapi::mkl::vm::device::detail::ep::exp2;
using oneapi::mkl::vm::device::detail::ep::expint1;
using oneapi::mkl::vm::device::detail::ep::expm1;
using oneapi::mkl::vm::device::detail::ep::fdim;
using oneapi::mkl::vm::device::detail::ep::floor;
using oneapi::mkl::vm::device::detail::ep::fmax;
using oneapi::mkl::vm::device::detail::ep::fmin;
using oneapi::mkl::vm::device::detail::ep::fmod;
using oneapi::mkl::vm::device::detail::ep::frac;
using oneapi::mkl::vm::device::detail::ep::hypot;
using oneapi::mkl::vm::device::detail::ep::i0;
using oneapi::mkl::vm::device::detail::ep::i1;
using oneapi::mkl::vm::device::detail::ep::inv;
using oneapi::mkl::vm::device::detail::ep::invcbrt;
using oneapi::mkl::vm::device::detail::ep::invsqrt;
using oneapi::mkl::vm::device::detail::ep::j0;
using oneapi::mkl::vm::device::detail::ep::j1;
using oneapi::mkl::vm::device::detail::ep::jn;
using oneapi::mkl::vm::device::detail::ep::lgamma;
using oneapi::mkl::vm::device::detail::ep::linearfrac;
using oneapi::mkl::vm::device::detail::ep::ln;
using oneapi::mkl::vm::device::detail::ep::log10;
using oneapi::mkl::vm::device::detail::ep::log1p;
using oneapi::mkl::vm::device::detail::ep::log2;
using oneapi::mkl::vm::device::detail::ep::logb;
using oneapi::mkl::vm::device::detail::ep::maxmag;
using oneapi::mkl::vm::device::detail::ep::minmag;
using oneapi::mkl::vm::device::detail::ep::modf;
using oneapi::mkl::vm::device::detail::ep::mul;
using oneapi::mkl::vm::device::detail::ep::mulbyconj;
using oneapi::mkl::vm::device::detail::ep::nearbyint;
using oneapi::mkl::vm::device::detail::ep::nextafter;
using oneapi::mkl::vm::device::detail::ep::pow;
using oneapi::mkl::vm::device::detail::ep::pow2o3;
using oneapi::mkl::vm::device::detail::ep::pow3o2;
using oneapi::mkl::vm::device::detail::ep::powr;
using oneapi::mkl::vm::device::detail::ep::powx;
using oneapi::mkl::vm::device::detail::ep::remainder;
using oneapi::mkl::vm::device::detail::ep::rint;
using oneapi::mkl::vm::device::detail::ep::round;
using oneapi::mkl::vm::device::detail::ep::sin;
using oneapi::mkl::vm::device::detail::ep::sincos;
using oneapi::mkl::vm::device::detail::ep::sincospi;
using oneapi::mkl::vm::device::detail::ep::sind;
using oneapi::mkl::vm::device::detail::ep::sinh;
using oneapi::mkl::vm::device::detail::ep::sinpi;
using oneapi::mkl::vm::device::detail::ep::sqr;
using oneapi::mkl::vm::device::detail::ep::sqrt;
using oneapi::mkl::vm::device::detail::ep::sub;
using oneapi::mkl::vm::device::detail::ep::tan;
using oneapi::mkl::vm::device::detail::ep::tand;
using oneapi::mkl::vm::device::detail::ep::tanh;
using oneapi::mkl::vm::device::detail::ep::tanpi;
using oneapi::mkl::vm::device::detail::ep::tgamma;
using oneapi::mkl::vm::device::detail::ep::trunc;
using oneapi::mkl::vm::device::detail::ep::y0;
using oneapi::mkl::vm::device::detail::ep::y1;
using oneapi::mkl::vm::device::detail::ep::yn;

} // ep

// === explicit accuracy NOT_DEFINED ===
namespace la {

using oneapi::mkl::vm::device::detail::la::abs;
using oneapi::mkl::vm::device::detail::la::acos;
using oneapi::mkl::vm::device::detail::la::acosh;
using oneapi::mkl::vm::device::detail::la::acospi;
using oneapi::mkl::vm::device::detail::la::add;
using oneapi::mkl::vm::device::detail::la::arg;
using oneapi::mkl::vm::device::detail::la::asin;
using oneapi::mkl::vm::device::detail::la::asinh;
using oneapi::mkl::vm::device::detail::la::asinpi;
using oneapi::mkl::vm::device::detail::la::atan;
using oneapi::mkl::vm::device::detail::la::atan2;
using oneapi::mkl::vm::device::detail::la::atan2pi;
using oneapi::mkl::vm::device::detail::la::atanh;
using oneapi::mkl::vm::device::detail::la::atanpi;
using oneapi::mkl::vm::device::detail::la::cbrt;
using oneapi::mkl::vm::device::detail::la::cdfnorm;
using oneapi::mkl::vm::device::detail::la::cdfnorminv;
using oneapi::mkl::vm::device::detail::la::ceil;
using oneapi::mkl::vm::device::detail::la::cis;
using oneapi::mkl::vm::device::detail::la::conj;
using oneapi::mkl::vm::device::detail::la::copysign;
using oneapi::mkl::vm::device::detail::la::cos;
using oneapi::mkl::vm::device::detail::la::cosd;
using oneapi::mkl::vm::device::detail::la::cosh;
using oneapi::mkl::vm::device::detail::la::cospi;
using oneapi::mkl::vm::device::detail::la::div;
using oneapi::mkl::vm::device::detail::la::erf;
using oneapi::mkl::vm::device::detail::la::erfc;
using oneapi::mkl::vm::device::detail::la::erfcinv;
using oneapi::mkl::vm::device::detail::la::erfcx;
using oneapi::mkl::vm::device::detail::la::erfinv;
using oneapi::mkl::vm::device::detail::la::exp;
using oneapi::mkl::vm::device::detail::la::exp10;
using oneapi::mkl::vm::device::detail::la::exp2;
using oneapi::mkl::vm::device::detail::la::expint1;
using oneapi::mkl::vm::device::detail::la::expm1;
using oneapi::mkl::vm::device::detail::la::fdim;
using oneapi::mkl::vm::device::detail::la::floor;
using oneapi::mkl::vm::device::detail::la::fmax;
using oneapi::mkl::vm::device::detail::la::fmin;
using oneapi::mkl::vm::device::detail::la::fmod;
using oneapi::mkl::vm::device::detail::la::frac;
using oneapi::mkl::vm::device::detail::la::hypot;
using oneapi::mkl::vm::device::detail::la::i0;
using oneapi::mkl::vm::device::detail::la::i1;
using oneapi::mkl::vm::device::detail::la::inv;
using oneapi::mkl::vm::device::detail::la::invcbrt;
using oneapi::mkl::vm::device::detail::la::invsqrt;
using oneapi::mkl::vm::device::detail::la::j0;
using oneapi::mkl::vm::device::detail::la::j1;
using oneapi::mkl::vm::device::detail::la::jn;
using oneapi::mkl::vm::device::detail::la::lgamma;
using oneapi::mkl::vm::device::detail::la::linearfrac;
using oneapi::mkl::vm::device::detail::la::ln;
using oneapi::mkl::vm::device::detail::la::log10;
using oneapi::mkl::vm::device::detail::la::log1p;
using oneapi::mkl::vm::device::detail::la::log2;
using oneapi::mkl::vm::device::detail::la::logb;
using oneapi::mkl::vm::device::detail::la::maxmag;
using oneapi::mkl::vm::device::detail::la::minmag;
using oneapi::mkl::vm::device::detail::la::modf;
using oneapi::mkl::vm::device::detail::la::mul;
using oneapi::mkl::vm::device::detail::la::mulbyconj;
using oneapi::mkl::vm::device::detail::la::nearbyint;
using oneapi::mkl::vm::device::detail::la::nextafter;
using oneapi::mkl::vm::device::detail::la::pow;
using oneapi::mkl::vm::device::detail::la::pow2o3;
using oneapi::mkl::vm::device::detail::la::pow3o2;
using oneapi::mkl::vm::device::detail::la::powr;
using oneapi::mkl::vm::device::detail::la::powx;
using oneapi::mkl::vm::device::detail::la::remainder;
using oneapi::mkl::vm::device::detail::la::rint;
using oneapi::mkl::vm::device::detail::la::round;
using oneapi::mkl::vm::device::detail::la::sin;
using oneapi::mkl::vm::device::detail::la::sincos;
using oneapi::mkl::vm::device::detail::la::sincospi;
using oneapi::mkl::vm::device::detail::la::sind;
using oneapi::mkl::vm::device::detail::la::sinh;
using oneapi::mkl::vm::device::detail::la::sinpi;
using oneapi::mkl::vm::device::detail::la::sqr;
using oneapi::mkl::vm::device::detail::la::sqrt;
using oneapi::mkl::vm::device::detail::la::sub;
using oneapi::mkl::vm::device::detail::la::tan;
using oneapi::mkl::vm::device::detail::la::tand;
using oneapi::mkl::vm::device::detail::la::tanh;
using oneapi::mkl::vm::device::detail::la::tanpi;
using oneapi::mkl::vm::device::detail::la::tgamma;
using oneapi::mkl::vm::device::detail::la::trunc;
using oneapi::mkl::vm::device::detail::la::y0;
using oneapi::mkl::vm::device::detail::la::y1;
using oneapi::mkl::vm::device::detail::la::yn;

} // la

// === explicit accuracy NOT_DEFINED ===
namespace ha {

using oneapi::mkl::vm::device::detail::ha::abs;
using oneapi::mkl::vm::device::detail::ha::acos;
using oneapi::mkl::vm::device::detail::ha::acosh;
using oneapi::mkl::vm::device::detail::ha::acospi;
using oneapi::mkl::vm::device::detail::ha::add;
using oneapi::mkl::vm::device::detail::ha::arg;
using oneapi::mkl::vm::device::detail::ha::asin;
using oneapi::mkl::vm::device::detail::ha::asinh;
using oneapi::mkl::vm::device::detail::ha::asinpi;
using oneapi::mkl::vm::device::detail::ha::atan;
using oneapi::mkl::vm::device::detail::ha::atan2;
using oneapi::mkl::vm::device::detail::ha::atan2pi;
using oneapi::mkl::vm::device::detail::ha::atanh;
using oneapi::mkl::vm::device::detail::ha::atanpi;
using oneapi::mkl::vm::device::detail::ha::cbrt;
using oneapi::mkl::vm::device::detail::ha::cdfnorm;
using oneapi::mkl::vm::device::detail::ha::cdfnorminv;
using oneapi::mkl::vm::device::detail::ha::ceil;
using oneapi::mkl::vm::device::detail::ha::cis;
using oneapi::mkl::vm::device::detail::ha::conj;
using oneapi::mkl::vm::device::detail::ha::copysign;
using oneapi::mkl::vm::device::detail::ha::cos;
using oneapi::mkl::vm::device::detail::ha::cosd;
using oneapi::mkl::vm::device::detail::ha::cosh;
using oneapi::mkl::vm::device::detail::ha::cospi;
using oneapi::mkl::vm::device::detail::ha::div;
using oneapi::mkl::vm::device::detail::ha::erf;
using oneapi::mkl::vm::device::detail::ha::erfc;
using oneapi::mkl::vm::device::detail::ha::erfcinv;
using oneapi::mkl::vm::device::detail::ha::erfcx;
using oneapi::mkl::vm::device::detail::ha::erfinv;
using oneapi::mkl::vm::device::detail::ha::exp;
using oneapi::mkl::vm::device::detail::ha::exp10;
using oneapi::mkl::vm::device::detail::ha::exp2;
using oneapi::mkl::vm::device::detail::ha::expint1;
using oneapi::mkl::vm::device::detail::ha::expm1;
using oneapi::mkl::vm::device::detail::ha::fdim;
using oneapi::mkl::vm::device::detail::ha::floor;
using oneapi::mkl::vm::device::detail::ha::fmax;
using oneapi::mkl::vm::device::detail::ha::fmin;
using oneapi::mkl::vm::device::detail::ha::fmod;
using oneapi::mkl::vm::device::detail::ha::frac;
using oneapi::mkl::vm::device::detail::ha::hypot;
using oneapi::mkl::vm::device::detail::ha::i0;
using oneapi::mkl::vm::device::detail::ha::i1;
using oneapi::mkl::vm::device::detail::ha::inv;
using oneapi::mkl::vm::device::detail::ha::invcbrt;
using oneapi::mkl::vm::device::detail::ha::invsqrt;
using oneapi::mkl::vm::device::detail::ha::j0;
using oneapi::mkl::vm::device::detail::ha::j1;
using oneapi::mkl::vm::device::detail::ha::jn;
using oneapi::mkl::vm::device::detail::ha::lgamma;
using oneapi::mkl::vm::device::detail::ha::linearfrac;
using oneapi::mkl::vm::device::detail::ha::ln;
using oneapi::mkl::vm::device::detail::ha::log10;
using oneapi::mkl::vm::device::detail::ha::log1p;
using oneapi::mkl::vm::device::detail::ha::log2;
using oneapi::mkl::vm::device::detail::ha::logb;
using oneapi::mkl::vm::device::detail::ha::maxmag;
using oneapi::mkl::vm::device::detail::ha::minmag;
using oneapi::mkl::vm::device::detail::ha::modf;
using oneapi::mkl::vm::device::detail::ha::mul;
using oneapi::mkl::vm::device::detail::ha::mulbyconj;
using oneapi::mkl::vm::device::detail::ha::nearbyint;
using oneapi::mkl::vm::device::detail::ha::nextafter;
using oneapi::mkl::vm::device::detail::ha::pow;
using oneapi::mkl::vm::device::detail::ha::pow2o3;
using oneapi::mkl::vm::device::detail::ha::pow3o2;
using oneapi::mkl::vm::device::detail::ha::powr;
using oneapi::mkl::vm::device::detail::ha::powx;
using oneapi::mkl::vm::device::detail::ha::remainder;
using oneapi::mkl::vm::device::detail::ha::rint;
using oneapi::mkl::vm::device::detail::ha::round;
using oneapi::mkl::vm::device::detail::ha::sin;
using oneapi::mkl::vm::device::detail::ha::sincos;
using oneapi::mkl::vm::device::detail::ha::sincospi;
using oneapi::mkl::vm::device::detail::ha::sind;
using oneapi::mkl::vm::device::detail::ha::sinh;
using oneapi::mkl::vm::device::detail::ha::sinpi;
using oneapi::mkl::vm::device::detail::ha::sqr;
using oneapi::mkl::vm::device::detail::ha::sqrt;
using oneapi::mkl::vm::device::detail::ha::sub;
using oneapi::mkl::vm::device::detail::ha::tan;
using oneapi::mkl::vm::device::detail::ha::tand;
using oneapi::mkl::vm::device::detail::ha::tanh;
using oneapi::mkl::vm::device::detail::ha::tanpi;
using oneapi::mkl::vm::device::detail::ha::tgamma;
using oneapi::mkl::vm::device::detail::ha::trunc;
using oneapi::mkl::vm::device::detail::ha::y0;
using oneapi::mkl::vm::device::detail::ha::y1;
using oneapi::mkl::vm::device::detail::ha::yn;

} // ha

// === runtime selector (RTS) ===
using oneapi::mkl::vm::device::detail::rts::abs;
using oneapi::mkl::vm::device::detail::rts::acos;
using oneapi::mkl::vm::device::detail::rts::acosh;
using oneapi::mkl::vm::device::detail::rts::acospi;
using oneapi::mkl::vm::device::detail::rts::add;
using oneapi::mkl::vm::device::detail::rts::arg;
using oneapi::mkl::vm::device::detail::rts::asin;
using oneapi::mkl::vm::device::detail::rts::asinh;
using oneapi::mkl::vm::device::detail::rts::asinpi;
using oneapi::mkl::vm::device::detail::rts::atan;
using oneapi::mkl::vm::device::detail::rts::atan2;
using oneapi::mkl::vm::device::detail::rts::atan2pi;
using oneapi::mkl::vm::device::detail::rts::atanh;
using oneapi::mkl::vm::device::detail::rts::atanpi;
using oneapi::mkl::vm::device::detail::rts::cbrt;
using oneapi::mkl::vm::device::detail::rts::cdfnorm;
using oneapi::mkl::vm::device::detail::rts::cdfnorminv;
using oneapi::mkl::vm::device::detail::rts::ceil;
using oneapi::mkl::vm::device::detail::rts::cis;
using oneapi::mkl::vm::device::detail::rts::conj;
using oneapi::mkl::vm::device::detail::rts::copysign;
using oneapi::mkl::vm::device::detail::rts::cos;
using oneapi::mkl::vm::device::detail::rts::cosd;
using oneapi::mkl::vm::device::detail::rts::cosh;
using oneapi::mkl::vm::device::detail::rts::cospi;
using oneapi::mkl::vm::device::detail::rts::div;
using oneapi::mkl::vm::device::detail::rts::erf;
using oneapi::mkl::vm::device::detail::rts::erfc;
using oneapi::mkl::vm::device::detail::rts::erfcinv;
using oneapi::mkl::vm::device::detail::rts::erfcx;
using oneapi::mkl::vm::device::detail::rts::erfinv;
using oneapi::mkl::vm::device::detail::rts::exp;
using oneapi::mkl::vm::device::detail::rts::exp10;
using oneapi::mkl::vm::device::detail::rts::exp2;
using oneapi::mkl::vm::device::detail::rts::expint1;
using oneapi::mkl::vm::device::detail::rts::expm1;
using oneapi::mkl::vm::device::detail::rts::fdim;
using oneapi::mkl::vm::device::detail::rts::floor;
using oneapi::mkl::vm::device::detail::rts::fmax;
using oneapi::mkl::vm::device::detail::rts::fmin;
using oneapi::mkl::vm::device::detail::rts::fmod;
using oneapi::mkl::vm::device::detail::rts::frac;
using oneapi::mkl::vm::device::detail::rts::hypot;
using oneapi::mkl::vm::device::detail::rts::i0;
using oneapi::mkl::vm::device::detail::rts::i1;
using oneapi::mkl::vm::device::detail::rts::inv;
using oneapi::mkl::vm::device::detail::rts::invcbrt;
using oneapi::mkl::vm::device::detail::rts::invsqrt;
using oneapi::mkl::vm::device::detail::rts::j0;
using oneapi::mkl::vm::device::detail::rts::j1;
using oneapi::mkl::vm::device::detail::rts::jn;
using oneapi::mkl::vm::device::detail::rts::lgamma;
using oneapi::mkl::vm::device::detail::rts::linearfrac;
using oneapi::mkl::vm::device::detail::rts::ln;
using oneapi::mkl::vm::device::detail::rts::log10;
using oneapi::mkl::vm::device::detail::rts::log1p;
using oneapi::mkl::vm::device::detail::rts::log2;
using oneapi::mkl::vm::device::detail::rts::logb;
using oneapi::mkl::vm::device::detail::rts::maxmag;
using oneapi::mkl::vm::device::detail::rts::minmag;
using oneapi::mkl::vm::device::detail::rts::modf;
using oneapi::mkl::vm::device::detail::rts::mul;
using oneapi::mkl::vm::device::detail::rts::mulbyconj;
using oneapi::mkl::vm::device::detail::rts::nearbyint;
using oneapi::mkl::vm::device::detail::rts::nextafter;
using oneapi::mkl::vm::device::detail::rts::pow;
using oneapi::mkl::vm::device::detail::rts::pow2o3;
using oneapi::mkl::vm::device::detail::rts::pow3o2;
using oneapi::mkl::vm::device::detail::rts::powr;
using oneapi::mkl::vm::device::detail::rts::powx;
using oneapi::mkl::vm::device::detail::rts::remainder;
using oneapi::mkl::vm::device::detail::rts::rint;
using oneapi::mkl::vm::device::detail::rts::round;
using oneapi::mkl::vm::device::detail::rts::sin;
using oneapi::mkl::vm::device::detail::rts::sincos;
using oneapi::mkl::vm::device::detail::rts::sincospi;
using oneapi::mkl::vm::device::detail::rts::sind;
using oneapi::mkl::vm::device::detail::rts::sinh;
using oneapi::mkl::vm::device::detail::rts::sinpi;
using oneapi::mkl::vm::device::detail::rts::sqr;
using oneapi::mkl::vm::device::detail::rts::sqrt;
using oneapi::mkl::vm::device::detail::rts::sub;
using oneapi::mkl::vm::device::detail::rts::tan;
using oneapi::mkl::vm::device::detail::rts::tand;
using oneapi::mkl::vm::device::detail::rts::tanh;
using oneapi::mkl::vm::device::detail::rts::tanpi;
using oneapi::mkl::vm::device::detail::rts::tgamma;
using oneapi::mkl::vm::device::detail::rts::trunc;
using oneapi::mkl::vm::device::detail::rts::y0;
using oneapi::mkl::vm::device::detail::rts::y1;
using oneapi::mkl::vm::device::detail::rts::yn;


} // oneapi::mkl::vm::device


#endif // ONEAPI_MKL_VM_DEVICE_VM_HPP
