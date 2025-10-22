#!/usr/bin/env python3

'''
This example exercises the two sample statistical tests
available from scipy:
* scipy.stats.ttest_ind
* scipy.stats.ks_2samp
* scipy.stats.anderson_ksamp
* scipy.stats.epps_singleton_2samp
* scipy.stats.mannwhitneyu
* scipy.stats.ranksums
* scipy.stats.wilcoxon
* scipy.stats.kruskal
* scipy.stats.friedmanchisquare
* scipy.stats.brunnermunzel
'''

import collections
import subprocess

import numpy
import scipy.stats  # type: ignore[import]
import pylab  # type: ignore[import]
import matplotlib  # type: ignore[import]

import voka.model
import voka.metrics

matplotlib.use('agg')

def voka_2sample(sample1, sample2):
    print(sample1, sample2)

    # Checkout OnlineL2_SplitTime2_SPE2itFitEnergy
    # hiccup #1 (AD) ValueError: anderson_ksamp needs more than one distinct observation
    # hiccup #2 (ES) numpy.linalg.LinAlgError: SVD did not converge
    # hiccup #3 (TT) Ttest_indResult(statistic=nan, pvalue=nan)
    # hiccup #4 (MW) ValueError: All numbers are identical in mannwhitneyu
    # hiccup #5 (WP) ValueError: zero_method 'wilcox' and 'pratt' do not work if x - y is zero for all elements
    # hiccup #6 (FC) ValueError: Less than 3 levels.  Friedman test not appropriate.

    result = dict()

    r = scipy.stats.ttest_ind(sample1, sample2)
    result['TTest'] = {
        'statistic': r.statistic,
        'pvalue': r.pvalue
    }

    r = scipy.stats.ks_2samp(sample1, sample2)
    result['KolmogorovSmirnov'] = {
        'statistic': r.statistic,
        'pvalue': r.pvalue
    }

    try:
        r = scipy.stats.anderson_ksamp([sample1, sample2])
        result['AndersonDarling'] = {
            'statistic': r.statistic,
            'significance_level': r.significance_level
        }
    except ValueError:
        #print("    skipping anderson_ksamp")
        pass

    try:
        r = scipy.stats.epps_singleton_2samp(sample1, sample2)
        result['EppsSingleton'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except numpy.linalg.LinAlgError:
        #print("    skipping epps_singleton_2samp")
        pass

    try:
        r = scipy.stats.mannwhitneyu(sample1, sample2)
        result['MannWhitneyU'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except ValueError:
        #print("    skipping mannwhitneyu")
        pass

    r = scipy.stats.ranksums(sample1, sample2)
    result['Ranksums'] = {
        'statistic': r.statistic,
        'pvalue': r.pvalue
    }

    try:
        r = scipy.stats.wilcoxon(sample1, sample2)
        result['Wilcoxon'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except ValueError:
        #print("    skipping wilcoxon")
        pass

    try:
        r = scipy.stats.kruskal(sample1, sample2)
        result['Kruskal'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except:
        #print("    skipping kruskal")
        pass

    try:
        r = scipy.stats.friedmanchisquare(sample1, sample2)
        result['FriedmanChiSquare'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except ValueError:
        #print("    skipping friedmanchisquare")
        pass

    r = scipy.stats.brunnermunzel(sample1, sample2)
    result['BrunnerMunzel'] = {
        'statistic': r.statistic,
        'pvalue': r.pvalue
    }

    return result

# make two samples containing
# 'standard' numpy distributions
locs = numpy.arange(-0.25, 0.25, 0.01)

def gaussian_sample(loc=0.0, size=1000):
    RANGE = (-5,5)
    SCALE = 1.0
    return numpy.histogram(numpy.random.normal(size=size, scale=SCALE, loc=loc),
                           range=RANGE)[0]

unbinned_test_samples = [numpy.random.normal(size=1000, scale=1.0, loc=loc)
                         for loc in locs]

voka_test_samples = [gaussian_sample(loc=loc, size=1000) for loc in locs]
benchmark_samples = [gaussian_sample(size=1000) for _ in range(7)]

results = collections.defaultdict(list)
cmd = "convert -delay 50 -loop 0".split()
for idx, test_sample in enumerate(unbinned_test_samples):

    print("loc = %.2f" % locs[idx])
    benchmark_sample = numpy.random.normal(size=1000)
    voka_2samp_result = voka_2sample(test_sample, benchmark_sample)
    for name, result in voka_2samp_result.items():
        if 'pvalue' in result:
            results[name].append(numpy.log(result['pvalue']))

    lof, test_cluster, reference_cluster = voka.model.average_lof(voka_test_samples[idx], benchmark_samples)
    results['voka'].append(lof)

    pylab.figure()
    marker = 'ro' if lof > 2. else 'go'
    pylab.title('gaussian pull = %f' % locs[idx])
    pylab.xlabel('chisq')
    pylab.ylabel('AD')
    pylab.xlim(0,50)
    pylab.ylim(0,50)
    pylab.plot([p[0] for p in test_cluster],
               [p[1] for p in test_cluster],
               marker)
    pylab.plot([p[0] for p in reference_cluster],
               [p[1] for p in reference_cluster],
               'bo')
    fn = 'illustration_%d.png' % idx
    pylab.savefig(fn)
    cmd.append(fn)
cmd.append('animation.gif')
subprocess.run(cmd)

# 1) now just calculate the metrics for the benchmarks
# and test samples for each pull value
# 2) add the vline for the lof threshold
# 3) animation showing the color change

pylab.figure()
for name, result in results.items():
    if name=='voka':
        continue
    pylab.plot(locs, result, label=name)
pylab.title('Unbinned 2-sample Tests')
pylab.xlabel('gaussian pull')
pylab.axhline(-3.0)
pylab.ylabel('log(p-value)')
pylab.legend()

pylab.figure()
pylab.plot(locs, results['voka'], label='icecube')
pylab.title('LOF-based Method')
pylab.xlabel('gaussian pull')
pylab.axhline(2.0)
pylab.ylabel('<lof>')
pylab.legend()

# #benchmark_x = list()
# #benchmark_y = list()
# #for idx in range(len(benchmark_samples)-1):
# #    for jdx in range(idx+1, len(benchmark_samples)):
# #        benchmark_x = voka.metric.shape_chisq(,)
#
#pylab.show()
