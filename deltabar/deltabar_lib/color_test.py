#!/usr/bin/python3

import unittest

from color import Color


class TestSmoke(unittest.TestCase):
  def testConvertingFromHex(self):
    color = Color('#000000', 0.25)
    self.assertEqual(color.rgb, (0.0, 0.0, 0.0))
    self.assertEqual(color.rgba, (0.0, 0.0, 0.0, 0.25))
    self.assertEqual(color.alpha, 0.25)

    color = Color('#ffFFfF')
    self.assertEqual(color.rgb, (1.0, 1.0, 1.0))
    self.assertEqual(color.rgba, (1.0, 1.0, 1.0, 1.0))
    self.assertEqual(color.alpha, 1.0)

    color = Color('#c08040')
    self.assertEqual(color.rgb, (0.75, 0.5, 0.25))
    self.assertEqual(color.rgba, (0.75, 0.5, 0.25, 1.0))
    self.assertEqual(color.alpha, 1.0)

    color = Color('#201000')
    self.assertEqual(color.rgb, (0.125, 0.0625, 0.0))
    self.assertEqual(color.rgba, (0.125, 0.0625, 0.0, 1.0))
    self.assertEqual(color.alpha, 1.0)

    color = Color('#b13371')
    self.assertEqual(color.rgb, (177.0 / 255.0, 51.0 / 255.0, 113.0 / 255.0))
    self.assertEqual(color.rgba, (177.0 / 255.0, 51.0 / 255.0, 113.0 / 255.0, 1.0))
    self.assertEqual(color.alpha, 1.0)

    color = Color('#f9E001')
    self.assertEqual(color.rgb, (249.0 / 255.0, 224.0 / 255.0, 1.0 / 255.0))
    self.assertEqual(color.rgba, (249.0 / 255.0, 224.0 / 255.0, 1.0 / 255.0, 1.0))
    self.assertEqual(color.alpha, 1.0)

  def testConvertingFromShortHex(self):
    color = Color('#fff', 0.0)
    self.assertEqual(color.rgb, (1.0, 1.0, 1.0))
    self.assertEqual(color.rgba, (1.0, 1.0, 1.0, 0.0))
    self.assertEqual(color.alpha, 0.0)

  def testInitializingWithRGBAndAlpha(self):
    color = Color((1.0, 0.5, 0.125), 0.3)
    self.assertEqual(color.rgb, (1.0, 0.5, 0.125))
    self.assertEqual(color.rgba, (1.0, 0.5, 0.125, 0.3))
    self.assertEqual(color.alpha, 0.3)

  def testInitializingWithIntegers(self):
    color = Color('#fff', 0)
    self.assertEqual(color.rgb, (1.0, 1.0, 1.0))
    self.assertEqual(color.rgba, (1.0, 1.0, 1.0, 0.0))
    self.assertEqual(color.alpha, 0.0)

    color = Color((1, 1, 1), 0)
    self.assertEqual(color.rgb, (1.0, 1.0, 1.0))
    self.assertEqual(color.rgba, (1.0, 1.0, 1.0, 0.0))
    self.assertEqual(color.alpha, 0.0)

  def testRaisesTypeErrorIfValueHasUnexpectedType(self):
    with self.assertRaises(Exception):
      Color({'red': 1.0, 'green': 1.0, 'blue': 1.0})
    with self.assertRaises(Exception):
      Color({'red': 1.0, 'green': 1.0, 'blue': 1.0}, 0.0)

  def testRaisesIfValuesAreOutOfRange(self):
    with self.assertRaises(Exception):
      Color('#ffffff', 255.0)
    with self.assertRaises(Exception):
      Color((255.0, 1.0, 1.0), 0.0)
    with self.assertRaises(Exception):
      Color((1.0, 255.0, 1.0), 0.0)
    with self.assertRaises(Exception):
      Color((1.0, 1.0, 255.0), 0.0)

  def testRaisesIfColorFormatIsUnexpected(self):
    with self.assertRaises(Exception):
      Color('fff')
    with self.assertRaises(Exception):
      Color('ffffff')
    with self.assertRaises(Exception):
      Color('1.0,1.0,1.0')


if __name__ == '__main__':
  unittest.main()
