
import numpy
import scipy.stats  # type: ignore[import]

def traditional(sample1, sample2):

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
