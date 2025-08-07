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

# Garbe-Kourou analysis
<!-- markdownlint-disable MD013 -->

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt

from src.datasources import grdc, glofas
from src.constants import *
```

```python
station_name = "garbekourou"
```

```python
glofas.process_reanalysis(station_name=station_name)
```

```python
df_rea = glofas.load_reanalysis(station_name=station_name)
```

```python
df_rea
```

```python
df_gk = grdc.load_grdc(station_id=GARBEKOUROU_GRDC_ID)
```

```python
df_niamey = grdc.load_grdc(station_id=NIAMEY_GRDC_ID)
```

```python
df_niamey = df_niamey.rename(columns={"runoff_mean": "runoff_mean_niamey"})
```

```python
df_niamey
```

```python
df_compare = df_rea.merge(df_gk, how="outer").merge(df_niamey, how="outer")
```

```python
df_compare.corr()
```

```python
min_year = 1979
```

```python
df_compare = df_compare[df_compare["time"].dt.year >= min_year]
```

```python
df_plot = df_compare.copy()
for x in ["dis24", "runoff_mean", "runoff_mean_niamey"]:
    df_plot[f"{x}_rel"] = df_plot[x] / df_plot[x].max()

for year, group in df_plot.groupby(df_plot["time"].dt.year):
    fig, ax = plt.subplots(figsize=(10, 4))
    group.set_index("time").plot(ax=ax, y=[x for x in df_plot if "rel" in x])
    ax.set_ylim((0, 1))
    [ax.spines[x].set_visible(False) for x in ["top", "right"]]
```

```python
gk_drop_years = [
    1981,
    1991,
    1992,
    1993,
    1994,
    1996,
    1997,
    2000,
    2004,
    2005,
    2021,
]
```

```python

```

```python
df_peaks = (
    df_compare[df_compare["time"].dt.month < 11]
    .groupby(df_compare["time"].dt.year)
    .max()[["dis24", "runoff_mean", "runoff_mean_niamey"]]
    .reset_index(names="year")
)
```

```python
df_peaks = df_peaks[
    (~df_peaks["year"].isin(gk_drop_years)) & (df_peaks["year"] < 2025)
]
```

```python
df_peaks.corr()
```

```python
fig, ax = plt.subplots(figsize=(7, 7))

df_peaks.plot(x="runoff_mean", y="dis24", ax=ax, linewidth=0)

for year, row in df_peaks.set_index("year").iterrows():
    ax.annotate(year, row[["runoff_mean", "dis24"]], va="center", ha="center")
```

```python

```
