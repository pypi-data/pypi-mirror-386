import numpy as np

class Softmax:
    '''
    Softmax activation function
    '''
    def f(self, list):
        return np.exp(list) / np.sum(np.exp(list))

    def activate(self, list):
        self.output = self.f(list)
        self.derivative = self.grad(list)

    def grad(self, list):
        grad = [] # derivative output
        d = 0.0001 # small value for derivative calculation using numerical method

        for i in range(len(list)):
          for j in range(len(list[0])):
            list_plus = list[i].copy()
            list_plus[j] += d
            list_minus = list[i].copy()
            list_minus[j] -= d
            grad.append((self.f(list_plus) - self.f(list_minus)) / (2 * d))

        return np.array(grad)