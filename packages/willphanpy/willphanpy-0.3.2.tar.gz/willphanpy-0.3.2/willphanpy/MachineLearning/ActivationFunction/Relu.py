import numpy as np

class Relu:
    '''
    Relu activation function
        @method forward
    '''
    def __init__(self):
        pass

    def forward(self, x):
        '''
        Method combination for activate and slope
            @param x: a real value or numpy array
            @return activate, slope
        '''
        return self._activate(x), self._grad(x)

    def _activate(self, x):
        return np.where(x >= 0, x, 0)

    def _grad(self, x):
        return np.where(x >= 0, 1, 0)