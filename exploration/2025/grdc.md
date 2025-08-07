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

# GRDC
<!-- markdownlint-disable MD013 -->
Debugging loading [GRDC](https://portal.grdc.bafg.de/applications/public.html?publicuser=PublicUser#dataDownload/Stations) data.

Replaced by functions in `src.datasources.grdc`

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import fsspec

import ocha_stratus as stratus
import xarray as xr

from src.constants import *
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/grdc/GRDC-Daily.nc"
```

```python
url = stratus.get_container_client().get_blob_client(blob_name).url
```

```python
fs = fsspec.filesystem("https")
```

```python
ds = xr.open_dataset(fs.open(url), engine="h5netcdf", chunks={})
```

```python
ds.compute()
```

```python

```

```python
df = ds.to_dataframe().reset_index()
```

```python
df
```

```python
df[df["station_name"].str.startswith("G")]
```

```python
garbekourou_id = 1234130
```

```python
cols = ["time", "runoff_mean"]
```

```python
dff = df[df["id"] == garbekourou_id][cols].dropna()
```

```python
dff.set_index("time").plot()
```

```python
ds
```

```python
ds.sel(id=garbekourou_id).to_dataframe().reset_index()[cols].copy()
```

```python

```
