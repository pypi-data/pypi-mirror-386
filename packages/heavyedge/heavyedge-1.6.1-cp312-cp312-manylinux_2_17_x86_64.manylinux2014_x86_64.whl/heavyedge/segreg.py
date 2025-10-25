"""
Segmented regression
--------------------

Broken line regression with two segments.

.. deprecated:: 1.5
   This module will be removed in HeavyEdge 2.0,
   as it is no longer required by public API.
"""

import warnings

import numpy as np

__all__ = [
    "segreg",
    "predict",
]


def _deprecated(version, replace):
    removed_version = str(int(version.split(".")[0]) + 1) + ".0"

    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__}() is deprecated since HeavyEdge {version} "
                f"and will be removed in {removed_version}. "
                f"Use {replace} instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _ols(Xi, Y):
    XT_X_inv = np.linalg.inv(Xi.T @ Xi)
    params = XT_X_inv @ (Xi.T @ Y)
    return params


@_deprecated("1.5", "HeavyEdge-Landmarks package")
def segreg(x, Y, psi0, tol=1e-5, maxiter=30):
    r"""Segmented regression with one breakpoint.

    .. deprecated:: 1.5
        This module will be removed in HeavyEdge 2.0,
        as it is no longer required by public API.

    Parameters
    ----------
    x, Y : (M,) ndarray
        Data points.
    psi0 : scalar
        Initial guess for breakpoint coordinate.
    tol : float, default=1e-5
        Convergence tolerance.
    maxiter : int, default=30
        Force break after this iterations.

    Returns
    -------
    params : (4,) ndarray
        Estimated parameters: b0, b1, b2, psi.
    reached_max : bool
        Iteration is finished not by convergence but by reaching maximum iteration.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.segreg import segreg, predict
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     Y = next(data.profiles())
    ...     X = data.x()[:len(Y)]
    >>> x = X[X < 10]
    >>> (b0, b1, b2, psi1), _ = segreg(x, Y[:len(x)], 7)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(X, Y.T, color="gray")
    ... plt.plot(x, predict(x, b0, b1, b2, psi1))

    """
    Xi = np.array(
        [
            np.ones_like(x),
            x,
            (x - psi0) * np.heaviside(x - psi0, 0),
            -np.heaviside(x - psi0, 0),
        ]
    ).T

    b0, b1, b2, gamma = _ols(Xi, Y)
    RSS = np.sum((Y - predict(x, b0, b1, b2, psi0)) ** 2)

    psi_converged = False
    for _ in range(maxiter):
        RSS_new = RSS
        lamda = 1
        while True:
            psi0_new = psi0 + lamda * gamma / b2
            RSS_new = np.sum((Y - predict(x, b0, b1, b2, psi0_new)) ** 2)
            lamda /= 2

            if (psi0_new <= x[0]) or (psi0_new >= x[-1]):
                # exceeded domain; make step size smaller
                continue
            if RSS_new >= RSS:
                # RSS not decreased; make step size smaller
                continue
            psi_converged = np.abs(psi0 - psi0_new) <= tol
            if psi_converged:
                break

        if not psi_converged:
            psi_converged = np.abs(psi0 - psi0_new) <= tol
        if psi_converged:
            psi0 = psi0_new
            reached_max = False
            break

        psi0 = psi0_new
        RSS = RSS_new
        Xi[:, 2] = (x - psi0) * np.heaviside(x - psi0, 0)
        Xi[:, 3] = -np.heaviside(x - psi0, 0)
        b0, b1, b2, gamma = _ols(Xi, Y)
    else:
        reached_max = True

    params = np.array([b0, b1, b2, psi0_new])
    return params, reached_max


@_deprecated("1.5", "HeavyEdge-Landmarks package")
def predict(x, b0, b1, b2, psi):
    r"""Predict y values from x coordinates by segmented regression model.

    The model is

    .. math::

        \beta_0 + \beta_1 + \beta_2 (\xi - \psi)_+.

    .. deprecated:: 1.5
        This module will be removed in HeavyEdge 2.0,
        as it is no longer required by public API.

    Parameters
    ----------
    x : (M,) ndarray
        X coordinates.
    b0, b1, b2, psi : scalar
        Model parameters.

    Returns
    -------
    (M,) ndarray
        Predicted y coordinates.
    """
    x = np.asarray(x)
    return b0 + b1 * x + b2 * (x - psi) * np.heaviside(x - psi, 0)
