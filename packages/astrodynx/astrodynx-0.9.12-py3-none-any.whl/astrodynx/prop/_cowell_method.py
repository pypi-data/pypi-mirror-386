from astrodynx import diffeq
from jaxtyping import ArrayLike, DTypeLike, PyTree
from typing import Any, NamedTuple

"""General implementations of Cowell's method for propagating orbits under perturbing forces."""


class OrbDynx(NamedTuple):
    """Orbital dynamics configuration for Cowell's method propagation.

    This NamedTuple encapsulates the essential components needed for orbital
    propagation using Cowell's method, including the differential equation terms,
    static arguments, and optional event detection.

    Attributes:
        terms: The differential equation terms defining the
            orbital dynamics. Typically an ODETerm containing the vector field
            function that computes accelerations from gravitational and
            perturbation forces.
        args: Static arguments passed to the differential equation.
            Common arguments include gravitational parameter (mu), perturbation
            parameters (J2, R_eq), and event thresholds (rmin).
            Defaults to {"mu": 1.0}.
        event: Event detection configuration for terminating propagation early when specific conditions are met (e.g., ground impact, apogee passage).

    Notes:
        This class is designed to work with the ODE solver. The terms should define the complete
        orbital dynamics including all relevant forces and perturbations.

        The args parameter uses JAX's PyTree structure, allowing for efficient
        compilation and automatic differentiation of the propagation process.

    Examples:
        Basic two-body orbital dynamics:

        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )

        With J2 perturbations and event detection:

        >>> def perturbed_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     acc += adx.gravity.j2_acc(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(perturbed_field),
        ...     args={"mu": 1.0, "J2": 1e-3, "R_eq": 1.0, "rmin": 0.1},
        ...     event=diffeq.Event(adx.events.radius_islow)
        ... )
    """

    terms: diffeq.ODETerm
    args: PyTree[Any] = {"mu": 1.0}
    event: diffeq.Event = None


def cowell_method(
    orbdyn: OrbDynx,
    x0: ArrayLike,
    t1: DTypeLike,
    saveat: diffeq.SaveAt,
    dt0: DTypeLike = None,
    max_steps: int = 4096,
    solver: diffeq.AbstractSolver = diffeq.Tsit5(),
    stepsize_controller: diffeq.AbstractStepSizeController = diffeq.PIDController(
        rtol=1e-8, atol=1e-8
    ),
) -> diffeq.Solution:
    """General Cowell's method orbital propagation function.

    This function provides a flexible interface for propagating orbital states
    using Cowell's method with customizable step size control and output times.

    Args:
        orbdyn: Orbital dynamics configuration containing the differential equation terms, static arguments, and optional events.
        x0: (6,)Initial state vector [x, y, z, vx, vy, vz] in
            canonical units. Position components are in distance units,
            velocity components are in distance/time units.
        t1: Final integration time in canonical time units.
            Must be positive for forward propagation.
        saveat: Configuration specifying when to save the solution during integration.
        dt0: Initial time step size for integration in canonical time units.
            If None, the solver will choose an appropriate initial step size.
        max_steps: Maximum number of integration steps before
            terminating unconditionally. Prevents infinite loops in case of
            integration issues. Defaults to 4096.
        solver: Numerical integration method. Defaults to diffeq.Tsit5() (5th-order Runge-Kutta method).
        stepsize_controller: Step size controller for adaptive or fixed stepping.
    Returns:
        Integration solution containing
            - ts: Array of time points where solution was saved
            - ys: Array of state vectors at each time point
            - stats: Integration statistics and diagnostics
            - result: Integration termination status
    Notes:
        This function serves as a general interface for Cowell's method orbital
        propagation. Users can specify custom step size controllers and output
        times to suit their specific needs. It is recommended to use the
        specialized functions (:meth:`fixed_steps`, :meth:`adaptive_steps`, :meth:`custom_steps`, :meth:`to_final`)
        for common use cases for better clarity and ease of use.
    Examples:
        Basic orbital propagation with dense output:
        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        >>> t1 = jnp.pi*2  # One orbital period
        >>> saveat=diffeq.SaveAt(dense=True,subs=diffeq.SubSaveAt(t1=True))
        >>> sol = adx.prop.cowell_method(
        ...     orbdyn, x0, t1,
        ...     saveat=saveat
        ... )
        >>> tf = sol.ts[-1]
        >>> yf = sol.ys[-1]
        >>> yf_dense = sol.evaluate(tf)
        >>> assert jnp.allclose(yf, yf_dense, atol=1e-7)
    """
    return diffeq.diffeqsolve(
        terms=orbdyn.terms,
        solver=solver,
        t0=0,
        t1=t1,
        dt0=dt0,
        y0=x0,
        args=orbdyn.args,
        max_steps=max_steps,
        stepsize_controller=stepsize_controller,
        saveat=saveat,
        event=orbdyn.event,
    )


def fixed_steps(
    orbdyn: OrbDynx,
    x0: ArrayLike,
    t1: DTypeLike,
    dt: DTypeLike,
    max_steps: int = 4096,
    solver: diffeq.AbstractSolver = diffeq.Tsit5(),
) -> diffeq.Solution:
    """Propagate orbital state using Cowell's method with fixed step sizes.

    This function solves the orbital dynamics differential equation using a
    constant step size integrator. It's suitable for scenarios where uniform
    time sampling is required or when computational efficiency is prioritized
    over adaptive error control.

    Args:
        orbdyn: Orbital dynamics configuration containing the differential equation terms, static arguments, and optional events.
        x0: (6,)Initial state vector [x, y, z, vx, vy, vz] in
            canonical units. Position components are in distance units,
            velocity components are in distance/time units.
        t1: Final integration time in canonical time units.
            Must be positive for forward propagation.
        dt: Fixed time step size for integration in canonical time units. Smaller values increase accuracy but require more computational time.
        max_steps: Maximum number of integration steps before
            terminating unconditionally. Prevents infinite loops in case of
            integration issues. Defaults to 4096.
        solver: Numerical integration method. Defaults to diffeq.Tsit5() (5th-order Runge-Kutta method).

    Returns:
        Integration solution containing
            - ts: Array of time points where solution was saved
            - ys: Array of state vectors at each time point
            - stats: Integration statistics and diagnostics
            - result: Integration termination status


    Notes:
        This function uses a constant step size controller, which means the
        integrator will take exactly dt-sized steps regardless of local error.
        This can be more efficient than adaptive methods but may sacrifice
        accuracy in regions where the dynamics change rapidly.

        The solution is saved at the initial time (t0=True) and at every
        integration step (steps=True), providing a complete trajectory.

    Examples:
        Basic orbital propagation with fixed steps:

        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        >>> t1 = jnp.pi*2  # One orbital period
        >>> dt = 0.01  # Fixed step size
        >>> sol = adx.prop.fixed_steps(orbdyn, x0, t1, dt)
    """
    return diffeq.diffeqsolve(
        terms=orbdyn.terms,
        solver=solver,
        t0=0,
        t1=t1,
        dt0=dt,
        y0=x0,
        args=orbdyn.args,
        max_steps=max_steps,
        stepsize_controller=diffeq.ConstantStepSize(),
        saveat=diffeq.SaveAt(t0=True, steps=True),
        event=orbdyn.event,
    )


def adaptive_steps(
    orbdyn: OrbDynx,
    x0: ArrayLike,
    t1: DTypeLike,
    max_steps: int = 4096,
    solver: diffeq.AbstractSolver = diffeq.Tsit5(),
    stepsize_controller: diffeq.AbstractStepSizeController = diffeq.PIDController(
        rtol=1e-8, atol=1e-8
    ),
) -> diffeq.Solution:
    """Propagate orbital state using Cowell's method with adaptive step sizes.

    This function solves the orbital dynamics differential equation using an
    adaptive step size integrator that automatically adjusts the time step
    based on local error estimates. This provides optimal balance between
    accuracy and computational efficiency.

    Args:
        orbdyn: Orbital dynamics configuration containing the differential equation terms, static arguments, and optional events.
        x0: (6,)Initial state vector [x, y, z, vx, vy, vz] in
            canonical units. Position components are in distance units,
            velocity components are in distance/time units.
        t1: Final integration time in canonical time units.
            Must be positive for forward propagation.
        max_steps: Maximum number of integration steps before
            terminating unconditionally. Prevents infinite loops and controls
            computational cost. Defaults to 4096.
        solver: Numerical integration method.
            Defaults to diffeq.Tsit5() (5th-order Runge-Kutta method with
            embedded error estimation).
        stepsize_controller: Adaptive step size controller.

    Returns:
        Integration solution containing
            - ts: Array of time points where solution was saved (variable spacing)
            - ys: Array of state vectors at each time point
            - stats: Integration statistics including step counts and rejections
            - result: Integration termination status


    Notes:
        The adaptive step size controller automatically adjusts the time step
        to maintain the specified error tolerances. This results in smaller
        steps during periods of rapid change (e.g., near periapsis) and larger
        steps during smoother motion (e.g., near apoapsis).

        The initial step size is set to 1% of the total integration time (t1 * 0.01),
        which provides a reasonable starting point for most orbital scenarios.

        The solution is saved at the initial time and at every accepted step,
        providing a complete trajectory with optimal time resolution.

    Examples:
        Orbital propagation with adaptive steps:

        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        >>> t1 = jnp.pi*2  # One orbital period
        >>> sol = adx.prop.adaptive_steps(orbdyn, x0, t1)
        >>> xf = sol.ys[jnp.isfinite(sol.ts)][-1]

        Eccentric orbit with J2 perturbations and event detection:

        >>> def perturbed_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     acc += adx.gravity.j2_acc(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(perturbed_field),
        ...     args = {"mu": 1.0, "rmin": 0.7, "J2": 1e-6, "R_eq": 1.0},
        ...     event = diffeq.Event(adx.events.radius_islow)
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 0.9, 0.0])
        >>> sol = adx.prop.adaptive_steps(orbdyn, x0, t1)
        >>> xf = sol.ys[jnp.isfinite(sol.ts)][-1]
        >>> expected = jnp.array([-0.59,0.36, 0.,-0.58,-1.16, 0.])
    """
    return diffeq.diffeqsolve(
        terms=orbdyn.terms,
        solver=solver,
        t0=0,
        t1=t1,
        dt0=None,
        y0=x0,
        args=orbdyn.args,
        max_steps=max_steps,
        stepsize_controller=stepsize_controller,
        saveat=diffeq.SaveAt(t0=True, steps=True),
        event=orbdyn.event,
    )


def custom_steps(
    orbdyn: OrbDynx,
    x0: ArrayLike,
    t1: DTypeLike,
    ts: ArrayLike,
    solver: diffeq.AbstractSolver = diffeq.Tsit5(),
    stepsize_controller: diffeq.AbstractStepSizeController = diffeq.PIDController(
        rtol=1e-8, atol=1e-8
    ),
) -> diffeq.Solution:
    """Propagate orbital state using Cowell's method with custom output times.

    This function solves the orbital dynamics differential equation and saves
    the solution at user-specified time points. It uses adaptive step size
    control for accuracy while providing output at exactly the requested times
    through interpolation.

    Args:
        orbdyn: Orbital dynamics configuration containing the differential equation terms, static arguments, and optional events.
        x0: (6,)Initial state vector [x, y, z, vx, vy, vz] in
            canonical units. Position components are in distance units,
            velocity components are in distance/time units.
        t1: Final integration time in canonical time units.
            Must be positive and should be >= max(ts) for complete coverage.
        ts: Array of time points where the solution should be
            saved, in canonical time units. Can be irregularly spaced and
            does not need to include t=0 or t=t1.
        solver: Numerical integration method.
            Defaults to diffeq.Tsit5() (5th-order Runge-Kutta method).
        stepsize_controller: Adaptive step size controller.

    Returns:
        Integration solution containing
            - ts: Array of requested time points (same as input ts)
            - ys: Array of interpolated state vectors at requested times
            - stats: Integration statistics from the adaptive stepping
            - result: Integration termination status

    Notes:
        This function is ideal when you need the orbital state at specific
        times (e.g., for comparison with observations, mission planning, or
        analysis at predetermined epochs). The integrator uses adaptive
        stepping internally but interpolates to provide output at exactly
        the requested times.

        The max_steps parameter is set to None, allowing unlimited steps
        to ensure the integration can reach all requested time points.

        If any requested time in ts is beyond t1, those points will not
        be computed. Ensure t1 >= max(ts) for complete coverage.

    Examples:
        Orbital state at specific observation times:

        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        >>> t1 = jnp.pi*2  # One orbital period
        >>> obs_times = jnp.array([0.5, 1.2, 2.8, 4.1, 5.9])
        >>> sol = adx.prop.custom_steps(orbdyn, x0, t1, obs_times)
    """
    return diffeq.diffeqsolve(
        terms=orbdyn.terms,
        solver=solver,
        t0=0,
        t1=t1,
        dt0=None,
        y0=x0,
        args=orbdyn.args,
        max_steps=None,
        stepsize_controller=stepsize_controller,
        saveat=diffeq.SaveAt(ts=ts),
        event=orbdyn.event,
    )


def to_final(
    orbdyn: OrbDynx,
    x0: ArrayLike,
    t1: DTypeLike,
    solver: diffeq.AbstractSolver = diffeq.Tsit5(),
    stepsize_controller: diffeq.AbstractStepSizeController = diffeq.PIDController(
        rtol=1e-8, atol=1e-8
    ),
) -> diffeq.Solution:
    """Propagate orbital state using Cowell's method to final time only.

    This function solves the orbital dynamics differential equation and returns
    only the final state at time t1. It's the most memory-efficient option when
    intermediate trajectory points are not needed, such as for state transition
    matrix calculations or endpoint optimization problems.

    Args:
        orbdyn: Orbital dynamics configuration containing the differential equation terms, static arguments, and optional events.
        x0: (6,)Initial state vector [x, y, z, vx, vy, vz] in
            canonical units. Position components are in distance units,
            velocity components are in distance/time units.
        t1: Final integration time in canonical time units.
            Must be positive for forward propagation.
        solver: Numerical integration method.
            Defaults to diffeq.Tsit5() (5th-order Runge-Kutta method).
        stepsize_controller: Adaptive step size controller.

    Returns:
        Integration solution containing
            - ts: Single-element array containing only t1
            - ys: Single state vector at the final time t1
            - stats: Integration statistics from the adaptive stepping
            - result: Integration termination status



    Notes:
        This function is optimized for memory efficiency by saving only the
        final state. It uses adaptive step size control internally but discards
        all intermediate results, making it ideal for:

        - State transition matrix computations
        - Optimization problems requiring only final states
        - Monte Carlo simulations with many trajectories
        - Sensitivity analysis using automatic differentiation

        The maximum number of steps is limited to 4096 to prevent runaway
        computations while still allowing for complex orbital dynamics.

    Examples:
        Simple state propagation to final time:

        >>> import jax.numpy as jnp
        >>> from astrodynx import diffeq
        >>> import astrodynx as adx
        >>> def vector_field(t, x, args):
        ...     acc = adx.gravity.point_mass_grav(t, x, args)
        ...     return jnp.concatenate([x[3:], acc])
        >>> orbdyn = adx.prop.OrbDynx(
        ...     terms=diffeq.ODETerm(vector_field),
        ...     args={"mu": 1.0}
        ... )
        >>> x0 = jnp.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        >>> t1 = jnp.pi*2  # One orbital period
        >>> sol = adx.prop.to_final(orbdyn, x0, t1)
    """
    return diffeq.diffeqsolve(
        terms=orbdyn.terms,
        solver=solver,
        t0=0,
        t1=t1,
        dt0=None,
        y0=x0,
        args=orbdyn.args,
        max_steps=4096,
        stepsize_controller=stepsize_controller,
        saveat=diffeq.SaveAt(subs=diffeq.SubSaveAt(t1=True)),
        event=orbdyn.event,
    )
