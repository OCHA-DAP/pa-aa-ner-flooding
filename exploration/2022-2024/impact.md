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

# Impact data

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from unidecode import unidecode

import pandas as pd
import plotly.express as px

from ochanticipy import create_country_config, CodAB

import utils
```

```python
GAYA = "NER003006003"
PROC_DIR = utils.DATA_DIR / "public/processed/ner/anadia"
F1 = "NER003006003"
F2 = "NER003006005"
F3 = "NER003006004"
F4 = "NER003004008"
# remove F4 (Sambera) since it is the worst correlated and has lowest flooding
ADM3S = [F1, F2, F3]
GREEN = "#1bb580"
```

```python
adm1s = ["Dosso", "Tillabéri"]
country_config = create_country_config("ner")
codab = CodAB(country_config=country_config)
codab = codab.load(admin_level=3)
codab = codab[codab["adm_01"].isin(adm1s)]
codab = codab.set_crs(4326)

impact = utils.load_anadia()
impact["date"] = pd.to_datetime(impact["Date début event"])
impact = impact.dropna(subset="date")


# match impact admin3 to codab admin3

codab["match_adm3"] = codab["adm_03"].apply(lambda x: unidecode(x.lower()))


def replace_impact(name):
    replace = [
        (" arrondissement", ""),
        (" 1", " i"),
        (" 2", " ii"),
        (" 3", " iii"),
        (" 4", " iv"),
        (" 5", " v"),
        (" (doutchi)", ""),
    ]
    for pair in replace:
        name = name.replace(pair[0], pair[1])
    return name


impact["match_adm3"] = impact["Communes"].apply(
    lambda x: replace_impact(x.lower())
)

impact = impact.merge(codab[["match_adm3", utils.ID_COL]], on="match_adm3")

filename = "ner_anadia_processed.csv"
impact.to_csv(PROC_DIR / filename, index=False)
```

```python
print(impact["date"].min())
```

```python
codab.plot()
```

```python
impact["Communes"].unique()
```

```python
for commune in ["LIBORE", "KARMA", "N'DOUNGA"]:
    dff = impact[impact["Communes"] == commune]
    display(dff.groupby(dff["date"].dt.year)["Maisons détruites"].sum())
```

```python
df_plot = codab.merge(
    impact.groupby(utils.ID_COL).sum(numeric_only=True).reset_index(),
    on=utils.ID_COL,
)
display(df_plot.geometry)
for col in ["Personnes affectées", "Maisons détruites"]:
    fig = px.choropleth(
        df_plot, geojson=df_plot.geometry, locations=df_plot.index, color=col
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        width=800,
        height=500,
        #         margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    fig.show()
```

```python
years = [2020]
for year in years:
    dff = impact[impact.date.dt.year == year]
    dff = dff.groupby(utils.ID_COL).sum(numeric_only=True)
    df_plot = codab.merge(dff, on=utils.ID_COL)

    col = "Personnes affectées"
    fig = df_plot.sort_values(col).iloc[:].plot(column=col)

    col = "Maisons détruites"
    fig = df_plot.sort_values(col).iloc[:].plot(column=col)
```

```python
# check for correlation between floodscan and impact data

floodscan = utils.load_processed_floodscan()
```

```python
# fs_f = floodscan[floodscan[utils.ID_COL].isin(ADM3S)]
fs_f = floodscan.copy()
fs_f = fs_f.groupby([utils.ID_COL, "seasonyear"]).mean(numeric_only=True)
# impact_f = impact[impact[utils.ID_COL].isin(ADM3S)]
impact_f = impact.copy()
impact_f["seasonyear"] = impact_f.date.dt.year
impact_f = impact_f.groupby([utils.ID_COL, "seasonyear"]).sum(
    numeric_only=True
)

fs_im = fs_f.merge(impact_f, on=[utils.ID_COL, "seasonyear"]).reset_index()
fs_im = fs_im.merge(codab[[utils.ID_COL, "adm_03"]], on=utils.ID_COL)
```

```python
correlations = pd.DataFrame()
for adm3 in fs_im[utils.ID_COL].unique():
    dff = fs_im[fs_im[utils.ID_COL] == adm3]
    maison, personne = dff.corr(numeric_only=True).loc[
        "mean_cell", ["Maisons détruites", "Personnes affectées"]
    ]
    df_add = pd.DataFrame(
        {utils.ID_COL: adm3, "maison": maison, "personne": personne}, index=[0]
    )
    correlations = pd.concat([correlations, df_add], ignore_index=True)

correlations.dropna().sort_values("maison")

df_plot = codab.merge(correlations, on=utils.ID_COL)
col = "maison"
# df_plot = df_plot[df_plot[col] > 0]
df_plot = df_plot[df_plot[utils.ID_COL].isin(ADM3S)]
display(df_plot)
fig = df_plot.plot(column=col, legend=True)

for adm3 in ADM3S:
    df_plot = fs_im[fs_im[utils.ID_COL] == adm3]
    name = df_plot["adm_03"].iloc[0]
    display(
        df_plot[["Maisons détruites", "mean_cell"]].corr(numeric_only=True)
    )
    fig = px.scatter(
        df_plot,
        y="Maisons détruites",
        x="mean_cell",
        hover_data="seasonyear",
        trendline="ols",
    )
    fig.update_traces(marker_color=GREEN, marker_size=10)
    fig.update_layout(
        template="simple_white",
        title=name,
        height=500,
        width=500,
    )
    fig.update_xaxes(title="Étendue d'inondation", rangemode="tozero")
    fig.update_yaxes(rangemode="tozero")
    fig.show()
```

```python

```

```python

```
