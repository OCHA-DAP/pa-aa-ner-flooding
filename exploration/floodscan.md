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

# Floodscan

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import pandas as pd
import numpy as np
import plotly.express as px

from ochanticipy import create_country_config, CodAB

import utils
```

```python
adm1s = ["Dosso", "Tillabéri"]
country_config = create_country_config("ner")
codab = CodAB(country_config=country_config)
codab = codab.load(admin_level=3)
codab = codab[codab["adm_01"].isin(adm1s)]
codab = codab.set_crs(4326)
# codab = codab.set_index(utils.ID_COL)
GAYA = "NER003006003"
F1 = "NER003006003"
F2 = "NER003006005"
F3 = "NER003006004"
F4 = "NER003004008"
```

```python
# load raw data
ds = utils.read_raw_floodscan()
da = ds["SFED_AREA"]
```

```python
# load processed data
df = utils.load_processed_floodscan()
df["mean_cell_log"] = np.log(df["mean_cell"]).replace(
    [np.inf, -np.inf], np.nan
)
df["mean_cell_rolling5"] = df.groupby(utils.ID_COL)["mean_cell"].transform(
    lambda x: x.rolling(5).mean()
)
df = df.merge(codab[[utils.ID_COL, "adm_03"]], on=utils.ID_COL)
```

```python
# plot average for all adm3
df_plot = (
    df.groupby(["adm_03", "dayofseason"]).mean(numeric_only=True).reset_index()
)
fig = px.line(df_plot, x="dayofseason", y="mean_cell", color="adm_03")
fig.update_traces(line_width=1)
fig.update_layout(
    template="simple_white",
    showlegend=True,
    title="Inondations depuis 1998 à Dosso et Tillabéri<br><sup>Source: Floodscan</sup>",
    height=800,
)
fig.update_yaxes(title="Mesure de fraction inondée moyen", range=[0, 0.04])
fig.update_xaxes(title="Journée de saison (depuis 1 juin)")
fig.show()
```

```python
# plot by year for all adm3
years = [2020]
for year in years:
    df_plot = (
        df[df["seasonyear"] == year]
        .groupby(["adm_03", "dayofseason"])
        .mean(numeric_only=True)
        .reset_index()
    )
    px.line(df_plot, x="dayofseason", y="mean_cell", color="adm_03").show()
```

```python
# plot by adm3, average over all years
dff = df[df["dayofseason"] < 200]
df_plot = codab.merge(
    dff.groupby(["adm_03"]).mean(numeric_only=True), on="adm_03"
)

df_plot.plot(column="mean_cell")
```

```python
abn = utils.load_abn_niamey()
abn = utils.shift_to_floodseason(abn, use_index=True)
abn_peaks = utils.get_peak(abn, max_col="Water Level (cm)")
```

```python
# compare overall
compare = df.merge(abn, left_on=["date"], right_index=True)
compare.corr(numeric_only=True)["Water Level (cm)"]
compare
```

```python
# plot for Gaya

px.line(
    compare[compare[utils.ID_COL] == GAYA],
    x="dayofseason_x",
    y="mean_cell",
    color="seasonyear_x",
).show()

px.line(
    compare[compare[utils.ID_COL] == GAYA],
    x="dayofseason_x",
    y="Water Level (cm)",
    color="seasonyear_x",
).show()
```

```python
fs_cols = ["mean_cell", "min_cell", "max_cell", "mean_cell_log"]

for fs_col in fs_cols:
    df_peaks = utils.get_peak(df, max_col=fs_col)

    # check for correlations by adm3
    for adm3 in df_peaks[utils.ID_COL].unique():
        dff = df_peaks[df_peaks[utils.ID_COL] == adm3]
        fs_years = len(dff)
        dff = dff.merge(
            abn_peaks,
            left_on="seasonyear",
            right_on="seasonyear",
            suffixes=("_fs", "_abn"),
        )
        leadtime = (dff["dayofseason_abn"] - dff["dayofseason_fs"]).mean()
        corr = dff.drop(columns="seasonyear").corr(numeric_only=True)
        date_corr = corr.loc["dayofseason_fs", "dayofseason_abn"]
        level_corr = corr.loc[fs_col, "Water Level (cm)"]
        codab.loc[
            adm3,
            [
                "fs_years",
                f"{fs_col}_date_corr",
                f"{fs_col}_level_corr",
                f"{fs_col}_leadtime",
            ],
        ] = (
            fs_years,
            date_corr,
            level_corr,
            leadtime,
        )
```

```python
codab[(codab["fs_years"] >= 10)].mean(numeric_only=True)
```

```python
col = "mean_cell_level_corr"
codab[(codab["fs_years"] >= 10) & (codab[col] >= -10)].plot(
    column=col, legend=True
)
codab[(codab["fs_years"] >= 10) & (codab[col] >= 0)]
```

```python
compare = abn.merge(df_date, left_index=True, right_index=True)
compare.corr()
```

```python
compare_peaks = abn_peaks.merge(
    df_peaks,
    left_on="seasonyear",
    right_on="seasonyear",
    suffixes=("_abn", "_fs"),
)
compare_peaks
```

```python
compare_peaks.plot.scatter(x="dayofseason_abn", y="dayofseason_fs")
```

```python
norm = (compare - compare.min()) / (compare.max() - compare.min())
```

```python
norm[["mean_cell", "diff9"]].plot()
```

```python
date = "2020-06-01"

codab_plot = codab.merge(df_adm3, left_index=True, right_on=utils.ID_COL)
display(codab_plot)
codab_plot.plot(column="mean_cell")
```

```python
df.describe()
```

```python
ds
```

```python
da = ds["SFED_AREA"]
da = da.sel(time=date)
da = da.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
da = da.rio.write_crs(4326)
da = da.rio.clip(codab["geometry"], all_touched=True)
```

```python
da.plot()
```

```python

```
