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

# River admin

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

from src.datasources import codab
from src.constants import *
```

```python
adm3 = codab.load_codab_from_blob(admin_level=3)
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/hydrosheds/niger_river.shp"
gdf_river = stratus.load_shp_from_blob(blob_name)
```

```python
gdf_river.crs
```

```python
river_aoi = gpd.sjoin(gdf_river, adm3, how="inner", predicate="intersects")
```

```python
river_aoi.plot()
```

```python
distance = 20
```

```python
gdf_river_buffer = river_aoi.to_crs(3857).buffer(distance * 1000).to_crs(4326)
```

```python
gdf_river_buffer.plot()
```

```python
gdf_river_buffer.union_all()
```

```python
adm3_clipped = gpd.clip(adm3, gdf_river_buffer.union_all())
```

```python
adm3["target"] = adm3["ADM3_PCODE"].isin(ADM3_AOI_PCODES_2025)
```

```python
adm3["target"].sum()
```

```python
row.geometry.centroid.x
```

```python
fig, ax = plt.subplots(dpi=200, figsize=(8, 8))

adm3.boundary.plot(ax=ax, linewidth=0.5, color="k")

adm3_clipped.plot(ax=ax, linewidth=0, color="dodgerblue", alpha=0.2)
river_aoi.plot(ax=ax, color="dodgerblue")

adm3[adm3["target"]].plot(linewidth=0, color="crimson", alpha=0.2, ax=ax)

for _, row in adm3[adm3["target"]].iterrows():
    c = row.geometry.centroid
    ax.annotate(
        row["ADM3_FR"],
        (c.x, c.y),
        va="center",
        ha="center",
        color="crimson",
        fontsize=8,
    )

ax.set_xlim(0.1, 3.7)
ax.set_ylim(11.6, 15.5)
ax.axis("off")
ax.set_title(f"Communes ciblées\nFleuve Niger avec tampon de {distance} km")
```

```python
adm3_clipped.plot()
```

```python
for adm_level in [1, 2, 3]:
    adm3_clipped[f"adm{adm_level}_id"] = adm3_clipped[f"ADM{adm_level}_PCODE"]
    adm3_clipped[f"adm{adm_level}_src"] = adm3_clipped[f"ADM{adm_level}_PCODE"]
    adm3_clipped[f"adm{adm_level}_name"] = adm3_clipped[f"ADM{adm_level}_FR"]
```

```python
adm3_clipped
```

```python
def upload_geoparquet_to_blob(gdf, blob_name, stage="dev"):
    buffer = BytesIO()
    gdf.to_parquet(buffer, index=False)
    buffer.seek(0)
    stratus.upload_blob_data(
        data=buffer.getvalue(),
        blob_name=blob_name,
        stage=stage,
    )
```

```python
blob_name = (
    f"{PROJECT_PREFIX}/processed/codab/adm3_river_buffer_{distance}km.parquet"
)
upload_geoparquet_to_blob(adm3_clipped, blob_name)
```

```python
blob_name
```

```python

```
