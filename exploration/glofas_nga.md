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

# GloFAS Nigeria

Downloading for Nigeria here because there is a problem with Anticipy in the
other virtualenvs.
I am not sure how to fix it quickly, so just using this installation to
download for other countries.

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import os
import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr
from tqdm.notebook import tqdm

from ochanticipy import (
    create_country_config,
    CodAB,
    GeoBoundingBox,
    GlofasForecast,
    GlofasReanalysis,
    GlofasReforecast,
)

from src.constants import *
```

```python
country_config = create_country_config("nga")
```

```python
DATA_DIR = Path(os.getenv("AA_DATA_DIR"))
CODAB_DIR = DATA_DIR / "public" / "raw" / "nga" / "cod_ab"
AOI_ADM1_PCODES = ["NG008", "NG036", "NG002"]
ADAMAWA = "NG002"


def load_codab(admin_level: int = 0, aoi_only: bool = False):
    filename = f"nga_admbnda_adm{admin_level}_osgof_20190417.shp"
    gdf = gpd.read_file(CODAB_DIR / filename)
    if aoi_only:
        gdf = gdf[gdf["ADM1_PCODE"].isin(AOI_ADM1_PCODES)]
    return gdf


codab = load_codab(admin_level=1, aoi_only=True)
adamawa = codab[codab["ADM1_PCODE"] == ADAMAWA]
```

```python
adamawa.plot()
```

```python
geobb = GeoBoundingBox.from_shape(adamawa)
```

```python
geobb
```

```python
startdate = datetime.date(1970, 1, 1)
end
```

```python
forecast = GlofasForecast(
    country_config=country_config,
    geo_bounding_box=geobb,
    leadtime_max=15,
    start_date=datetime.date(2023, 1, 1),
    end_date=datetime.date(2024, 1, 1),
)
```

```python
reforecast = GlofasReforecast(
    country_config=country_config,
    geo_bounding_box=geobb,
    leadtime_max=15,
    # start_date=startdate,
    # end_date=enddate,
)
```

```python
reforecast.download()
```

```python
forecast.
```

```python
reanalysis = GlofasReanalysis(
    country_config=country_config,
    geo_bounding_box=geobb,
    # start_date=startdate,
    # end_date=enddate,
)
```

```python
df = (
    da.sel(latitude=WUROBOKI_LAT, longitude=WUROBOKI_LON, method="nearest")
    .to_dataframe()
    .reset_index()[["time", "dis24"]]
)
df
```

```python
df.plot(x="time", y="dis24")
```

```python
df
```

```python
da.sel(
    latitude=slice(WUROBOKI_LAT + step, WUROBOKI_LAT - step),
    longitude=slice(WUROBOKI_LON - step, WUROBOKI_LON + step),
).isel(time=0)
```

```python
shift = 0
da.sel(
    latitude=WUROBOKI_LAT + shift,
    longitude=WUROBOKI_LON + shift,
    method="nearest",
).plot()
```

```python
ds.sel(latitude=9.35, longitude=12.75, method="nearest")["dis24"].plot()
```
