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

# GloFAS

```python
%load_ext jupyter_black
```

```python
from dotenv import load_dotenv
import os
from pathlib import Path

from ochanticipy import (
    create_country_config,
    CodAB,
    GeoBoundingBox,
    GlofasForecast,
    GlofasReanalysis,
    GlofasReforecast,
)
import datetime
import xarray as xr
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
```

```python
load_dotenv()

PROC_DIR = Path(os.environ["OAP_DATA_DIR"]) / "public/processed/ner/glofas"
```

```python
adm1_sel = ["Tillabéri", "Niamey", "Dosso", "Maradi"]
startdate = datetime.date(2022, 8, 20)
enddate = datetime.date(2022, 9, 20)

country_config = create_country_config(iso3="ner")
codab = CodAB(country_config=country_config)
# codab.download()
gdf_adm1 = codab.load(admin_level=1)
gdf_aoi = gdf_adm1[gdf_adm1["adm_01"].isin(adm1_sel)]
geobb = GeoBoundingBox.from_shape(gdf_aoi)
print(gdf_adm1.columns)
```

```python


glofas_forecast = GlofasForecast(
    country_config=country_config,
    geo_bounding_box=geobb,
    leadtime_max=15,
    start_date=startdate,
    end_date=enddate,
)
```

```python
glofas_forecast.download()
```

```python
glofas_forecast.process()
```

```python
ra_startdate = datetime.date(1900, 1, 1)
ra_enddate = datetime.date(2023, 8, 21)
glofas_reanalysis = GlofasReanalysis(
    country_config=country_config,
    geo_bounding_box=geobb,
    start_date=ra_startdate,
    end_date=ra_enddate,
)
```

```python
glofas_reanalysis.download()
```

```python
glofas_reanalysis.process()
```

```python
ds = glofas_reanalysis.load()
df_re = ds.to_dataframe()
df_re
```

```python
# calculate return

df_re_max = df_re.groupby(df_re.index.year).max()
total_years = len(df_re_max)

return_years = [1.5, 2, 3, 5, 10]

df_count_yearly = pd.DataFrame()
df_return_periods = pd.DataFrame(index=return_years)

for station in df_re_max.columns:
    dff = df_re_max[station]
    quants = np.linspace(0, 1, 101)
    levels = dff.quantile(quants)
    #     print(levels)
    for level in levels:
        dfff = dff[dff >= level]
        years = "<br>".join(
            [str(x) for x in dfff.sort_index(ascending=False).index]
        )
        count = len(dfff)
        df_add = pd.DataFrame(
            {
                "station": station,
                "level": level,
                "count": count,
                "years": years,
                "return": total_years / count,
            },
            index=[0],
        )
        df_count_yearly = pd.concat(
            [df_count_yearly, df_add], ignore_index=True
        )
    df_i = df_count_yearly[df_count_yearly["station"] == station]
    df_return_periods[station] = np.interp(
        return_years, df_i["return"], df_i["level"]
    )


df_count_yearly["return"] = len(df_re_max) / df_count_yearly["count"]
```

```python
# plot return period for station

station = "Goulbi De Maradi A Nielloua"

df_plot = df_count_yearly[df_count_yearly["station"] == station]

min_year = df_re.index.year.min()

x_max = 20
y_max = df_plot[df_plot["return"] <= x_max]["level"].max()
y_min = df_plot["level"].min()
fig = px.line(df_plot, x="return", y="level")

for year in return_years:
    level = df_return_periods.loc[year, station]
    fig.add_trace(
        go.Scatter(
            x=[1, x_max],
            y=[level, level],
            mode="lines+text",
            text=[None, f"{year}-year"],
            line=dict(width=1, dash="dash", color="black"),
            textposition="top left",
        )
    )

fig.update_xaxes(range=(1, x_max), title="Return period (years)")
fig.update_yaxes(
    range=(y_min, y_max), title="One-day flow rate (m<sup>3</sup>/s)"
)

fig.update_layout(
    template="simple_white",
    title=f"GloFAS return period (since {min_year})<br>Station: {station}",
    showlegend=False,
)
```

```python
# plot historical for station

station = "Niamey"
start_date = pd.Timestamp(datetime.date(1999, 1, 1))
end_date = pd.Timestamp(datetime.date(2001, 1, 1))

df_plot = df_re.loc[:, station]

x_max = min(end_date, df_plot.index.max())
x_min = max(start_date, df_plot.index.min())

fig = px.line(df_plot)
for year in return_years:
    level = df_return_periods.loc[year, station]
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max],
            y=[level, level],
            mode="lines",
            line=dict(width=1, dash="dash", color="black"),
        )
    )
    fig.add_annotation(
        x=1,
        y=level,
        xref="paper",
        text=f"{year}-year",
        showarrow=False,
        xanchor="left",
    )


fig.update_layout(
    template="simple_white",
    showlegend=False,
    title=f"GloFAS reanalysis historical flow<br>Station: {station}",
)
fig.update_xaxes(title="Date", range=[x_min, x_max])
fig.update_yaxes(title="Flow rate (m<sup>3</sup>/s)", range=[0, df_plot.max()])
fig.show()
```

```python
# calculate return period based on chunks of consecutive days when above threshold
# this allows for multiple floods during one year if flow dips below threshold
# then increases again

consec_dayss = [1, 2, 3, 5, 10]

years = df_re.index.year.unique()
df_count = pd.DataFrame()

for consec_days in consec_dayss:
    for station in df.columns:
        dff = df_re[station].to_frame()
        # dff.plot()

        levels = np.round(
            np.linspace(0, dff[station].max(), 50, endpoint=False)
        )
        quants = np.linspace(0.9, 1, 80)
        levels = dff[station].quantile(quants)
        cols = [station]

        for day_shift in range(consec_days)[1:]:
            col_name = f"shift_{day_shift}"
            dff[col_name] = dff[station].shift(day_shift)
            cols.append(col_name)

        for level in levels:
            col_name = f"a_{level}"
            dff[col_name] = (dff[cols] > level).all(axis=1)
            dff["shift_count"] = dff[col_name] & ~dff[col_name].shift().fillna(
                False
            )
            counts = dff["shift_count"].value_counts()
            if True in counts.index:
                count = counts[True]
                df_add = pd.DataFrame(
                    {
                        "station": station,
                        "level": level,
                        "count": count,
                        "consec_days": consec_days,
                    },
                    index=[0],
                )
                df_count = pd.concat([df_count, df_add], ignore_index=True)

df_count["return"] = len(years) / df_count["count"]
```

```python
station = "Niamey"
df_plot = df_count[df_count["station"] == station]

fig = px.line(df_plot, x="return", y="level", color="consec_days")
fig.update_layout(template="simple_white")
fig.show()
```

```python
# seems to be problem with glofas_forecast.load()
# doing it manually instead

files = [file for file in os.listdir(PROC_DIR) if "forecast" in file]

dss = []

for file in files:
    date = file.split("ner_cems-glofas-forecast_")[1]
    date = datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:10]))
    date = np.datetime64(date)
    ds = xr.open_dataset(PROC_DIR / file)
    print(file)
    ds = ds.expand_dims(dim={"date": [date]})
    dss.append(ds)

ds = xr.concat(dss, dim="date")
df_fo = ds.to_dataframe()
df_fo
```

```python
# calculate forecast skill

station = "Niamey"

dff = df_fo[station].reset_index()
dff = dff.rename(columns={station: "forecast"})
dff["f_date"] = dff["step"] + dff["date"] - pd.Timedelta(days=1)
dff = dff.set_index("f_date")
dff = dff.join(df_re[station])

display(df_re)
display(dff)
```

```python
# load reforecast

start_date = datetime.date(1999, 1, 1)
end_date = datetime.date(2001, 9, 1)

glofas_reforecast = GlofasReforecast(
    country_config=country_config,
    geo_bounding_box=geobb,
    leadtime_max=15,
    start_date=start_date,
    end_date=end_date,
)
glofas_reforecast.download()
glofas_reforecast.process()
ds = glofas_reforecast.load()
df_ref = ds.to_dataframe().reset_index()
df_ref["f_date"] = df_ref["time"] + df_ref["step"] - pd.Timedelta(days=1)
df_ref
```

```python
# historical triggers based on reforecast
# assuming we only trigger once per year

stations = df_re.columns
frac_threshs = np.linspace(0.5, 1, 3)

return_year = 3
consec_thresh = 3
consec_days = range(consec_thresh)[1:]

df_confuse = pd.DataFrame()

for frac_thresh in frac_threshs:
    for station in stations:
        level = df_return_periods.loc[return_year, station]
        for step in df_ref["step"].unique():
            dff = df_ref[df_ref["step"] == step][["number", "f_date", station]]
            dff = dff.set_index("f_date")
            dff = dff.rename(columns={station: "forecast"})
            dff = dff.join(df_re[station]).rename(columns={station: "actual"})
            dff["gt_thres"] = (dff["forecast"] > level).astype(int)
            dff = dff.groupby(dff.index).agg(
                {"gt_thres": sum, "number": "count", "actual": "first"}
            )
            dff["frac"] = dff["gt_thres"] / dff["number"]
            dff["trigger_perday"] = dff["frac"] > frac_thresh
            dff["actual_perday"] = dff["actual"] > level
            for x in ["trigger", "actual"]:
                for day_shift in consec_days:
                    dff[f"{x}_perday_{day_shift}"] = dff[f"{x}_perday"].shift(
                        day_shift, fill_value=False
                    )
                dff[f"{x}_overall"] = dff[
                    [col for col in dff.columns if f"{x}_perday" in col]
                ].all(axis=1)
            dff = dff.groupby(dff.index.year)[
                ["trigger_overall", "actual_overall"]
            ].any()
            df_ct = pd.crosstab(
                dff["actual_overall"].astype(int),
                dff["trigger_overall"].astype(int),
            )
            for b in [1, 0]:
                df_ct[b] = 0 if b not in df_ct.columns else df_ct[b]
                df_ct.loc[b] = 0 if b not in df_ct.index else df_ct.loc[b]
            TP = df_ct.loc[1, 1]
            FP = df_ct.loc[0, 1]
            TN = df_ct.loc[0, 0]
            FN = df_ct.loc[1, 0]
            df_add = pd.DataFrame(
                {
                    "TP": TP,
                    "FP": FP,
                    "TN": TN,
                    "FN": FN,
                    "station": station,
                    "return_year": return_year,
                    "leadtime": step,
                    "consec": consec_thresh,
                    "frac_thresh": frac_thresh,
                },
                index=[0],
            )
            df_confuse = pd.concat([df_confuse, df_add])

df_confuse["P"] = df_confuse["TP"] + df_confuse["FN"]
df_confuse["N"] = df_confuse["TN"] + df_confuse["FP"]
df_confuse["total"] = df_confuse["P"] + df_confuse["N"]
df_confuse["TPR"] = df_confuse["TP"] / df_confuse["P"]
df_confuse["FPR"] = df_confuse["FP"] / df_confuse["P"]
df_confuse["PP"] = df_confuse["TP"] + df_confuse["FP"]
df_confuse["activation"] = df_confuse["PP"] / df_confuse["total"]
```

```python
# plot ROC

selected_steps = [5, 10, 15]

for station in stations:
    df_plot = df_confuse[df_confuse["station"] == station]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            line=dict(width=0.5, dash="dash", color="black"),
            mode="lines",
            showlegend=False,
        )
    )
    for leadtime in df_confuse["leadtime"].unique():
        if leadtime.days not in selected_steps:
            continue
        dff_plot = df_plot[df_plot["leadtime"] == leadtime]
        fig.add_trace(
            go.Scatter(
                x=dff_plot["FPR"],
                y=dff_plot["TPR"],
                name=leadtime.days,
                mode="lines",
            )
        )

    fig.update_xaxes(range=(0, 1), visible=False)
    fig.update_yaxes(range=(0, 1), visible=False)
    fig.update_layout(
        template="simple_white", width=500, height=500, title=station
    )
    fig.show()
```

```python
# plot curve


for station in stations:
    fig = go.Figure()
    df_plot = df_confuse[df_confuse["station"] == station]
    fig.add_trace(
        go.Scatter(
            x=df_plot["leadtime"].dt.days,
            y=df_plot["TPR"],
            mode="lines",
        )
    )

    fig.update_layout(template="simple_white")
    fig.show()
```
