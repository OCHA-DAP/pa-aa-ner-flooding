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

# Priorization de communes

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from src.datasources import ocha, codab, floodscan, hydrosheds
```

```python
adm3 = codab.load_codab(admin_level=3, aoi_only=True)
adm1 = codab.load_codab(admin_level=1, aoi_only=True)
```

```python
river = hydrosheds.load_niger_river()
river_aoi = gpd.sjoin(river, adm3, how="inner", predicate="intersects")
```

```python
adm3[adm3["ADM3_FR"] == "Sinder"]
```

```python
ciblage = floodscan.load_ciblage()
```

```python
ciblage["commune"] = ciblage["Commune"].str.lower()
```

```python
ciblage["commune"].sort_values().unique()
```

```python
df = ocha.load_communes()
df = df.fillna(0)
for col in [col for col in df.columns if df[col].dtype == float]:
    df[col] = df[col].astype(int)

df["commune"] = df["COMMUNE"].str.lower()
df = df.merge(ciblage, how="left").drop(
    columns=["commune", "DEPARTEMENT", "COMMUNE"]
)

agences_cols = [
    "PAM",
    "FAO",
    "UNICEF",
    "PNUD",
    "OMS",
    "UNFPA",
    "HCR",
    "OIM",
    "SAP",
    "CRN",
    "DMN",
    "BM",
]
df["agences_total"] = df[agences_cols].sum(axis=1)

quartile_labels = [0, 1, 2, 3]
df["score_acces"] = df["Acces"]
df["score_agences"] = pd.qcut(
    df["agences_total"], q=4, labels=quartile_labels
).astype(int)
df["score_impact"] = pd.qcut(
    df["Maisons détruites"], q=4, labels=quartile_labels
).astype(int)
score_cols = [x for x in df.columns if "score" in x]
df["score_total"] = df[score_cols].sum(axis=1)
df = df.sort_values("score_total", ascending=False)
first_cols = ["ADM3_PCODE", "Département", "Commune", "Région"]
cols = first_cols + [x for x in df.columns if x not in first_cols]
df = df[cols]
```

```python
filename = "ner-ciblage-communes_avec-agences.xlsx"
df.to_excel(floodscan.PROC_FS_DIR / filename, index=False)
```

```python
fig, ax = plt.subplots(dpi=300)
adm3.merge(df).plot(column="score_total", cmap="RdYlGn", legend=True, ax=ax)
river_aoi.plot(ax=ax, color="dodgerblue", linewidth=1)
adm1.boundary.plot(ax=ax, linewidth=0.5, color="k")
ax.axis("off")
```

```python

```
