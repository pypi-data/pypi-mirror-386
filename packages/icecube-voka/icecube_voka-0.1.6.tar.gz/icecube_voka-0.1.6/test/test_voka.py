#!/usr/bin/env python3
'''
Module that tests the main voka class 'model'
'''

import unittest
import random

import numpy

import voka.model

class TestVoka(unittest.TestCase):
    '''
    Test class that tests the main voka model.
    '''

    def setUp(self):
        dist_mean = 0.
        sigma = 1.

        histogram_names = ["Histogram%d" % i for i in range(100)]
        self.test_hist = dict()
        for name in histogram_names:
            dist = [random.gauss(dist_mean, sigma) for _ in range(1000)]
            self.test_hist[name] = numpy.histogram(dist)[0]

        reference_names = ["ReferenceRun%d" % i for i in range(5)]
        self.reference_collection = {name:dict() for name in reference_names}
        for reference_name in reference_names:
            # For each run generate a set of histograms
            # with the same structure and names as the test histograms

            for name in histogram_names:
                dist = [random.gauss(dist_mean, sigma) for _ in range(1000)]
                self.reference_collection[reference_name][name] =\
                    numpy.histogram(dist)[0]

    def test_voka(self):
        model = voka.model.Voka()
        model.train(self.reference_collection)
        result = model.execute(self.test_hist)
        self.assertTrue(len(result) == 100)

if __name__ == '__main__':
    unittest.main()
