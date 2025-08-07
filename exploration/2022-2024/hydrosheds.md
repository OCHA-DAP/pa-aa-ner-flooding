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

# Hydrosheds

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import os
import fiona
import geopandas as gpd

from src.datasources import hydrosheds, codab
from src.constants import *
```

```python
adm3 = codab.load_codab(admin_level=3, aoi_only=True)
```

```python
gdf = hydrosheds.load_all_rivers()
```

```python
gdf_1 = gdf[gdf["ORD_CLAS"] == 1]
```

```python
gdf_2 = gdf[gdf["ORD_CLAS"] <= 2]
```

```python
gdf_1_0 = gdf_1[gdf_1["NEXT_DOWN"] == 0]
```

```python
gdf_1_0.sort_values("DIST_UP_KM", ascending=False)
```

```python
gdf_niger_only = gdf_1[gdf_1["MAIN_RIV"] == NIGER_MAINRIVER_ID]
```

```python
gdf_niger_only.plot()
```

```python
filename = "niger_river"
save_dir = hydrosheds.HS_PROC_DIR / filename
if not save_dir.exists():
    os.makedirs(save_dir)
gdf_niger_only.to_file(
    hydrosheds.HS_PROC_DIR / filename / f"{filename}.shp",
    driver="ESRI Shapefile",
)
```

```python
gdf_niger = gdf[gdf["MAIN_RIV"] == NIGER_MAINRIVER_ID]
```

```python
gdf_niger.plot()
```

```python
filename = "niger_system_rivers"
save_dir = hydrosheds.HS_PROC_DIR / filename
if not save_dir.exists():
    os.makedirs(save_dir)
gdf_niger.to_file(
    hydrosheds.HS_PROC_DIR / filename / f"{filename}.shp",
    driver="ESRI Shapefile",
)
```

```python
niger_aoi = gpd.sjoin(
    gdf_niger_only, adm3, how="inner", predicate="intersects"
)
```

```python
ax = adm3.plot(alpha=0.2)
niger_aoi.plot(ax=ax)
```
