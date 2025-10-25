from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR


class IRFResult(TypedDict):
    values: np.ndarray  # shape: (horizon+1, n_response, n_impulse)
    stderr: Optional[np.ndarray | Tuple[np.ndarray, np.ndarray]]
    names: List[str]
    model: Any


def compute_irf(
    df: pd.DataFrame,
    lags: int = 2,
    horizon: int = 7,
    *,
    stderr_type: str = "asym",
    signif: float = 0.05,
    repl: int = 1000,
    seed: Optional[int] = 1024,
    orth: bool = False,
    cumulative: bool = True,
) -> IRFResult:
    if stderr_type not in {"asym", "mc"}:
        raise ValueError("stderr_type must be 'asym' or 'mc'")

    var_model = VAR(df)
    var_fit = var_model.fit(lags)
    irf_obj = var_fit.irf(horizon)

    values = irf_obj.cum_effects if cumulative else irf_obj.irfs
    if stderr_type == "asym":
        if cumulative:
            stderr = irf_obj.cum_effect_cov(orth=orth)
        else:
            stderr = irf_obj.orth_irf_cov
    else:
        if cumulative:
            stderr = irf_obj.cum_errband_mc(
                orth=orth, repl=repl, signif=signif, seed=seed
            )
        else:
            stderr = irf_obj.errband_mc(
                orth=orth, repl=repl, signif=signif, seed=seed
            )

    return IRFResult(values=values, stderr=stderr, names=irf_obj.model.names, model=irf_obj)


def plot_irf_from_dataframe(
    df: pd.DataFrame,
    *,
    impulse: str,
    response: str,
    lags: int = 2,
    horizon: int = 7,
    stderr_type: str = "asym",
    signif: float = 0.05,
    repl: int = 1000,
    seed: Optional[int] = 1024,
    orth: bool = False,
    cumulative: bool = True,
    ax: Any | None = None,
    figsize: Tuple[int, int] = (5, 5),
    line_color: str = "black",
    linewidth: Optional[float] = None,
    marker: Any | None = None,
    markersize: Optional[float] = None,
    shade_alpha: Optional[float] = None,
    shade_hatch: Optional[str] = None,
    shade_layer: Optional[int] = None,
):
    from .plot import irf_plot

    result = compute_irf(
        df,
        lags=lags,
        horizon=horizon,
        stderr_type=stderr_type,
        signif=signif,
        repl=repl,
        seed=seed,
        orth=orth,
        cumulative=cumulative,
    )

    ax, y1, y2, y3 = irf_plot(
        result["values"],
        result["stderr"],
        impulse,
        response,
        result["names"],
        stderr_type=stderr_type,
        signif=signif,
        ax=ax,
        figsize=figsize,
        linewidth=linewidth,
        marker=marker,
        markersize=markersize,
        shade_alpha=shade_alpha,
        shade_hatch=shade_hatch,
        shade_layer=shade_layer,
        plot=True,
        line_color=line_color,
    )

    return ax, (y1, y2, y3), result


