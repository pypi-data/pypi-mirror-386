"""
SEC/Models/Simple.py
"""
import numpy as np

def gaussian(x, A, mu, sigma):
    """
    The Gaussian function.

    Parameters
    ----------
    x : float or array-like
        The input value(s).
    A : float
        The amplitude of the Gaussian.
    mu : float
        The mean of the Gaussian.
    sigma : float
        The standard deviation of the Gaussian.

    Returns
    -------
    float or array-like
        The computed Gaussian value(s).
    """
    return A*np.exp(-((x - mu)**2/(2*sigma**2)))

def _egh_impl(x, H, tR, sigma, tau):
    x_  = x - tR
    s2  = 2 * sigma**2
    z   = s2 + tau*x_
    z_neg   = z <= 0
    z_pos   = z > 0

    zero_part = np.zeros( len(x) )[z_neg]
    posi_part = H * np.exp( -x_[z_pos]**2/( s2 + tau*x_[z_pos] ) )

    if tau > 0:
        parts = [ zero_part, posi_part ]
    else:
        parts = [ posi_part, zero_part ]

    return np.hstack( parts )

def egh(x, H, tR, sigma, tau):
    """
    The exponential-Gaussian hybrid (EGH) function.

    See also: `Exponential-Gaussian Hybrid <https://biosaxs-dev.github.io/molass-essence/chapters/20/egh.html>`_.

    Parameters
    ----------
    x : float or array-like
        The input value(s).
    H : float
        The height parameter.
    tR : float
        The retention time parameter.
    sigma : float
        The standard deviation of the Gaussian component.
    tau : float
        The decay constant of the exponential component.

    Returns
    -------
    float or array-like
        The computed EGH value(s).
    """
    if np.isscalar(x):
        x = np.array([x])
        return _egh_impl(x, H, tR, sigma, tau)[0]
    else:
        return _egh_impl(x, H, tR, sigma, tau)

"""
Kevin Lan, James W. Jorgenson, Journal of Chromatography A, 915 (2001) 1?13
"""
A0i = np.array([4, -6.293724, 9.232834, -11.342910, 9.123978, -4.173753, 0.827797])
e0 = np.poly1d(A0i[::-1])
"""
e0(th) = a0 + a1*th + a2*th**2 + ... + am*th**m
"""
A1i = np.array([0.75, 0.033807, -0.301080, 1.200371, -1.813317, 1.279318, -0.326582])
e1 = np.poly1d(A1i[::-1])

A2i = np.array([1, -0.982254, 0.568593, 0.512587, -1.184361, 0.939222, -0.240814])
e2 = np.poly1d(A2i[::-1])

# A3i = np.array([0.5, -0.664611, 0.706192, -0.293500, -0.083980, 0.200306, -0.064264])
A3i = np.array([0.49106035, -0.45648717, -0.93606276, 5.25394258, -9.16354757, 7.36039624, -2.25720537])
e3 = np.poly1d(A3i[::-1])

def egh_var(sigma, tau):
    """
    Returns the variance of the EGH distribution.

    Parameters
    ----------
    sigma : float
        The standard deviation of the Gaussian component.
    tau : float
        The decay constant of the exponential component.

    Returns
    -------
    float
        The variance of the EGH distribution.
    """
    tau_ = abs(tau)
    th = np.arctan2(tau_, sigma)
    return (sigma**2 + sigma*tau_ + tau**2) * e2(th)

def egh_std(sigma, tau):
    """
    Returns the standard deviation for the EGH distribution.

    Parameters
    ----------
    sigma : float
        The standard deviation of the Gaussian component.
    tau : float
        The decay constant of the exponential component.

    Returns
    -------
    float
        The standard deviation for the EGH distribution.
    """
    return np.sqrt(egh_var(sigma, tau))

SQRT_PI_8 = np.sqrt(np.pi/8)
def egh_pdf(x, tR=0, sigma=1.0, tau=0.0, scale=1):
    """
    The probability density function (PDF) of the EGH distribution.
 
    Parameters
    ----------
    x : float or array-like
        The input value(s).
    tR : float, optional
        The retention time parameter, by default 0.
    sigma : float, optional
        The standard deviation of the Gaussian component, by default 1.0.
    tau : float, optional
        The decay constant of the exponential component, by default 0.0.
    scale : float, optional
        The scaling factor, by default 1.

    Returns
    -------
    float or array-like
        The computed PDF value(s).
    """
    tau_ = abs(tau)
    th = np.arctan2(tau_, sigma)
    H_ = (sigma*SQRT_PI_8 + tau_)*e0(th)
    return egh(x, scale, tR, sigma, tau)/H_
