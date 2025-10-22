from math import isnan
class Histogram(object) :
    '''
    Simple 1-D histogram base class.

    You have to specify several things on construction.

    - xmin : Minimum x value
       * x < xmin goes into the underflow.
    - xmax : Maximum x value
       * x >= xmax goes into the overflow.        
    - nbins : Number of bins.
    - name : Name of this histogram.  This will be the key
             in the dictionary that's pickled.
    '''
    def __init__(self, xmin, xmax, nbins, name):
       
        self.xmin = xmin
        self.xmax = xmax
        self.name = name
        
        self.overflow = 0
        self.underflow = 0
        self.nan_count = 0
        self.bin_values = [0 for i in range(nbins)]

        # Inverse BinWidth, used in the calculation
        # of the index in the fill method
        self.__inv_bw = nbins/float(self.xmax - self.xmin) 
                       
    def fill(self, value):
        '''
        Note that the leading edge is inclusive
          * x < xmin goes into the underflow.
          * x >= xmax goes into the overflow.        
        '''
        if value >= self.xmin and value < self.xmax :
            index = int(self.__inv_bw * (value - self.xmin))
            self.bin_values[ index ] += 1
        else:
            if isnan(value):
                self.nan_count += 1
            else:
                if value >= self.xmax :
                    self.overflow += 1
                if value < self.xmin :
                    self.underflow += 1
                        
    def __getstate__(self):
        '''
        Allows Histograms to be pickled.
        '''
        state = {
            "name" : self.name,
            "xmin" : self.xmin,
            "xmax" : self.xmax,
            "overflow" : self.overflow,
            "underflow" : self.underflow,
            "nan_count" : self.nan_count,
            "bin_values" : self.bin_values
            }
        return state

    def __setstate__(self, state):
        '''
        Allows Histograms to be pickled.
        '''
        for name, value in state.items():
            setattr(self, name, value)

        nbins = len(self.bin_values)
        self.__inv_bw = nbins/float(self.xmax - self.xmin) 
