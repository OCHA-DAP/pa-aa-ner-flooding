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

Tracking activation in 2025/26

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from datetime import datetime

import ocha_stratus as stratus
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

from src.datasources import grdc, abn
from src.utils.rating_curve import calculate_stage
from src.constants import *
```

```python
df_grdc = grdc.load_grdc(station_id=NIAMEY_GRDC_ID)
```

```python
def date_to_season(date):
    if date.month < 6:
        return date.year - 1
    else:
        return date.year
```

```python
def set_flood_phase(date):
    if date.month >= 6 and date.month <= 9:
        return "l"
    else:
        return "g"
```

```python
df_grdc["flood_type"] = df_grdc["time"].apply(set_flood_phase)
```

```python
df_grdc = df_grdc.rename(columns={"time": "date"})
```

```python
df_grdc["level"] = calculate_stage(df_grdc["runoff_mean"])
```

```python
df_grdc = df_grdc.dropna(subset="level")
df_grdc["source"] = "grdc"
```

```python
df_monitoring_2024 = abn.load_current_monitoring()
```

```python
df_monitoring_2024 = df_monitoring_2024.dropna(subset="level")
```

```python
df_monitoring_2024["source"] = "abn"
```

```python
READINESS_THRESH = 592
ACTION_THRESH = 604
```

```python
df_historical = pd.concat([df_grdc, df_monitoring_2024])
```

```python
df_historical
```

```python
def set_plot_date(row):
    try:
        if row["date"].year == row["season"]:
            return datetime(1900, row["date"].month, row["date"].day)
        else:
            return datetime(1901, row["date"].month, row["date"].day)

    except Exception as e:
        print(e)
        print(row["date"])
```

```python
df_historical["season"] = df_historical["date"].apply(date_to_season)
df_historical["plot_date"] = df_historical.apply(set_plot_date, axis=1)
df_historical["flood_type"] = df_historical["date"].apply(set_flood_phase)
```

```python
df_historical = df_historical.sort_values(
    by="source", ascending=False, key=lambda s: s.eq("abn")
)

# Drop duplicates, keeping the first occurrence (which will be "abn" if present)
df_historical = df_historical.drop_duplicates(subset="date", keep="first")
```

```python
df_historical = df_historical.sort_values("date")
```

```python
df_monitoring_2025 = abn.load_current_monitoring(year=2025)
```

```python
df_monitoring_2025
```

```python
df_combined = pd.concat([df_historical, df_monitoring_2025], ignore_index=True)
```

```python
df_combined["season"] = df_combined["date"].apply(date_to_season)
df_combined["plot_date"] = df_combined.apply(set_plot_date, axis=1)
df_combined["flood_type"] = df_combined["date"].apply(set_flood_phase)
```

```python
gui_df = df_combined[df_combined["flood_type"] == "g"]
```

```python
gui_df.loc[
    gui_df[gui_df["level"] >= READINESS_THRESH]
    .groupby("season")["date"]
    .idxmin()
]
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
min_year = 2000

fig, ax = plt.subplots(dpi=200, figsize=(7, 7))

seasonyear_colors = {
    2022: "mediumpurple",
    2024: "deepskyblue",
}

for seasonyear in gui_df["season"].unique():
    if seasonyear < min_year:
        continue
    dff = (
        gui_df[gui_df["season"] == seasonyear].copy().dropna(subset=["level"])
    )
    if seasonyear == 2025:
        color = CHD_GREEN
        label = None
        width = 2
    elif seasonyear in seasonyear_colors:
        color = seasonyear_colors.get(seasonyear)
        label = dff[dff["level"] >= READINESS_THRESH]["date"].min().year
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

ax.legend(title="Déclenchements\nguinéens\nprécédents", loc="lower left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylabel("Niveau d'eau (cm)")
ax.set_xlim(left=datetime(1900, 11, 1), right=datetime(1901, 3, 1))
ax.set_ylim(bottom=400, top=650)

ax.axhspan(0, 530, facecolor="green", alpha=0.1)
ax.axhspan(530, 580, facecolor="yellow", alpha=0.1)
ax.axhspan(580, 620, facecolor="orange", alpha=0.1)
ax.axhspan(620, 700, facecolor="red", alpha=0.1)

alpha = 0.7
for thresh, color, label in [
    (ACTION_THRESH, "crimson", "action"),
    (READINESS_THRESH, "darkorange", "mobilisation"),
]:
    ax.axhline(thresh, color=color, linestyle="--", zorder=-1, alpha=alpha)
    ax.annotate(
        f" {label} : {thresh} cm",
        (datetime(1900, 11, 1), thresh),
        ha="left",
        va="bottom",
        color=color,
        fontsize=8,
        alpha=alpha,
    )

# French dates formatting
ax.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

ax.set_title(f"Fleuve Niger à Niamey\nCrues guinéennes (depuis {min_year})")
```

```python
gui_df[gui_df["season"] >= min_year].groupby("season")[
    "level"
].max().reset_index()
```

```python
gui_df_recent = gui_df[(gui_df["season"] >= 2000) & (gui_df["season"] < 2025)]
```

```python
df_recent_peaks = gui_df_recent.loc[
    gui_df_recent.groupby("season")["level"].idxmax()
]
```

```python
fig, ax = plt.subplots(dpi=200, figsize=(7, 7))

df_recent_peaks.plot(
    x="plot_date", y="level", linewidth=0, ax=ax, legend=False
)


[
    ax.annotate(
        row["season"],
        row[["plot_date", "level"]],
        ha="center",
        va="center",
        fontsize=8,
    )
    for _, row in df_recent_peaks.iterrows()
]

alpha = 0.7
for thresh, color, label in [
    (ACTION_THRESH, "crimson", "action"),
    # (READINESS_THRESH, "darkorange", "mobilisation"),
]:
    ax.axhline(thresh, color=color, linestyle="--", zorder=-1, alpha=alpha)
    ax.annotate(
        f" {label} : {thresh} cm",
        (datetime(1900, 12, 9), thresh),
        ha="left",
        va="bottom",
        color=color,
        fontsize=8,
        alpha=alpha,
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


ax.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

ax.set_ylabel("Niveau du pic (cm) [ABN]")
ax.set_xlabel("Date du pic")
ax.set_title("Fleuve Niger à Niamey\nTiming des crues guinéennes")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

```python
drop_years = [1984, 1936]
gui_df_recent_long = gui_df[
    (gui_df["season"] >= 1900)
    & (gui_df["season"] < 2025)
    & ~gui_df["season"].isin(drop_years)
]
```

```python
df_recent_peaks_long = gui_df_recent_long.loc[
    gui_df_recent_long.groupby("season")["level"].idxmax()
]
```

```python
fig, ax = plt.subplots(dpi=200, figsize=(7, 7))

df_recent_peaks_long.plot(
    x="plot_date", y="level", linewidth=0, ax=ax, legend=False
)


[
    ax.annotate(
        row["season"],
        row[["plot_date", "level"]],
        ha="center",
        va="center",
        fontsize=8,
    )
    for _, row in df_recent_peaks_long.iterrows()
]

alpha = 0.7
for thresh, color, label in [
    (ACTION_THRESH, "crimson", "action"),
    # (READINESS_THRESH, "darkorange", "mobilisation"),
]:
    ax.axhline(thresh, color=color, linestyle="--", zorder=-1, alpha=alpha)
    ax.annotate(
        f" {label} : {thresh} cm",
        (datetime(1900, 11, 25), thresh),
        ha="left",
        va="bottom",
        color=color,
        fontsize=8,
        alpha=alpha,
    )

latest_row = gui_df.loc[gui_df["date"].idxmax()]
# ax.annotate(
#     f' {latest_row["date"].date()}:\n {latest_row["level"]} cm',
#     (latest_row["plot_date"], latest_row["level"] + 4),
#     color=CHD_GREEN,
#     fontsize=12,
#     fontweight="bold",
# )
ax.plot(
    latest_row["plot_date"],
    latest_row["level"],
    color=CHD_GREEN,
    marker=".",
    markersize=10,
)


ax.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

ax.set_ylabel("Niveau du pic (cm) [ABN]")
ax.set_xlabel("Date du pic")
ax.set_title("Fleuve Niger à Niamey\nTiming des crues guinéennes")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

```python
gui_df[(gui_df["season"] == 2024) & (gui_df["level"] >= 604)]
```

```python
gui_df[(gui_df["season"] == 2024) & (gui_df["level"] >= 620)]
```

```python
gui_df[(gui_df["season"] == 2024) & (gui_df["level"] >= 640)]
```
