#!/usr/bin/python3

import unittest

import colors


class TestSmoke(unittest.TestCase):
  def testConvertingFromHex(self):
    color = colors.rgba_from_hex('#000000')
    self.assertEqual(color, (0.0, 0.0, 0.0, 1.0))

    color = colors.rgba_from_hex('#ffFFfF')
    self.assertEqual(color, (1.0, 1.0, 1.0, 1.0))

    color = colors.rgba_from_hex('#c08040')
    self.assertEqual(color, (0.75, 0.5, 0.25, 1.0))

    color = colors.rgba_from_hex('#201000')
    self.assertEqual(color, (0.125, 0.0625, 0.0, 1.0))

    color = colors.rgba_from_hex('#b13371')
    self.assertEqual(color, (177.0 / 255.0, 51.0 / 255.0, 113.0 / 255.0, 1.0))

    color = colors.rgba_from_hex('#f9E001')
    self.assertEqual(color, (249.0 / 255.0, 224.0 / 255.0, 1.0 / 255.0, 1.0))

  def testAddingAlpha(self):
    rgb = '#ff8020'
    alpha = 0.3
    color = colors.rgba_from_hex_alpha(rgb, alpha)
    self.assertEqual(color, (1.0, 0.5, 0.125, 0.3))


if __name__ == '__main__':
  unittest.main()
