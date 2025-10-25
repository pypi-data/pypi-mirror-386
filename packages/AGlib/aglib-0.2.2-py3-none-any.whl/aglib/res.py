'''
Functions to allow easy addition of resolution functions to other functions.
Each resolution function class can be used either by calling it with the function
to be used and it's parameters or as a decorator in function definition.
'''
import types
import numpy

class ResolutionFunction(object):
    '''
    Base class for resolution function classes. Derived classes can be used
    as decorators or directly as objects to add resolution to any 1D function.
    
    The resolution can be added by ither FFT-convolution with the resolution
    function or by direct convolution with a larger set of datapoints using sum
    or integration with trapezoidal rule. The resolution classes can be used in
    one of the following 4 ways:
    
    1. Decorator with resolution parameters:
      
        @resolution(p1, p2, p3, kwd=abc)
        def function(x, a, b):
            return y
    
    2. Decorator for function including the resolution parameters:
    
        @resolution(kwd=abc)
        def function(x, a, b, p1, p2, p3):
            return y
    
    3. Class instance to use with external function:
    
        res=resolution(p1, p2, p3, kwd=abc)
        y=res(function, x, a, b)

    4. Class to use with external function:
    
        y=resolution.calc(function, (x, a, b), p1, p2, p3, kwd=abc)
    '''
    # attributes that should be overwritten by subclasses
    _PARAMS=[] #: Parameter names for the resolution function
    _KWDS={} #: Keywords and default values used for the resolution function
    name='None' #: Name for the resolution function

    # fixed attributes
    _KWDS_ADD={
               'method': 'sum',
               'points': 25,
               }

    # TODO: Parameter checking
    def __new__(cls, *args, **opts):
        # instantiation of class
        out=object.__new__(cls)
        if len(args)==0:
            # only for decorator
            out.options=None
        elif len(args)!=len(out._PARAMS):
            raise ValueError('You need to provide values for all parameters: '+\
                                ', '.join(out._PARAMS))
        else:
            out.options=list(args)
        out.keywords=dict(out._KWDS.items()+cls._KWDS_ADD.items())
        for key, value in opts.items():
            if not key in out.keywords:
                raise ValueError('Unknown keyword option "%s"'%key)
            out.keywords[key]=value
        return out

    def __call__(self, *args):
        '''
        Used when instance is called as decorator or to actually calculate a
        function including its resolution. 
        '''
        if isinstance(args[0], types.FunctionType):
            if self.options is None:
                evstr='lambda *args: res.calc(_func_, args[:-%i], *args[-%i:], **res.keywords)'%(
                                                    len(self._PARAMS), len(self._PARAMS))
                ev_global={'_func_': args[0], 'res': self}
            else:
                evstr='lambda *args: res.calc(_func_, args, *res.options, **res.keywords)'
                ev_global={'_func_': args[0], 'res': self}
            outfunc=eval(evstr, ev_global)
            outfunc.res=self
            return outfunc
        elif isinstance(args[0], types.MethodType):
            pass
        elif self.options is None:
            raise (ValueError,
                'This instance of %s was created without parameters and can only be used as decorator'%
                    self.__class__.__name__)
        args=[args[0], args[1:]]+self.options
        return self.calc(*args, **self.keywords)

    @classmethod
    def calc(cls, *args, **kwds):
        func=args[0]
        func_params=args[1]
        res_params=args[2:]
        return cls.convolve_resolution(func, func_params, res_params, **kwds)


    @staticmethod
    def resolution_function(delta_x, *args):
        '''
        This method defines the probability for a given position offset delta_x,
        for e.g. a gaussian resolution function this would be exp(-0.5*delta_x**2/sigma**2).
        
        Each subclass needs to overwrite this method. 
        '''
        raise NotImplementedError('ResolutionFunction needs to be subclassed to be used')

    @classmethod
    def get_respoints(cls, x, points, *args):
        '''
        This method defines the x-values to be calculated for the convolution
        in dependance of the parameters for the resolution function.
        By default the first argument is taken and multiplied by 3 to get the
        range for these points, as this is a reasonable value for e.g. sigma
        of gaussian resolution functions  
        '''
        delta_x=numpy.linspace(-3.*args[0], 3.*args[0], points)
        P=cls.resolution_function(delta_x, *args)
        # normalize probabilities
        P/=P.sum()
        X=x+delta_x[:, numpy.newaxis]
        P=numpy.ones_like(x)*P[:, numpy.newaxis]
        return P, X

    @classmethod
    def convolve_resolution(cls, func, func_params, res_params, **kwds):
        '''
        Calculate the convolution of the resolution and user supplied functions.
        The method used for the convolution is defined via the method keyword.
        '''
        for key, value in cls._KWDS.items()+cls._KWDS_ADD.items():
            if key not in kwds:
                kwds[key]=value
        method=kwds['method']
        points=kwds['points']
        x=func_params[0]
        if method=='fast':
            # only calculate the function values for the given x-array
            # much faster but does only work with equally spaced, dense points
            y_clean=func(x, *func_params[1:])
            y_res=cls.resolution_function(x-x.mean(), res_params)
            y_res/=y_res.sum()
            return numpy.convolve(y_clean, y_res, 'same')
        else:
            # calculate extra points for the resolution function
            # and convolute by integrating over the values with their probabilities.
            # this can lead to artifacts if the resolution is very broad and
            # the number of points too low.
            P, X=cls.get_respoints(x, points, *res_params)
            Y=[]
            for Pi, Xi in zip(P, X):
                Y.append(Pi*func(Xi, *func_params[1:]))
            Y=numpy.array(Y)
            if method=='sum':
                # integrate by simply taking the sum
                return Y.sum(axis=0)
            elif method=='trapz':
                # integrate using the trapezoidal rule
                return numpy.trapz(Y, axis=0)
            else:
                raise ValueError('Unknown convolution method "%s"'%method)


class gauss_res(ResolutionFunction):
    _PARAMS=['sigma']
    name='Gaussian'

    @staticmethod
    def resolution_function(delta_x, sigma):
        return numpy.exp(-0.5*(delta_x/sigma)**2)

