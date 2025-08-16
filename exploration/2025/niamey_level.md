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

# Niamey level
<!-- markdownlint-disable MD013 -->

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

from src.datasources import grdc, glofas
from src.utils.rp_calc import calculate_one_group_rp
from src.utils.rating_curve import calculate_stage
from src.constants import *
```

```python
df_grdc = grdc.load_grdc(station_id=NIAMEY_GRDC_ID)
```

```python
def date_to_season(date):
    if date.month < 6:
        return date.year - 1
    else:
        return date.year
```

```python
df_grdc["season"] = df_grdc["time"].apply(date_to_season)
```

```python
def set_flood_phase(date):
    if date.month >= 6 and date.month <= 9:
        return "l"
    else:
        return "g"
```

```python
df_grdc["flood_type"] = df_grdc["time"].apply(set_flood_phase)
```

```python
df_grdc
```

```python
min_year = 1979
```

```python
df_plot = df_grdc[df_grdc["season"] >= min_year].copy()
df_plot["plot_date"] = df_plot["time"].map(
    lambda x: pd.Timestamp(
        year=1904,
        month=x.month,
        day=x.day,
    )
)
```

```python
fig, ax = plt.subplots(figsize=(10, 5), dpi=200)

for year, group in df_plot.groupby(df_plot["time"].dt.year):
    group.plot(
        x="plot_date",
        y="runoff_mean",
        ax=ax,
        legend=False,
        color="k",
        alpha=0.2,
        linewidth=0.5,
    )

df_plot.groupby("plot_date")["runoff_mean"].mean().plot(ax=ax, color="k")

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

ax.set_ylim(bottom=0)
ax.set_xlim((df_plot["plot_date"].min(), df_plot["plot_date"].max()))
[ax.spines[x].set_visible(False) for x in ["top", "right"]]
```

```python
df_locale = df_grdc[df_grdc["flood_type"] == "l"]
```

```python
df_locale_peaks = (
    df_locale.groupby(df_locale["time"].dt.year)["runoff_mean"]
    .max()
    .reset_index()
    .rename(columns={"time": "year"})
)
```

```python
df_locale_peaks = calculate_one_group_rp(
    df_locale_peaks, col_name="runoff_mean", ascending=False
)
```

```python
df_locale_peaks["level"] = calculate_stage(df_locale_peaks["runoff_mean"])
```

```python
df_locale_peaks.sort_values("runoff_mean_rp")
```

```python
df_recent = df_grdc[
    (df_grdc["season"] >= min_year) & (df_grdc["season"] < 2025)
].copy()
```

```python
df_recent["level"] = calculate_stage(df_recent["runoff_mean"])
```

```python
df_peaks = df_recent.groupby("season")["level"].max().reset_index()
```

```python
df_peaks_l = (
    df_recent[df_recent["flood_type"] == "l"]
    .groupby("season")["level"]
    .max()
    .reset_index()
)
```

```python
df_peaks_g = (
    df_recent[df_recent["flood_type"] == "g"]
    .groupby("season")["level"]
    .max()
    .reset_index()
)
```

```python
df_peaks_l = calculate_one_group_rp(
    df_peaks_l, col_name="level", ascending=False
)
```

```python
df_peaks = calculate_one_group_rp(df_peaks, col_name="level", ascending=False)
```

```python
df_peaks.sort_values("level_rank")
```

```python
thresh = 600
```

```python
total_years = df_recent["time"].dt.year.nunique()
```

```python
(total_years + 1) / df_recent[
    (df_recent["level"] >= thresh) & (df_recent["flood_type"] == "l")
]["season"].nunique()
```

```python
(total_years + 1) / df_recent[
    (df_recent["level"] >= thresh) & (df_recent["flood_type"] == "g")
]["season"].nunique()
```

```python
def get_flood_type_rp(thresh, flood_type):
    trig_years = df_recent[
        (df_recent["level"] >= thresh)
        & (df_recent["flood_type"] == flood_type)
    ]["season"].nunique()
    if trig_years == 0:
        return np.inf
    else:
        return (total_years + 1) / trig_years
```

```python
df_peaks["l_rp"] = df_peaks["level"].apply(get_flood_type_rp, flood_type="l")
df_peaks["g_rp"] = df_peaks["level"].apply(get_flood_type_rp, flood_type="g")
```

```python
df_peaks = df_peaks.sort_values("level_rp")
```

```python
df_peaks
```

```python
rp = np.interp(600, df_peaks["level"], df_peaks["level_rp"])
```

```python
rp
```

```python
rp_l = np.interp(600, df_peaks_l["level"], df_peaks_l["level_rp"])
```

```python
rp_l
```

```python
fig, ax = plt.subplots(dpi=200)
for col, label in [
    ("level_rp", "Globale"),
    ("l_rp", "Locales"),
    ("g_rp", "Guinnéennes"),
]:
    df_peaks.sort_values("level").plot(x=col, y="level", ax=ax, label=label)

ax.set_xlabel("Période de retour (ans)")
ax.set_ylabel("Niveau d'eau à Niamey")

ax.set_xlim((1, 10))
ax.set_ylim(top=680)

ax.axhline(600, linestyle="--", color="crimson")

ax.legend(title="Période de retour\nd'inondations")

ax.set_title(
    "Période de retour d'inondations Niamey\nAnnées d'analyse : 1979-2024"
)

[ax.spines[x].set_visible(False) for x in ["top", "right"]]
```

```python
minval, maxval = (
    min(df_peaks_g["level"].min(), df_peaks_l["level"].min()),
    df_peaks["level"].max(),
)
span = maxval - minval
minlim, maxlim = (minval - span * 0.1, maxval + span * 0.1)
lims = (minlim, maxlim)
```

```python
xcolor, ycolor = "crimson", "darkorange"
```

```python
fig, ax = plt.subplots(dpi=200, figsize=(7, 7))

for season in df_peaks["season"].unique():
    color = "grey"
    l_peak = df_peaks_l.set_index("season").loc[season, "level"]
    g_peak = df_peaks_g.set_index("season").loc[season, "level"]
    if l_peak >= thresh:
        color = xcolor
    if g_peak >= thresh:
        color = ycolor
    if (l_peak >= thresh) & (g_peak >= thresh):
        color = "maroon"
    ax.annotate(
        season, (l_peak, g_peak), va="center", ha="center", color=color
    )

ax.axhline(thresh, color=ycolor)
ax.axhspan(thresh, maxlim, facecolor=ycolor, alpha=0.1)

ax.axvline(thresh, color=xcolor)
ax.axvspan(thresh, maxlim, facecolor=xcolor, alpha=0.1)

ax.set_xlim(lims)
ax.set_ylim(lims)

ax.set_xlabel("Niveau d'eau de crues locales (cm)")
ax.set_ylabel("Niveau d'eau de crues guinnéennes (cm)")

[ax.spines[x].set_visible(False) for x in ["top", "right"]]
```

```python
df_recent
```

```python
dicts = []
for season, group in df_recent[df_recent["flood_type"] == "l"].groupby(
    "season"
):
    dff = group[group["level"] >= thresh]
    if not dff.empty:
        dicts.append({"trig_date": dff["time"].min(), "season": season})
```

```python
df_trig_dates_grdc = pd.DataFrame(dicts)
```

```python
df_trig_dates_grdc
```

```python
df_gf = glofas.load_reanalysis(station_name="garbekourou")
```

```python
df_gf
```

```python
df_gf_peaks = df_gf.groupby(df_gf["time"].dt.year)["dis24"].max().reset_index()
```

```python
df_gf_peaks = calculate_one_group_rp(
    df_gf_peaks, col_name="dis24", ascending=False
)
```

```python
df_gf_peaks = df_gf_peaks.sort_values("dis24_rp")
```

```python
gf_thresh = np.interp(rp_l, df_gf_peaks["dis24_rp"], df_gf_peaks["dis24"])
```

```python
gf_thresh
```

```python
dicts = []
for season, group in df_gf.groupby(df_gf["time"].dt.year):
    dff = group[group["dis24"] >= gf_thresh]
    if not dff.empty:
        dicts.append({"trig_date": dff["time"].min(), "season": season})
```

```python
df_trig_dates_gf = pd.DataFrame(dicts)
```

```python
df_trig_dates_gf
```

```python
df_trig_dates = df_trig_dates_grdc.merge(
    df_trig_dates_gf, on="season", suffixes=("_grdc", "_gf"), how="outer"
)
```

```python
df_trig_dates["grdc_lt"] = (
    df_trig_dates["trig_date_grdc"] - df_trig_dates["trig_date_gf"]
)
```

```python
df_trig_dates
```

```python
df_trig_dates["grdc_lt"].mean()
```

## Plot timing after certain level

```python
initial_level = 566
```

```python
thresh
```

```python
df_timing = df_trig_dates_grdc.copy()
```

```python
df_locale_recent = df_recent[df_recent["flood_type"] == "l"]
```

```python
df_locale_recent
```

```python
df_timing
```

```python
def get_level_initial_date(season, level):
    dff = df_locale_recent[
        (df_locale_recent["level"] >= level)
        & (df_locale_recent["season"] == season)
    ]
    return dff["time"].min()
```

```python
seasons = df_locale_recent[df_locale_recent["level"] >= initial_level][
    "season"
].unique()
```

```python
seasons
```

```python
df_timing["first_date"] = df_timing["season"].apply(
    get_level_initial_date, level=initial_level
)
```

```python
df_timing
```

```python
df_timing["delay"] = df_timing["trig_date"] - df_timing["first_date"]
```

```python
dicts = []
for season, group in df_recent[df_recent["flood_type"] == "l"].groupby(
    "season"
):
    dff = group[group["level"] >= initial_level]
    if not dff.empty:
        dicts.append({"initial_date": dff["time"].min(), "season": season})

df_timing = pd.DataFrame(dicts)
```

```python
df_timing["trig_date"] = df_timing["season"].apply(
    get_level_initial_date, level=thresh
)
```

```python
df_timing["delay"] = df_timing["trig_date"] - df_timing["initial_date"]
```

```python
df_timing["delay"].mean()
```

```python
df_timing
```

```python
len(df_timing)
```

```python
df_timing.dropna()
```

```python
len(df_timing.dropna()) / len(df_timing)
```

```python
df_locale_recent
```

```python
ax = df_locale_recent[df_locale_recent["season"] == 2024].plot(
    x="time", y="level"
)
ax.axhline(600, color="crimson")
ax.axhline(580, color="darkorange")
```
