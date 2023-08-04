---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.7
  kernelspec:
    display_name: pa-aa-ner-flooding
    language: python
    name: pa-aa-ner-flooding
---

# ABN

Les données historiques de la station Niamey

```python
%load_ext jupyter_black
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

from ochanticipy import (
    create_country_config,
    CodAB,
    GeoBoundingBox,
    GlofasForecast,
    GlofasReanalysis,
    GlofasReforecast,
)

pio.renderers.default = "notebook"
```

```python
load_dotenv()

RAW_DIR = Path(os.environ["OAP_DATA_DIR"]) / "public/raw/ner"
ABN_PATH = RAW_DIR / "abn/Données_ Niamey2005_2022.xlsx"

adm1_sel = ["Tillabéri", "Niamey", "Dosso", "Maradi"]
startdate = datetime.date(2005, 1, 1)
enddate = datetime.date(2024, 1, 1)

country_config = create_country_config(iso3="ner")
codab = CodAB(country_config=country_config)
gdf_adm1 = codab.load(admin_level=1)
gdf_aoi = gdf_adm1[gdf_adm1["adm_01"].isin(adm1_sel)]
geobb = GeoBoundingBox.from_shape(gdf_aoi)
```

```python
# read ABN data
# note - this is originally from Niger-HYCOS

df_abn = pd.read_excel(ABN_PATH, skiprows=[0, 1], index_col=0)
df_abn
```

```python
fig = px.line(df_abn, y="Water Level (cm)")
fig.update_layout(template="simple_white")
fig.show()
```

```python
df_plot = df_abn.copy()
df_plot["year"] = df_abn.index.year
px.scatter(
    df_abn, x="Discharges (m3/s)", y="Water Level (cm)", color="year"
).show()
```

```python
df_abn.corr(method="pearson")
```

```python
# calculate return

df_max = df_abn.groupby(df_abn.index.year)["Water Level (cm)"].max()
total_years = len(df_max)

return_years = [1.5, 2, 3, 5, 10]

df_count_yearly = pd.DataFrame()
df_return_periods = pd.DataFrame(index=return_years)

dff = df_max
print(dff)
quants = np.linspace(0, 1, 101)
levels = dff.quantile(quants)
#     print(levels)
for level in levels:
    dfff = dff[dff >= level]
    years = "<br>".join(
        [str(x) for x in dfff.sort_index(ascending=False).index]
    )
    count = len(dfff)
    df_add = pd.DataFrame(
        {
            "level": level,
            "count": count,
            "years": years,
            "return": total_years / count,
        },
        index=[0],
    )
    df_count_yearly = pd.concat([df_count_yearly, df_add], ignore_index=True)
df_i = df_count_yearly
df_return_periods["level"] = np.interp(
    return_years, df_i["return"], df_i["level"]
)

df_count_yearly["return"] = len(df_max) / df_count_yearly["count"]
```

```python
df_count_yearly
```

```python
# plot return period station

df_plot = df_count_yearly

min_year = df_abn.index.year.min()

x_max = 10
y_max = df_plot[df_plot["return"] <= x_max]["level"].max()
y_min = df_plot["level"].min()
fig = px.line(df_plot, x="return", y="level")

for year in return_years:
    level = df_return_periods.loc[year, "level"]
    fig.add_trace(
        go.Scatter(
            x=[1, x_max],
            y=[level, level],
            mode="lines+text",
            text=[None, f"{year}-year"],
            line=dict(width=1, dash="dash", color="black"),
            textposition="top left",
        )
    )

fig.update_xaxes(range=(1, x_max), title="Return period (years)")
fig.update_yaxes(
    range=(y_min, y_max), title="One-day flow rate (m<sup>3</sup>/s)"
)

fig.update_layout(
    template="simple_white",
    title=f"ABN période de retour (depuis {min_year})",
    showlegend=False,
)
```

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
