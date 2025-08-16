---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: pa-aa-ner-flooding
    language: python
    name: pa-aa-ner-flooding
---

# Niamey station fitting
<!-- markdownlint-disable MD013 -->
Using GRDC data, compared to ABN data. Define curve fit between discharge and stage

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress

from src.datasources import grdc, abn
from src.utils.rating_curve import calculate_stage
from src.constants import *
```

```python
df_abn = abn.load_abn_niamey(local=True)
```

```python
df_abn
```

```python
df_grdc = grdc.load_grdc(station_id=NIAMEY_GRDC_ID)
```

```python
df_grdc
```

```python
df_compare = (
    df_abn.reset_index().rename(columns={"Date": "time"}).merge(df_grdc)
)
```

```python
df_compare.corr()
```

```python
recent_x, recent_y = 508, 1311
```

```python
df_compare
```

```python
xcol, ycol = "Water Level (cm)", "Discharges (m3/s)"

fig, ax = plt.subplots()
df_compare.plot(x=xcol, y=ycol, ax=ax)
for year, row in (
    df_compare.groupby(df_compare["time"].dt.year)[[xcol, ycol]]
    .max()
    .iterrows()
):
    ax.annotate(year, row[[xcol, ycol]], ha="center", va="center", fontsize=8)

ax.plot([recent_x], [recent_y], marker=".", color="red")
```

Looks like the update the discharge-level curve every few years. But based on the recent point (from 2025), they are still using that most recent curve (from 2016 to 2022), so we can use that one.

```python
def fit_rating_curve_loglog(
    df, stage_col="stage", discharge_col="discharge", h0=None
):
    # Drop NaNs and non-positive discharge
    df = df[[stage_col, discharge_col]].dropna()
    df = df[df[discharge_col] > 0]

    h = df[stage_col].values
    Q = df[discharge_col].values

    if h0 is None:
        h0 = np.min(h)  # You can tweak this manually

    h_adj = h - h0
    mask = h_adj > 0
    h_adj = h_adj[mask]
    Q = Q[mask]

    log_h = np.log(h_adj)
    log_Q = np.log(Q)

    slope, intercept, _, _, _ = linregress(log_h, log_Q)
    b = slope
    a = np.exp(intercept)

    return a, b, h0
```

```python
df_curve_fit = df_compare[df_compare["time"].dt.year >= 2017].copy()
```

```python
df_curve_fit.plot(x=xcol, y=ycol)
```

```python
df_curve_fit = df_curve_fit.sort_values("Water Level (cm)")
```

```python
df_curve_fit.plot(x=xcol, y=ycol)
```

```python
a, b, h0 = fit_rating_curve_loglog(
    df_curve_fit,
    stage_col="Water Level (cm)",
    discharge_col="Discharges (m3/s)",
)
print(f"Fitted parameters:\na = {a:.4f}, b = {b:.4f}, h0 = {h0:.4f}")
```

```python
def predict_discharge(stage, a, b, h0):
    stage = np.array(stage)
    stage_adj = np.maximum(stage - h0, 1e-6)
    return a * stage_adj**b
```

```python
df_curve_fit["pred_dis"] = predict_discharge(
    df_curve_fit["Water Level (cm)"], a, b, h0
)
```

```python
df_curve_fit["pred_dis"] = predict_discharge(
    df_curve_fit["Water Level (cm)"], a, b, h0
)
```

```python
fig, ax = plt.subplots()
df_curve_fit.plot(x="Water Level (cm)", y="Discharges (m3/s)", ax=ax)
df_curve_fit.plot(x="Water Level (cm)", y="pred_dis", ax=ax)
```

Ok after various tweaks to the standard fitting it doesn't really look that good. We can try

```python
def fit_polynomial_rating_curve(
    df,
    stage_col="Water Level (cm)",
    discharge_col="Discharges (m3/s)",
    degree=2,
):
    df = df[[stage_col, discharge_col]].dropna()

    x = df[stage_col].values
    y = df[discharge_col].values

    coeffs = np.polyfit(x, y, deg=degree)
    poly = np.poly1d(coeffs)

    return poly  # This is a callable function
```

```python
poly = fit_polynomial_rating_curve(df_curve_fit, degree=2)
df_curve_fit["Q_pred"] = poly(df_curve_fit["Water Level (cm)"])
```

```python
poly
```

```python
fig, ax = plt.subplots()
df_curve_fit.plot(x="Water Level (cm)", y="Discharges (m3/s)", ax=ax)
df_curve_fit.plot(x="Water Level (cm)", y="Q_pred", ax=ax)
```

```python
def invert_quadratic(Q, poly, root="max"):
    """
    Invert a quadratic polynomial to get stage from discharge.

    Parameters:
    - Q: scalar or array of discharge values
    - poly: a degree-2 numpy.poly1d object
    - root: 'max' (default) or 'min' to choose which root to return

    Returns:
    - h: estimated stage(s)
    """
    Q = np.atleast_1d(Q)
    a, b, c = poly.coefficients  # poly1d stores in descending order

    h_values = []
    for q in Q:
        discriminant = b**2 - 4 * a * (c - q)
        if discriminant < 0:
            h_values.append(np.nan)
        else:
            sqrt_d = np.sqrt(discriminant)
            h1 = (-b + sqrt_d) / (2 * a)
            h2 = (-b - sqrt_d) / (2 * a)
            h_values.append(max(h1, h2) if root == "max" else min(h1, h2))

    return np.array(h_values) if len(h_values) > 1 else h_values[0]
```

```python
df_curve_fit["stage_pred"] = invert_quadratic(
    df_curve_fit["Discharges (m3/s)"], poly
)
```

```python
fig, ax = plt.subplots()
df_curve_fit.plot(x="stage_pred", y="Discharges (m3/s)", ax=ax)
df_curve_fit.plot(x="Water Level (cm)", y="Discharges (m3/s)", ax=ax)
```

```python
df_curve_fit["stage_pred_func"] = calculate_stage(
    df_curve_fit["Discharges (m3/s)"]
)
```

```python
fig, ax = plt.subplots()
df_curve_fit.plot(x="stage_pred_func", y="Discharges (m3/s)", ax=ax)
df_curve_fit.plot(x="Water Level (cm)", y="Discharges (m3/s)", ax=ax)
```

```python

```
