'''
The model module currently consists solely of the Voka class.
'''

import math
import collections
import voka.lof
        
def average_lof(test_sequence, benchmark_sequences):
    
    # this is a list of statistical test points
    reference_cluster = list()
    for idx in range(len(benchmark_sequences)-1):
        for jdx in range(idx, len(benchmark_sequences)):
            s0 = benchmark_sequences[idx]
            s1 = benchmark_sequences[jdx]
            c = voka.metrics.shape_chisq(s0, s1)
            a = voka.metrics.anderson_darling(s0, s1)    
            p = (c,a)
            reference_cluster.append(p)

    test_cluster = list()
    for s1 in benchmark_sequences:
        s0 = test_sequence
        c = voka.metrics.shape_chisq(s0, s1)
        a = voka.metrics.anderson_darling(s0, s1)
        p = (c,a)        
        test_cluster.append(p)

    print('calculating...')
    # now calculate local outlier factors
    k = 3
    lofs = list()
    print(len(test_cluster))
    print(len(reference_cluster))    
    for test_point in test_cluster:
        lofs.append(voka.lof.local_outlier_factor(test_point, k, reference_cluster))
    average_lof = sum(lofs)/float(len(lofs))
    return (average_lof, test_cluster, reference_cluster)
        
        
class Voka:
    '''
    Class to handle determination of the outlier detection thresholds
    for a given set of benchmark samples.
    '''
    def __init__(self):
        # the reference collection is a dictionary containing
        # as values dictionaries with the same structure as the test
        # dictionary.  The keys are arbitrary names for the different
        # sets.
        # Reference {'', {'', []}}
        # Test {'', []}
        self.__reference_collection = dict()
        self.__k = int()
        self.__thresholds = dict()

    def train(self,
              reference_collection,
              k=3,
              tolerance_factor=math.sqrt(2)):
        '''
        Calculate LOF thresholds from the reference set.
        '''

        # there should be a transformation of the reference collection here
        # involving a comparison using statistical tests
        
        self.__reference_collection = reference_collection
        self.__k = k
    
        # we use each one as a test and the others
        # as a benchmark set and determine the
        lof_values = collections.defaultdict(list)
        for test_collection in reference_collection.values():
            # No need to remove the set from itself.
            # Identity should resolve to 0 in each test
            # contributing nothing to the calculation of
            # the average.
            result = self.execute(test_collection)
            assert(result)

            for key, lof in result.items():
                lof_values[key].append(lof)

        self.__thresholds = {histogram_name: tolerance_factor*max(lofs)
                             for histogram_name, lofs in lof_values.items()}
        assert(self.__thresholds)

    def execute(self, test):
        '''
        calculate the thresholds from the benchmark set
        '''
        result = dict()
        for test_key, test_sequence in test.items():

            # pull the reference sequences out of the collection
            reference_sequences = list()
            for ref_set in self.__reference_collection.values():
                if test_key in ref_set:
                    reference_sequences.append(ref_set[test_key])

            # the transformation has to happen here
            # we have a single test_sequence and we have
            # reference sequences
                    
            lof = voka.lof.local_outlier_factor(test_sequence,
                                                self.__k,
                                                reference_sequences)

            result[test_key] = lof
        return result

    def results(self, results):
        '''
        Apply the thresholds determined during training
        and indicate pass/fail.
        '''
        result = dict()
        for key, lof in results.items():
            if key not in self.__thresholds:
                continue
            result[key] = {
                'pass': lof <= self.__thresholds[key],
                'lof': lof,
                'threshold': self.__thresholds[key]
            }
        return result
