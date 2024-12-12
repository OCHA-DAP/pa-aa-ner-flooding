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

# ABN

Les données historiques de la station Niamey

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import os
from pathlib import Path

from dotenv import load_dotenv
import datetime
import xarray as xr
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import utils

from ochanticipy import (
    create_country_config,
    CodAB,
    GeoBoundingBox,
    GlofasForecast,
    GlofasReanalysis,
    GlofasReforecast,
)

# pio.renderers.default = "notebook"
```

```python
# load and get maxima
df = utils.load_combined_abn()
df = utils.shift_to_floodseason(df)
df_max = utils.get_peak(
    df, max_col="Water Level (cm)", agg_col="station", date_col="date"
)
```

```python
# plot average by station
df_plot = df.groupby(["station", "dayofseason"]).mean().reset_index()
px.line(df_plot, x="dayofseason", y="Water Level (cm)", color="station").show()
```

```python
# plot yearly for station
station = "Garbe Kourou"
df_plot = df[df["station"] == station]
px.line(
    df_plot, x="dayofseason", y="Water Level (cm)", color="seasonyear"
).show()
```

```python
px.scatter(
    df.sort_values("Discharges (m3/s)"),
    y="Water Level (cm)",
    x="Discharges (m3/s)",
    color="station",
)
```

```python
value_col = "Water Level (cm)"
year_col = "seasonyear"
agg_col = "station"
quants = np.linspace(0, 1, 101)

df_return_periods = pd.DataFrame()
df_count_yearly = pd.DataFrame()

return_years = [1.5, 2, 3, 5, 10]

for station in df_max[agg_col].unique():
    dff = df_max[df_max[agg_col] == station].set_index(year_col)[value_col]
    levels = dff.quantile(quants)
    total_years = len(dff)
    for level in levels:
        dfff = dff[dff >= level]
        years = "<br>".join(
            [str(x) for x in dfff.sort_index(ascending=False).index]
        )
        count = len(dfff)
        df_add = pd.DataFrame(
            {
                agg_col: station,
                value_col: level,
                "count": count,
                f"{year_col}s": years,
                "return": total_years / count,
            },
            index=[0],
        )
        df_count_yearly = pd.concat(
            [df_count_yearly, df_add], ignore_index=True
        )

    df_i = df_count_yearly[df_count_yearly[agg_col] == station]
    df_i = df_i.sort_values(value_col, ascending=True)
    # interpolate to find precise return periods
    interp = np.interp(return_years, df_i["return"], df_i[value_col])
    for index, return_year in enumerate(return_years):
        # but, if exact value in return periods, take lowest value
        if return_year in df_i["return"].values:
            lower_value = df_i[df_i["return"] == return_year].iloc[0][
                value_col
            ]
            interp[index] = lower_value

    df_add = pd.DataFrame()
    df_add[value_col] = interp
    df_add["return_period"] = return_years
    df_add[agg_col] = station
    df_return_periods = pd.concat(
        [df_return_periods, df_add], ignore_index=True
    )

df_return_periods = df_return_periods.set_index(["return_period", agg_col])
```

```python
for station in df_max[agg_col].unique():
    min_year = df_max[df_max["station"] == station]["date"].min().year
    df_plot = df_count_yearly[df_count_yearly[agg_col] == station]
    x_max = 10
    y_max = df_plot[df_plot["return"] <= x_max][value_col].max()
    y_min = df_plot[value_col].min()
    fig = px.line(df_plot, x="return", y=value_col)

    for year in return_years[:-1]:
        level = df_return_periods.loc[year, station].values[0]
        fig.add_trace(
            go.Scatter(
                x=[1, x_max * 0.8],
                y=[level, level],
                mode="lines+text",
                text=[None, f" {year}-ans = {level:.0f} cm"],
                line=dict(width=1, dash="dot", color="black"),
                textposition="middle right",
            )
        )

    fig.update_xaxes(range=(1, x_max), title="Période de retour (ans)")
    fig.update_yaxes(range=(y_min, y_max), title="Niveau d'eau (cm)")

    fig.update_layout(
        template="simple_white",
        title=f"{station} période de retour (depuis {min_year})",
        showlegend=False,
        width=800,
    )
    fig.show()
```

## Comparison with GloFAS

```python
# load GloFAS reanalysis

start_date = df_abn.index.min().date()
end_date = df_abn.index.max().date()

g_re = GlofasReanalysis(
    country_config=country_config,
    geo_bounding_box=geobb,
    start_date=start_date,
    end_date=end_date,
)
g_re.download()
g_re.process()
ds = g_re.load()
df_re = ds.to_dataframe()["Niamey"]
```

```python
df_re
```

```python
# GloFAS 4.0 reanalysis

g_re4 = GlofasReanalysis(
    country_config=country_config,
    geo_bounding_box=geobb,
    start_date=datetime.date(2020, 1, 1),
    end_date=datetime.date(2020, 12, 31),
)
g_re4.process()
da = g_re4.load()
df_re4 = da.to_dataframe()
df_re4
```

```python
df_compare = df_abn.merge(df_re, left_index=True, right_index=True)
df_compare = df_compare.merge(
    df_re4, left_index=True, right_index=True, suffixes=["3", "4"]
)
df_compare
```

```python
# compare with GloFAS analysis

fig = go.Figure()
fig.update_layout(template="simple_white", title="Comparaison à Niamey")
fig.add_trace(
    go.Scatter(
        x=df_compare.index,
        y=df_compare["Discharges (m3/s)"],
        name="Observé (ABN)",
    )
)
fig.add_trace(
    go.Scatter(x=df_compare.index, y=df_compare["Niamey3"], name="GloFAS 3.1")
)
fig.add_trace(
    go.Scatter(x=df_compare.index, y=df_compare["Niamey4"], name="GloFAS 4.0")
)

ymax = df_compare[["Niamey3", "Niamey4", "Discharges (m3/s)"]].max().max()
fig.update_yaxes(title="Débit (m<sup>3</sup>/s)", range=[0, ymax * 1.1])


fig.show()

fig = go.Figure()
fig.update_layout(template="simple_white")
fig.add_trace(
    go.Scatter(
        x=df_compare["Water Level (cm)"],
        y=df_compare["Niamey4"],
        name="GloFAS",
        mode="markers",
    )
)
fig.show()
```

```python
df_compare.corr()
```

```python
df_re4.plot()
```

```python

```
