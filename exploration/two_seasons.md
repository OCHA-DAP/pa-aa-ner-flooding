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

# Two-season trigger

Comparing triggering in the first flooding season (crue rouges / locale) and
second flooding season (crue guinéenne)

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from src.datasources import abn
from src.constants import *
from src.utils import shift_to_floodseason
from utils import FLOODSEASON_ENDDAY
```

```python
THRESH = 580
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "time", "Water Level (cm)": "level"})
level = shift_to_floodseason(level, date_col="time")
# drop duplicates due to leapyears (just on Jan 1)
level = level[~level.duplicated(subset=["dayofseason", "seasonyear"])]
# keep only full seasons
level = level[level["seasonyear"].isin(range(2005, 2022))]
level
```

```python
# crues locales
locale = level[level["dayofseason"] < FLOODSEASON_ENDDAY]
l_peaks = locale.loc[locale.groupby("seasonyear")["level"].idxmax()]
l_peaks[l_peaks["level"] >= THRESH]
```

```python
(2023 - 2005 + 1) / 7
```

```python
# crues guineennes
gui = level[level["dayofseason"] >= FLOODSEASON_ENDDAY]
g_peaks = gui.loc[gui.groupby("seasonyear")["level"].idxmax()]
g_peaks[g_peaks["level"] >= THRESH]
```

```python
(2023 - 2005 + 1) / 2
```
