import torch 
import numpy as np 
import scipy.special

class AbstractOrthoPolys(object):
    r"""
    Abstract class for [classic orthogonal polynomials](https://en.wikipedia.org/wiki/Classical_orthogonal_polynomials#Table_of_classical_orthogonal_polynomials). 
    """

    def __init__(self):
        self.factor_lweight = float(2*np.log(self.c00)-float(self.lnorm(0)))

    def __call__(self, n, x):
        r"""
        Evaluate polynomials. 

        Args:
            n (int): non-negative maximum degree of the polynomial.
            x (torch.Tensor): nodes at which to evaluate.

        Returns: 
            y (torch.Tensor): polynomial evaluations with shape `[n+1]+list(x.shape)`.
        """
        assert n>=0
        assert (x>=self.a).all()
        assert (x<=self.b).all()
        lC = self.lnorm(n)
        v = torch.exp(lC[0]/2-lC/2-np.log(self.c00))
        y = torch.empty([n+1]+list(x.shape))
        y[0] = self.c00
        if n>0:
            y[1] = self.c11*x+self.c10
        if n>1: 
            t1,t2,t3 = self.recur_terms(n)
            for i in range(1,n):
                y[i+1] = (t1[i]*x+t2[i])*y[i]-t3[i]*y[i-1]
        return torch.einsum("i,i...->i...",v,y)
    
    def coeffs(self, n):
        r"""
        Evaluate coefficients. 

        Args:
            n (int): non-negative maximum degree of the polynomial.

        Returns: 
            c (torch.Tensor): coefficients with shape `[n+1,n+1]`.
        """
        assert n>=0 
        lC = self.lnorm(n)
        v = torch.exp(lC[0]/2-lC/2-np.log(self.c00))
        c = torch.zeros((n+1,n+1))
        c[0,0] = self.c00
        if n>0:
            c[1,0] = self.c10
            c[1,1] = self.c11
        if n>1:
            t1,t2,t3 = self.recur_terms(n)
            for i in range(1,n):
                c[i+1,:i] = -t3[i]*c[i-1,:i]
                c[i+1,:(i+1)] = c[i+1,:(i+1)]+t2[i]*c[i,:(i+1)]
                c[i+1,1:(i+2)] = c[i+1,1:(i+2)]+t1[i]*c[i,:(i+1)]
        return v[:,None]*c
    
    def recur_terms(self, n):
        assert n>=0
        nrange = torch.arange(n+1)
        y = self._recur_terms(nrange)
        return y
    
    def lweight(self, x):
        r"""
        Log of the weight function. 

        Args:
            x (torch.Tensor): nodes at which to evaluate.

        Returns: 
            y (torch.Tensor): log-scaled weight evaluations with the same shape as `x`.
        """
        assert (x>=self.a).all()
        assert (x<=self.b).all()
        y = self._lweight(x)
        return y
    
    def lnorm(self, n):
        r"""
        Log of the normalization constants. 

        Args:
            n (int): non-negative maximum degree of the polynomial.

        Returns: 
            y (torch.Tensor): log-scaled normalization constants with shape `[n+1,]`.
        """
        assert n>=0
        nrange = torch.arange(n+1)
        y = self._lnorm(nrange)
        return y


class Hermite(AbstractOrthoPolys):

    r"""
    Orthonormal [Hermite polynomials](https://en.wikipedia.org/wiki/Hermite_polynomials)
    supported on $(-\infty,\infty)$ with the weight normalized to be a density function. 

    Examples:
        >>> torch.set_default_dtype(torch.float64)
        >>> rng = torch.Generator().manual_seed(17)

        >>> poly = Hermite()

        >>> u = scipy.stats.qmc.Sobol(d=1,rng=7).random(2**16)[:,0]
        >>> x = torch.from_numpy(scipy.stats.norm.ppf(u,scale=1/np.sqrt(2)))
        >>> n = 4
        
        >>> y = poly(n,x)
        >>> y.shape
        torch.Size([5, 65536])
        >>> (y[:,None]*y[None,:]).mean(-1)
        tensor([[ 1.0000e+00,  5.7021e-07, -2.4570e-05,  1.2231e-05, -2.2798e-04],
                [ 5.7021e-07,  9.9997e-01,  2.1992e-05, -4.9851e-04,  1.5973e-04],
                [-2.4570e-05,  2.1992e-05,  9.9937e-01,  2.4418e-04, -4.3017e-03],
                [ 1.2231e-05, -4.9851e-04,  2.4418e-04,  9.9481e-01,  1.4077e-03],
                [-2.2798e-04,  1.5973e-04, -4.3017e-03,  1.4077e-03,  9.7405e-01]])
        
        >>> lrho = poly.lweight(x) 
        >>> lrhohat = torch.from_numpy(scipy.stats.norm.logpdf(x.numpy(),scale=1/np.sqrt(2)))
        >>> assert torch.allclose(lrho,lrhohat)

        >>> Cs = torch.exp(poly.lnorm(n))
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[0]/Cs[0])*y[0],1+0*x)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[1]/Cs[0])*y[1],2*x)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[2]/Cs[0])*y[2],4*x**2-2)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[3]/Cs[0])*y[3],8*x**3-12*x)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[4]/Cs[0])*y[4],16*x**4-48*x**2+12)

        >>> coeffs = poly.coeffs(n)
        >>> coeffs.shape
        torch.Size([5, 5])
        >>> coeffs
        tensor([[ 1.0000,  0.0000,  0.0000,  0.0000,  0.0000],
                [ 0.0000,  1.4142,  0.0000,  0.0000,  0.0000],
                [-0.7071,  0.0000,  1.4142,  0.0000,  0.0000],
                [-0.0000, -1.7321,  0.0000,  1.1547,  0.0000],
                [ 0.6124, -0.0000, -2.4495,  0.0000,  0.8165]])
        >>> xpows = x[...,None]**torch.arange(n+1)
        >>> xpows.shape
        torch.Size([65536, 5])
        >>> yhat = torch.einsum("ij,...j->i...",coeffs,xpows) # generally unstable
        >>> yhat.shape
        torch.Size([5, 65536])
        >>> assert torch.allclose(y,yhat)
    """

    def __init__(self):
        self.c00 = 1
        self.c11 = 2 
        self.c10 = 0
        self.a = float(-np.inf) 
        self.b = float(np.inf) 
        self.distrib = torch.distributions.Normal(0,1/np.sqrt(2))
        super().__init__()
    
    def _lnorm(self, nrange):
        return np.log(np.sqrt(np.pi))+nrange*np.log(2)+torch.lgamma(nrange+1)
    
    def _lweight(self, x):
        return self.distrib.log_prob(x)
    
    def _recur_terms(self, nrange):
        t1 = 2+0*nrange
        t2 = 0*nrange
        t3 = 2*nrange
        return t1,t2,t3
    

class Laguerre(AbstractOrthoPolys):

    r"""
    Orthonormal [Generalized Laguerre polynomials](https://en.wikipedia.org/wiki/Laguerre_polynomials#Generalized_Laguerre_polynomials)
    supported on $[0,\infty)$ with the weight normalized to be a density function. 

    Examples:
        >>> torch.set_default_dtype(torch.float64)
        >>> rng = torch.Generator().manual_seed(17)

        >>> alpha = -1/np.sqrt(3)
        >>> poly = Laguerre(alpha=alpha)

        >>> u = scipy.stats.qmc.Sobol(d=1,rng=7).random(2**16)[:,0]
        >>> x = torch.from_numpy(scipy.stats.gamma.ppf(u,a=alpha+1))
        >>> n = 4

        >>> y = poly(n,x)
        >>> y.shape
        torch.Size([5, 65536])
        >>> (y[:,None]*y[None,:]).mean(-1)
        tensor([[ 1.0000e+00,  1.1409e-05, -1.1488e-04,  4.2222e-04, -6.7890e-04],
                [ 1.1409e-05,  9.9967e-01,  2.4873e-03, -8.2370e-03,  1.2887e-02],
                [-1.1488e-04,  2.4873e-03,  9.8360e-01,  5.1614e-02, -8.0659e-02],
                [ 4.2222e-04, -8.2370e-03,  5.1614e-02,  8.3976e-01,  2.5730e-01],
                [-6.7890e-04,  1.2887e-02, -8.0659e-02,  2.5730e-01,  5.5508e-01]])
       
        >>> lrho = poly.lweight(x) 
        >>> lrhohat = torch.from_numpy(scipy.stats.gamma.logpdf(x.numpy(),a=alpha+1))
        >>> assert torch.allclose(lrho,lrhohat,atol=1e-3)

        >>> Cs = torch.exp(poly.lnorm(n)) 
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[0]/Cs[0])*y[0],1+0*x)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[1]/Cs[0])*y[1],-x+alpha+1)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[2]/Cs[0])*y[2],1/2*(x**2-2*(alpha+2)*x+(alpha+1)*(alpha+2)))
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[3]/Cs[0])*y[3],1/6*(-x**3+3*(alpha+3)*x**2-3*(alpha+2)*(alpha+3)*x+(alpha+1)*(alpha+2)*(alpha+3)))
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[4]/Cs[0])*y[4],1/24*(x**4-4*(alpha+4)*x**3+6*(alpha+3)*(alpha+4)*x**2-4*(alpha+2)*(alpha+3)*(alpha+4)*x+(alpha+1)*(alpha+2)*(alpha+3)*(alpha+4)))

        >>> coeffs = poly.coeffs(n)
        >>> coeffs.shape
        torch.Size([5, 5])
        >>> coeffs
        tensor([[ 1.0000,  0.0000,  0.0000,  0.0000,  0.0000],
                [ 0.6501, -1.5382,  0.0000,  0.0000,  0.0000],
                [ 0.5483, -2.5946,  0.9119,  0.0000,  0.0000],
                [ 0.4927, -3.4974,  2.4584, -0.3383,  0.0000],
                [ 0.4558, -4.3136,  4.5481, -1.2516,  0.0914]])
        >>> xpows = x[...,None]**torch.arange(n+1)
        >>> xpows.shape
        torch.Size([65536, 5])
        >>> yhat = torch.einsum("ij,...j->i...",coeffs,xpows) # generally unstable
        >>> yhat.shape
        torch.Size([5, 65536])
        >>> assert torch.allclose(y,yhat)
    """

    def __init__(self, alpha=0):
        r"""
        Args:
            alpha (float): parameter $\alpha>-1$.
        """
        self.alpha = float(alpha) 
        assert self.alpha > -1
        self.c00 = 1
        self.c11 = -1 
        self.c10 = 1+self.alpha
        self.a = float(0) 
        self.b = float(np.inf)
        self.distrib = torch.distributions.Gamma(concentration=self.alpha+1,rate=1)
        super().__init__()
    
    def _lnorm(self, nrange):
        return torch.lgamma(nrange+self.alpha+1)-torch.lgamma(nrange+1) 
    
    def _lweight(self, x):
        return self.distrib.log_prob(x)
    
    def _recur_terms(self, nrange):
        t1 = -1/(nrange+1)
        t2 = (2*nrange+1+self.alpha)/(nrange+1)
        t3 = (nrange+self.alpha)/(nrange+1)
        return t1,t2,t3


class Jacobi(AbstractOrthoPolys):

    r"""
    Orthonormal [Jacobi polynomials](https://en.wikipedia.org/wiki/Jacobi_polynomials) 
    supported on $[-1,1]$ with the weight normalized to be a density function. 

    Examples:
        >>> torch.set_default_dtype(torch.float64)
        >>> rng = torch.Generator().manual_seed(17)

        >>> alpha = 1/2
        >>> beta = 3/4 
        >>> poly = Jacobi(alpha=alpha,beta=beta)

        >>> u = scipy.stats.qmc.Sobol(d=1,rng=7).random(2**16)[:,0]
        >>> x = torch.from_numpy(scipy.stats.beta.ppf(u,a=beta+1,b=alpha+1,loc=-1,scale=2))
        >>> n = 4
        
        >>> y = poly(n,x)
        >>> y.shape
        torch.Size([5, 65536])
        >>> (y[:,None]*y[None,:]).mean(-1)
        tensor([[ 1.0000e+00,  1.4714e-08, -1.1409e-07,  1.9097e-07, -6.1552e-07],
                [ 1.4714e-08,  1.0000e+00,  2.2747e-07, -7.7976e-07,  1.0676e-06],
                [-1.1409e-07,  2.2747e-07,  1.0000e+00,  1.1397e-06, -2.8870e-06],
                [ 1.9097e-07, -7.7976e-07,  1.1397e-06,  1.0000e+00,  3.6799e-06],
                [-6.1552e-07,  1.0676e-06, -2.8870e-06,  3.6799e-06,  9.9999e-01]])

        >>> lrho = poly.lweight(x) 
        >>> lrhohat = torch.from_numpy(scipy.stats.beta.logpdf(x.numpy(),a=beta+1,b=alpha+1,loc=-1,scale=2))
        >>> assert torch.allclose(lrho,lrhohat,1e-3)
        
        >>> Cs = torch.exp(poly.lnorm(n))
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[0]/Cs[0])*y[0],1+0*x)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[1]/Cs[0])*y[1],(alpha+1)+(alpha+beta+2)*(x-1)/2)
        >>> assert torch.allclose(poly.c00*torch.sqrt(Cs[2]/Cs[0])*y[2],(alpha+1)*(alpha+2)/2+(alpha+2)*(alpha+beta+3)*(x-1)/2+(alpha+beta+3)*(alpha+beta+4)/2*((x-1)/2)**2)

        >>> coeffs = poly.coeffs(n)
        >>> coeffs.shape
        torch.Size([5, 5])
        >>> coeffs
        tensor([[  1.0000,   0.0000,   0.0000,   0.0000,   0.0000],
                [ -0.1591,   2.0677,   0.0000,   0.0000,   0.0000],
                [ -0.9729,  -0.3985,   4.1846,   0.0000,   0.0000],
                [  0.1742,  -4.0069,  -0.8711,   8.4202,   0.0000],
                [  0.9690,   0.7848, -12.2100,  -1.8273,  16.9029]])
        >>> xpows = x[...,None]**torch.arange(n+1)
        >>> xpows.shape
        torch.Size([65536, 5])
        >>> yhat = torch.einsum("ij,...j->i...",coeffs,xpows) # generally unstable
        >>> yhat.shape
        torch.Size([5, 65536])
        >>> assert torch.allclose(y,yhat)
    """
    
    def __init__(self, alpha=0, beta=0):
        r"""
        Args:
            alpha (float): parameter $\alpha>-1$.
            beta (float): parameter $\beta>-1$.
        """
        self.alpha = float(alpha)
        self.beta = float(beta)
        assert self.alpha > -1 
        assert self.beta > -1
        self.c00 = 1
        self.c11 = (self.alpha+self.beta+2)/2
        self.c10 = (self.alpha+1)-(self.alpha+self.beta+2)/2
        self.a = float(-1) 
        self.b = float(1) 
        self.distrib = torch.distributions.Beta(self.beta+1,self.alpha+1)
        super().__init__()
    
    def _lnorm(self, nrange):
        t0 = (1+self.alpha+self.beta)*np.log(2)+scipy.special.gammaln(self.alpha+1)+scipy.special.gammaln(self.beta+1)-scipy.special.gammaln(self.alpha+self.beta+2)+np.log(scipy.special.betainc(1+self.alpha,1+self.beta,1/2)+scipy.special.betainc(1+self.beta,1+self.alpha,1/2))
        lognum = (self.alpha+self.beta+1)*np.log(2) + torch.lgamma(nrange[1:]+self.alpha+1)+torch.lgamma(nrange[1:]+self.beta+1)
        logdenom = torch.log(2*nrange[1:]+self.alpha+self.beta+1) + torch.lgamma(nrange[1:]+1) + torch.lgamma(nrange[1:]+self.alpha+self.beta+1)
        trest = lognum-logdenom
        return torch.hstack([t0*torch.ones(1),trest])
    
    def _lweight(self, x):
        return self.distrib.log_prob((1+x)/2)-np.log(2)
    
    def _recur_terms(self, nrange):
        t1num = (2*nrange+1+self.alpha+self.beta)*(2*nrange+2+self.alpha+self.beta)
        t1denom = 2*(nrange+1)*(nrange+1+self.alpha+self.beta)
        t2num = (self.alpha**2-self.beta**2)*(2*nrange+1+self.alpha+self.beta)
        t2denom = 2*(nrange+1)*(2*nrange+self.alpha+self.beta)*(nrange+1+self.alpha+self.beta)
        t3num = (nrange+self.alpha)*(nrange+self.beta)*(2*nrange+2+self.alpha+self.beta)
        t3denom = (nrange+1)*(nrange+1+self.alpha+self.beta)*(2*nrange+self.alpha+self.beta)
        return t1num/t1denom,t2num/t2denom,t3num/t3denom

class Gegenbauer(Jacobi):
    
    r"""
    Orthonormal [Gegenbauer polynomials](https://en.wikipedia.org/wiki/Gegenbauer_polynomials) 
    supported on $[-1,1]$ with the weight normalized to be a density function. 
    
    These are a special case of the Jacobi polynomials with $\alpha=\beta$.
    """

    def __init__(self, alpha=0):
        r"""
        Args:
            alpha (float): parameter $\alpha>-1$.
        """
        self.alpha = float(alpha)
        super().__init__(alpha=alpha,beta=alpha)


class Chebyshev1(Gegenbauer):

    r"""
    Orthonormal [Chebyshev polynomials](https://en.wikipedia.org/wiki/Chebyshev_polynomials) of the first kind
    supported on $[-1,1]$ with the weight normalized to be a density function. 
    
    These are a special case of the Gegenbauer polynomials with $\alpha=-1/2$.
    """

    def __init__(self):
        super().__init__(alpha=-1/2)


class Chebyshev2(Gegenbauer):

    r"""
    Orthonormal [Chebyshev polynomials](https://en.wikipedia.org/wiki/Chebyshev_polynomials) of the second kind
    supported on $[-1,1]$ with the weight normalized to be a density function. 
    
    These are a special case of the Gegenbauer polynomials with $\alpha=1/2$.
    """

    def __init__(self):
        super().__init__(alpha=1/2)
    
class Legendre(Gegenbauer):

    r"""
    Orthonormal [Legendre polynomials](https://en.wikipedia.org/wiki/Legendre_polynomials) 
    supported on $[-1,1]$ with the weight normalized to be a density function. 
    
    These are a special case of the Gegenbauer polynomials with $\alpha=0$.
    """

    def __init__(self):
        super().__init__(alpha=0)
