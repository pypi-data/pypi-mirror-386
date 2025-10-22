'''
This module contains the compare function.
'''
import voka.metrics

ALL_METRICS = {"NormChiSq":voka.metrics.norm_chisq,
               "ShapeChiSq":voka.metrics.shape_chisq,
               "BDM":voka.metrics.bdm,
               "KolmogorovSmirnov":voka.metrics.kolmogorov_smirnov,
               "LLHRatio":voka.metrics.llh_ratio,
               "LLHValue":voka.metrics.llh_value,
               "CramerVonMises":voka.metrics.cramer_von_mises,
               "AndersonDarling":voka.metrics.anderson_darling}

DEFAULT_METRICS = {"ShapeChiSq":voka.metrics.shape_chisq,
                   "AndersonDarling":voka.metrics.anderson_darling}

def compare(values1, values2, metrics=None):
    r'''
    To use all metrics set metrics to voka.compare.ALL_METRICS,
    otherwise pass a dictionary where the values are the metrics
    to use with named keys (can be anything), e.g.:

        metrics = {
                   'foo': voka.metrics.norm_chisq, 
                   'bar': voka.metrics.anderson_darling
                  }

    Output:
        result : dict
            test name : value of test statistic
            Will be empty if no tests enabled, or histograms inconsistent.
    '''

    result = {}
    if len(values1) != len(values2):
        print("ERROR : sequences are inconsistent.")
        return result

    _metrics = metrics if metrics else DEFAULT_METRICS

    for name, metric in _metrics.items():
        result[name] = metric(values1, values2)

    return result
