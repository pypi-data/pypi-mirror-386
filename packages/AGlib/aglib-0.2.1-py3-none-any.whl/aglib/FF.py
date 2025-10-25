'''
General purpose form factors with and without directional average.
All FF with directional average begin with capital letter.

Most function definitions are taken from:
    Rémi Lazzari, IsGISAXS: a program for graying incidence small-angle X-ray
                  scattering analysis of supported islands,
                  Journal of Applied Crystallography (2002), 35, 406-421
'''

import numpy as np
from scipy.special import j1

def Tfactor(Qx, Qy, Qz, x, y, z):
    '''
    Prefactor for any form factor to translate a particle in real space
    
    :param: x, y, z translation in real space coordinates
    '''
    return np.exp(-1j*(Qx*x+Qy*y+Qz*z))

#################### form factors with directional dependence ######################
def sphere(Qx, Qy, Qz, R):
    '''
    Form factor of a sphere
    
    :param: R radius
    '''
    Q=np.sqrt(Qx**2+Qy**2+Qz**2)
    return Sphere(Q, R)

def cuboid(Qx, Qy, Qz, a, b, c):
    '''
    Form factor of a cuboid
    
    :param: a, b, c the edge lengths in x, y and z direction
    '''
    FFx=a*np.sinc(Qx*a/2./np.pi)
    FFy=b*np.sinc(Qy*b/2./np.pi)
    FFz=c*np.sinc(Qz*c/2./np.pi)
    return FFx*FFy*FFz

def cube(Qx, Qy, Qz, a):
    '''
    Form factor of a cube
    
    :param: a edge length
    '''
    return cuboid(Qx, Qy, Qz, a, a, a)

def cylinder(Qx, Qy, Qz, R, h):
    '''
    Form factor of a cylinder oriented parallel to z-axis
    
    :param: R raidus
    :param: h height
    '''
    # xy part
    Qr=np.sqrt(Qx**2+Qy**2)
    QR=(Qr*R)
    FFr=np.ones_like(QR)
    FFrscale=2.*np.pi*R**2
    # make sure we don't divide by zero
    QRpos=QR!=0.
    QR=QR[QRpos]
    FFr[QRpos]=j1(QR)/QR
    # z part
    FFz=h*np.sinc(Qz*h/2./np.pi)
    return FFrscale*FFr*FFz

def prism(Qx, Qy, Qz, a, h):
    '''
    Form factor of a prism oriented along the z-axis and one edge parallel to x-axis
    
    :param: a edge length
    :param: h height
    '''
    # xy part
    FFxyscale=2j*(np.sqrt(3.))
    Q1=np.sqrt(3)*Qy-Qx
    Q2=np.sqrt(3)*Qy+Qx
    FFxy=FFxyscale*(Q1*np.sin(Q2*a)*np.exp(1j*Qx*a)-
                    Q2*np.sin(Q1*a)*np.exp(-1j*Qx*a))
    FFdec=(Qx*(Qx**2-3.*Qy**2))
    xypos=(FFdec!=0.)
    FFxy[xypos]/=FFdec[xypos]
    # z part
    FFz=h*np.sinc(Qz*h/2./np.pi)
    return FFxy*FFz

def prism6(Qx, Qy, Qz, a, h):
    '''
    Form factor of a 6 sided prism oriented along the z-axis 
    and one edge parallel to x-axis
    
    :param: a edge length
    :param: h height
    '''
    s3h=np.sqrt(3.)/2.
    FF=prism(Qx, Qy, Qz, a, h)+prism(-Qx,-Qy, Qz, a, h)
    FF+=prism(0.5*Qx-s3h*Qy, s3h*Qx+0.5*Qy, Qz, a, h)
    FF+=prism(-0.5*Qx+s3h*Qy,-s3h*Qx-0.5*Qy, Qz, a, h)
    FF+=prism(-0.5*Qx-s3h*Qy, s3h*Qx-0.5*Qy, Qz, a, h)
    FF+=prism(0.5*Qx+s3h*Qy,-s3h*Qx+0.5*Qy, Qz, a, h)
    return FF
    

def truncube(Qx, Qy, Qz, a, tau):
    '''
    Form factor of a truncated cube with flat corners
    
    :param: a edge length
    :param: tau degree of truncation (0-1) 
    '''
    # Untruncated cubes form factor
    FC=cube(Qx, Qy, Qz, a)
    if tau!=0:
        a2=a/2.
        # truncated edge length is edge length/2 times tau
        b=tau*a2
        # there are a lot of cases where the corners lead to division by zero
        # so the Q-arrays are translated by a very small amount to prevent
        # either Qi=0 or Qi-Qj=0
        Qx=Qx+1e-10
        Qy=Qy+2e-10
        Qz=Qz+3e-10
        # For the truncation calculate the scattering from all 8 edges is subtracted,
        # this is done by moving and rotating a quarter of an octahedron
        # as given in By R. W. HENDRICKS, J. SCHELTEN and W. SCHMA, Philosophical Magazine (1974)
        F8=np.zeros((Qx+Qy+Qz).shape, dtype=complex)
        for s1 in [-1, 1]:
            for s2 in [-1, 1]:
                for s3 in [-1, 1]:
                    F8+=F0(s1*Qx, s2*Qy, s3*Qz, b)*np.exp(-1j*a2*(s1*Qx+s2*Qy+s3*Qz))
        return FC-F8
    else:
        return FC

def F0(Qx, Qy, Qz, b):
    '''
    Help function for calculation of truncated cubes.
    Defines one quarter of an octahedron with edge length b.
    '''
    A=np.exp(1j*b*Qx)/(Qx*(Qx-Qy)*(Qx-Qz))
    B=np.exp(1j*b*Qy)/(Qy*(Qy-Qx)*(Qy-Qz))
    C=np.exp(1j*b*Qz)/(Qz*(Qz-Qx)*(Qz-Qy))
    D=1.0/(Qx*Qy*Qz)
    return 1j*(A+B+C-D)

def facetsphere(Qx, Qy, Qz, R, f, N=10):
    '''
    Form factor of a faceted sphere
    
    :param: R radius
    :param: f fraction of radius to be removed at each facet (<1-1/sqrt(2))
    '''
    FF=sphere(Qx, Qy, Qz, R)
    H=f*R
    dh=H/N
    # coordinates to rotate cylinder to z, y and x direction
    Qsets=[(Qx, Qy, Qz), (Qz, Qx, Qy), (Qy, Qz, Qx)]
    for i in range(N):
        h=R-dh*(i+0.5)
        Rc=np.sqrt(R**2-h**2)
        for Q1, Q2, Q3 in Qsets:
            FFc=cylinder(Q1, Q2, Q3, Rc, dh)
            # translation factor for two copies of the cylinder at top and bottom
            Tc=2.*np.cos(Q3*h) # exp(1j*Q3*h)+exp(-1j*Q3*h)
            FF-=Tc*FFc
    return FF

############# Directional integrated variants, if available in analytic form ##############
def Sphere(Q, R):
    '''
    Form factor of a sphere
    
    :param: R radius 
    '''
    QR=Q*R
    FF=np.ones_like(QR)
    FFscale=4./3.*np.pi*R**3
    # make sure we don't divide by zero
    QRpos=QR!=0
    QR=QR[QRpos]
    FF[QRpos]=(np.sin(QR)-QR*np.cos(QR))/(QR)**3
    return FFscale*FF

