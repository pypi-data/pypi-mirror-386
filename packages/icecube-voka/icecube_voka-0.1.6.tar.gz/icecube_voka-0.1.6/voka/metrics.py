from math import fabs, log, sqrt

from scipy.special import binom  # type: ignore[import]


def norm_chisq(vector1, vector2):
    r"""Compare sequences vector1, vector2 with a Chi^2 test.
        Assumes they have the same binning.
        Output:
        chisq : float
            A Chi^2 sum over all bins.
    """
    assert len(vector1) == len(vector2)

    # calculate the \chi^2 test statistic
    terms = [(u - v)**2/(u + v) \
             for u, v in zip(vector1, vector2)\
             if u > 0 and v > 0]
    result = sum(terms)
    return result

def shape_chisq(vector1, vector2):
    r"""Compare sequences vector1, vector2 with a Chi^2 test after
    normalizing them.
    Output:
        chisq : float
            A Chi^2 sum over all bins.
    """
    assert len(vector1) == len(vector2)
    
    sum1 = sum(vector1)
    sum2 = sum(vector2)
    try:
        n1sq = sum1**2
        n2sq = sum2**2
        terms = [(u/sum1 - v/sum2)**2/(u/n1sq + v/n2sq) \
                 for u, v in zip(vector1, vector2) \
                 if u > 0 and v > 0]
    except ZeroDivisionError:
        ratio = float(sum1)/sum2
        ssq = ratio**2
        terms = [(u/ratio - v)**2/(u/ssq + v) \
                 for u, v in zip(vector1, vector2) \
                 if u > 0 and v > 0]
        
    result = sum(terms)
    return result

def bdm(vector1, vector2):
    r"""Compare numerical set vector1 and vector2
        using the Bhattacharyya distance measure.
        Treating their entries vectors, normalize, and take the dot product.
        Output:
        ts : float
            The BDM test statistic
        """
    assert len(vector1) == len(vector2)
    
    if sum(vector1) == 0 or sum(vector2) == 0:
        return 1. # if they're both empty they're identical

    terms = [u*v for u, v in zip(vector1, vector2)]
    sum1 = sum(vector1)
    sum2 = sum(vector2)
    denominator = sqrt(sum1*sum2)
    result = sqrt(sum(terms))/denominator\
        if denominator else 0.
    return result
    
def anderson_darling(vector1, vector2):
    r"""
    Calculates the AD test statistic between
    vector1 and vector2
    """
    result = 0.
    n_1 = float(sum(vector1))
    n_2 = float(sum(vector2))

    if n_1 == 0 or n_2 == 0:
        return 0.

    factor = 1./(n_1+n_2)
    sigma_j = 0.
    sigma_uj = 0.
    sigma_vj = 0.
    for v_1, v_2 in zip(vector1, vector2):

        if v_1 == 0 and v_2 == 0:
            continue
        term = v_1 + v_2
        
        sigma_uj += v_1
        sigma_vj += v_2
        sigma_j += term
        
        term1 = (1./n_1)*((n_1+n_2)*sigma_uj - n_1*sigma_j)**2
        term2 = (1./n_2)*((n_1+n_2)*sigma_vj - n_2*sigma_j)**2

        denominator = sigma_j *(n_1 + n_2 - sigma_j)
        if denominator == 0:
            continue
        result += term*(term1 + term2)/denominator
        
    result *= factor
    return result

def cramer_von_mises(vector1, vector2):
    r"""
    Compare sequences vector1, vector2 with the Cramer-von-Mises test.
    """
    result = 0.
    if not any(vector1) and not any(vector2):
        return result

    sum1 = float(sum(vector1))
    sum2 = float(sum(vector2))

    for i, u_v in enumerate(zip(vector1, vector2)):
        u_ecdf = sum(vector1[:i])/sum1
        v_ecdf = sum(vector2[:i])/sum2
        result += sum(u_v)*(u_ecdf - v_ecdf)**2
    factor = sum1*sum2/(sum1+sum2)**2
    result *= factor
    return result

def kolmogorov_smirnov(vector1, vector2):
    r"""Calculate the Kolmogorov-Smirnov test statistic
        for two numerical sequences of the same length
    
        Output:
        T : float
    Maximum distance between the cumulative distributions.
    """
    assert len(vector1) == len(vector2)
    
    nbins = len(vector1)
    sum1 = sum(vector1)
    sum2 = sum(vector2)

    if sum1 == 0 and sum2 == 0:
        return 0.

    cdf_diffs = [fabs(sum(vector1[:i])/sum1 - sum(vector2[:i])/sum2)
                 for i in range(nbins)]
    result = max(cdf_diffs)
    return result

def llh_ratio(vector1, vector2):
    r"""
    Calculates the Likelihood ratio between two sequences.
    """
    result = 0.
    if not any(vector1) and not any(vector2):
        return result
    
    sum1 = float(sum(vector1))
    sum2 = float(sum(vector2))

    for u_1, u_2 in zip(vector1, vector2):
        sum12 = u_1 + u_2
        if u_1 == 0 and u_2 == 0:
            result += 1
            continue
        if u_1 == 0:
            result += sum12*log(sum1/(sum1+sum2))
            continue
        if u_2 == 0:
            result += sum12*log(sum2/(sum1+sum2))
            continue
        term1 = sum12*log((1+u_2/u_1)/(1+sum2/sum1))
        term2 = u_2*log((sum2/sum1)*(u_1/u_2))
        result += term1 + term2

    return -2*result

def llh_value(vector1, vector2):
    r"""
    Compare histograms h1, h2 with the log likelihood value test.
    FIXME: This is currently returning inf on occasion.  It should
           never do that. Taking it out of the rotation.
    """
    result = 0.
    if not any(vector1) and not any(vector2):
        return result

    sum1 = float(sum(vector1))
    sum2 = float(sum(vector2))

    for u_1, u_2 in zip(vector1, vector2):
        sum12 = u_1 + u_2
        term1 = log(binom(sum12, u_2))
        term2 = sum12*log(sum1/(sum1 + sum2))
        term3 = u_2*log(sum2/sum1)
        result += term1 + term2 + term3

    return -result




