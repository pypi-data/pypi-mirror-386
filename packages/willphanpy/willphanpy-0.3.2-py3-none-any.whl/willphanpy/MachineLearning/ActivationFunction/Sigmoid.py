import numpy as np

class Sigmoid:
    '''
    Sigmoid activation function
        @method forward
    '''
    def __init__(self):
        pass

    def forward(self, x):
        '''
        Forward method to get both activated value and slope at a given point
            @param x: a real value or numpy array
            @return: activated value, slope
        '''
        a = self._activate(x)
        g = self._grad(x)
        return a,g
    
    def _activate(self, x):
        '''
        @param x: a real value
        @Return sigmoid value
        '''
        return 1 / (1 + np.exp(-x))
    
    def _grad(self, x):
        '''
        Compute gradient at a point
            @param x: a real value
            @return: slope at the input value
        '''
        dx = 0.0001
        return (self._activate(x + dx) - self._activate(x - dx)) / (2*dx)
    
