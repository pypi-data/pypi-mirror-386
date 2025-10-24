from jax import numpy as jnp
from jaxtyping import ArrayLike, DTypeLike, PyTree
from typing import Any

"""General gravity perturbations"""


def point_mass_grav(
    t: DTypeLike, x: ArrayLike, args: PyTree[Any] = {"mu": 1.0}
) -> ArrayLike:
    r"""Returns the acceleration due to a point mass.

    Args:
        t: The time.
        x: (N,) The state vector, where the first 3 elements are the position vector.
        args: Static arguments.

    Returns:
        The acceleration due to a point mass.

    Notes:
        The acceleration due to a point mass is defined as:
        $$
        \boldsymbol{a} = -\frac{\mu}{r^3} \boldsymbol{r}
        $$
        where $\boldsymbol{a}$ is the acceleration, $\mu$ is the gravitational parameter, and $\boldsymbol{r}$ is the position vector.

    References:
        Battin, 1999, pp.114.

    Examples:
        >>> import jax.numpy as jnp
        >>> import astrodynx as adx
        >>> t = 0.0
        >>> x = jnp.array([1.0, -1.0, 1.0, 0.0, 0.0, 0.0])
        >>> args = {"mu": 1.0}
        >>> adx.gravity.point_mass_grav(t, x, args)
        Array([-0.1924...,  0.1924..., -0.1924...], dtype=float32)
    """
    mu = args["mu"]
    mu_ = mu / jnp.linalg.vector_norm(x[:3]) ** 3
    return jnp.stack([-mu_ * x[0], -mu_ * x[1], -mu_ * x[2]])


def j2_acc(
    t: DTypeLike, x: ArrayLike, args: PyTree[Any] = {"mu": 1.0, "J2": 0.0, "R_eq": 1.0}
) -> ArrayLike:
    r"""Returns the acceleration due to J2 perturbation.

    Args:
        t: The time.
        x: (N,) The state vector, where the first 3 elements are the position vector.
        args: Static arguments.

    Returns:
        The acceleration due to J2 perturbation.

    Notes:
        The acceleration due to J2 perturbation is defined as:
        $$
        \begin{align*}
        a_x &= -\frac{3}{2} \frac{\mu J_2 R_{eq}^2}{r^5} x \left( 1 - 5 \frac{z^2}{r^2} \right) \\
        a_y &= -\frac{3}{2} \frac{\mu J_2 R_{eq}^2}{r^5} y \left( 1 - 5 \frac{z^2}{r^2} \right) \\
        a_z &= -\frac{3}{2} \frac{\mu J_2 R_{eq}^2}{r^5} z \left( 3 - 5 \frac{z^2}{r^2} \right)
        \end{align*}
        $$
        where $\boldsymbol{a}$ is the acceleration, $\mu$ is the gravitational parameter, $J_2$ is the second zonal harmonic, $R_{eq}$ is the equatorial radius, and $\boldsymbol{r} = [x, y, z]$ is the position vector.

    References:
        Vallado, 2013, pp.594.

    Examples:
        >>> import jax.numpy as jnp
        >>> import astrodynx as adx
        >>> t = 0.0
        >>> x = jnp.array([1.0, -1.0, 1.0, 0.0, 0.0, 0.0])
        >>> args = {"mu": 1.0, "J2": 1e-3, "R_eq": 1.0}
        >>> expected = jnp.array([ 6.4150023e-05, -6.4150023e-05, -1.2830009e-04])
        >>> actual = adx.gravity.j2_acc(t, x, args)
        >>> jnp.allclose(expected, actual)
        Array(True, dtype=bool)
    """
    mu = args["mu"]
    J2 = args["J2"]
    R_eq = args["R_eq"]
    r = jnp.linalg.vector_norm(x[:3])
    zsq_over_rsq = (x[2] / r) ** 2
    factor = -1.5 * mu * J2 * R_eq**2 / r**5
    ax = factor * x[0] * (1 - 5 * zsq_over_rsq)
    ay = factor * x[1] * (1 - 5 * zsq_over_rsq)
    az = factor * x[2] * (3 - 5 * zsq_over_rsq)
    return jnp.stack([ax, ay, az])


def j3_acc(
    t: DTypeLike, x: ArrayLike, args: PyTree[Any] = {"mu": 1.0, "J3": 0.0, "R_eq": 1.0}
) -> ArrayLike:
    r"""Returns the acceleration due to J3 perturbation.

    Args:
        t: The time.
        x: The state vector.
        args: Static arguments.

    Returns:
        The acceleration due to J3 perturbation.

    Notes:
        The acceleration due to J3 perturbation is defined as:
        $$
        \begin{align*}
        a_x &= -\frac{5}{2} \frac{\mu J_3 R_{eq}^3}{r^7} x
        \left( 3 z - \frac{7 z^3}{r^2} \right) \\
        a_y &= -\frac{5}{2} \frac{\mu J_3 R_{eq}^3}{r^7} y
        \left( 3 z - \frac{7 z^3}{r^2} \right) \\
        a_z &= -\frac{5}{2} \frac{\mu J_3 R_{eq}^3}{r^7}
        \left( 6 z^2 - \frac{7 z^4}{r^2} - \frac{3}{5} r^2 \right)
        \end{align*}
        $$
        where $\boldsymbol{a}$ is the acceleration, $\mu$ is the gravitational parameter, $J_3$ is the third zonal harmonic, $R_{eq}$ is the equatorial radius, and $\boldsymbol{r} = [x, y, z]$ is the position vector.

    References:
        Vallado, 2013, pp.594.

    Examples:
        >>> import jax.numpy as jnp
        >>> import astrodynx as adx
        >>> t = 0.0
        >>> x = jnp.array([1.0, -1.0, 1.0, 0.0, 0.0, 0.0])
        >>> args = {"mu": 1.0, "J3": 1e-6, "R_eq": 1.0}
        >>> expected = jnp.array([-3.5638898e-08, 3.5638898e-08, -9.9788920e-08])
        >>> actual = adx.gravity.j3_acc(t, x, args)
        >>> jnp.allclose(expected, actual)
        Array(True, dtype=bool)
    """
    mu = args["mu"]
    J3 = args["J3"]
    R_eq = args["R_eq"]
    r = jnp.linalg.vector_norm(x[:3])
    z3_over_rsq = x[2] ** 3 / r**2
    factor = -2.5 * mu * J3 * R_eq**3 / r**7
    ax = factor * x[0] * (3 * x[2] - 7 * z3_over_rsq)
    ay = factor * x[1] * (3 * x[2] - 7 * z3_over_rsq)
    az = factor * (6 * x[2] ** 2 - 7 * z3_over_rsq * x[2] - 0.6 * r**2)
    return jnp.stack([ax, ay, az])


def j4_acc(
    t: DTypeLike, x: ArrayLike, args: PyTree[Any] = {"mu": 1.0, "J4": 0.0, "R_eq": 1.0}
) -> ArrayLike:
    r"""Returns the acceleration due to J4 perturbation.

    Args:
        t: The time.
        x: The state vector.
        args: Static arguments.

    Returns:
        The acceleration due to J4 perturbation.

    Notes:
        The acceleration due to J4 perturbation is defined as:
        $$
        \begin{align*}
        a_x &= \frac{15}{8} \frac{\mu J_4 R_{eq}^4}{r^7} x
        \left( 1 - \frac{14 z^2}{r^2} + \frac{21 z^4}{r^4} \right) \\
        a_y &= \frac{15}{8} \frac{\mu J_4 R_{eq}^4}{r^7} y
        \left( 1 - \frac{14 z^2}{r^2} + \frac{21 z^4}{r^4} \right) \\
        a_z &= \frac{15}{8} \frac{\mu J_4 R_{eq}^4}{r^7} z
        \left( 5 - \frac{70 z^2}{3 r^2} + \frac{21 z^4}{r^4} \right)
        \end{align*}
        $$
        where $\boldsymbol{a}$ is the acceleration, $\mu$ is the gravitational parameter, $J_4$ is the fourth zonal harmonic, $R_{eq}$ is the equatorial radius, and $\boldsymbol{r} = [x, y, z]$ is the position vector.

    References:
        Vallado, 2013, pp.594.

    Examples:
        >>> import jax.numpy as jnp
        >>> import astrodynx as adx
        >>> t = 0.0
        >>> x = jnp.array([1.0, -1.0, 1.0, 0.0, 0.0, 0.0])
        >>> args = {"mu": 1.0, "J4": 1e-6, "R_eq": 1.0}
        >>> expected = jnp.array([-5.345836e-08, 5.345836e-08, -1.781946e-08])
        >>> actual = adx.gravity.j4_acc(t, x, args)
        >>> jnp.allclose(expected, actual)
        Array(True, dtype=bool)
    """
    mu = args["mu"]
    J4 = args["J4"]
    R_eq = args["R_eq"]
    r = jnp.linalg.vector_norm(x[:3])
    zsq_over_rsq = (x[2] / r) ** 2
    factor = 1.875 * mu * J4 * R_eq**4 / r**7
    ax = factor * x[0] * (1 - 14 * zsq_over_rsq + 21 * zsq_over_rsq**2)
    ay = factor * x[1] * (1 - 14 * zsq_over_rsq + 21 * zsq_over_rsq**2)
    az = factor * x[2] * (5 - 70 * zsq_over_rsq / 3 + 21 * zsq_over_rsq**2)
    return jnp.stack([ax, ay, az])
