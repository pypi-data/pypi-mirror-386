#!/usr/bin/env python
'''
Tests the LOF function.
'''

import unittest

import random
import numpy

import voka.lof

class TestLOF(unittest.TestCase):
    '''
    Test the LOF function.  Generate dummy histograms
    and ensure the algorithm runs as expected.

    The LOF function takes a test point, a k-distance,
    and a cluster (i.e. benchmark).  For test 'point'
    and benchmark we use histograms here since that's
    the focus and main input of this project.
    '''
    def setUp(self):
        '''
        Generate a test point and benchmark set.
        Sampling from a Gaussian distribution.
        '''
        dist_mean = 0.
        sigma = 1.

        self.test_hist = numpy.histogram([random.gauss(dist_mean, sigma)
                                          for _ in range(1000)])[0]
        self.reference_collection = \
            [numpy.histogram([random.gauss(dist_mean, sigma)
                              for i in range(1000)])[0]
             for j in range(5)]

    def test_lof_basic_exection(self):
        '''
        Execute the fuction.
        TODO: Test other distributions and k-distances.
              Test for pathological inputs and ensure the fail
              in a sane manner.
        '''
        k_distance = 3
        result = voka.lof.local_outlier_factor(self.test_hist,
                                               k_distance,
                                               self.reference_collection)
        self.assertFalse(numpy.isnan(result))

if __name__ == '__main__':
    unittest.main()
