#!/usr/bin/env python
'''
Module that tests the individual metrics.
'''

import unittest

import random
from math import isnan

import numpy

import voka.compare
import voka.metrics

class TestMetrics(unittest.TestCase):
    '''
    Test class that sets the test conditions and
    tests all the metrics defined in voka.compare.ALL_METRICS
    '''
    def setUp(self):
        hist1 = numpy.histogram([random.gauss(0., 1.)
                                 for _ in range(1000)])
        hist2 = numpy.histogram([random.gauss(0., 1.)
                                 for _ in range(1000)])

        self.gaussian1 = hist1[0]
        self.gaussian2 = hist2[0]

    def test_all(self):
        for metric in voka.compare.ALL_METRICS.values():
            result = metric(self.gaussian1, self.gaussian2)
            self.assertFalse(isnan(result))

    def test_default_compare(self):
        result = voka.compare.compare(self.gaussian1, self.gaussian2)
        self.assertEqual(len(result), 2)
        self.assertTrue('AndersonDarling' in result)
        self.assertTrue('ShapeChiSq' in result)

if __name__ == '__main__':
    unittest.main()
