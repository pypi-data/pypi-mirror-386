#!/usr/bin/env python3

'''
Vanilla gaussian example.
'''


import numpy
import pylab  # type: ignore[import]
import scipy.stats  # type: ignore[import]

import voka.metrics

histograms = dict()
N_HISTOGRAMS = 1000
SCALE = 1.0
LOC = 0.0
SIZE = 1000
params = (SIZE/(SCALE * numpy.sqrt(2 * numpy.pi)), LOC, SCALE)
for i in range(N_HISTOGRAMS):
    data = numpy.random.normal(size=SIZE, loc=LOC, scale=SCALE)
    histograms['Histogram%d' % i] = numpy.histogram(data)

def gauss(x, *p):
    '''
    Gaussian distribution
    '''
    amplitude, mean, sigma = p
    return amplitude*numpy.exp(-(x-mean)**2/(2.*sigma**2))

test_stat = voka.metrics.norm_chisq
NDOF = None
T_dist = list()
for i in range(N_HISTOGRAMS):
    h = histograms["Histogram%d" % i]
    bin_values = h[0]
    bin_edges = h[1]
    bin_centers = (bin_edges[:-1] + bin_edges[1:])/2
    bw = bin_centers[1] - bin_centers[0]
    expectation = [gauss(x, bw*params[0], LOC, SCALE) for x in bin_centers]

    if not NDOF:
        NDOF = len(bin_values) - 2

    T_dist.append(test_stat(bin_values, expectation))

if NDOF is None:
    raise RuntimeError('NDOF was never set (is None)')

pylab.figure(1)
pylab.hist(T_dist, bins=100)

pylab.figure(2)
rv = scipy.stats.chi2(NDOF)
x_values = range(20)
pylab.plot(x_values, rv.pdf(x_values), 'k-')

pylab.figure(3)
h = histograms["Histogram0"]
bin_values = h[0]
bin_edges = h[1]
bin_centers = (bin_edges[:-1] + bin_edges[1:])/2
bw = bin_centers[1] - bin_centers[0]
print("bw = %f" % bw)
pylab.plot(bin_centers, bin_values)
pylab.plot(bin_centers, [gauss(bc, bw*params[0], LOC, SCALE)
                         for bc in bin_centers])

pylab.show()
