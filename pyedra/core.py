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

from collections.abc import Mapping

import attr

# ============================================================================
# CLASSES
# ============================================================================


@attr.s(frozen=True, repr=False)
class MetaData(Mapping):
    """Implements an inmutable dict-like to store the metadata.

    Also provides attribute like access to the keys.

    Example
    -------
    >>> metadata = MetaData({"a": 1, "b": 2})
    >>> metadata.a
    1

    >>> metadata["a"]
    1
    """

    _data = attr.ib(converter=dict, factory=dict)

    def __repr__(self):
        """repr(x) <=> x.__repr__()."""
        return f"Metadata({repr(self._data)})"

    def __getitem__(self, k):
        """x[k] <=> x.__getitem__(k)."""
        return self._data[k]

    def __iter__(self):
        """iter(x) <=> x.__iter__()."""
        return iter(self._data)

    def __len__(self):
        """len(x) <=> x.__len__()."""
        return len(self._data)

    def __getattr__(self, a):
        """getattr(x, y) <==> x.__getattr__(y) <==> getattr(x, y)."""
        return self[a]


@attr.s(frozen=True)
class PyedraFitDataFrame:
    """Initialize a dataframe model_df to which we can apply function a."""

    model_df = attr.ib()
    plot = attr.ib()
    metadata = attr.ib(factory=MetaData, converter=MetaData)

    def __getattr__(self, a):
        """getattr(x, y) <==> x.__getattr__(y) <==> getattr(x, y)."""
        return getattr(self.model_df, a)


@attr.s(frozen=True)
class BasePlot:
    """Plots for HG fit."""

    model_df = attr.ib()

    default_plot_kind = "curvefit"

    def __call__(self, kind=None, **kwargs):
        """``plot() <==> plot.__call__()``."""
        kind = self.default_plot_kind if kind is None else kind

        if kind.startswith("_"):
            raise AttributeError(f"Ivalid plot method '{kind}'")

        method = getattr(self, kind)

        if not callable(method):
            raise AttributeError(f"Ivalid plot method '{kind}'")

        return method(**kwargs)

    def __getattr__(self, kind):
        """getattr(x, y) <==> x.__getattr__(y) <==> getattr(x, y)."""
        return getattr(self.model_df.plot, kind)


# ============================================================================
# FUNCTIONS
# ============================================================================


def obs_counter(df, obs):
    """Count the observations. A minimum is needed to the fits.

    Parameters
    ----------
    df: ``pandas.DataFrame``
        The dataframe must contain 3 columns as indicated here:
        id (mpc number of the asteroid), alpha (phase angle) and
        v (reduced magnitude in Johnson's V filter).

    obs: int
        Minimum number of observations needed to perform the fit.

    Return
    ------
    out: ndarray
        Numpy array containing the asteroids whose number of
        observations is less than obs.
    """
    df_cnt = df.groupby("id").count()
    lt_idx = df_cnt[df_cnt.alpha < obs].index
    return lt_idx.to_numpy()
