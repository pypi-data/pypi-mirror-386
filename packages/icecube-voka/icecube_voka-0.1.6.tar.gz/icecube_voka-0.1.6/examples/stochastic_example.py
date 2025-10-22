#!/usr/bin/env python3

'''
This example illustrates the failure of traditional statistical
comparisons, such as chi^2, for weighted histograms from
stochastic processes.

Histogram the arrival time, expected to be gaussian, of the charge
sampled from a gaussian.
'''

import numpy
import pylab  # type: ignore[import]
import scipy.stats  # type: ignore[import]

import voka.metrics

histograms = dict()
N_HISTOGRAMS = 100
for i in range(N_HISTOGRAMS):
    charge_data = list()
    time_data = numpy.random.normal(size=1000)
    for time in time_data:
        # for each time the charge is sampled from
        # another distribution
        charge = numpy.random.normal(loc=5.0, scale=0.25)
        for c in range(int(charge)):
            charge_data.append(time)
    histograms['ChargeHistogram%d' % i] = numpy.histogram(charge_data)
    histograms['TimeHistogram%d' % i] = numpy.histogram(time_data)

charge_T_dist = list()
time_T_dist = list()
test_stat = voka.metrics.norm_chisq

NDOF = None
for i in range(N_HISTOGRAMS):
    for j in range(i+1, N_HISTOGRAMS):
        ch1 = histograms["ChargeHistogram%d" % i][0]
        ch2 = histograms["ChargeHistogram%d" % j][0]
        th1 = histograms["TimeHistogram%d" % i][0]
        th2 = histograms["TimeHistogram%d" % j][0]

        if not NDOF:
            NDOF = len(ch1)

        charge_T_dist.append(test_stat(ch1, ch2))
        time_T_dist.append(test_stat(th1, th2))

if NDOF is None:
    raise RuntimeError('NDOF was never set (is None)')

rv = scipy.stats.chi2(NDOF)
pylab.figure(1)
pylab.hist(charge_T_dist, density=True, bins=100)

pylab.figure(2)
pylab.hist(time_T_dist, density=True, range=(0, 100), bins=100)
x = range(100)
pylab.plot(x, rv.pdf(x), 'k-')
pylab.show()
