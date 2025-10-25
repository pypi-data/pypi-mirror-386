from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from statsmodels.compat.python import lrange


def plot_with_error(
    y: np.ndarray,
    error: Optional[np.ndarray | Tuple[np.ndarray, np.ndarray]],
    *,
    x: Optional[Iterable[int]] = None,
    ax: Any | None = None,
    alpha: float = 0.05,
    linewidth: Optional[float] = None,
    marker: Any | None = None,
    markersize: Optional[float] = None,
    shade_alpha: Optional[float] = None,
    shade_hatch: Optional[str] = None,
    shade_layer: Optional[int] = None,
    plot: bool = True,
    figsize: Tuple[int, int] = (5, 5),
    line_color: str = "black",
):
    x = list(x) if x is not None else lrange(len(y))

    if error is None:
        y1 = np.asarray(y)
        y2 = np.asarray(y)
        y3 = np.asarray(y)
    elif isinstance(error, (tuple, list)) and len(error) == 2:
        y1 = np.asarray(error[0])
        y2 = np.asarray(y)
        y3 = np.asarray(error[1])
    else:
        q = stats.norm.ppf(1 - alpha / 2)
        err = np.asarray(error)
        y = np.asarray(y)
        y1 = y - q * err
        y2 = y
        y3 = y + q * err

    if plot:
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        ax.plot(
            x,
            y2,
            marker=marker,
            color=line_color,
            linewidth=linewidth,
            markersize=markersize,
        )

        layer_count = 100 if shade_layer is None else shade_layer
        alpha_total = 0.5 if shade_alpha is None else shade_alpha

        for i in range(layer_count):
            alpha1 = (i + 1) / layer_count * alpha_total
            alpha2 = (layer_count - i) / layer_count * alpha_total
            ax.fill_between(
                x,
                y1 + (y2 - y1) * i / layer_count,
                y1 + (y2 - y1) * (i + 1) / layer_count,
                color="dimgrey",
                alpha=alpha1,
                hatch=shade_hatch,
            )
            ax.fill_between(
                x,
                y2 + (y3 - y2) * i / layer_count,
                y2 + (y3 - y2) * (i + 1) / layer_count,
                color="dimgrey",
                alpha=alpha2,
                hatch=shade_hatch,
            )
    else:
        ax = None

    return ax, y1, y2, y3


def irf_plot(
    values: np.ndarray,
    stderr: Optional[np.ndarray | Tuple[np.ndarray, np.ndarray]],
    impcol: str,
    rescol: str,
    names: list[str],
    *,
    hlines: Optional[float] = None,
    stderr_type: Optional[str] = None,
    signif: float = 0.05,
    ax: Any | None = None,
    figsize: Tuple[int, int] = (5, 5),
    title: Optional[str] = None,
    linewidth: Optional[float] = None,
    marker: Any | None = None,
    markersize: Optional[float] = None,
    shade_alpha: Optional[float] = None,
    shade_hatch: Optional[str] = None,
    shade_layer: Optional[int] = None,
    plot: bool = True,
    line_color: str = "black",
):
    j = names.index(impcol)
    i = names.index(rescol)

    if stderr is not None:
        if stderr_type is None:
            stderr_type = "mc" if isinstance(stderr, (tuple, list)) else "asym"
        if stderr_type == "asym":
            n = len(names)
            error = np.sqrt(stderr[:, j * n + i, j * n + i])
        elif stderr_type in ("mc", "sz1", "sz2", "sz3"):
            error = (stderr[0][:, i, j], stderr[1][:, i, j])
        else:
            error = None
    else:
        error = None

    if ax is None and plot:
        fig, ax = plt.subplots(figsize=figsize)

    ax, y1, y2, y3 = plot_with_error(
        values[:, i, j],
        error,
        x=lrange(len(values)),
        ax=ax,
        alpha=signif,
        linewidth=linewidth,
        marker=marker,
        markersize=markersize,
        shade_alpha=shade_alpha,
        shade_hatch=shade_hatch,
        shade_layer=shade_layer,
        plot=plot,
        figsize=figsize,
        line_color=line_color,
    )

    if title is not None and plot:
        ax.set_title(title)

    return ax, y1, y2, y3


def plot_irf(
    result: dict,
    impulse: str,
    response: str,
    *,
    ax: Any | None = None,
    direction: str = "single",
    band: str = "shaded",
    layout: str = "overlay",
    shaded: bool = True,
    figsize: Tuple[int, int] = (10, 8),
    linewidth: Optional[float] = None,
    marker: Any | None = None,
    markersize: Optional[float] = None,
    line_color: str = "black",
    second_line_color: str = "grey",
    second_linewidth: Optional[float] = None,
    second_shade_alpha: Optional[float] = None,
    shade_alpha: Optional[float] = None,
    shade_hatch: Optional[str] = None,
    shade_layer: Optional[int] = None,
    signif: float = 0.05,
):
    values = result["values"]
    stderr = result.get("stderr")
    names = result["names"]
    direction = direction.lower()
    band = band.lower()
    layout = layout.lower().replace("side by side", "side-by-side")

    if band not in ("shaded", "interval"):
        raise ValueError("band must be 'shaded' or 'interval'")
    if direction not in ("single", "bi"):
        raise ValueError("direction must be 'single' or 'bi'")
    if layout not in ("overlay", "side-by-side"):
        raise ValueError("layout must be 'overlay' or 'side-by-side'")

    def _plot_single_shaded(the_ax: Any, imp: str, res: str, color: str, lw: Optional[float], sa: Optional[float]):
        effective_alpha = 0.0 if not shaded else sa
        return irf_plot(
            values,
            stderr,
            imp,
            res,
            names,
            signif=signif,
            ax=the_ax,
            figsize=figsize,
            linewidth=lw,
            marker=marker,
            markersize=markersize,
            shade_alpha=effective_alpha,
            shade_hatch=shade_hatch,
            shade_layer=shade_layer,
            plot=True,
            line_color=color,
        )

    def _plot_single_interval(the_ax: Any, imp: str, res: str, color: str):
        _, y1, y2, y3 = irf_plot(
            values,
            stderr,
            imp,
            res,
            names,
            signif=signif,
            ax=None,
            figsize=figsize,
            linewidth=linewidth,
            marker=marker,
            markersize=markersize,
            shade_alpha=shade_alpha,
            shade_hatch=shade_hatch,
            shade_layer=shade_layer,
            plot=False,
            line_color=color,
        )
        if the_ax is None:
            fig, the_ax = plt.subplots(figsize=figsize)
        horizon = len(y2)
        for k in range(horizon):
            the_ax.plot([k, k], [y1[k], y3[k]], color=color)
            the_ax.plot([k - 0.1, k + 0.1], [y1[k], y1[k]], color=color)
            the_ax.plot([k - 0.1, k + 0.1], [y3[k], y3[k]], color=color)
            the_ax.plot(k, y2[k], "o", color=color)
        return the_ax

    if direction == "single":
        if band == "shaded":
            ax, _, _, _ = _plot_single_shaded(ax, impulse, response, line_color, linewidth, shade_alpha)
            return ax
        else:
            ax = _plot_single_interval(ax, impulse, response, line_color)
            return ax

    if direction == "bi":
        if band == "shaded":
            if layout == "overlay":
                if ax is None:
                    fig, ax = plt.subplots(figsize=figsize)
                lw1 = 4.0 if linewidth is None else linewidth
                lw2 = 1.0 if second_linewidth is None else second_linewidth
                sa1 = 0.8 if shade_alpha is None else shade_alpha
                sa2 = 0.4 if second_shade_alpha is None else second_shade_alpha
                _plot_single_shaded(ax, impulse, response, line_color, lw1, sa1)
                _plot_single_shaded(ax, response, impulse, second_line_color, lw2, sa2)
                return ax
            else:
                fig, axes = plt.subplots(ncols=2, figsize=(figsize[0] * 1.6, figsize[1]))
                left_ax = axes[0]
                right_ax = axes[1]
                _plot_single_shaded(left_ax, impulse, response, line_color, linewidth, shade_alpha)
                _plot_single_shaded(
                    right_ax,
                    response,
                    impulse,
                    second_line_color,
                    second_linewidth if second_linewidth is not None else linewidth,
                    second_shade_alpha if second_shade_alpha is not None else shade_alpha,
                )
                # unify y-limits for side-by-side comparison
                ly0, ly1 = left_ax.get_ylim()
                ry0, ry1 = right_ax.get_ylim()
                y0 = min(ly0, ry0)
                y1 = max(ly1, ry1)
                left_ax.set_ylim(y0, y1)
                right_ax.set_ylim(y0, y1)
                return (left_ax, right_ax)
        else:
            if layout == "overlay":
                if ax is None:
                    fig, ax = plt.subplots(figsize=figsize)
                _, y1_ab, y2_ab, y3_ab = irf_plot(
                    values,
                    stderr,
                    impulse,
                    response,
                    names,
                    signif=signif,
                    ax=None,
                    figsize=figsize,
                    linewidth=linewidth,
                    marker=marker,
                    markersize=markersize,
                    shade_alpha=shade_alpha,
                    shade_hatch=shade_hatch,
                    shade_layer=shade_layer,
                    plot=False,
                    line_color=line_color,
                )
                _, y1_ba, y2_ba, y3_ba = irf_plot(
                    values,
                    stderr,
                    response,
                    impulse,
                    names,
                    signif=signif,
                    ax=None,
                    figsize=figsize,
                    linewidth=linewidth,
                    marker=marker,
                    markersize=markersize,
                    shade_alpha=shade_alpha,
                    shade_hatch=shade_hatch,
                    shade_layer=shade_layer,
                    plot=False,
                    line_color=second_line_color,
                )
                horizon = len(y2_ab)
                for k in range(horizon):
                    ax.plot([k - 0.2, k - 0.2], [y1_ab[k], y3_ab[k]], color=line_color)
                    ax.plot([k - 0.3, k - 0.1], [y1_ab[k], y1_ab[k]], color=line_color)
                    ax.plot([k - 0.3, k - 0.1], [y3_ab[k], y3_ab[k]], color=line_color)
                    ax.plot(k - 0.2, y2_ab[k], "o", color=line_color)
                    ax.plot([k + 0.2, k + 0.2], [y1_ba[k], y3_ba[k]], color=second_line_color)
                    ax.plot([k + 0.1, k + 0.3], [y1_ba[k], y1_ba[k]], color=second_line_color)
                    ax.plot([k + 0.1, k + 0.3], [y3_ba[k], y3_ba[k]], color=second_line_color)
                    ax.plot(k + 0.2, y2_ba[k], "o", color=second_line_color)
                return ax
            else:
                fig, axes = plt.subplots(ncols=2, figsize=(figsize[0] * 1.6, figsize[1]))
                left_ax = _plot_single_interval(axes[0], impulse, response, line_color)
                right_ax = _plot_single_interval(axes[1], response, impulse, second_line_color)
                # unify y-limits for side-by-side comparison
                ly0, ly1 = left_ax.get_ylim()
                ry0, ry1 = right_ax.get_ylim()
                y0 = min(ly0, ry0)
                y1 = max(ly1, ry1)
                left_ax.set_ylim(y0, y1)
                right_ax.set_ylim(y0, y1)
                return (left_ax, right_ax)

    raise RuntimeError("Unhandled plotting configuration")


