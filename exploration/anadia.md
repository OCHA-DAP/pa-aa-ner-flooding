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

# ANADIA

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.datasources import codab, anadia, floodscan, hydrosheds, abn
from src.utils import shift_to_floodseason
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
fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
adm3.boundary.plot(ax=ax, linewidth=0.1, color="k")
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
adm1.boundary.plot(ax=ax, color="k", linewidth=2)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
for index, row in adm3.iterrows():
    centroid = row["geometry"].centroid
    ax.annotate(
        row["ADM3_FR"],
        xy=(centroid.x, centroid.y),
        xytext=(0, 0),
        textcoords="offset points",
        ha="center",
        va="center",
        fontsize=6,
    )

ax.axis("off")
```

```python
impact = anadia.load_processed_anadia()
impact = impact.rename(columns={"Maisons détruites": "destroyed"})
```

```python
impact["date"].dt.year.value_counts()
```

```python
years = range(2006, 2021)
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "time", "Water Level (cm)": "level"})
level = shift_to_floodseason(level, date_col="time")
# drop duplicates due to leapyears (just on Jan 1)
level = level[~level.duplicated(subset=["dayofseason", "seasonyear"])]
# keep only full seasons
level = level[level["seasonyear"].isin(range(2005, 2022))]
# take first chunk of season
level_first = level[level["dayofseason"] < 153]
level_max = (
    level_first.groupby("seasonyear")["level"]
    .max()
    .reset_index()
    .rename(columns={"seasonyear": "year"})
)
level_max["activate"] = level_max["level"] > 580

level_max_years = level_max[level_max["year"].isin(years)]
```

```python
level_max_years
```

```python
19 / 7
```

```python
7 / 19
```

```python
level_max_years.plot(x="year", y="level")
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
exp_max = (
    exp.groupby([exp["time"].dt.year, "ADM3_PCODE"])
    .max()
    .drop(columns="time")
    .reset_index()
    .rename(columns={"time": "year"})
)
exp_max_years = exp_max[exp_max["year"].isin(years)]
exp_max_years
```

```python
exp_max_years_mean
```

```python
impact_sum = (
    impact.groupby([impact["date"].dt.year, impact["ADM3_PCODE"]])["destroyed"]
    .sum()
    .reset_index()
    .rename(columns={"date": "year"})
)
impact_sum_years = impact_sum[impact_sum["year"].isin(years)]
```

```python
compare
```

```python
impact_sum_years["year"].nunique()
```

```python
impact_sum_years.groupby("year").sum()["destroyed"].plot()
```

```python
compare = impact_sum_years.merge(
    exp_max_years, on=["year", "ADM3_PCODE"], how="right"
)
compare = compare.merge(level_max_years, on="year")
compare["destroyed"] = compare["destroyed"].fillna(0).astype(int)
compare
```

```python
def is_worst_third(group):
    q = group["destroyed"].quantile(q=2 / 3)
    group["worst_third"] = group["destroyed"] > q
    # print(group)
    return group.drop(columns="ADM3_PCODE")


compare = (
    compare.groupby("ADM3_PCODE")
    .apply(is_worst_third)
    .reset_index()
    .drop(columns="level_1")
)
compare["TP"] = compare["activate"] & compare["worst_third"]
compare["FP"] = compare["activate"] & ~compare["worst_third"]
compare["TN"] = ~compare["activate"] & ~compare["worst_third"]
compare["FN"] = ~compare["activate"] & compare["worst_third"]
compare
```

```python
impact_sum_years_mean = (
    compare.groupby("ADM3_PCODE")
    .mean()[["destroyed", "fs_roll3"]]
    .reset_index()
)
```

```python
dicts = []
for pcode, group in compare.groupby("ADM3_PCODE"):
    corr = group.drop(columns=["year", "ADM3_PCODE", "total_exposed"]).corr()[
        "destroyed"
    ]
    P = group["worst_third"].sum()
    TP = group["TP"].sum()
    TPR = TP / P
    dicts.append(
        {
            "ADM3_PCODE": pcode,
            "exp_corr": corr["fs_roll3"],
            "level_corr": corr["level"],
            "TPR": TPR,
        }
    )


all_corr = pd.DataFrame(dicts)
all_corr = all_corr.merge(impact_sum_years_mean, on="ADM3_PCODE")
all_corr = all_corr.sort_values("destroyed", ascending=False)
```

```python
all_corr.plot(x="destroyed", y="TPR", linestyle="", marker=".")
```

```python

```

```python
for pcode in all_corr["ADM3_PCODE"].iloc[:5]:
    name = adm3[adm3["ADM3_PCODE"] == pcode]["ADM3_FR"].iloc[0]
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
    compare_f = compare[compare["ADM3_PCODE"] == pcode]
    compare_f.plot(
        x="level",
        y="destroyed",
        ax=ax,
        marker=".",
        linestyle="",
        color="k",
        legend=False,
    )
    for idx, row in compare_f.iterrows():
        ax.annotate(
            f' {row["year"]}',
            (row["level"], row["destroyed"]),
            ha="left",
            va="bottom",
            fontsize=8,
        )

    level_t = 580
    ax.axvline(x=level_t, color="dodgerblue", linestyle="-", linewidth=0.3)
    ax.axvspan(
        level_t,
        720 + 1,
        ymin=0,
        ymax=1,
        color="dodgerblue",
        alpha=0.1,
    )

    q = compare_f["destroyed"].quantile(q=2 / 3)
    ax.axhline(y=q, color="red", linestyle="-", linewidth=0.3)
    ax.axhspan(
        q,
        compare_f["destroyed"].max() * 1.2,
        color="red",
        alpha=0.05,
        linestyle="None",
    )

    ax.set_xlabel("Niveau d'eau à Niamey maximum (cm)")
    ax.set_ylabel("Maisons détruites")
    ax.set_title(name)
    ax.set_ylim(bottom=0, top=compare_f["destroyed"].max() * 1.1)
    ax.set_xlim(right=720)
    # ax.spines["top"].set_visible(False)
    # ax.spines["right"].set_visible(False)
```

```python
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax = adm3.merge(impact_sum_years_mean, on="ADM3_PCODE").plot(
    column="destroyed", cmap="Reds", ax=ax, legend=True
)
adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
adm1.boundary.plot(ax=ax, color="k", linewidth=2)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
ax.axis("off")
ax.set_title("Moyenne de maisons détruites par inondations (2006-2020)")
```

```python
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
adm3.merge(all_corr.iloc[:20], on="ADM3_PCODE").plot(
    column="TPR", vmin=0, vmax=1, legend=True, ax=ax
)
adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
adm1.boundary.plot(ax=ax, color="k", linewidth=2)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
ax.axis("off")
ax.set_title(
    "Taux de réussite de niveau du fleuve contre maisons détruites\n"
    "20 communes les plus touchées"
)
```

```python
admin_names = {
    "ADM1_FR": "Région",
    "ADM2_FR": "Département",
    "ADM3_FR": "Commune",
}
var_names = {
    "TPR": "Taux de réussite (%)",
    "destroyed": "Maisons détruites",
    "fs_roll3": "Population exposée",
}

df_disp = (
    all_corr.merge(adm3[["ADM3_FR", "ADM3_PCODE", "ADM2_FR", "ADM1_FR"]])
    .sort_values("destroyed", ascending=False)
    .drop(columns=["ADM3_PCODE", "exp_corr", "level_corr"])
    .iloc[:20]
)
df_disp = df_disp[
    ["ADM1_FR", "ADM2_FR", "ADM3_FR", "destroyed", "fs_roll3", "TPR"]
]
df_disp["destroyed"] = df_disp["destroyed"].astype(int)
df_disp["TPR"] = df_disp["TPR"] * 100
int_cols = ["destroyed", "fs_roll3", "TPR"]
df_disp[int_cols] = df_disp[int_cols].astype(int)
df_disp = df_disp.rename(columns=admin_names | var_names)
df_disp.style.background_gradient(cmap="Blues")
```

```python
df_save = (
    all_corr.merge(adm3[["ADM3_FR", "ADM3_PCODE", "ADM2_FR", "ADM1_FR"]])
    .sort_values("destroyed", ascending=False)
    .drop(columns=["exp_corr", "level_corr"])
)
df_save = df_save[
    [
        "ADM3_PCODE",
        "ADM1_FR",
        "ADM2_FR",
        "ADM3_FR",
        "destroyed",
        "fs_roll3",
        "TPR",
    ]
]
df_save["destroyed"] = df_save["destroyed"].astype(int)
df_save["TPR"] = df_save["TPR"] * 100
df_save = df_save.dropna()
int_cols = ["destroyed", "fs_roll3", "TPR"]
df_save[int_cols] = df_save[int_cols].astype(int)
df_save = df_save.rename(columns=admin_names | var_names)

filename = "ner-ciblage-communes.xlsx"
df_save.to_excel(floodscan.PROC_FS_DIR / filename, index=False)
```

```python
admin_names = {
    "ADM1_FR": "Région",
    "ADM2_FR": "Département",
    "ADM3_FR": "Commune",
}
var_names = {
    "TPR": "Taux de réussite (%)",
    "destroyed": "Maisons détruites",
    "fs_roll3": "Population exposée",
}

df_disp = (
    all_corr.merge(adm3[["ADM3_FR", "ADM3_PCODE", "ADM2_FR", "ADM1_FR"]])
    .sort_values("destroyed", ascending=False)
    .drop(columns=["ADM3_PCODE", "exp_corr", "level_corr"])
    .iloc[:20]
)
df_disp = df_disp[["ADM1_FR", "ADM2_FR", "ADM3_FR", "destroyed"]]
df_disp["destroyed"] = df_disp["destroyed"].astype(int)
int_cols = ["destroyed"]
df_disp[int_cols] = df_disp[int_cols].astype(int)
df_disp = df_disp.rename(columns=admin_names | var_names)
df_disp.style.background_gradient(cmap="Reds", vmin=0)
```

```python
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax = adm3.merge(impact_sum_years_mean, on="ADM3_PCODE").plot(
    column="destroyed", cmap="Reds", ax=ax, legend=True
)
adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
adm1.boundary.plot(ax=ax, color="k", linewidth=2)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
ax.axis("off")
ax.set_title("Moyenne de maisons détruites par inondations (2006-2020)")
```

```python
cerf_years = [2009, 2012, 2013, 2020]
vmax = impact_sum[impact_sum["year"].isin(cerf_years)]["destroyed"].max()

for year in cerf_years:
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax = adm3.merge(
        impact_sum.set_index("year").loc[year], on="ADM3_PCODE"
    ).plot(column="destroyed", cmap="Reds", ax=ax, legend=True, vmax=vmax)
    adm3.boundary.plot(ax=ax, color="k", linewidth=0.1)
    adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
    adm1.boundary.plot(ax=ax, color="k", linewidth=2)
    river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
    ax.axis("off")
    ax.set_title(year)
```
