#!/usr/bin/python3

import random
import unittest

import config


class TestSmoke(unittest.TestCase):
  def testSaveLoad(self):
    config_dict = { 'a': 0, 'b': { 'random_number': random.random() } }

    config.save(config_dict)

    x = config.load()
    del x['sectors']  # for smoke test only
    self.assertEqual(x, config_dict)

    config_dict['c'] = 5
    config.save(config_dict)

    x = config.load()
    del x['sectors']  # for smoke test only
    self.assertEqual(x, config_dict)

  def testDefaults(self):
    # eww
    original_filename = config.CONFIG_FILENAME
    config.CONFIG_FILENAME = 'does_not_exist_yet'
    try:
      x = config.load()
      self.assertTrue(isinstance(x, dict))
      self.assertTrue('bar_mode' in x, msg=x)
    finally:
      config.CONFIG_FILENAME = original_filename


if __name__ == '__main__':
  unittest.main()
