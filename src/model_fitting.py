import numpy as np
from scipy.optimize import curve_fit
from datetime import datetime


def modelPoly1(x, a, b):
    return a + b * x


def modelPoly2(x, a, b, c):
    return modelPoly1(x, a, b) + c * x * x


def modelPoly3(x, a, b, c, d):
    return modelPoly2(x, a, b, c) + d * x * x * x


def modelAnnual(x, a, b):
    return a * np.sin(x * 2 * np.pi / 365.25) + b * np.cos(x * 2 * np.pi / 365.25)


def modelExponential(x, a, b, c):
    x = normalize(x)  # normalize ordinal dates to avoid overflow
    return a + b * np.exp(c * x)


def fitExponential(x, y):
    """Try fitting exponential model, if it fails, fit polynomial model. Return the best fit model."""
    try:
        initial_params = [1, 1, 0.01]
        popt, pcov = curve_fit(modelExponential, x, y, p0=initial_params, maxfev=2000)
        model = modelExponential
    except RuntimeError:
        popt, pcov = curve_fit(modelPoly1, x, y)
        model = modelPoly1
    return popt, pcov, model


def normalize(x):
    return (x - x.min()) / (x.max() - x.min())


def ordinalTodates(ordinals):
    return [datetime.fromordinal(int(x)) for x in ordinals]


class FittingModels:
    def __init__(self, x=None, y=None, model="poly-1"):
        self.x = x
        self.y = y
        self.mask = np.isfinite(np.array(y, dtype=np.float64))

        self.model = model
        self.ordinal_dates = self.datesToOrdinal()

    def datesToOrdinal(self):
        return np.array([x.toordinal() for x in self.x])

    def fit(self, model=None, seasonal=False):
        x = self.ordinal_dates
        y = self.y
        mask = self.mask

        if model is None:
            model = self.model
        fit_models_dict = {"poly-1": modelPoly1, "poly-2": modelPoly2,
                           "poly-3": modelPoly3, "exp": modelExponential}
        fit_model = fit_models_dict[model]
        if fit_model == modelExponential:
            popt, pcov, fit_model = fitExponential(x[mask], y[mask])
        else:
            popt, pcov = curve_fit(fit_model, x[mask], y[mask])

        model_x_linspace = np.linspace(min(x), max(x), 100)
        model_x = ordinalTodates(model_x_linspace)
        model_y = fit_model(model_x_linspace, *popt)
        fit_y = fit_model(x, *popt)

        if seasonal:
            residual = y - fit_y
            popt_seasonal, _ = curve_fit(modelAnnual, x[mask], residual[mask])
            model_y_seasonal = modelAnnual(model_x_linspace, *popt_seasonal)
            fit_y_seasonal = modelAnnual(x, *popt_seasonal)
            model_y += model_y_seasonal
            fit_y += fit_y_seasonal

        return fit_y, model_x, model_y

    def fitVelocity(self):
        x = self.ordinal_dates
        y = self.y
        mask = self.mask
        popt, pcov = curve_fit(modelPoly1, x[mask], y[mask])
        return popt[1] * 365.25
