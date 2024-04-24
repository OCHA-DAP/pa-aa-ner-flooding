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

# Flood exposure

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from tqdm.notebook import tqdm

from src.datasources import worldpop, codab, floodscan, abn, hydrosheds
from src.constants import *
from src.utils import shift_to_floodseason
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "time", "Water Level (cm)": "level"})
level = shift_to_floodseason(level, date_col="time")
# drop duplicates due to leapyears (just on Jan 1)
level = level[~level.duplicated(subset=["dayofseason", "seasonyear"])]
# keep only full seasons
level = level[level["seasonyear"].isin(range(2005, 2022))]
level
```

```python
level[level.duplicated(subset=["dayofseason", "seasonyear"])]
```

```python
level.pivot(index="dayofseason", columns="seasonyear", values="level").plot()
```

```python
# codab.download_codab()
```

```python
adm3 = codab.load_codab(admin_level=3, aoi_only=True)
adm2 = codab.load_codab(admin_level=2, aoi_only=True)
adm1 = codab.load_codab(admin_level=1, aoi_only=True)
```

```python
river = hydrosheds.load_niger_river()
river_aoi = gpd.sjoin(river, adm3, how="inner", predicate="intersects")
```

```python
# floodscan.clip_ner_from_glb()
```

```python
exp = floodscan.load_daily_exposure()
```

```python
rolls = [1, 3, 5, 7, 9, 11]
for roll in rolls:
    exp[f"fs_roll{roll}"] = (
        exp.groupby("ADM3_PCODE")["total_exposed"]
        .transform(lambda x: x.rolling(window=roll, min_periods=roll).mean())
        .shift(-np.floor(roll / 2).astype(int))
    )
```

```python
exp
```

```python
exp_f = exp[exp["ADM3_PCODE"] == GAYA].copy().sort_values("time")
exp_f = shift_to_floodseason(exp_f, date_col="time")
exp_f
```

```python
exp_max = (
    exp.groupby(["ADM3_PCODE", exp["time"].dt.year])
    .max()
    .drop(columns="time")
    .reset_index()
)
exp_max_mean = (
    exp_max.groupby("ADM3_PCODE").mean().drop(columns="time").reset_index()
)
```

```python
exp_max_mean.merge(
    adm3[["ADM3_PCODE", "ADM3_FR"]], on="ADM3_PCODE"
).sort_values("total_exposed", ascending=False).iloc[:10]
```

```python
exp_max[exp_max["ADM3_PCODE"] == GAYA].plot(x="time", y="fs_roll7")
```

```python
compare = exp.merge(level, on="time")
```

```python
compare_f = compare[compare["ADM3_PCODE"] == TANDA]
compare_f.pivot(
    index="dayofseason",
    columns="seasonyear",
    values="fs_roll9",
).plot(linewidth=0.3)
```

```python
dicts = []

for pcode, group in compare.groupby("ADM3_PCODE"):
    corr = (
        group[["total_exposed", "level"]].corr().loc["level", "total_exposed"]
    )
    # dicts
```

```python
corr
```

```python
exp_max_mean
```

```python
adm3
```

```python
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax = adm3.merge(exp_max_mean, on="ADM3_PCODE").plot(
    column="fs_roll3", cmap="Purples", ax=ax, legend=True
)
adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
adm1.boundary.plot(ax=ax, color="k", linewidth=2)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
ax.axis("off")
ax.set_title("Population moyenne exposée aux inondations (1998-2023)")
```

```python
exp_max
```

```python
cerf_years = [2009, 2012, 2013, 2020]
vmax = exp_max[exp_max["time"].isin(cerf_years)]["fs_roll3"].max()

for year in cerf_years:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax = adm3.merge(exp_max.set_index("time").loc[year], on="ADM3_PCODE").plot(
        column="fs_roll3", cmap="Purples", ax=ax, legend=True, vmax=vmax
    )
    adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
    adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
    adm1.boundary.plot(ax=ax, color="k", linewidth=2)
    river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
    ax.axis("off")
    ax.set_title(f"Population exposée aux inondations ({year})")
```
