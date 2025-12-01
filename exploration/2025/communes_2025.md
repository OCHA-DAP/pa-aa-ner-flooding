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

# Communes for 2025

Plotting communes for targeting in 2025 framework revision

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import unicodedata
import re
from io import BytesIO

import ocha_stratus as stratus
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from matplotlib.ticker import EngFormatter
from matplotlib.patches import Patch

from src.datasources import hydrosheds, codab, anadia
from src.blob_utils import PROJECT_PREFIX
```

```python
# just for loading old local file into blob
# gdf_river = hydrosheds.load_niger_river(local=True)
# blob_name = f"{PROJECT_PREFIX}/processed/hydrosheds/niger_river.shp"
# stratus.upload_shp_to_blob(gdf_river, blob_name)
```

```python
# codab.download_codab_to_blob()
```

```python
adm3 = codab.load_codab_from_blob(admin_level=3, aoi_only=True)
```

```python
adm3_all = codab.load_codab_from_blob(admin_level=3, aoi_only=False)
```

```python
adm3.plot()
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/hydrosheds/niger_river.shp"
gdf_river = stratus.load_shp_from_blob(blob_name)
```

```python
gdf_river.plot()
```

```python
river_aoi = gpd.sjoin(gdf_river, adm3_all, how="inner", predicate="intersects")
```

```python
adm3["niger_distance"] = (
    adm3.to_crs(3857).geometry.distance(gdf_river.to_crs(3857).union_all())
    / 1000
)
```

```python
d_thresh = 10
adm3["along_niger"] = adm3["niger_distance"] <= d_thresh

fig, ax = plt.subplots()

adm3[adm3["along_niger"]].plot(ax=ax)
river_aoi.plot(ax=ax, color="crimson")
```

```python
lon, lat = 2, 13.5
adm3["downstream"] = (
    (adm3.geometry.centroid.x > lon)
    & (adm3.geometry.centroid.y < lat)
    & (adm3["along_niger"])
)

fig, ax = plt.subplots()

adm3[adm3["downstream"]].plot(ax=ax)
river_aoi.plot(ax=ax, color="crimson")
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/hydrosheds/sirba_river_in_niger"
gdf_sirba = stratus.load_shp_from_blob(blob_name)
```

```python
gdf_sirba.plot()
```

```python
lon, lat = 1.5, 13.8
adm3["downstream_sirba"] = (
    (adm3.geometry.centroid.x > lon)
    & (adm3.geometry.centroid.y < lat)
    & (adm3["along_niger"])
)

fig, ax = plt.subplots()

adm3[adm3["downstream_sirba"]].plot(ax=ax)
gdf_sirba.plot(ax=ax, color="green")
river_aoi.plot(ax=ax, color="crimson")
```

```python
# for loading old ANADIA data
df_anadia_old = anadia.load_processed_anadia(from_blob=True)

df_anadia_old_grouped = (
    df_anadia_old.groupby("ADM3_PCODE").sum(numeric_only=True).reset_index()
)
```

```python
df_anadia_old_grouped
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/anadia/anadia_summary_2024.parquet"
df_anadia = stratus.load_parquet_from_blob(blob_name)
df_anadia_grouped = df_anadia.copy()
```

```python
df_anadia_grouped
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/ocha/Book1_fromDaniel.xlsx"
blob_data = stratus.load_blob_data(blob_name)

df_vuln = pd.read_excel(BytesIO(blob_data), skiprows=[0])
df_vuln = df_vuln.iloc[:-1]
df_vuln["Commune"] = df_vuln["Commune"].replace("Ayorou", "Ayerou")
df_vuln = df_vuln.merge(
    adm3.rename(columns={"ADM3_FR": "Commune"})[["Commune", "ADM3_PCODE"]]
)
int_cols = ["Vulnérables"]
df_vuln[int_cols] = df_vuln[int_cols].astype(int)
df_vuln
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/wfp/Communes_fleuve_niger.xlsx"
blob_data = stratus.load_blob_data(blob_name)
df_wfp = pd.read_excel(BytesIO(blob_data))
df_wfp["ADM3_PCODE"] = df_wfp["rowcacode3"].str.replace("R", "")
drop_cols = [
    "NOM_COM",
    "adm_01",
    "adm_02",
    "adm_03",
    "rowcacode1",
    "rowcacode2",
    "rowcacode3",
    "Shape_Leng",
    "Shape_Area",
    "ISO3",
    "ISO2",
]
df_wfp = df_wfp.drop(columns=drop_cols)
```

```python
def wfp_rang_to_class(rang):
    if rang <= 6:
        return 1
    elif rang <= 11:
        return 2
    elif rang <= 28:
        return 3
    else:
        return None


df_wfp["priorisation"] = df_wfp["Rang"].apply(wfp_rang_to_class)
```

```python
df_wfp
```

```python
cols = [x for x in adm3 if "ADM" in x] + [
    "along_niger",
    "downstream",
    "downstream_sirba",
]
df_combine = (
    adm3[cols]
    .merge(df_vuln, how="left")
    .merge(df_anadia_grouped, how="left")
    .merge(df_anadia_old_grouped, how="left")
    .merge(df_wfp, how="left")
)

drop_cols = ["N°", "Région", "Département", "Commune", "Communes", "idEvent"]
df_combine = df_combine.drop(columns=drop_cols).rename(
    columns={
        "along_niger": "sur_fleuve",
        "downstream": "aval_de_niamey",
        "downstream_sirba": "aval_de_sirba",
    }
)
df_combine
```

```python
df_combine.corr(numeric_only=True)["TOTAL"]
```

```python
cols = ["freqMoy1998-2024", "Vulnérables", "Personnes affectées", "TOTAL", ]
```

```python
ordered_priority = [
    "Première catégorie",
    "Deuxième catégorie",
    "Troisième catégorie",
    "Non classé",
]
priority_map = {
    1: "Première catégorie",
    2: "Deuxième catégorie",
    3: "Troisième catégorie",
    None: "Non classé",
}
color_map = {
    "Première catégorie": "green",
    "Deuxième catégorie": "gold",
    "Troisième catégorie": "crimson",
    "Non classé": "grey",
}
```

```python
def plot_targeting_scatter(xcol, ycol):
    fig, ax = plt.subplots(figsize=(7, 7), dpi=200)

    df_plot = df_combine[df_combine["sur_fleuve"]]
    df_plot.loc[:, [xcol, ycol]] = df_plot[[xcol, ycol]].fillna(0)
    df_plot.plot.scatter(y=ycol, x=xcol, ax=ax, marker="")

    legend_entries = {}
    for name, row in df_plot.set_index("ADM3_FR").iterrows():
        priority_word = priority_map.get(row["priorisation"], "Non classé")
        color = color_map[priority_word]
        zorder = 1 if priority_word != "Non classé" else 0
        fontweight = "bold" if row["aval_de_niamey"] else "normal"

        ax.annotate(
            name,
            row[[xcol, ycol]],
            rotation=45,
            fontsize=6,
            color=color,
            zorder=zorder,
            fontweight=fontweight,
            ha="center",
            va="center",
        )

        # Track legend entries
        if priority_word not in legend_entries:
            legend_entries[priority_word] = Patch(
                color=color, label=priority_word
            )
    ax.xaxis.set_major_formatter(EngFormatter(sep=""))
    ax.yaxis.set_major_formatter(EngFormatter(sep=""))

    ax.set_title(
        "Identification de communes dans Tillabéri et Dosso\n"
        "Noms en $\\bf{gras}$ : communes en aval du Sirba"
    )

    legend_patches = [
        legend_entries[p] for p in ordered_priority if p in legend_entries
    ]
    ax.legend(handles=legend_patches, title="Prioritisation PAM")

    [ax.spines[x].set_visible(False) for x in ["top", "right"]]
    return fig, ax
```

```python
fig, ax = plot_targeting_scatter("freqMoy1998-2024", "Vulnérables")
ax.set_xlabel("Fréquence moyenne des inondations (1998-2024)")
```

```python
fig, ax = plot_targeting_scatter("Maisons détruites", "Vulnérables")
ax.set_xlabel("Maisons détruites (total 1998-2020)")
```

```python
fig, ax = plot_targeting_scatter("Personnes affectées", "Vulnérables")
ax.set_xlabel("Personnes affectées (total 1998-2020)")
```

```python
fig, ax = plot_targeting_scatter("freqMoy1998-2024", "Maisons détruites")
ax.set_xlabel("Fréquence moyenne des inondations (1998-2024)")
ax.set_ylabel("Maisons détruites (total 1998-2020)")
```

```python
fig, ax = plt.subplots(dpi=300)

gdf_plot = adm3[["ADM3_PCODE", "geometry"]].merge(
    df_combine[df_combine["sur_fleuve"]]
)

gdf_plot.boundary.plot(ax=ax, linewidth=0.5, color="k")

for name, row in gdf_plot.set_index("ADM3_FR").iterrows():
    ax.annotate(
        name,
        (row["geometry"].centroid.x, row["geometry"].centroid.y),
        ha="center",
        va="center",
        fontsize=4,
        rotation=45,
    )

river_aoi.plot(ax=ax, color="dodgerblue")
gdf_sirba.plot(ax=ax, color="green")
ax.axis("off")
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/targeting_2025.csv"
stratus.upload_csv_to_blob(df_combine, blob_name)
```

```python
def remove_accents(text):
    if isinstance(text, str):
        return "".join(
            c
            for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )
    return text


def normalize_df(df):
    # Remove accents from column names
    df.columns = [remove_accents(col) for col in df.columns]

    # Remove accents from string entries in object or string columns
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].apply(remove_accents)

    return df
```

```python
# remove accents because this messses up some CSVs
df_combine_clean = normalize_df(df_combine)
df_combine_clean
```

```python
filename = "targeting_2025_clean.csv"
savepath = f"temp/{filename}"
df_combine_clean.to_csv(savepath, index=False)

blob_name = f"{PROJECT_PREFIX}/processed/{filename}"
stratus.upload_csv_to_blob(df_combine_clean, blob_name)
```

```python

```
