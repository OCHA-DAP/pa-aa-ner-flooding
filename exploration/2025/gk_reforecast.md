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

# Garbé-Kourou reforecast

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
min_season, max_season = 1979, 2024
```

```python
df_grdc = df_grdc[(df_grdc["season"].isin(range(min_season, max_season + 1)))]
```

```python
df_grdc["level"] = calculate_stage(df_grdc["runoff_mean"])
```

```python
df_locale = df_grdc[df_grdc["flood_type"] == "l"]
df_gui = df_grdc[df_grdc["flood_type"] == "g"]
```

```python
df_locale
```

```python
df_rea_niamey = glofas.load_reanalysis("niamey")
```

```python
df_rea_niamey["season"] = df_rea_niamey["time"].apply(date_to_season)
```

```python
df_plot = df_rea_niamey.copy()
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
        y="dis24",
        ax=ax,
        legend=False,
        color="k",
        alpha=0.2,
        linewidth=0.5,
    )

df_plot.groupby("plot_date")["dis24"].mean().plot(ax=ax, color="k")

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

ax.set_ylim(bottom=0)
ax.set_xlim((df_plot["plot_date"].min(), df_plot["plot_date"].max()))
[ax.spines[x].set_visible(False) for x in ["top", "right"]]
```

```python
df_rea_niamey.set_index("season").loc[2024].plot(x="time", y="dis24")
```

```python
df_gui = df_gui.merge(df_rea_niamey)
```

```python
df_gui_peaks = df_gui.groupby("season")[["dis24", "level"]].max().reset_index()
```

```python
df_gui_peaks[df_gui_peaks["season"] >= 2000].plot.scatter(x="dis24", y="level")
```

```python
df_gui_peaks = calculate_one_group_rp(
    df_gui_peaks, col_name="dis24", ascending=False
)
df_gui_peaks = calculate_one_group_rp(
    df_gui_peaks, col_name="level", ascending=False
)
```

```python
df_rea_peaks = df_rea_niamey.groupby("season")["dis24"].max().reset_index()
```

```python
df_rea_peaks = calculate_one_group_rp(
    df_rea_peaks, col_name="dis24", ascending=False
)
```

```python
thresh_action = 600
```

```python
rp_readiness = 4
```

```python
df_gui_peaks = df_gui_peaks.sort_values("dis24_rp")
thresh_readiness_g_oct = np.interp(
    rp_readiness, df_gui_peaks["dis24_rp"], df_gui_peaks["dis24"]
)
df_rea_peaks = df_rea_peaks.sort_values("dis24_rp")
thresh_readiness_g = np.interp(
    rp_readiness, df_rea_peaks["dis24_rp"], df_rea_peaks["dis24"]
)
```

```python
thresh_readiness_g
```

```python
dicts = []
for season in df_gui["season"].unique():
    dff_trig = df_rea_niamey[
        (df_rea_niamey["dis24"] >= thresh_readiness_g)
        & (df_rea_niamey["season"] == season)
    ]
    dff_trig_oct_only = df_gui[
        (df_gui["dis24"] >= thresh_readiness_g_oct)
        & (df_gui["season"] == season)
    ]
    dff_actual = df_gui[
        (df_gui["level"] >= thresh_action) & (df_gui["season"] == season)
    ]
    dicts.append(
        {
            "season": season,
            "readiness_date": dff_trig["time"].min(),
            "readiness_date_oct": dff_trig_oct_only["time"].min(),
            "action_date": dff_actual["time"].min(),
        }
    )

df_gui_timing = pd.DataFrame(dicts)
```

```python
df_gui_timing
```

```python
(2025 - 1979 + 1 + 1) / 12
```

```python
df_rea_gk = glofas.load_reanalysis("garbekourou")
```

```python
df_rea_gk
```

```python
df_ref_gk = glofas.load_reforecast("garbekourou")
df_ref_gk = df_ref_gk[df_ref_gk["leadtime"] <= 7]
```

```python
df_ref_gk
```

```python
df_locale = df_locale.merge(df_rea_gk)
```

```python
df_locale
```

```python
df_loc_peaks = (
    df_locale.groupby("season")[["level", "dis24"]].max().reset_index()
)
```

```python
df_loc_peaks = calculate_one_group_rp(df_loc_peaks, "dis24", ascending=False)
df_loc_peaks = calculate_one_group_rp(df_loc_peaks, "level", ascending=False)
```

```python
df_loc_peaks = df_loc_peaks.sort_values("dis24_rp")
gk_rea_thresh = np.interp(
    rp_readiness, df_loc_peaks["dis24_rp"], df_loc_peaks["dis24"]
)
```

```python
gk_rea_thresh
```

```python
dicts = []
for season, group in df_locale.groupby("season"):
    dff_trig = group[(group["dis24"] >= gk_rea_thresh)]
    dff_actual = group[(group["level"] >= thresh_action)]
    dff_red = group[group["level"] >= 620]
    dicts.append(
        {
            "season": season,
            "readiness_date": dff_trig["time"].min(),
            "action_date": dff_actual["time"].min(),
            "red_date": dff_red["time"].min(),
        }
    )

df_loc_timing = pd.DataFrame(dicts)
df_loc_timing["action_lt"] = (
    df_loc_timing["red_date"] - df_loc_timing["action_date"]
)
df_loc_timing["readiness_lt"] = (
    df_loc_timing["red_date"] - df_loc_timing["readiness_date"]
)
```

```python
df_loc_timing["readiness_lt"].mean()
```

```python
df_loc_timing["action_lt"].mean()
```

```python
df_ref_gk["season"] = df_ref_gk["valid_time"].apply(date_to_season)
```

```python
df_ref_gk
```

```python
dfs = []
dicts = []
for lt in df_ref_gk["leadtime"].unique():
    dff = df_ref_gk[df_ref_gk["leadtime"] <= lt]
    dff_peaks = dff.groupby("season")["dis24"].max().reset_index()
    dff_peaks = calculate_one_group_rp(
        dff_peaks, col_name="dis24", ascending=False
    )
    dff_peaks = dff_peaks.sort_values("dis24_rp")
    thresh_lt = np.interp(
        rp_readiness, dff_peaks["dis24_rp"], dff_peaks["dis24"]
    )
    dicts.append({"lt_max": lt, "thresh": thresh_lt})
    dff_trig = dff[dff["dis24"] >= thresh_lt]
    dff_timing = dff_trig.groupby("season")["time"].min().reset_index()
    dff_timing["lt_max"] = lt
    dfs.append(dff_timing)
```

```python
df_timing_pivot = pd.concat(dfs, ignore_index=True).pivot(
    index="season", columns="lt_max", values="time"
)
df_timing_pivot = df_timing_pivot.rename(
    columns={x: f"ltmax{x}" for x in df_timing_pivot.columns}
).reset_index()
df_timing_pivot.columns.name = None
```

```python
df_timing_pivot
```

```python
df_ref_timing = df_timing_pivot.merge(df_loc_timing)
```

```python
dicts = []
for lt in range(1, 8):
    ref_col = f"ltmax{lt}"
    tps = (
        ~df_ref_timing[ref_col].isnull() & ~df_ref_timing["red_date"].isnull()
    )
    tp = tps.sum()
    readiness_lts = df_ref_timing["red_date"] - df_ref_timing[ref_col]
    print(readiness_lts)
    dicts.append(
        {"lt_max": lt, "tp": tp, "readiness_lt": readiness_lts.mean()}
    )
```

```python
readiness_lts
```

```python
df_ref_metrics = pd.DataFrame(dicts)
```

```python
df_ref_metrics
```

```python

```
