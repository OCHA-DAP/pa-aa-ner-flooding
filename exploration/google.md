---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.7
  kernelspec:
    display_name: pa-aa-ner-flooding
    language: python
    name: pa-aa-ner-flooding
---

# Google flood model

Looking into feasibility of using downstream station

[Station](https://sites.research.google/floods/l/11.385801758733372/4.12261962890625/10/g/hybas_1120760290)

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import os
from pathlib import Path
import datetime

from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
```

```python
pio.renderers.default = "notebook"
```

```python
load_dotenv()
GFH_DATA_DIR = Path(os.environ["GFH_DATA_DIR"])
NOWCAST_DIR = GFH_DATA_DIR / "inputs/historic_nowcasts"
RAW_DIR = Path(os.environ["OAP_DATA_DIR"]) / "public/raw/ner"
ABN_PATH = RAW_DIR / "abn/Données_ Niamey2005_2022.xlsx"
HYBAS_ID = 1120760290
```

```python
# read data
# google
ggl = pd.read_csv(NOWCAST_DIR / f"hybas_{HYBAS_ID}.csv")
ggl["time"] = pd.to_datetime(ggl["time"])
ggl = ggl.set_index("time")

# abn
abn = pd.read_excel(ABN_PATH, skiprows=[0, 1], index_col=0)
# merge
df = ggl.merge(abn, right_index=True, left_index=True)
df = df.rename(columns={"prediction": "Google"})
df

# process
# find minimum average minimum flow day to shift to seasonyear
min_day = (
    df.groupby(df.index.year).idxmin()["Water Level (cm)"].dt.dayofyear.mean()
)
df["dayofseason"] = df.index.dayofyear - min_day
df["dayofseason"] = (
    df["dayofseason"].apply(lambda x: x + 365 if x < 1 else x).astype(int)
)
df["seasonyear"] = (
    pd.to_datetime(df.index.date) - pd.DateOffset(days=min_day)
).year

df = df.sort_values(["seasonyear", "dayofseason"])

# keep only complete years
df = df[df["seasonyear"] != df["seasonyear"].min()]
df = df[df["seasonyear"] != df["seasonyear"].max()]
display(df)
```

```python
fig = px.line(
    x=df["dayofseason"],
    y=df["Google"],
    color=df["seasonyear"],
)
fig.add_trace(go.Scatter(x=[125, 125], y=[0, 1000], mode="lines"))
fig.update_traces(line_width=1)
fig.update_layout(template="simple_white")
fig.show()
```

```python
# find first peak flow date
# cutoff based on eyeballing previous plot
cutoff_dayofseason = 125
df_first_peak = df[df["dayofseason"] < cutoff_dayofseason]
df_max = df_first_peak.groupby("seasonyear").max()
df_max_date = df_first_peak.groupby(df_first_peak["seasonyear"]).idxmax()
df_max_dayofyear = df_max_date.applymap(lambda x: x.dayofyear)
px.scatter(df_max_dayofyear, x="Google", y="Water Level (cm)").show()
display(df_max_dayofyear.corr())
px.scatter(df_max, x="Google", y="Water Level (cm)").show()
display(df_max.corr())
```

```python
df_norm = (df - df.min()) / (df.max() - df.min())

df_max = df.groupby("seasonyear").max()
df_max_norm = (df_max - df_max.min()) / (df_max.max() - df_max.min())
df_max_date = df.groupby(df.index.year).idxmax()
df_max_date = df_max_date.apply(lambda col: col.dt.dayofyear)
```
