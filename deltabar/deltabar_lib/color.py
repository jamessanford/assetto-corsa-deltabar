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

import re


class Color:
  """
  Use this class for color format conversions.
  """

  def __init__(self, rgb_value, alpha=1.0):
    """
    :param rgb_value: RGB color value. Use 3-tuple of floats in range [0..1] or hexadecimal color string.
    :param alpha: alpha component (opacity). Should be float in range [0..1].
    """
    self.rgb = None
    self.rgba = None
    self.alpha = float(alpha)

    if isinstance(rgb_value, str):
      rgb = self._rgb_from_hex(rgb_value)
      self._initialize(rgb)
    elif isinstance(rgb_value, tuple):
      self._initialize(rgb_value)
    else:
      raise TypeError('rgb_value should be a 3-tuple of floats in range [0..1] or hexadecimal color string')

  def _initialize(self, rgb):
    self.rgb = tuple(float(component) for component in rgb)
    self.rgba = self._rgba_from_rgb_alpha(self.rgb, self.alpha)

    for component in self.rgba:
      self._check_color_component_range(component)

  @staticmethod
  def _check_color_component_range(component):
    if component < 0 or component > 1:
      raise AssertionError('color component should be a float in range [0..1]')

  @staticmethod
  def _rgba_from_rgb_alpha(rgb, alpha):
    """
    Constructs RGBA value from RGB and alpha.
    """
    return rgb + (alpha,)

  @staticmethod
  def _rgb_from_hex(hex_value):
    """
    Converts a hexadecimal color value to a 3-tuple of floats.
    :type hex_value: str
    """
    return Color._rgb_to_rgb_float(Color._hex_to_rgb_integer(hex_value))

  @staticmethod
  def _hex_to_rgb_integer(hex_value):
    """
    Converts a hexadecimal color value to a 3-tuple of integers.
    :type hex_value: str
    """
    hex_value = Color._normalize_hex(hex_value)
    hex_value = int(hex_value[1:], 16)
    return (hex_value >> 16,
            hex_value >> 8 & 0xff,
            hex_value & 0xff)

  @staticmethod
  def _normalize_hex(hex_value):
    """
    Normalizes a hexadecimal color value to 6 digits, lowercase.
    """
    regex = re.compile(r'^#([a-fA-F0-9]{3}|[a-fA-F0-9]{6})$')
    match = regex.match(hex_value)
    if match is None:
      raise ValueError('"%s" is not a valid hexadecimal color value' % hex_value)
    hex_digits = str(match.group(1))
    if len(hex_digits) == 3:
      hex_digits = ''.join(2 * s for s in hex_digits)
    return '#%s' % hex_digits.lower()

  @staticmethod
  def _rgb_to_rgb_float(rgb):
    """
    Converts a 3-tuple of integers to a 3-tuple of floats in range [0..1].
    """
    # In order to maintain precision for common values,
    # special-case them.
    specials = {255: 1.0, 192: 0.75, 128: 0.5, 64: 0.25,
                32: 0.125, 16: 0.0625, 0: 0.0}
    return tuple(specials.get(value, value / 255.0)
                 for value in Color._normalize_rgb_integer(rgb))

  @staticmethod
  def _normalize_rgb_integer(rgb):
    """
    Normalizes an integer RGB triplet so that all values are within the range [0..255].
    """
    return tuple(Color._normalize_component_integer(value) for value in rgb)

  @staticmethod
  def _normalize_component_integer(value):
    """
    Normalizes an integer color component so that the value fits within the range [0..255].
    """
    if value < 0:
      return 0
    if value > 255:
      return 255
    return value
