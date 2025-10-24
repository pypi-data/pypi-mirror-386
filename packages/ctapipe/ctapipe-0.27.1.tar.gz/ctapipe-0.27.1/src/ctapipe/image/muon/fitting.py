import astropy.units as u
import numpy as np
from astropy.units import Quantity

from ...exceptions import OptionalDependencyMissing
from ...utils.quantities import all_to_value

__all__ = ["kundu_chaudhuri_circle_fit", "taubin_circle_fit"]

try:
    from iminuit import Minuit
except ModuleNotFoundError:
    Minuit = None


def kundu_chaudhuri_circle_fit(x, y, weights, nan_errors_flag=False):
    """
    Fast and reliable analytical circle fitting method.

    Previously used in the H.E.S.S. experiment for muon identification.
    Implementation based on :cite:p:`chaudhuri93`

    Parameters
    ----------
    x: array-like or astropy quantity
        x coordinates of the points
    y: array-like or astropy quantity
        y coordinates of the points
    weights: array-like
        weights of the points
    nan_errors_flag: bool
        The flag defines whether errors are set to NaN.

    Returns
    -------
    radius : astropy.units.Quantity
        Fitted radius of the circle.
    center_x : astropy.units.Quantity
        Fitted x-coordinate of the circle center.
    center_y : astropy.units.Quantity
        Fitted y-coordinate of the circle center.
    radius_err : astropy.units.Quantity
        Fitted radius of the circle error.
    center_x_err : astropy.units.Quantity
        Fitted x-coordinate of the circle center error.
    center_y_err : astropy.units.Quantity
        Fitted y-coordinate of the circle center error.
    """

    weights_sum = np.sum(weights)
    mean_x = np.sum(x * weights) / weights_sum
    mean_y = np.sum(y * weights) / weights_sum

    a1 = np.sum(weights * (x - mean_x) * x)
    a2 = np.sum(weights * (y - mean_y) * x)

    b1 = np.sum(weights * (x - mean_x) * y)
    b2 = np.sum(weights * (y - mean_y) * y)

    c1 = 0.5 * np.sum(weights * (x - mean_x) * (x**2 + y**2))
    c2 = 0.5 * np.sum(weights * (y - mean_y) * (x**2 + y**2))

    center_x = (b2 * c1 - b1 * c2) / (a1 * b2 - a2 * b1)
    center_y = (a2 * c1 - a1 * c2) / (a2 * b1 - a1 * b2)

    radius = np.sqrt(
        np.sum(weights * ((center_x - x) ** 2 + (center_y - y) ** 2)) / weights_sum
    )

    if nan_errors_flag:
        radius_err = np.nan
        center_x_err = np.nan
        center_y_err = np.nan
    else:
        radius_err, center_x_err, center_y_err = naive_circle_fit_error_calculator(
            x, y, weights, radius, center_x, center_y
        )

    return radius, center_x, center_y, radius_err, center_x_err, center_y_err


def taubin_circle_fit(
    x, y, mask, weights=None, r_initial=None, xc_initial=None, yc_initial=None
):
    """
    Perform a Taubin circle fit with weights (optional).

    The minimized loss function in this method tends to
    maximize the radius of the ring, whereas using a simple
    ring equation systematically results in a smaller radius.
    Adding weights mitigates both effects and yields a more accurate fit.

    Parameters
    ----------
    x : array-like or astropy.units.Quantity
        x-coordinates of the points.
    y : array-like or astropy.units.Quantity
        y-coordinates of the points.
    mask : array-like of bool
        Boolean mask indicating which pixels survive the cleaning process.
    weights : array-like of float, optional
        Weights for the points. If not provided, all points are assigned equal weights (1).
    r_initial : astropy.units.Quantity, optional
        Initial guess for the radius of the circle. If not provided, it defaults to 1.1 deg.
        1.1 deg. is the approximate Cherenkov photon angle produced by muons in the atmosphere
        at La Palma altitude (2426 m a.s.l.), with momentum greater than 15 GeV.
    xc_initial : astropy.units.Quantity, optional
        Initial guess for the x-coordinate of the circle center. Defaults to 0.
    yc_initial : astropy.units.Quantity, optional
        Initial guess for the y-coordinate of the circle center. Defaults to 0.

    Returns
    -------
    radius : astropy.units.Quantity
        Fitted radius of the circle.
    center_x : astropy.units.Quantity
        Fitted x-coordinate of the circle center.
    center_y : astropy.units.Quantity
        Fitted y-coordinate of the circle center.
    radius_err : astropy.units.Quantity
        Fitted radius of the circle error.
    center_x_err : astropy.units.Quantity
        Fitted x-coordinate of the circle center error.
    center_y_err : astropy.units.Quantity
        Fitted y-coordinate of the circle center error.

    Raises
    ------
    OptionalDependencyMissing
        If the iminuit package is not installed.

    Notes
    -----
    The Taubin circle fit minimizes a specific loss function that balances the
    squared residuals of the points from the circle with the weights. This method
    is particularly useful for fitting circles to noisy data.

    References
    ----------
    - Barcelona_Muons_TPA_final.pdf (slide 6)
    """

    if Minuit is None:
        raise OptionalDependencyMissing("iminuit")

    original_unit = x.unit
    x, y = all_to_value(x, y, unit=original_unit)

    x_masked = x[mask]
    y_masked = y[mask]

    max_fov = 2 * x.max()

    if weights is None:
        weights_masked = np.ones(len(x_masked))
    else:
        weights_masked = weights[mask]

    if original_unit.is_equivalent(u.deg):
        r_initial = (1.1 * u.deg).to(original_unit) if r_initial is None else r_initial
    else:
        r_initial = max_fov / 4.0 * original_unit if r_initial is None else r_initial

    xc_initial = 0 * original_unit if xc_initial is None else xc_initial
    yc_initial = 0 * original_unit if yc_initial is None else yc_initial

    # minimization method
    fit = Minuit(
        make_loss_function(x_masked, y_masked, weights_masked),
        xc=xc_initial.to_value(original_unit),
        yc=yc_initial.to_value(original_unit),
        r=r_initial.to_value(original_unit),
    )
    fit.errordef = Minuit.LEAST_SQUARES

    # set initial parameters uncertainty to a big value
    taubin_error = max_fov * 0.1
    fit.errors["xc"] = taubin_error
    fit.errors["yc"] = taubin_error
    fit.errors["r"] = taubin_error

    # set wide rage for the minimisation
    fit.limits["xc"] = (-max_fov, max_fov)
    fit.limits["yc"] = (-max_fov, max_fov)
    fit.limits["r"] = (0, max_fov)

    fit.migrad()

    radius = Quantity(fit.values["r"], original_unit)
    center_x = Quantity(fit.values["xc"], original_unit)
    center_y = Quantity(fit.values["yc"], original_unit)
    radius_err = Quantity(fit.errors["r"], original_unit)
    center_x_err = Quantity(fit.errors["xc"], original_unit)
    center_y_err = Quantity(fit.errors["yc"], original_unit)

    return radius, center_x, center_y, radius_err, center_x_err, center_y_err


def make_loss_function(x, y, w):
    """closure around taubin_loss_function to make
    surviving pixel positions availaboe inside.

    x, y: positions of pixels surviving the cleaning
        should not be quantities
    w : array-like of float, weights for the points
    """

    def taubin_loss_function(xc, yc, r):
        """taubin fit formula
        reference : Barcelona_Muons_TPA_final.pdf (slide 6)
        """

        distance_squared = (x - xc) ** 2 + (y - yc) ** 2
        upper_term = ((w * (distance_squared - r**2)) ** 2).sum()
        lower_term = (w * distance_squared).sum()

        return np.abs(upper_term) / np.abs(lower_term)

    return taubin_loss_function


def naive_circle_fit_error_calculator(x, y, weights, radius, center_x, center_y):
    """
    Naive (simplified) error calculator for circular data with weights.

    In this naive approach, we assume zero correlation between the radius,
    center_x, and center_y. However, the error in the radius is twice as
    small as that of center_x and center_y, which are assumed to have equal errors.

    Parameters
    ----------
    x: array-like or astropy quantity
        x coordinates of the points
    y: array-like or astropy quantity
        y coordinates of the points
    weights: array-like
        weights of the points
    radius : astropy.units.Quantity
        Fitted radius of the circle.
    center_x : astropy.units.Quantity
        Fitted x-coordinate of the circle center.
    center_y : astropy.units.Quantity
        Fitted y-coordinate of the circle center.

    Returns
    -------
    radius_err : astropy.units.Quantity
        Fitted radius of the circle error.
    center_x_err : astropy.units.Quantity
        Fitted x-coordinate of the circle center error.
    center_y_err : astropy.units.Quantity
        Fitted y-coordinate of the circle center error.
    """

    weights_sum = np.sum(weights)
    radius_squared = (x - center_x) ** 2 + (y - center_y) ** 2
    delta = radius_squared - radius**2
    partial_derivative = np.sqrt(radius_squared + radius**2 / 4)

    delta_weighted_mean = np.average(delta, weights=weights)
    partial_derivative_weighted_mean = np.average(partial_derivative, weights=weights)

    delta_weighted_variance = np.average(
        (delta - delta_weighted_mean) ** 2,
        weights=weights,
    )
    partial_derivative_weighted_variance = np.average(
        (partial_derivative - partial_derivative_weighted_mean) ** 2,
        weights=weights,
    )

    parameter_err = (
        np.sqrt(delta_weighted_variance)
        / np.sqrt(partial_derivative_weighted_variance)
        / weights_sum
        / 2
        / np.sqrt(2)
    )

    radius_err = parameter_err / 2
    center_x_err = parameter_err
    center_y_err = parameter_err

    return radius_err, center_x_err, center_y_err
