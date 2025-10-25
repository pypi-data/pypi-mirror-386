'''
Often used functions.
'''

from numpy import array, exp

__all__=['gauss', 'lorentz']

def gauss(x, I=1., x0=0., sigma=1.):
    x=array(x, copy=False)
    return I*exp(-0.5*((x-x0)/sigma)**2)

def lorentz(x, I=1., x0=0., gamma=1.):
    x=array(x, copy=False)
    return I*(1./(1.+((x-x0)/gamma)**2))

