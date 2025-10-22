'''
  Module that contains the function that calculates a Local Outlier Factor.
  https://www.dbs.ifi.lmu.de/Publikationen/Papers/LOF.pdf
'''
import numpy

def distance(vector1, vector2):
    '''
    Euclidean distance.
    '''
    array1 = numpy.array(vector1)
    array2 = numpy.array(vector2)
    return numpy.linalg.norm(array1-array2)

def reach(candidate, k_distance, cluster_member, cluster):

    '''
    k-distance of candidate object p is defined as the distance d(p,o)
    between candidate p and an object o in cluster D such that:
        i)  For at least k objects o' in D/{p} d(p,o') <= d(p,o)
        ii) For at most k-1 objects o' in D/{p} d(p,o') < d(p,o)
    '''
    distances = list()
    for member in cluster:
        d = distance(candidate, member)
        if d > 0:
            distances.append(d)
    distances.sort()
    result = max(distances[:k_distance]) if distances[:k_distance] else 0.
    return max([result, distance(candidate, cluster_member)])

def local_reachability_density(test_point, k_distance, cluster):
    '''
    Local Reachability Density
    '''
    denominator = sum([reach(test_point, k_distance, member, cluster)
                       for member in cluster])
    return len(cluster)/denominator if denominator else 0.

def local_outlier_factor(test_point, k_distance, cluster):
    '''
    Return the LocalOutlierFactor for point 'p' compared
    to collection of reference points in 'D', using k-distance 'k'.
    '''
    ratios = list()
    for member in cluster:
        numerator = local_reachability_density(member,
                                               k_distance,
                                               cluster)

        denominator = local_reachability_density(test_point,
                                                 k_distance,
                                                 cluster)
        if denominator:
            ratios.append(numerator/denominator)

    result = sum(ratios)/float(len(ratios)) if ratios else 0.
    return result
