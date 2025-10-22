#!/usr/bin/env python3

'''
This example exercises the two sample statistical tests
available from scipy:
* scipy.stats.ttest_ind
* scipy.stats.ks_2samp
* scipy.stats.epps_singleton_2samp
* scipy.stats.mannwhitneyu
* scipy.stats.ranksums
* scipy.stats.wilcoxon
* scipy.stats.kruskal
* scipy.stats.friedmanchisquare
* scipy.stats.brunnermunzel
* scipy.stats.anderson_ksamp
'''

import collections

import numpy
import pylab  # type: ignore[import]
import scipy.stats  # type: ignore[import]

import voka.tools.render

# Low p-value is bad here.
# The null hypothesis H_0 is that the two samples
# were sampled from the same underlying distribution.
# A low p-value implies there's a low probability
# that the difference observed is due to fluctuations
# alone, indicating a systematic and significant difference.
# In an analysis this would be evidence of a signl.
# We effectively want background and background.
# We want no signal.

# Note:
# 1) friedman chisq test fails with
#    'ValueError: Less than 3 levels.  Friedman test not appropriate.'
# 2) wolcoxon fails if the two are distributions are identical.
# 3) anderson_ksamp result for equal distributions:
#    anderson_ksampResult(statistic=-1.3146384545742542,
#                         critical_values=array([0.325,
#                                                1.226,
#                                                1.961,
#                                                2.718,
#                                                3.752,
#                                                4.592,
#                                                6.546]),
#                         significance_level=0.25)
#
# Either way I'm creating a voka.2sample and voka.ksample.

def voka_2sample(sample1, sample2):
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
        r = scipy.stats.epps_singleton_2samp(sample1, sample2)
        result['EppsSingleton'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except numpy.linalg.LinAlgError:
        print("    skipping epps_singleton_2samp")

    try:
        r = scipy.stats.mannwhitneyu(sample1, sample2)
        result['MannWhitneyU'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except ValueError:
        print("    skipping mannwhitneyu")

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
        print("    skipping wilcoxon")

    try:
        r = scipy.stats.kruskal(sample1, sample2)
        result['Kruskal'] = {
            'statistic': r.statistic,
            'pvalue': r.pvalue
        }
    except:
        print("    skipping kruskal")

#    try:
#        r = scipy.stats.friedmanchisquare(sample1, sample2)
#        result['FriedmanChiSquare'] = {
#            'statistic': r.statistic,
#            'pvalue': r.pvalue
#        }
#    except ValueError:
#        print("    skipping friedmanchisquare")

    r = scipy.stats.brunnermunzel(sample1, sample2)
    result['BrunnerMunzel'] = {
        'statistic': r.statistic,
        'pvalue': r.pvalue
    }

    return result

DENSITY = True

def compare(benchmark_distribution, systematic_distribution, pvalues, density=False):
    # Use the same histogram settings for each.
    _range = (-5,5)
    _bins = 100

    # First histogram to make samples
    benchmark_sample = numpy.histogram(benchmark_distribution,
                                       density=density,
                                       range=_range,
                                       bins=_bins)[0]
    systematic_sample = numpy.histogram(systematic_distribution,
                                        range=_range,
                                        density=density,
                                        bins=_bins)[0]

    # Compare and print the results
    comparison = voka_2sample(benchmark_sample, systematic_sample)
    for k, v in comparison.items():
        pvalues[k].append(v['pvalue'])

if __name__ == '__main__':

    # Tests to perform
    # 1) Poissonian-only differences
    # 2) Normalization differences
    # 3) Mean pull
    # 4) Width differences

    benchmark_width = 1.0
    benchmark_center = 0.0
    benchmark_size = 100000

    widths = numpy.arange(0.5*benchmark_width,
                          1.5*benchmark_width,
                          0.001)

    centers = numpy.arange(-0.5,
                           0.5,
                           0.001)

    sizes = numpy.arange(0.5*benchmark_size,
                         1.5*benchmark_size,
                         10)

    draw_width_idx = int(0.9*len(widths))
    draw_center_idx = int(0.9*len(centers))

    benchmark_distribution = numpy.random.normal(loc=benchmark_center,
                                                 scale=benchmark_width,
                                                 size=benchmark_size)

    # Generate systematic distributions
    print(80*'-')
    figure_number = 1

    pvalues_width_systematic: dict = collections.defaultdict(list)
    for idx, systematic_width in enumerate(widths):
        #print('width = %.4f' % systematic_width)
        systematic_distribution = numpy.random.normal(loc=benchmark_center,
                                                      scale=systematic_width,
                                                      size=benchmark_size)
        compare(benchmark_distribution,
                systematic_distribution,
                pvalues_width_systematic,
                density=DENSITY)

        if idx == draw_width_idx:
            print('width = %.4f' % systematic_width)
            # Use the same histogram settings for each.
            _range = (-5,5)
            _bins = 100

            # First histogram to make samples
            benchmark_sample = numpy.histogram(benchmark_distribution,
                                               density=DENSITY,
                                               range=_range,
                                               bins=_bins)[0]
            systematic_sample = numpy.histogram(systematic_distribution,
                                                density=DENSITY,
                                                range=_range,
                                                bins=_bins)[0]

            pylab.figure(figure_number)
            figure_number += 1
            voka.tools.render.draw_ratio(systematic_sample, benchmark_sample)


    pylab.figure(figure_number)
    figure_number += 1
    for label, pvs in pvalues_width_systematic.items():
        min_pvalue = min(pvs)
        y = [numpy.log10(p) for p in pvs]
        pylab.plot(widths, y, label=label)

    pylab.title("Systematic Width Variation")
    pylab.legend()
    pylab.xlabel('width')
    pylab.ylabel('log(p-value)')

    print(80 * '-')
    pvalues_center_systematic: dict = collections.defaultdict(list)
    for idx, systematic_center in enumerate(centers):
        #print('center = %.4f' % systematic_center)
        systematic_distribution = numpy.random.normal(loc=systematic_center,
                                                      scale=benchmark_width,
                                                      size=benchmark_size)
        compare(benchmark_distribution,
                systematic_distribution,
                pvalues_center_systematic,
                density=DENSITY)

        if idx == draw_center_idx:
            print('center = %.4f' % systematic_center)
            # Use the same histogram settings for each.
            _range = (-5,5)
            _bins = 100

            # First histogram to make samples
            benchmark_sample = numpy.histogram(benchmark_distribution,
                                               density=DENSITY,
                                               range=_range,
                                               bins=_bins)[0]
            systematic_sample = numpy.histogram(systematic_distribution,
                                                density=DENSITY,
                                                range=_range,
                                                bins=_bins)[0]

            pylab.figure(figure_number)
            figure_number += 1
            voka.tools.render.draw_ratio(systematic_sample, benchmark_sample)

    pylab.figure(figure_number)
    figure_number += 1
    for label, pvs in pvalues_center_systematic.items():
        y = [numpy.log10(p) for p in pvs]
        pylab.plot(centers, y, label=label)

    pylab.title("Systematic Center Variation")
    pylab.legend()
    pylab.xlabel('center')
    pylab.ylabel('log(p-value)')

    print(80*'-')
    pylab.figure(figure_number)
    figure_number += 1
    pvalues_size_systematic: dict = collections.defaultdict(list)
    for systematic_size in sizes:
        #print('size = %d' % int(systematic_size))
        systematic_distribution = numpy.random.normal(loc=benchmark_center,
                                                      scale=benchmark_width,
                                                      size=int(systematic_size))
        compare(benchmark_distribution,
                systematic_distribution,
                pvalues_size_systematic,
                density=DENSITY)

    for label, pvs in pvalues_size_systematic.items():
        y = [numpy.log10(p) for p in pvs]
        pylab.plot(sizes, y, label=label)

    pylab.title("Systematic Size Variation")
    pylab.legend()
    pylab.xlabel('size')
    pylab.ylabel('log(p-value)')

    pylab.show()
