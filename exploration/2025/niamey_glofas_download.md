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

# Niamey download

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from tqdm.auto import tqdm

from src.datasources import glofas
```

```python
lon_guess, lat_guess = 2.075, 13.525
year = 2022
```

```python
glofas.download_reanalysis_year(
    lon=lon_guess,
    lat=lat_guess,
    year=year,
    pitch=0.5,
    clobber=True,
    centered=True,
)
```

```python
da_guess = glofas.load_reanalysis_year(
    data_type="raw", lon=lon_guess, lat=lat_guess, year=2022
)
```

```python
da_guess.mean(dim="time")["dis24"].plot()
```

```python
da_guess.mean(dim="time")["dis24"].plot(vmin=0, vmax=1)
```

```python
da_guess.sel(latitude=slice(13.55, 13.45), longitude=slice(2.0, 2.15)).mean(
    dim="time"
)["dis24"].plot(vmin=0, vmax=1)
```

```python
da_guess.sel(latitude=slice(13.55, 13.45), longitude=slice(2.0, 2.15)).mean(
    dim="time"
)["dis24"]
```

```python
lon, lat = 2.075, 13.52
```

```python
glofas.download_reanalysis_year(
    lon=lon,
    lat=lat,
    year=year,
)
```

```python
da_better_guess = glofas.load_reanalysis_year(
    data_type="raw", lon=lon, lat=lat, year=2022
)
```

```python
da_better_guess.mean(dim="time")
```

```python
station_name = "niamey"
```

```python
for year in tqdm(range(1979, 2025)):
    glofas.download_reanalysis_year(year=year, station_name=station_name)
```

```python
glofas.download_reanalysis_year(year=2025, station_name=station_name)
```

```python
glofas.process_reanalysis(station_name)
```
