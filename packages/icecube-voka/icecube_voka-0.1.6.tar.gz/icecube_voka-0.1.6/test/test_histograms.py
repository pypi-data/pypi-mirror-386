import unittest
import os
import sys

from math import sqrt
from math import isnan
import random

import numpy

from voka.histogram import Histogram

class TestHistogram(unittest.TestCase):

    def setUp(self):
        xmin=-5
        xmax=5
        nbins=20
        name='gaussian'
        self.N = 1000
        self.histogram = Histogram(xmin=xmin,
                                   xmax=xmax,
                                   nbins=20,
                                   name='gaussian')

        for _ in range(self.N):
            self.histogram.fill(random.gauss(0., 1.))
        
    def test_fill(self):
        self.assertEqual(sum(self.histogram.bin_values), self.N)
        print(self.histogram.bin_values)
        
    def test_get_state(self):
        state = self.histogram.__getstate__()
        print(state)
        self.assertEqual(state['name'], 'gaussian')            
        self.assertEqual(sum(state['bin_values']), self.N)
        
    def test_set_state(self):
        name = 'possion'
        xmin = 0
        xmax = 10
        nbins = 30
        
        bin_values, _ = numpy.histogram(numpy.random.poisson(5, 1000), bins=nbins, range=(xmin, xmax))
        
        state = {
            "name" : name,
            "xmin" : xmin,
            "xmax" : xmax,
            "overflow" : 0,
            "underflow" : 0,
            "nan_count" : 0,
            "bin_values" : bin_values
            }

        histogram = Histogram(0,1,0,'')
        
        histogram.__setstate__(state)        
        self.assertEqual(histogram.name, name)            
        self.assertEqual(histogram.xmin, xmin)
        self.assertEqual(histogram.xmax, xmax)            
        self.assertEqual(len(histogram.bin_values), nbins)            
        
if __name__ == '__main__':        
    unittest.main()

