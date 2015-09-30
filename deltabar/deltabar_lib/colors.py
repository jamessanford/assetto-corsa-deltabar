# Utilities for color conversions.
#
# Partly used code from 'webcolors' python module:
# https://github.com/ubernostrum/webcolors
#
# webcolors:
# Copyright (c) 2008-2015, James Bennett
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of the author nor the names of other
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


def rgba_from_rgb_alpha(rgb, alpha):
  """
  Construct RGBA value from RGB and alpha.
  """
  return rgb + (alpha,)


def rgb_from_hex(hex_value):
  """
  Convert a hexadecimal color (#000000) value to a 3-tuple of floats.
  """
  return _rgb_to_rgb_float(_hex_to_rgb_integer(hex_value))


def _hex_to_rgb_integer(hex_value):
  """
  Convert a hexadecimal color (#000000) value to a 3-tuple of integers.
  """
  hex_value = int(hex_value[1:], 16)
  return (hex_value >> 16,
          hex_value >> 8 & 0xff,
          hex_value & 0xff)


def _rgb_to_rgb_float(rgb):
  """
  Convert a 3-tuple of integers to a 3-tuple of floats in range [0..1].
  """
  # In order to maintain precision for common values,
  # special-case them.
  specials = {255: 1.0, 192: 0.75, 128: 0.5, 64: 0.25,
              32: 0.125, 16: 0.0625, 0: 0.0}
  return tuple(specials.get(value, value / 255.0)
               for value in _normalize_rgb_integer(rgb))


def _normalize_rgb_integer(rgb):
  """
  Normalize an integer RGB triplet so that all values are within the range [0..255].
  """
  return tuple(_normalize_component_integer(value) for value in rgb)


def _normalize_component_integer(value):
  """
  Normalize an integer color component so that the value fits within the range [0..255].
  """
  if value < 0:
    return 0
  if value > 255:
    return 255
  return value
