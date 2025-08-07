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

# Sirba river selection

Selecting Sirba river from HydroSheds

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import geopandas as gpd
import ocha_stratus as stratus

from src.datasources import hydrosheds, codab
from src.constants import *
```

```python
adm1 = codab.load_codab_from_blob(admin_level=1)
```

```python
adm1.plot()
```

```python
adm1_aoi = adm1[adm1["ADM1_PCODE"] == TILLABERI]
```

```python
adm1_aoi.plot()
```

```python
lat, lon = 13.738147, 1.615367
```

```python
gdf = hydrosheds.load_niger_system_rivers(local=True)
```

```python
gdf.plot()
```

```python
gdf_aoi = gpd.sjoin(gdf, adm1_aoi, how="inner", predicate="intersects")
```

```python
gdf_aoi.plot()
```

```python
gdf_aoi["DIS_AV_CMS"].hist()
```

```python
dis_thresh = 600
```

```python
gdf_niger = gdf_aoi[gdf_aoi["DIS_AV_CMS"] > dis_thresh]
gdf_niger.plot()
```

```python
gdf_aoi[gdf_aoi["DIS_AV_CMS"] < dis_thresh]["DIS_AV_CMS"].hist()
```

```python
dis_thresh_2 = 30
```

```python
gdf_aoi[
    (gdf_aoi["DIS_AV_CMS"] < dis_thresh)
    & (gdf_aoi["DIS_AV_CMS"] > dis_thresh_2)
].plot()
```

```python
gdf_aoi[gdf_aoi["DIS_AV_CMS"] > dis_thresh_2].plot()
```

```python
gdf_aoi[gdf_aoi["DIS_AV_CMS"] < dis_thresh_2]["DIS_AV_CMS"].hist()
```

```python
gdf_selected = gdf_aoi[
    (gdf_aoi["DIS_AV_CMS"] < dis_thresh)
    & (gdf_aoi["DIS_AV_CMS"] > dis_thresh_3)
]
```

```python
dis_thresh_3 = 10
ax = adm1_aoi.boundary.plot(color="k")
gdf_selected.plot(ax=ax)
gdf_niger.plot(ax=ax, color="crimson")
```

```python
lat_min, lat_max = 13, 14
```

```python
gdf_bounds = gdf_selected.copy()
gdf_bounds["min_lat"] = gdf_bounds.bounds.miny
gdf_bounds["max_lat"] = gdf_bounds.bounds.maxy
gdf_filtered = gdf_bounds[
    (gdf_bounds["min_lat"] >= lat_min) & (gdf_bounds["max_lat"] <= lat_max)
]
```

```python
gdf_filtered.plot()
```

```python
gdf_filtered
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/hydrosheds/sirba_river_in_niger"
stratus.upload_shp_to_blob(gdf_filtered, blob_name)
```

```python
gdf_aoi["MAIN_RIV"].unique()
```

```python
NIGER_MAINRIVER_ID
```

```python

```
