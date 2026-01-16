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

# GFM

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from io import BytesIO

import ocha_stratus as stratus
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from src.datasources import codab
from src.constants import *
```

```python
adm3 = codab.load_codab_from_blob(admin_level=3)
```

```python
adm3.plot()
```

```python
adm3["target"] = adm3["ADM3_PCODE"].isin(ADM3_AOI_PCODES_2025)
```

```python
gfm_date_str = "2026-01-11"
```

```python
blob_name = f"ds-flood-gfm/processed/exposed_population/ner_flooding_adm3s_{gfm_date_str.replace('-', '')}_cumulative_b100.csv"
df_exp = stratus.load_csv_from_blob(blob_name)
```

```python
df_exp = df_exp.rename(columns={"adm3_src": "ADM3_PCODE"})
```

```python
df_exp["target"] = df_exp["ADM3_PCODE"].isin(ADM3_AOI_PCODES_2025)
```

```python
df_exp["target"].sum()
```

```python
df_exp["color"] = df_exp["target"].map({True: "crimson", False: "grey"})
```

```python
df_exp = df_exp.sort_values("pop_exposed")
```

```python
df_exp
```

```python
cutoff = df_exp[df_exp["target"]]["pop_exposed"].min()
if cutoff == 0:
    cutoff = 1
```

```python
cutoff
```

```python
def french_thousands(x, pos):
    return f"{int(x):,}".replace(",", "\u202f")
```

```python
fig, ax = plt.subplots(dpi=200)

df_plot = df_exp[df_exp["pop_exposed"] >= cutoff]

colors = df_plot["target"].map({True: "crimson", False: "grey"})

df_plot.plot.bar(
    x="adm3_name", y="pop_exposed", color=colors, ax=ax, legend=False
)

xtick_labels = ax.get_xticklabels()
for label, color in zip(xtick_labels, colors):
    label.set_color(color)

ax.yaxis.set_major_formatter(FuncFormatter(french_thousands))
[ax.spines[x].set_visible(False) for x in ["top", "right"]]

ax.set_title(
    f"Fleuve Niger : exposition aux inondations estimée\nDate : {gfm_date_str}\nSource : GloFAS GFM"
)
ax.set_xlabel("Commune")
```

```python

```
