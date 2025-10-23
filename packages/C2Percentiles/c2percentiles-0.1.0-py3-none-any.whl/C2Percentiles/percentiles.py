#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantile_kit – All nine Hyndman-Fan quantile estimators + helpers
==================================================================

A zero-dependency (only numpy & pandas) micro-library that gives you
the nine sample-quantile estimators described in Hyndman & Fan (1996)
together with ready-made helpers for:

* single vectors
* many columns at once
* group-wise calculations
* quick visual checks

Author  : <your-name>
License : MIT
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Iterable, List, Union, Optional

# ------------------------------------------------------------------
# 1.  Nine individual estimators (qtype1 … qtype9)
# ------------------------------------------------------------------
def qtype1(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Inverse ECDF (step function)."""
    x = np.sort(x)
    n = len(x)
    return [x[min(int(np.ceil(n * p)) - 1, n - 1)] for p in probs]


def qtype2(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Averaged inverse ECDF (mid-step)."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        j = n * p
        if j.is_integer() and j > 0:
            j = int(j)
            val = (x[j - 1] + x[min(j, n - 1)]) / 2
        else:
            val = x[min(int(np.ceil(j)) - 1, n - 1)]
        out.append(val)
    return out


def qtype3(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Nearest order statistic (rounding)."""
    x = np.sort(x)
    n = len(x)
    return [x[min(max(int(round(n * p)) - 1, 0), n - 1)] for p in probs]


def qtype4(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Linear interp. of ECDF (k/n)."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = n * p
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


def qtype5(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Mid-step uniform (Hazen)."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = n * p + 0.5
        j = int(np.floor(h))
        g = h - j
        j = min(max(j, 1), n)
        if j == n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


def qtype6(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Weibull (k/(n+1)) – unbiased plotting position."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 1) * p
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


def qtype7(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Default in NumPy/pandas – (k-1)/(n-1)."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = 1 + (n - 1) * p
        j = int(np.floor(h))
        g = h - j
        if j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


def qtype8(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Median-unbiased – (k − ⅓)/(n + ⅓)."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 1 / 3) * p + 1 / 3
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


def qtype9(x: np.ndarray, probs: Iterable[float]) -> List[float]:
    """Blom – normal QQ-plot unbiased."""
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 0.25) * p + 3 / 8
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


# ------------------------------------------------------------------
# 2.  Helper: significant-digit formatter (keeps trailing zeros)
# ------------------------------------------------------------------
def _fmt_sig(x: float, n: int) -> str:
    """Return string with exactly n significant digits, no sci-note."""
    if x == 0:
        return f"0.{ '0'*(n-1) }"
    shift = int(np.floor(np.log10(abs(x))))
    decimals = n - 1 - shift
    return f"{x:.{max(0, decimals)}f}"


# ------------------------------------------------------------------
# 3.  Master function – quantile_custom
# ------------------------------------------------------------------
def quantile_custom(
    x: Iterable[float],
    probs: Iterable[float],
    qtype: Union[int, List[int], str] = 7,
    sig_digits: Optional[int] = None,
) -> Union[pd.Series, pd.DataFrame]:
    """
    Compute quantiles for a single numeric vector using any of the
    nine Hyndman-Fan estimators.

    Parameters
    ----------
    x : 1-D array-like
        Input data.
    probs : scalar or iterable of probabilities in (0, 1)
        Quantile(s) to compute.
    qtype : int 1-9, list/tuple of ints, or "all"
        Which estimator(s) to use.
    sig_digits : int ≥ 1, optional
        Forces every returned value to exactly this many significant
        digits (keeps trailing zeros) and returns strings.

    Returns
    -------
    pd.Series  if qtype is a single int
    pd.DataFrame otherwise (rows = probs, cols = Type1 … Type9)
    """
    x = np.asarray(x)
    probs = np.atleast_1d(probs)
    custom_funcs = {i: globals()[f"qtype{i}"] for i in range(1, 10)}

    if qtype == "all":
        out = {f"Type{qt}": custom_funcs[qt](x, probs) for qt in range(1, 10)}
        res = pd.DataFrame(out, index=probs)
        if sig_digits is not None:
            res = res.applymap(lambda v: _fmt_sig(v, sig_digits))
            #res = res.map(lambda v: _fmt_sig(v, sig_digits))
        return res

    elif isinstance(qtype, list):
        out = {f"Type{qt}": custom_funcs[qt](x, probs) for qt in qtype}
        res = pd.DataFrame(out, index=probs)
        if sig_digits is not None:
            res = res.applymap(lambda v: _fmt_sig(v, sig_digits))
            #res = res.map(lambda v: _fmt_sig(v, sig_digits))
        return res

    else:
        res = pd.Series(custom_funcs[qtype](x, probs), index=probs)
        if sig_digits is not None:
            res = res.apply(lambda v: _fmt_sig(v, sig_digits))
        return res


# ------------------------------------------------------------------
# 4.  Batch helpers
# ------------------------------------------------------------------
def quantiles_for_vars(
    df: pd.DataFrame,
    vars: List[str],
    probs: List[float] = [0.05, 0.5, 0.9],
    qtype: Union[int, List[int], str] = "all",
    sig_digits: Optional[int] = None,
) -> pd.DataFrame:
    """
    Compute quantiles for several columns in a DataFrame.

    Returns a long-form DataFrame with leading columns:
    Variable | Probability | Type1 … Type9
    """
    results = []
    for v in vars:
        x = df[v].dropna()
        res = quantile_custom(x, probs, qtype, sig_digits)
        if isinstance(res, pd.Series):
            res = res.to_frame().T
        res.insert(0, "Variable", v)
        res.insert(1, "Probability", probs)
        results.append(res)
    return pd.concat(results, ignore_index=True)


def quantiles_by_group(
    df: pd.DataFrame,
    group_var: str,
    num_vars: List[str],
    probs: List[float] = [0.05, 0.5, 0.9],
    qtype: Union[int, List[int], str] = "all",
    sig_digits: Optional[int] = None,
) -> pd.DataFrame:
    """
    Same as quantiles_for_vars but stratified by a categorical column.
    """
    results = []
    for grp, sub in df.groupby(group_var):
        temp = quantiles_for_vars(sub, num_vars, probs, qtype, sig_digits)
        temp.insert(2, group_var, grp)
        results.append(temp)
    return pd.concat(results, ignore_index=True)


# ------------------------------------------------------------------
# 5.  Quick plotting helpers (require seaborn & matplotlib)
# ------------------------------------------------------------------
def plot_quantile_line(
    x: Iterable[float],
    probs: Iterable[float],
    sig_digits: Optional[int] = None,
    wid: int = 12,
    ht: int = 3,
    palette: str = "viridis",
    lw: int = 2,
) -> None:
    """
    Line plot: x = Type (1-9), y = quantile value, hue = probability level.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    wide = quantile_custom(x, probs, qtype="all", sig_digits=sig_digits)
    long = (
        wide.stack()
        .rename("Quantile")
        .rename_axis(["Probability", "Type"])
        .reset_index()
    )
    long["Type"] = long["Type"].str.replace("Type", "").astype(int)

    plt.figure(figsize=(wid, ht))
    sns.lineplot(
        data=long,
        x="Type",
        y="Quantile",
        hue="Probability",
        marker="o",
        sort=False,
        palette=palette,
        linewidth=lw,
        markersize=lw * 4,
    )
    plt.xticks(range(1, 10))
    plt.xlabel("Quantile Type")
    plt.title("Quantile values across Types 1-9")
    plt.legend(title="Probability", bbox_to_anchor=(1.02, 0.5), loc="center left")
    plt.tight_layout()
    plt.show()


def plot_qfv(
    df: pd.DataFrame,
    vars: List[str],
    probs: Iterable[float],
    sig_digits: Optional[int] = None,
    height: float = 2.5,
    aspect: float = 1.2,
    col_wrap: int = 2,
    palette: str = "viridis",
    lw: int = 2,
) -> None:
    """
    Faceted line plots (one panel per variable) of quantile types.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    pieces = []
    for v in vars:
        wide = quantile_custom(df[v].dropna(), probs, qtype="all", sig_digits=sig_digits)
        pieces.append(
            wide.stack()
            .rename("Quantile")
            .rename_axis(["Probability", "Type"])
            .reset_index()
            .assign(Variable=v, Type=lambda d: d["Type"].str.replace("Type", "").astype(int))
        )
    long = pd.concat(pieces, ignore_index=True)

    g = sns.FacetGrid(
        long,
        col="Variable",
        col_wrap=col_wrap,
        sharex=True,
        sharey=False,
        height=height,
        aspect=aspect,
    )
    g.map_dataframe(
        sns.lineplot,
        x="Type",
        y="Quantile",
        hue="Probability",
        marker="o",
        sort=False,
        palette=palette,
        linewidth=lw,
        markersize=lw * 4,
    )
    g.set_axis_labels("Quantile Type", "Quantile value")
    for ax in g.axes.flat:
        ax.set_xticks(range(1, 10))
    g.add_legend()
    plt.tight_layout()
    plt.show()


def plot_qbg(
    df: pd.DataFrame,
    group_var: str,
    vars: List[str],
    probs: Iterable[float],
    sig_digits: Optional[int] = None,
    height: float = 2,
    aspect: float = 1.1,
    palette: str = "viridis",
    lw: int = 2,
) -> None:
    """
    Faceted quantile plots by group **and** variable.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    long = (
        quantiles_by_group(df, group_var, vars, probs, qtype="all", sig_digits=sig_digits)
        .melt(
            id_vars=[group_var, "Variable", "Probability"],
            value_vars=[f"Type{i}" for i in range(1, 10)],
            var_name="Type",
            value_name="Quantile",
        )
        .assign(Type=lambda d: d["Type"].str.replace("Type", "").astype(int))
    )

    g = sns.FacetGrid(
        long,
        row=group_var,
        col="Variable",
        sharex=True,
        sharey=False,
        height=height,
        aspect=aspect,
    )
    g.map_dataframe(
        sns.lineplot,
        x="Type",
        y="Quantile",
        hue="Probability",
        marker="o",
        sort=False,
        palette=palette,
        linewidth=lw,
        markersize=lw * 4,
    )
    g.set_axis_labels("Quantile Type", "Quantile value")
    for ax in g.axes.flat:
        ax.set_xticks(range(1, 10))
    g.add_legend()
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------------
# 6.  Tiny self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "X1": np.random.randn(10),
            "X2": np.random.randn(10) * 50 + 100,
            "X3": np.random.randn(10) * 50 - 100,
            "Group": np.random.choice(["A", "B"], 10),
        }
    )
    print("Single vector, all types:")
    print(quantile_custom(df["X1"], [0.05, 0.5, 0.9], qtype="all", sig_digits=4))
    print("\nMultiple variables:")
    print(quantiles_for_vars(df, ["X1", "X2"], probs=[0.05, 0.5, 0.9], sig_digits=3))
    print("\nBy group:")
    print(
        quantiles_by_group(df, "Group", ["X1", "X2"], probs=[0.1, 0.5, 0.9], sig_digits=2)
    )