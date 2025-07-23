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

# Framework communes accuracy

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import matplotlib.pyplot as plt

from src.datasources import codab, anadia, abn
from src.constants import *
from src.utils import shift_to_floodseason_corrected
```

```python
adm3 = codab.load_codab(admin_level=3, aoi_only=True)
adm3_aoi = adm3[adm3["ADM3_PCODE"].isin(ADM3_AOI_PCODES)]
```

```python
impact = anadia.load_processed_anadia()
impact = impact.rename(columns={"Maisons détruites": "destroyed"})
impact_aoi = impact[impact["ADM3_PCODE"].isin(ADM3_AOI_PCODES)].copy()
```

```python
impact_aoi["year"].max()
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "date", "Water Level (cm)": "level"})
level = shift_to_floodseason_corrected(level)
level = level[level["seasonyear"].isin(range(2005, 2022))]
peaks = level.groupby("seasonyear")["level"].max().reset_index()
```

```python
peaks
```

```python
impact_aoi = shift_to_floodseason_corrected(impact_aoi)
```

```python
impact_aoi
```

```python
# impact_year = (
#     impact_aoi.groupby(["seasonyear"])["destroyed"].sum().reset_index()
# )
impact_year = impact_aoi.groupby(["year"])["destroyed"].sum().reset_index()
```

```python
impact_year.sort_values("year")
```

```python
compare = impact_year.merge(
    peaks.rename(columns={"seasonyear": "year"})
).fillna(0)
# compare = (
#     impact_year.rename(columns={"seasonyear": "year"})
#     .merge(peaks.rename(columns={"seasonyear": "year"}), how="right")
#     .fillna(0)
# )
```

```python
q = impact_year["destroyed"].quantile(q=2 / 3 + 0.01)
```

```python
q
```

```python
impact_year[impact_year["destroyed"] > q]
```

```python
13 / 4
```

```python
compare = compare[(compare["year"] < 2021) & (compare["year"] >= 2010)]
```

```python
compare
```

```python
fig, ax = plt.subplots(dpi=300)

compare.plot(
    x="level",
    y="destroyed",
    ax=ax,
    marker=".",
    linestyle="",
    color="k",
    legend=False,
)
for idx, row in compare.iterrows():
    ax.annotate(
        f' {int(row["year"])}',
        (row["level"], row["destroyed"]),
        ha="left",
        va="bottom",
        fontsize=8,
        color="black",
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

q = impact_year["destroyed"].quantile(q=2 / 3 + 0.01)
ax.axhline(y=q, color="red", linestyle="-", linewidth=0.3)
ax.axhspan(
    q,
    compare["destroyed"].max() * 1.2,
    color="red",
    alpha=0.05,
    linestyle="None",
)

for spine in ax.spines.values():
    spine.set_linewidth(0.5)

ax.set_xlabel("Niveau d'eau à Niamey maximum (cm)")
ax.set_ylabel("Maisons détruites,\ntotal à travers communes cibles du cadre")
ax.set_title("Comparaison d'impact et niveau d'eau (2010-2020)")
ax.set_ylim(bottom=0, top=compare["destroyed"].max() * 1.1)
ax.set_xlim(right=720)
```

```python
compare
```

```python
fig, ax = plt.subplots(dpi=300)

ax.axvspan(
    level_t,
    720 + 1,
    ymin=0,
    ymax=1,
    color="dodgerblue",
    alpha=1,
)
```

```python
(2020 - 2005 + 1) / 5
```

```python
peaks
```
