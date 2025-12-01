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

# Garbe Kourou reforecast download

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from src.datasources import glofas
```

```python
station_name = "garbekourou"
```

```python
months = [7, 8, 9, 10]
```

```python
glofas.download_reforecast(station_name=station_name, months=months)
```

```python
test = glofas.process_reforecast(station_name)
```
