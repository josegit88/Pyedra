#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the
#   Pyedra Project (https://github.com/milicolazo/Pyedra/).
# Copyright (c) 2020, Milagros Colazo
# License: MIT
#   Full Text: https://github.com/milicolazo/Pyedra/blob/master/LICENSE

# ============================================================================
# DOCS
# ============================================================================

"""Implementation of phase function for asteroids."""

# =============================================================================
# IMPORTS
# =============================================================================

import attr

import matplotlib.pyplot as plt

import numpy as np

import pandas as pd

import scipy
import scipy.interpolate
import scipy.optimize as optimization

from . import core, datasets

# ============================================================================
# CLASSES
# ============================================================================


@attr.s(frozen=True)
class HG1G2Plot(core.BasePlot):
    """Plots for HG1G2 fit."""

    def curvefit(self, df, ax=None, **kwargs):
        """Plot the phase function using the HG1G2 model.

        Parameters
        ----------
        df : ``pandas.DataFrame``
            The dataframe must contain 3 columns as indicated here:
            id (mpc number of the asteroid), alpha (phase angle) and
            v (reduced magnitude in Johnson's V filter).

        ax : ``matplotlib.pyplot.Axis``, (optional)
            Matplotlib axis

        **kwargs :
            Extra variables are not used


        Return
        ------
        ``matplotlib.pyplot.Axis`` :
            The axis where the method draws.

        """
        penttila2016 = datasets.load_penttila2016()

        alphap = penttila2016["alpha"].to_numpy()
        phi1 = penttila2016["phi1"].to_numpy()
        phi2 = penttila2016["phi2"].to_numpy()
        phi3 = penttila2016["phi3"].to_numpy()

        y_interp1 = scipy.interpolate.interp1d(alphap, phi1)
        y_interp2 = scipy.interpolate.interp1d(alphap, phi2)
        y_interp3 = scipy.interpolate.interp1d(alphap, phi3)

        if ax is None:
            ax = plt.gca()

        ax.invert_yaxis()
        ax.set_title("Phase curves")
        ax.set_xlabel("Phase angle")
        ax.set_ylabel("V")

        for idx, m_row in self.model_df.iterrows():
            data = df[df["id"] == m_row.id]

            def fit_y(d, e, f):
                y = d - 2.5 * np.log10(e * fi1 + f * fi2 + (1 - e - f) * fi3)
                return y

            fi1 = np.array([])
            fi2 = np.array([])
            fi3 = np.array([])

            for alpha_b in data.alpha:

                p1 = y_interp1(alpha_b)
                fi1 = np.append(fi1, p1)

                p2 = y_interp2(alpha_b)
                fi2 = np.append(fi2, p2)

                p3 = y_interp3(alpha_b)
                fi3 = np.append(fi3, p3)

            v_fit = fit_y(m_row.H12, m_row.G1, m_row.G2)
            ax.plot(data.alpha, v_fit, "--", label=f"Fit {int(m_row.id)}")
            ax.plot(
                data.alpha,
                data.v,
                marker="o",
                linestyle="None",
                label=f"Data {int(m_row.id)}",
            )

        ax.legend(bbox_to_anchor=(1.05, 1))
        return ax


# ============================================================================
# FUNCTIONS
# ============================================================================


def _HG1G2_model(X, a, b, c):
    x, y, z = X
    return a * x + b * y + c * z


def HG1G2_fit(df):
    """Fit (H-G1-G2) system to data from table.

    HG1G2_fit calculates the H,G1 and G2 parameters of the phase
    function following the procedure described in [5]_ .

    Parameters
    ----------
    df: ``pandas.DataFrame``
        The dataframe must contain 3 columns as indicated here:
        id (mpc number of the asteroid), alpha (phase angle) and
        v (reduced magnitude in Johnson's V filter).

    Returns
    -------
    model_df: ``pandas.DataFrame``
        The output dataframe contains eight columns: id (mpc number of
        the asteroid), H (absolute magnitude returned by the fit),
        H error (fit H parameter error), G1 (G1 parameter returned by
        the fit), G1 error (fit G1 parameter error), G2 (G2 parameter
        returned bythe fit), G2 error (fit G2 parameter error), and R
        (fit determination coefficient).

    References
    ----------
    .. [5] Muinonen K., Belskaya I. N., Cellino A., Delbò M.,
       Levasseur-Regourd A.-C.,Penttilä A., Tedesco E. F., 2010,
       Icarus, 209, 542.
    """
    lt = core.obs_counter(df, 3)
    if len(lt):
        lt_str = " - ".join(str(idx) for idx in lt)
        raise ValueError(
            f"Some asteroids has less than 3 observations: {lt_str}"
        )

    noob = df.drop_duplicates(subset="id", keep="first", inplace=False)
    size = len(noob)
    id_column = np.empty(size, dtype=int)
    H_1_2_column = np.empty(size)
    error_H_1_2_column = np.empty(size)
    G_1_column = np.empty(size)
    error_G_1_column = np.empty(size)
    G_2_column = np.empty(size)
    error_G_2_column = np.empty(size)
    R_column = np.empty(size)

    penttila2016 = datasets.load_penttila2016()

    alpha = penttila2016["alpha"].to_numpy()
    phi1 = penttila2016["phi1"].to_numpy()
    phi2 = penttila2016["phi2"].to_numpy()
    phi3 = penttila2016["phi3"].to_numpy()

    y_interp1 = scipy.interpolate.interp1d(alpha, phi1)
    y_interp2 = scipy.interpolate.interp1d(alpha, phi2)
    y_interp3 = scipy.interpolate.interp1d(alpha, phi3)

    for idx, id in enumerate(noob.id):

        data = df[df["id"] == id]

        fi1 = np.array([])
        fi2 = np.array([])
        fi3 = np.array([])

        for alpha_b in data.alpha:

            p1 = y_interp1(alpha_b)
            fi1 = np.append(fi1, p1)

            p2 = y_interp2(alpha_b)
            fi2 = np.append(fi2, p2)

            p3 = y_interp3(alpha_b)
            fi3 = np.append(fi3, p3)

        v = data["v"].to_numpy()
        v_fit = 10 ** (-0.4 * v)

        op, cov = optimization.curve_fit(_HG1G2_model, (fi1, fi2, fi3), v_fit)

        a, b, c = op
        error_a, error_b, error_c = np.sqrt(np.diag(cov))

        H_1_2 = -2.5 * np.log10(a + b + c)
        error_H_1_2 = (
            1.0857362
            * np.sqrt(error_a ** 2 + error_b ** 2 + error_c ** 2)
            / (a + b + c)
        )
        G_1 = a / (a + b + c)
        error_G_1 = np.sqrt(
            ((b + c) * error_a) ** 2 + (a * error_b) ** 2 + (a * error_c) ** 2
        ) / ((a + b + c) ** 2)
        G_2 = b / (a + b + c)
        error_G_2 = np.sqrt(
            (b * error_a) ** 2 + ((a + c) * error_b) ** 2 + (b * error_c) ** 2
        ) / ((a + b + c) ** 2)

        residuals = v_fit - _HG1G2_model((fi1, fi2, fi3), *op)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((v_fit - np.mean(v_fit)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        id_column[idx] = id
        H_1_2_column[idx] = H_1_2
        error_H_1_2_column[idx] = error_H_1_2
        G_1_column[idx] = G_1
        error_G_1_column[idx] = error_G_1
        G_2_column[idx] = G_2
        error_G_2_column[idx] = error_G_2
        R_column[idx] = r_squared

    model_df = pd.DataFrame(
        {
            "id": id_column,
            "H12": H_1_2_column,
            "error_H12": error_H_1_2_column,
            "G1": G_1_column,
            "error_G1": error_G_1_column,
            "G2": G_2_column,
            "error_G2": error_G_2_column,
            "R": R_column,
        }
    )

    plotter = HG1G2Plot(model_df=model_df)

    pentilla_cache = {
        "alpha": penttila2016["alpha"].to_numpy(),
        "phi1": penttila2016["phi1"].to_numpy(),
        "phi2": penttila2016["phi2"].to_numpy(),
        "phi3": penttila2016["phi3"].to_numpy(),
        "y_interp1": scipy.interpolate.interp1d(alpha, phi1),
        "y_interp2": scipy.interpolate.interp1d(alpha, phi2),
        "y_interp3": scipy.interpolate.interp1d(alpha, phi3),
    }
    metadata = {"pentilla2016": core.MetaData(pentilla_cache)}

    return core.PyedraFitDataFrame(
        model_df=model_df, metadata=metadata, plot=plotter
    )