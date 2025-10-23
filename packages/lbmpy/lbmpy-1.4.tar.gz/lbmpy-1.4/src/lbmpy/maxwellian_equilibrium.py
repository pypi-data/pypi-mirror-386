"""
This module contains a functional interface to the continuous Maxwell-Boltzmann equilibrium and its discrete
polynomial approximation, often used to formulate lattice-Boltzmann methods for hydrodynamics.
Additionally functions are provided to compute moments and cumulants of these distributions.

The functionality of this module has mostly been replaced by the :mod:`lbmpy.equilibrium` module.
In particular, the continuous and discrete Maxwellians are now represented by
:class:`lbmpy.equilibrium.ContinuousHydrodynamicMaxwellian` and
:class:`lbmpy.equilibrium.DiscreteHydrodynamicMaxwellian`.
"""

import warnings

import sympy as sp
from sympy.core.numbers import Zero

from pystencils.cache import disk_cache
from pystencils.sympyextensions import remove_higher_order_terms

from lbmpy.moments import MOMENT_SYMBOLS
from lbmpy.continuous_distribution_measures import (
    continuous_moment,
    continuous_central_moment,
    continuous_cumulant,
)


def get_weights(stencil):
    def weight_for_direction(direction):
        squared_length = sum([d**2 for d in direction])
        return get_weights.weights[stencil.D][stencil.Q][squared_length]

    return [weight_for_direction(d) for d in stencil]


get_weights.weights = dict(
    {
        2: dict(
            {
                9: dict(
                    {
                        0: sp.Rational(4, 9),
                        1: sp.Rational(1, 9),
                        2: sp.Rational(1, 36),
                    }
                ),
                # weights taken from Coreixas et al. (2017), PRE.
                # https://doi.org/10.1103/PhysRevE.96.033306
                # (Appendix D Table 1)
                17: dict(
                    {
                        0: sp.S((575 + 193 * sp.sqrt(193)) / 8100),
                        1: sp.S((3355 - 91 * sp.sqrt(193)) / 18000),
                        2: sp.S((655 + 17 * sp.sqrt(193)) / 27000),
                        8: sp.S((685 - 49 * sp.sqrt(193)) / 54000),
                        9: sp.S((1445 - 101 * sp.sqrt(193)) / 162000),
                    }
                ),
                # weights taken from Coreixas et al. (2017), PRE.
                # https://doi.org/10.1103/PhysRevE.96.033306
                # (Appendix D Table 1)
                37: dict(
                    {
                        0: sp.S(0.23315066913235250228650),
                        1: sp.S(0.10730609154221900241246),
                        2: sp.S(0.05766785988879488203006),
                        4: sp.S(0.01420821615845075026469),
                        5: sp.S(0.00535304900051377523273),
                        8: sp.S(0.00101193759267357547541),
                        9: sp.S(0.00024530102775771734547),
                        10: sp.S(0.00028341425299419821740),
                    }
                ),
            }
        ),
        3: dict(
            {
                7: dict(
                    {
                        0: Zero(),
                        1: sp.Rational(1, 6),
                    }
                ),
                15: dict(
                    {
                        0: sp.Rational(2, 9),
                        1: sp.Rational(1, 9),
                        3: sp.Rational(1, 72),
                    }
                ),
                19: dict(
                    {
                        0: sp.Rational(1, 3),
                        1: sp.Rational(1, 18),
                        2: sp.Rational(1, 36),
                    }
                ),
                27: dict(
                    {
                        0: sp.Rational(8, 27),
                        1: sp.Rational(2, 27),
                        2: sp.Rational(1, 54),
                        3: sp.Rational(1, 216),
                    }
                ),
            }
        ),
    }
)


@disk_cache
def discrete_maxwellian_equilibrium(
    stencil,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    order=2,
    c_s_sq=sp.Symbol("c_s") ** 2,
    compressible=True,
):
    """
    Returns the common discrete LBM equilibrium as a list of sympy expressions

    Args:
        stencil: tuple of directions
        rho: sympy symbol for the density
        u: symbols for macroscopic velocity, only the first 'dim' entries are used
        order: highest order of velocity terms (for hydrodynamics order 2 is sufficient)
        c_s_sq: square of speed of sound
        compressible: compressibility
    """
    weights = get_weights(stencil)
    assert stencil.Q == len(weights)
    u = u[: stencil.D]

    res = [
        discrete_equilibrium(e_q, u, rho, w_q, order, c_s_sq, compressible)
        for w_q, e_q in zip(weights, stencil)
    ]
    return tuple(res)


def discrete_equilibrium(
    v=sp.symbols("v_:3"),
    u=sp.symbols("u_:3"),
    rho=sp.Symbol("rho"),
    weight=sp.Symbol("w"),
    order=2,
    c_s_sq=sp.Symbol("c_s") ** 2,
    compressible=True,
):
    """
    Returns the common discrete LBM equilibrium depending on the mesoscopic velocity and the directional lattice weight

    Args:
        v: symbols for mesoscopic velocity
        u: symbols for macroscopic velocity
        rho: sympy symbol for the density
        weight: symbol for stencil weights
        order: highest order of velocity terms (for hydrodynamics order 2 is sufficient)
        c_s_sq: square of speed of sound
        compressible: compressibility
    """
    rho_outside = rho if compressible else sp.Rational(1, 1)
    rho_inside = rho if not compressible else sp.Rational(1, 1)

    e_times_u = 0
    for c_q_alpha, u_alpha in zip(v, u):
        e_times_u += c_q_alpha * u_alpha

    fq = rho_inside + e_times_u / c_s_sq

    if order <= 1:
        return fq * rho_outside * weight

    u_times_u = 0
    for u_alpha in u:
        u_times_u += u_alpha * u_alpha
    fq += (
        sp.Rational(1, 2) / c_s_sq**2 * e_times_u**2
        - sp.Rational(1, 2) / c_s_sq * u_times_u
    )

    if order <= 2:
        return fq * rho_outside * weight

    fq += (
        sp.Rational(1, 6) / c_s_sq**3 * e_times_u**3
        - sp.Rational(1, 2) / c_s_sq**2 * u_times_u * e_times_u
    )

    return sp.expand(fq * rho_outside * weight)


@disk_cache
def generate_equilibrium_by_matching_moments(
    stencil,
    moments,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    c_s_sq=sp.Symbol("c_s") ** 2,
    order=None,
):
    """
    Computes discrete equilibrium, by setting the discrete moments to values taken from the continuous Maxwellian.
    The number of moments has to match the number of directions in the stencil. For documentation of other parameters
    see :func:`get_equilibrium_values_of_maxwell_boltzmann_function`
    """
    from lbmpy.moments import moment_matrix

    assert (
        len(moments) == stencil.Q
    ), f"Moment count({len(moments)}) does not match stencil size({stencil.Q})"
    continuous_moments_vector = get_equilibrium_values_of_maxwell_boltzmann_function(
        moments, stencil.D, rho, u, c_s_sq, order, space="moment"
    )
    continuous_moments_vector = sp.Matrix(continuous_moments_vector)
    M = moment_matrix(moments, stencil)
    assert (
        M.rank() == stencil.Q
    ), f"Rank of moment matrix ({M.rank()}) does not match stencil size ({stencil.Q})"
    return M.inv() * continuous_moments_vector


@disk_cache
def continuous_maxwellian_equilibrium(
    dim=3,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    v=sp.symbols("v_:3"),
    c_s_sq=sp.Symbol("c_s") ** 2,
):
    """
    Returns sympy expression of Maxwell Boltzmann distribution

    Args:
        dim: number of space dimensions
        rho: sympy symbol for the density
        u: symbols for macroscopic velocity (expected value for velocity)
        v: symbols for particle velocity
        c_s_sq: symbol for speed of sound squared, defaults to symbol c_s**2
    """
    u = u[:dim]
    v = v[:dim]

    vel_term = sum([(v_i - u_i) ** 2 for v_i, u_i in zip(v, u)])
    return (
        rho
        / (2 * sp.pi * c_s_sq) ** (sp.Rational(dim, 2))
        * sp.exp(-vel_term / (2 * c_s_sq))
    )


# -------------------------------- Equilibrium moments  ----------------------------------------------------------------
@disk_cache
def get_equilibrium_values_of_maxwell_boltzmann_function(
    moments,
    dim,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    c_s_sq=sp.Symbol("c_s") ** 2,
    order=None,
    space="moment",
):
    """
    Computes equilibrium values from the continuous Maxwell Boltzmann equilibrium.

    Args:
        moments: moments to compute, either in polynomial or exponent-tuple form
        dim: dimension (2 or 3)
        rho: symbol or value for the density
        u: symbols or values for the macroscopic velocity
        c_s_sq: symbol for speed of sound squared, defaults to symbol c_s**2
        order: if this parameter is not None, terms that have a higher polynomial order in the macroscopic velocity
               are removed
        space: function space of the equilibrium values. Either moment, central moment or cumulant space are supported.

    >>> get_equilibrium_values_of_maxwell_boltzmann_function( ( (0,0,0), (1,0,0), (0,1,0), (0,0,1), (2,0,0) ), dim=3 )
    [rho, rho*u_0, rho*u_1, rho*u_2, rho*(c_s**2 + u_0**2)]
    """
    # trick to speed up sympy integration (otherwise it takes multiple minutes, or aborts):
    # use a positive, real symbol to represent c_s_sq -> then replace this symbol afterwards with the real c_s_sq
    c_s_sq_helper = sp.Symbol("csq_helper", positive=True, real=True)
    mb = continuous_maxwellian_equilibrium(
        dim, rho, u, MOMENT_SYMBOLS[:dim], c_s_sq_helper
    )
    if space == "moment":
        result = [
            continuous_moment(mb, moment, MOMENT_SYMBOLS[:dim]).subs(
                c_s_sq_helper, c_s_sq
            )
            for moment in moments
        ]
    elif space == "central moment":
        result = [
            continuous_central_moment(
                mb, moment, MOMENT_SYMBOLS[:dim], velocity=u
            ).subs(c_s_sq_helper, c_s_sq)
            for moment in moments
        ]
    elif space == "cumulant":
        result = [
            continuous_cumulant(mb, moment, MOMENT_SYMBOLS[:dim]).subs(
                c_s_sq_helper, c_s_sq
            )
            for moment in moments
        ]
    else:
        raise ValueError("Only moment, central moment or cumulant space are supported")

    if order is not None:
        result = [remove_higher_order_terms(r, order=order, symbols=u) for r in result]

    return result


@disk_cache
def get_moments_of_discrete_maxwellian_equilibrium(
    stencil,
    moments,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    c_s_sq=sp.Symbol("c_s") ** 2,
    order=None,
    compressible=True,
):
    """Compute moments of discrete maxwellian equilibrium.

    Args:
        stencil: stencil is required to compute moments of discrete function
        moments: moments in polynomial or exponent-tuple form
        rho: symbol or value for the density
        u: symbols or values for the macroscopic velocity
        c_s_sq: symbol for speed of sound squared, defaults to symbol c_s**2
        order: highest order of u terms
        compressible: compressible or incompressible form
    """
    from lbmpy.moments import discrete_moment

    if order is None:
        order = 4
    mb = discrete_maxwellian_equilibrium(stencil, rho, u, order, c_s_sq, compressible)
    return tuple([discrete_moment(mb, moment, stencil).expand() for moment in moments])


def compressible_to_incompressible_moment_value(term, rho, u):
    """**[DEPRECATED]** Compressible to incompressible equilibrium moments

    Transforms so-called compressible equilibrium moments (as obtained from the continuous Maxwellian) by
    removing the density factor in all monomials where velocity components are multiplied to the density.

    Examples:
        >>> rho, *u = sp.symbols("rho u_:2")
        >>> compressible_to_incompressible_moment_value(rho  + rho * u[0] + rho * u[0]*u[1], rho, u)
        rho + u_0*u_1 + u_0

    Args:
        term: compressible equilibrium value
        rho: symbol for density
        u: symbol for velocity

    Returns:
        incompressible equilibrium value
    """
    warnings.warn(
        "Usage of `compressible_to_incompressible_moment_value` is deprecated,"
        " and the method will be removed soon."
    )
    term = sp.sympify(term)
    term = term.expand()
    if term.func != sp.Add:
        args = [
            term,
        ]
    else:
        args = term.args

    res = 0
    for t in args:
        contained_symbols = t.atoms(sp.Symbol)
        if rho in contained_symbols and len(contained_symbols.intersection(set(u))) > 0:
            res += t / rho
        else:
            res += t
    return res


# -------------------------------- Equilibrium cumulants ---------------------------------------------------------------


@disk_cache
def get_cumulants_of_discrete_maxwellian_equilibrium(
    stencil,
    cumulants,
    rho=sp.Symbol("rho"),
    u=sp.symbols("u_:3"),
    c_s_sq=sp.Symbol("c_s") ** 2,
    order=None,
    compressible=True,
):
    from lbmpy.cumulants import discrete_cumulant

    if order is None:
        order = 4
    mb = discrete_maxwellian_equilibrium(stencil, rho, u, order, c_s_sq, compressible)
    return tuple(
        [discrete_cumulant(mb, cumulant, stencil).expand() for cumulant in cumulants]
    )
