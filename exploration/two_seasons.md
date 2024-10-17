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
import pandas as pd

from src.datasources import abn
from src.constants import *
from src.utils import shift_to_floodseason_corrected, FLOODSEASON_START
from utils import FLOODSEASON_ENDDAY
```

```python
THRESH = 580
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "date", "Water Level (cm)": "level"})
level = shift_to_floodseason_corrected(level)
level = level[level["seasonyear"].isin(range(2005, 2022))]
level
```

```python
# either season
peaks = level.loc[level.groupby("seasonyear")["level"].idxmax()]
dummy_missing = pd.DataFrame(
    [{"seasonyear": 2022, "level": 0}, {"seasonyear": 2023, "level": 0}]
)
dummy_2024 = pd.DataFrame([{"seasonyear": 2024, "level": 670}])
peaks = pd.concat([peaks, dummy_missing, dummy_2024], ignore_index=True)
peaks["rank"] = peaks["level"].rank(ascending=False)
peaks["rp"] = len(peaks) / peaks["rank"]
peaks.sort_values("rank")
```

```python
# crues locales
locale = level[level["dayofseason"] < FLOODSEASON_ENDDAY]
l_peaks = locale.loc[locale.groupby("seasonyear")["level"].idxmax()]
l_peaks[l_peaks["level"] >= THRESH]
```

```python
l_triggers = locale[locale["level"] >= THRESH]
l_triggers = l_triggers.loc[
    l_triggers.groupby("seasonyear")["dayofseason"].idxmin()
]
l_triggers
```

```python
(2023 - 2005 + 1) / len(l_peaks[l_peaks["level"] >= THRESH])
```

```python
(2023 - 2005 + 1)
```

```python
# crues guineennes
gui = level[level["dayofseason"] >= FLOODSEASON_ENDDAY]
g_peaks = gui.loc[gui.groupby("seasonyear")["level"].idxmax()]
g_peaks[g_peaks["level"] >= THRESH]
```

```python
g_triggers = gui[gui["level"] >= THRESH]
g_triggers = g_triggers.loc[
    g_triggers.groupby("seasonyear")["dayofseason"].idxmin()
]
g_triggers
```

```python
(2023 - 2005 + 1) / len(g_peaks[g_peaks["level"] >= THRESH])
```

```python
level[level["level"] == 580]
```

```python

```
