"""Self nductance calculations for coils.

author: Darren Garnier <garnier@mit.edu>

basic equations come from analytic approximations of old.
tested in real life with the LDX Fcoil / Ccoil / Lcoil system.

One from Maxwell himself, and better ones from:

Lyle, T. R.  "On the Self-inductance of Circular Coils of
    Rectangular Section".  Roy. Soc. London. A.  V213 (1914) pp 421-435.
    https://doi.org/10.1098/rsta.1914.0009

Unfortunately, Lyle doesn't work that well with large dz/R coils.  Other
approximations are also included.

This code now uses numba to do just-in-time compiliation and parallel execution
to greatly increase speed. Also requires numba-scipy for elliptical functions.
numba-scipy can be fragile and sometimes needs to be "updated" before installation
to the newest version of numba.
"""

import math

import numpy as np

from ._numba import njit, prange
from .elliptics import ellipke
from .filaments import mutual_inductance_fil
from .mutual import lyle_equivalent_subcoil_filaments, mutual_lyles_method
from .utils import _lyle_terms, section_coil

MU0 = 4e-7 * math.pi  # permeability of free space


@njit
def L_maxwell(r, dr, dz, n):
    """Self inductance of a rectangular coil with constant current density by Maxwell.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, wp, phi, GMD = _lyle_terms(b, c)
    L = MU0 * (n**2) * a * (math.log(8 * a / GMD) - 2)
    return L


@njit
def L_round(r, a, n):
    """Self inductance of a round conductor coil with constant current density.

    Args:
        r (float): coil centerline radius
        a (float): coil conductor radius
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    L = MU0 * (n**2) * r * (math.log(8 * r / a) - 1.75)
    return L


@njit
def L_hollow_round(r, a, n):
    """Self inductance of a round conductor coil with skin current.

    Args:
        r (float): coil centerline radius
        a (float): coil conductor radius
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    L = MU0 * (n**2) * r * (math.log(8 * r / a) - 2)
    return L


@njit
def L_lyle4(r, dr, dz, n):
    """Self inductance of a rectangular coil via Lyle to 4th order, Eq3.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, wp, phi, GMD = _lyle_terms(b, c)
    p2 = 1 / (2**5 * 3 * d**2) * (3 * b**2 + c**2)
    q2 = (
        1
        / (2**5 * 3 * d**2)
        * (
            1 / 2 * b**2 * u
            - 1 / 10 * c**2 * v
            - 16 / 5 * b**2 * w
            - (3 * b**2 + c**2) * phi
            + 69 / 20 * b**2
            + 221 / 60 * c**2
        )
    )
    p4 = 1 / (2**11 * 3**2 * 5 * d**4) * (-90 * b**4 + 105 * (b * c) ** 2 + 22 * c**4)
    q4 = (
        1
        / (2**11 * 3**2 * 5 * d**4)
        * (
            -(-90 * b**4 + 105 * (b * c) ** 2 + 22 * c**4) * phi
            - 69 / 28 * c**4 * v
            - u / 4 * (115 * b**4 - 480 * (b * c) ** 2)
            + 2**8 * w / 7 * (6 * b**4 - 7 * (b * c) ** 2)
            - 1 / (2**3 * 5 * 7) * (36590 * b**4 - 2035 * (b * c) ** 2 - 11442 * c**4)
        )
    )

    ML = np.log(8 * a / GMD)

    # equation #3

    eq3 = (
        MU0
        * (n**2)
        * a
        * (ML - 2 + (d / a) ** 2 * (p2 * ML + q2) + (d / a) ** 4 * (p4 * ML + q4))
    )
    return eq3


# equation 4.. slightly different result... not sure which is better.
# equation 3 above matches what I did for the 6th order.
# and it also seems to match the 4th order in the paper.
# and in other papers with examples


@njit
def L_lyle4_eq4(r, dr, dz, n):
    """Self inductance of a rectangular coil via Lyle to 4th order, Eq4.

    this doesn't give quite the same answer as eq3 above.
    and it doesn't seem to work as well.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, wp, phi, GMD = _lyle_terms(b, c)
    p2 = 1 / (2**5 * 3 * d**2) * (3 * b**2 + c**2)
    q2 = (
        1
        / (2**5 * 3 * d**2)
        * (
            1 / 2 * b**2 * u
            - 1 / 10 * c**2 * v
            - 16 / 5 * b**2 * w
            - (3 * b**2 + c**2) * phi
            + 69 / 20 * b**2
            + 221 / 60 * c**2
        )
    )
    p4 = 1 / (2**11 * 3**2 * 5 * d**4) * (-90 * b**4 + 105 * (b * c) ** 2 + 22 * c**4)
    q4 = (
        1
        / (2**11 * 3**2 * 5 * d**4)
        * (
            -(-90 * b**4 + 105 * (b * c) ** 2 + 22 * c**4) * phi
            - 69 / 28 * c**4 * v
            - u / 4 * (115 * b**4 - 480 * (b * c) ** 2)
            + 2**8 * w / 7 * (6 * b**4 - 7 * (b * c) ** 2)
            - 1 / (2**3 * 5 * 7) * (36590 * b**4 - 2035 * (b * c) ** 2 - 11442 * c**4)
        )
    )

    m1 = p2
    n1 = -(p2 + q2)
    m2 = p4
    n2 = -(p4 + q4) + 1 / 2 * (m1 - n1) ** 2
    n3 = (m1 - n1) * (m2 - n2 - 1 / 6 * (m1 - n1) * (m1 + 2 * n1))

    A = a * (1 + m1 * (d / a) ** 2 + m2 * (d / a) ** 4)
    R = GMD * (1 + n1 * (d / a) ** 2 + n2 * (d / a) ** 4 + n3 * (d / a) ** 6)

    eq4 = MU0 * (n**2) * A * (np.log(8 * A / R) - 2)
    return eq4


@njit
def L_lyle6(r, dr, dz, n):
    """Self inductance of a rectangular coil via Lyle to 6th order.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, ww, phi, GMD = _lyle_terms(b, c)
    bd2 = (b / d) ** 2
    cd2 = (c / d) ** 2
    da2 = (d / a) ** 2
    ML = np.log(8 * a / d)

    # after further reduction in mathematica... all the terms.
    f = (
        ML
        + (1 + u + v - 8 * (w + ww)) / 12.0  # 0th order in d/a
        + (
            da2
            * (
                cd2 * (221 + 60 * ML - 6 * v)
                + 3 * bd2 * (69 + 60 * ML + 10 * u - 64 * w)
            )
        )
        / 5760.0  # 2nd order
        + (
            da2**2
            * (
                2 * cd2**2 * (5721 + 3080 * ML - 345 * v)
                + 5 * bd2 * cd2 * (407 + 5880 * ML + 6720 * u - 14336 * w)
                - 10 * bd2**2 * (3659 + 2520 * ML + 805 * u - 6144 * w)
            )
        )
        / 2.58048e7  # 4th order
        + (
            da2**3
            * (
                3 * cd2**3 * (4308631 + 86520 * ML - 10052 * v)
                - 14 * bd2**2 * cd2 * (617423 + 289800 * ML + 579600 * u - 1474560 * w)
                + 21 * bd2**3 * (308779 + 63000 * ML + 43596 * u - 409600 * w)
                + 42 * bd2 * cd2**2 * (-8329 + 46200 * ML + 134400 * u - 172032 * w)
            )
        )
        / 1.73408256e10  # 6th order
    )
    L = MU0 * (n**2) * a * f
    # print("Lyle6 r: %.4g, dr: %.4g, dz: %4g, n: %d, L: %.8g"%(a,c,b,n,L))
    return L


@njit
def dLdR_lyle6(r, dr, dz, n):
    """Radial derivative of self inductance of a rectangular coil via Lyle to 6th order.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: radial derivative of inductance in Henrys/meter
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, ww, phi, GMD = _lyle_terms(b, c)
    bd2 = (b / d) ** 2
    cd2 = (c / d) ** 2
    da2 = (d / a) ** 2

    ML = np.log(8 * a / d)

    f = (
        ML
        + (13 + u + v - 8 * w - 8 * ww) / 12.0  # zero
        + (
            da2
            * (
                cd2 * (-161 - 60 * ML + 6 * v)
                - 3 * bd2 * (9 + 60 * ML + 10 * u - 64 * w)
            )
        )
        / 5760.0  # 2nd order
        + (
            da2**2
            * (
                -2 * cd2**2 * (14083 + 9240 * ML - 1035 * v)
                - 15 * bd2 * cd2 * (-1553 + 5880 * ML + 6720 * u - 14336 * w)
                + 30 * bd2**2 * (2819 + 2520 * ML + 805 * u - 6144 * w)
            )
        )
        / 2.58048e7  # 4th order
        + (
            da2**3
            * (
                -3 * cd2**3 * (4291327 + 86520 * ML - 10052 * v)
                + 14 * bd2**2 * cd2 * (559463 + 289800 * ML + 579600 * u - 1474560 * w)
                - 21 * bd2**3 * (296179 + 63000 * ML + 43596 * u - 409600 * w)
                - 42 * bd2 * cd2**2 * (-17569 + 46200 * ML + 134400 * u - 172032 * w)
            )
        )
        / 3.46816512e9  # 6th order
    )

    dLdR = 4e-7 * np.pi * (n**2) * f
    return dLdR


@njit
def L_lyle6_appendix(r, dr, dz, n):
    """Self inductance of a rectangular coil via Lyle to 6th order, appendix.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    d, u, v, w, wp, phi, GMD = _lyle_terms(b, c)

    p6 = (
        1
        / (2**16 * 3 * 5 * 7 * d**6)
        * (525 * b**6 - 1610 * b**4 * c**2 + 770 * b**2 * c**4 + 103 * c**6)
    )
    q6 = (
        1
        / (2**16 * 3 * 5 * 7 * d**6)
        * (
            0
            + (3633 / 10 * b**6 - 3220 * b**4 * c**2 + 2240 * b**2 * c**4) * u
            - (359 / 30) * c**6 * v
            - 2**11 * (5 / 3 * b**6 - 4 * b**4 * c**2 + 7 / 5 * b**2 * c**4) * w
            + 2161453 / (2**3 * 3 * 5 * 7) * b**6
            - 617423 / (2**2 * 3**2 * 5) * b**4 * c**2
            - 8329 / (2**2 * 3 * 5) * b**2 * c**4
            + 4308631 / (2**3 * 3 * 5 * 7) * c**6
        )
    )

    # just add the correction to the 4th order solution
    L6 = L_lyle4(r, dr, dz, n) + 4e-7 * np.pi * (n**2) * a * (d / a) ** 6 * (
        p6 * np.log(8 * a / d) + q6
    )
    # print("Lyle6A r: %.4g, dr: %.4g, dz: %4g, n: %d, L: %.8g"%(a,c,b,n,L6))
    return L6


@njit
def L_lyle_sectioning(r, dr, dz, nt, nr, nz):
    """Self inductance by sectioning, Lyle's method, and Lyle's 4th order.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        nt (float): number of turns
        nr (int): number of radial sections
        nz (int): number of axial sections

    Returns:
        float: coil self inductance in Henrys
    """
    L = 0
    subcoils = section_coil(r, dr, dz, nt, nt, nr, nz)
    fils = lyle_equivalent_subcoil_filaments(subcoils)

    for i in range(nr * nz):
        for j in range(nr * nz):
            if i != j:
                L += mutual_lyles_method(*fils[i], *fils[j])
        L += 2 * L_lyle6(*subcoils[i])
    return L


@njit
def L_long_solenoid_butterworth(r, dr, dz, n):
    """Self inductance of a long solenoid by Butterworth's formula.

    As written in Grover, Bulletin of the Bureau of Standards, Vol. 14 pg. 558
    https://nvlpubs.nist.gov/nistpubs/bulletin/14/nbsbulletinv14n4p537_A2b.pdf

    Original S Butterworth 1914 Proc. Phys. Soc. London 27 371

    Applies when dz > 2*r.

    Args:
        r (float): coil centerline radius
        dr (float): coil radial width
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(r)
    b = float(dz)
    c = float(dr)
    # L = 4e-7 * np.pi * (n**2) * a / b

    k2 = 4 * a**2 / (4 * a**2 + b**2)
    kp2 = b**2 / (4 * a**2 + b**2)
    k = np.sqrt(k2)
    kp = np.sqrt(kp2)

    # assume dz > 2*r
    ell = k2 / ((1 + kp) * (1 + np.sqrt(kp)) ** 2)
    q = ell / 2 + 2 * (ell / 2) ** 5 + 15 * (ell / 2) ** 9  # + ....

    delta = 2 * q - 2 * q**4 + 2 * q**9
    gamma = q - 4 * q**4 + 9 * q**9
    beta = q**2 + 3 * q**6 + 6 * q**12
    alpha = q**2 + q**6 + q**12

    K = (  # K
        2.0
        / (3 * (1 - delta) ** 2)
        * (1 + 8 * beta / (1 + alpha) + kp2 / k2 * 8 * gamma / (1 - delta))
        - 4 / (3 * np.pi) * k / kp
    )

    DL_L1 = (  # delta L/L_1, eq 29A
        -1
        / 3
        * (c / a)
        * (
            1
            - c / (4 * a)
            - 1 / (2 * np.pi) * (c / b) * (np.log(8 * a / c) - 23 / 12)
            + 1
            / (160 * np.pi)
            * (c / a) ** 3
            * (a / b)
            * (np.log(8 * a / c) - 1.0 / 20)
            - 1
            / 4
            * (c * a / b**2)
            * (1 - 7 / 4 * (a / b) ** 2 + 17 / 4 * (a / b) ** 4)
            - 1 / 96 * (c / a) ** 3 * (a / b) ** 2 * (1 - 39 / 10 * (a / b) ** 2)
        )
    )
    L1 = L_lorentz(r, dr, dz, n)

    return L1 * (K + DL_L1)


@njit
def _L_thin_wall_babic_akyel(r, _dr, dz, n):
    """Self inductance thin wall solenoid by Babic and Akyel's formula.

    Follow formulae from:
    S. Babic and C. Akyel, "Improvement in calculation of the self- and mutual inductance
    of thin-wall solenoids and disk coils," in IEEE Transactions on Magnetics,
    vol. 36, no. 4, pp. 1970-1975, July 2000, doi: 10.1109/TMAG.2000.875240.

    this _is_ be the same as Lorentz formula..

    Args:
        r (float): coil centerline radius
        _dr (float): coil radial width (ignored)
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    a = float(dz) / 2
    # R1 = float(r) - float(dr) / 2
    # R2 = float(r) + float(dr) / 2
    # alpha = R2 / R1
    # lets double check why I'm not using alpha...
    beta = a / r

    k2 = 1 / (1 + beta**2)
    elk, ele = ellipke(k2)
    k = np.sqrt(k2)
    tk1 = 4.0 / (3 * np.pi * beta * k**3) * ((2 * k2 - 1) * ele + (1 - k2) * elk - k**3)
    eq8 = MU0 * (n**2) * r * np.pi / (2 * beta) * tk1  # eq 8
    return eq8


@njit
def L_lorentz(r, _dr, dz, n):
    """Self inductance of a thin wall solenoid by Lorentz's formula.

    Given in:
    Rosa and Grover, Formulas and Tables for the Calculation of Mutual and Self-Inductance
    https://nvlpubs.nist.gov/nistpubs/bulletin/08/nbsbulletinv8n1p1_A2b.pdf
    or
    https://www.jstor.org/stable/pdf/24521000.pdf
    (Formula 72 on page 118)

    Args:
        r (float): coil centerline radius
        _dr (float): coil radial width (ignored)
        dz (float): coil height
        n (int): number of turns

    Returns:
        float: coil self inductance in Henrys
    """
    beta = dz / (2 * r)
    k2 = 1 / (1 + beta**2)
    k3 = k2**1.5
    beta2 = beta**2
    elK, elE = ellipke(k2)

    f = 2 / 3 / beta2 * (((2 * k2 - 1) * elE + (1 - k2) * elK) / k3 - 1)
    Ls = MU0 * (n**2) * r * f
    return Ls


@njit(parallel=True)
def self_inductance_by_filaments(f, conductor="round", a=0.01, dr=0.01, dz=0.01):
    """Self inductance of filament set.

    Args:
        f (array): first filament array
        conductor (str, optional): conductor shape. Defaults to "round".
        a (float, optional): conductor radius. Defaults to 0.01.
        dr (float, optional): conductor radial width. Defaults to 0.01
        dz (float, optional): conductor vertical height. Defaults to 0.01

    Returns:
        float: self inductance of filament set in Henries
    """
    L = float(0)
    for i in prange(f.shape[0]):
        for j in range(f.shape[0]):
            if i != j:
                L += mutual_inductance_fil(f[i, :], f[j, :])
        if conductor == "round":
            L += L_round(f[i, 0], a, f[i, 2])
        elif conductor == "hollow_round":
            L += L_hollow_round(f[i, 0], a, f[i, 2])
        elif conductor == "rect":
            L += L_lyle6(f[i, 0], dr, dz, f[i, 2])
    return L
