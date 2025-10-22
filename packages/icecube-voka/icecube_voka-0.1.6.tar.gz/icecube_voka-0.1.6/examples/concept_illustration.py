#!/usr/bin/env python3

'''
This example illustrates the basic concept of this method,
showing that comparing two histograms using traditional methods
with a p-value threshold is unstable for non-poissonian
distributions.

Voka can be seen as the equivalent of emperically auto-tuning
the p-value threshold on-the-fly.
'''

import numpy
import pylab   # type: ignore[import]

import voka.tools.render
import voka.two_sample

# Generate the histograms
histograms = dict()
N_HISTOGRAMS = 6
for i in range(N_HISTOGRAMS):
    # start with a large Gaussian
    charge_data = list(numpy.random.normal(loc=5.0, scale=0.25, size=10000))

    loc = numpy.random.uniform(3.0, 7.0)
    print(loc)
    random_charge = numpy.random.normal(loc=loc, scale=0.25, size=1000)
    charge_data.extend(random_charge)

    histograms['ChargeHistogram%d' % i] = numpy.histogram(charge_data, bins=100)

# Render the histograms
i=0
for title, histogram in histograms.items():
    pylab.figure(i)
    i=i+1
    bin_values = histogram[0]
    voka.tools.render.draw(bin_values, title)

# Treat the 0-th histogram as the test histogram
# and histograms 1-5 constitute the benchmark ensemble.

# First compare the histograms with traditional statistical tests
test_sample = histograms['ChargeHistogram0'][0]
benchmark_ensemble = [histograms['ChargeHistogram%d' % i][0]
                      for i in range(1,6)]
print(benchmark_ensemble)
for benchmark_sample in benchmark_ensemble:
    result = voka.two_sample.traditional(test_sample, benchmark_sample)
    print(result['KolmogorovSmirnov'])

# Second compare the test histogram using voka.
model = voka.model.Voka()
reference_collection = {
    "Benchmark%d" % idx :
    {"ChargeHistogram":s}
    for idx, s in enumerate(benchmark_ensemble)
}

model.train(reference_collection)
results = model.execute({"ChargeHistogram": test_sample})
result = model.results(results)
print(result)

pylab.show()
