#!/usr/bin/python3

import unittest

import config
import lap
import lap_serialize


class TestInstantiate(unittest.TestCase):
  def testInitial(self):
    testlap = lap.Lap()

  def testAdd(self):
    testlap = lap.Lap()
    testlap.add(0.0, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(testlap.elapsed_seconds[0], 102398)

  def testSerialize(self):
    testlap = lap.Lap()
    testlap.add(0.0, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.07, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    json_str = lap_serialize.encode(testlap)
    restored_lap = lap_serialize.decode(json_str)
    self.assertEqual(restored_lap.offset[1], 0.07)
    self.assertEqual(testlap.__dict__, restored_lap.__dict__)

    # We can mutate the restored lap object and it works...
    restored_lap.add(0.13, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(restored_lap.offset[2], 0.13)

  def testSave(self):
    testlap = lap.Lap()
    # Add 100 points so that load() works
    for offset in range(100):
      testlap.add(offset / 100, 102398 + offset,
                  1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.track = 'vallelunga'
    testlap.car = 'ferrari_458'
    lap_serialize.save(testlap, 'best')

    x = lap_serialize.load('vallelunga', 'ferrari_458', 'best')
    self.assertEqual(x.elapsed_seconds[0], 102398)

  def testLoadFail(self):
    x = lap_serialize.load('trackname', 'carname', 'best')
    self.assertIsNone(x)

  def testJumpLocation(self):
    # If the track position suddenly changes, do not record that data.
    # For example, the Vallelunga pit exit.
    testlap = lap.Lap()
    testlap.add(0.00, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.09, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.13, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(3, len(testlap.offset))
    testlap.add(0.25, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(3, len(testlap.offset))  # The 0.25 point was not added.
    testlap.add(0.26, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(3, len(testlap.offset))  # The 0.26 point was not added.
    testlap.add(0.14, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.15, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.16, 102398, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(6, len(testlap.offset))  # But now we are back on track.

  def testOffsetForElapsed(self):
    testlap = lap.Lap()
    self.assertEqual(0.0, testlap.offset_for_elapsed(1000))
    testlap.add(0.00, 1000, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.09, 1200, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    testlap.add(0.13, 1400, 1.032, 0.88, 0.01, 0.0, 1, 2013013)
    self.assertEqual(0.09, testlap.offset_for_elapsed(1200))
    self.assertEqual(0.09, testlap.offset_for_elapsed(1300))
    self.assertEqual(0.13, testlap.offset_for_elapsed(1400))
    self.assertEqual(0.13, testlap.offset_for_elapsed(1450))

if __name__ == '__main__':
  unittest.main()
