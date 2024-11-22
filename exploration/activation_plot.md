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

# Activation plot

Plot for 2024 activation email

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

from src.datasources import abn
from src.constants import *
from src.utils import shift_to_floodseason_corrected, FLOODSEASON_START
from utils import FLOODSEASON_ENDDAY
```

```python
monitoring_df = abn.load_current_monitoring()
```

```python
monitoring_df
```

```python
THRESH = 580
```

```python
level = abn.load_abn_niamey().reset_index()
level = level.rename(columns={"Date": "date", "Water Level (cm)": "level"})
```

```python
level = pd.concat([level, monitoring_df])
```

```python
level = shift_to_floodseason_corrected(level)
level = level[level["seasonyear"] >= 2005]
level.sort_values("date")
```

```python
level.dtypes
```

```python
def set_plot_date(row):
    try:
        if row["date"].year == row["seasonyear"]:
            return datetime(1900, row["date"].month, row["date"].day)
        else:
            return datetime(1901, row["date"].month, row["date"].day)

    except Exception as e:
        print(e)
        print(row["date"])
```

```python
level["plot_date"] = level.apply(set_plot_date, axis=1)
```

```python
level.plot(x="plot_date", y="level")
```

```python
level["date"].apply(lambda x: x.month).max()
```

```python
FLOODSEASON_ENDDAY
```

```python
gui_df = level[(level["dayofseason"] > FLOODSEASON_ENDDAY)]
```

```python
gui_df[gui_df["level"] > THRESH]
```

```python

```

```python
def custom_date_formatter(x, pos):
    date = mdates.num2date(x)  # Convert numeric value to date
    month_abbr = date.strftime(
        "%b"
    )  # Get abbreviated month name (e.g., "Jan", "Feb")
    day = date.day  # Get day of the month
    translated_month = FRENCH_MONTHS.get(
        month_abbr, month_abbr
    )  # Translate month
    return f"{day} {translated_month}"  # Format as "Translated Month Day"
```

```python
fig, ax = plt.subplots(dpi=200, figsize=(8, 5))

seasonyear_colors = {2018: "mediumpurple", 2020: "deepskyblue"}

for seasonyear in gui_df["seasonyear"].unique():
    dff = (
        gui_df[gui_df["seasonyear"] == seasonyear]
        .copy()
        .dropna(subset=["level"])
    )
    if seasonyear == 2024:
        color = CHD_GREEN
        label = None
        width = 2
    elif seasonyear in seasonyear_colors:
        color = seasonyear_colors.get(seasonyear)
        label = dff[dff["level"] >= THRESH]["date"].min().year
        width = 1
    else:
        color = "grey"
        label = None
        width = 0.3
    ax.plot(
        dff["plot_date"],
        dff["level"],
        color=color,
        label=label,
        linewidth=width,
    )

latest_row = gui_df.loc[gui_df["date"].idxmax()]
ax.annotate(
    f' {latest_row["date"].date()}:\n {latest_row["level"]} cm',
    (latest_row["plot_date"], latest_row["level"] + 4),
    color=CHD_GREEN,
    fontsize=12,
    fontweight="bold",
)
ax.plot(
    latest_row["plot_date"],
    latest_row["level"],
    color=CHD_GREEN,
    marker=".",
    markersize=10,
)

ax.legend(title="Déclenchements\nguinéennes\nprécédents", loc="lower left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylabel("Niveau d'eau (cm)")
ax.set_xlim(left=datetime(1900, 11, 1), right=datetime(1901, 3, 1))
ax.set_ylim(bottom=400)

ax.axhspan(0, 530, facecolor="green", alpha=0.1)
ax.axhspan(530, 580, facecolor="yellow", alpha=0.1)
ax.axhspan(580, 620, facecolor="orange", alpha=0.1)
ax.axhspan(620, 700, facecolor="red", alpha=0.1)
ax.axhline(580, color="gray", linestyle="--")
ax.annotate(
    " seuil\n (580 cm)",
    (datetime(1900, 11, 1), 580),
    color="gray",
    ha="left",
    va="bottom",
)

# French dates formatting
ax.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

ax.set_title("Fleuve Niger à Niamey\nCrues guinéennes (depuis 2005)")
```

```python

```

```python
plot_df = gui_df.pivot(index="plot_date", columns="seasonyear", values="level")
```

```python
plot_df.plot()
```

```python

```
