import math


class Cobb_Douglas_Production_Function:
    def __init__(self, k, l , alpha, tfp=1):
        self.k = k
        self.l = l
        self.alpha = alpha
        self.TFP = tfp

    def y(self):
        y = self.TFP * (self.k ** self.alpha) * (self.l ** (1 - self.alpha))
        return y

    def rent(self):
        r = self.TFP * self.alpha * (self.l ** (1 - self.alpha)) / (self.k ** (1 - self.alpha))
        return r

    def wage(self):
        w = self.TFP * (1 - self.alpha) * (self.k ** self.alpha) * (self.l ** (0 - self.alpha))
        return w

class Utility_Function:
    def __init__(self, c, beta=0.98, sigma=2):
        self.c = c
        self.beta = beta
        self.sigma = sigma

    def logarithmic(self):
        u = math.log(self.c, math.e)
        return u

    def crra(self):
        u = (self.c ** (1 - self.sigma)) / (1 - self.sigma)
        return u
