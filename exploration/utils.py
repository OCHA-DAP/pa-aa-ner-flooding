import datetime
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from dotenv import load_dotenv
from rasterstats import zonal_stats

load_dotenv()

DATA_DIR = Path(os.environ["AA_DATA_DIR"])
FS_DIR = DATA_DIR / "private/raw/glb/floodscan"
FLOODSCAN_FILENAME = "aer_sfed_area_300s_19980112_20220424_v05r01.nc"
ID_COL = "rowcacode3"
DATA_VAR = "SFED_AREA"
PROC_DIR = DATA_DIR / "private/processed/ner/floodscan"
# start of season is June 1 according to ABN
FLOODSEASON_START = datetime.date(2000, 6, 1)
# this puts end of season at Nov 1
FLOODSEASON_ENDDAY = 153


def get_peak(
    df: pd.DataFrame,
    max_col: str,
    year_col: str = "seasonyear",
    end_dayofseason: int = FLOODSEASON_ENDDAY,
    agg_col: str = ID_COL,
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Finds the maxima for each year, for each station/adm.
    :param df: input df
    :param max_col: values from which to find maxima
    :param year_col: year / season of measurements
    :param end_dayofseason: cutoff date (only look for maxima before this day)
    :param agg_col: station or admin level
    :param date_col: date of measurement
    :return: df of maxima
    """
    df = df[df["dayofseason"] <= end_dayofseason]
    sort_cols = [year_col]
    if agg_col in df.columns:
        sort_cols.append(agg_col)
    df_max = df.sort_values(max_col, ascending=False).drop_duplicates(
        sort_cols
    )
    df_max = df_max.sort_values(year_col)
    return_cols = sort_cols + ["dayofseason", max_col]
    if date_col in df.columns:
        return_cols.append(date_col)
    df_max = df_max[return_cols].dropna()
    return df_max


def shift_to_floodseason(
    df: pd.DataFrame,
    date_col: str = "date",
    use_index: bool = False,
    season_startdate: datetime.date = FLOODSEASON_START,
) -> pd.DataFrame:
    """
    Calculate season year of flood
    (i.e., shift data to be centered on flood season)
    :param df: input DataFrame
    :param date_col: date column
    :param use_index: bool - if True, use index as date col
    :param season_startdate: date that season starts on (year doesn't matter)
    :return: DataFrame with columns indicating seasonyear and dayofseason
    """
    startdayofyear = season_startdate.timetuple().tm_yday
    if use_index:
        df["dayofseason"] = df.index.dayofyear - startdayofyear
        df["seasonyear"] = (
            pd.to_datetime(df.index.date) - pd.DateOffset(days=startdayofyear)
        ).year
    else:
        df["dayofseason"] = df[date_col].dt.dayofyear - startdayofyear
        df["seasonyear"] = (
            df[date_col] - pd.DateOffset(days=startdayofyear)
        ).dt.year - 1

    df["dayofseason"] = (
        df["dayofseason"].apply(lambda x: x + 365 if x < 1 else x).astype(int)
    )
    df = df.sort_values(["seasonyear", "dayofseason"])
    return df


def get_triggers(
    df: pd.DataFrame,
    threshold: int,
    trigger_col: str = "Water Level (cm)",
    year_col: str = "seasonyear",
    date_col: str = "date",
    season_endday: int = FLOODSEASON_ENDDAY,
) -> pd.DataFrame:
    df_agg = pd.DataFrame()
    df = df.reset_index()
    df = df.sort_values(date_col)
    df = df[df["dayofseason"] < season_endday]
    for year in df[year_col].unique():
        dff = df[df[year_col] == year]
        dff = dff[dff[trigger_col] >= threshold]
        if not dff.empty:
            df_add = pd.DataFrame(
                {"seasonyear": year, "t_date": dff.iloc[0][date_col]},
                index=[0],
            )
            df_agg = pd.concat([df_agg, df_add], ignore_index=True)
    return df_agg


def calculate_return(
    df: pd.DataFrame,
    return_years: list[int] = None,
    quants: np.array = np.linspace(0, 1, 100),
    year_col: str = "seasonyear",
    agg_col: str = "station",
) -> pd.DataFrame:
    if return_years is None:
        return_years = [1.5, 2, 3, 4, 5, 10]

    return


def load_anadia() -> pd.DataFrame:
    filename = "Niger_ANADIA_2023_03_08_allentries.xls"
    filepath = DATA_DIR / "public/raw/ner/anadia" / filename
    df = pd.read_excel(filepath)
    return df


def load_processed_anadia() -> pd.DataFrame:
    filepath = (
        DATA_DIR / "public/processed/ner/anadia/ner_anadia_processed.csv"
    )
    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_processed_floodscan():
    filename = "ner_floodscan_stats_adm3_sel_1998-01-12_to_2022-04-24.csv"
    df = pd.read_csv(PROC_DIR / filename)
    df = df.iloc[:, 1:]
    df["date"] = pd.to_datetime(df["date"])
    df = shift_to_floodseason(df)
    return df


def load_combined_abn() -> pd.DataFrame:
    niamey = load_abn_niamey()
    other = load_abn_other()
    niamey = niamey.reset_index()
    niamey["station"] = "Niamey"
    niamey = niamey.rename(columns={"Date": "date"})
    df = pd.concat([niamey, other])
    return df


def load_abn_niamey() -> pd.DataFrame:
    """
    Load ABN Niamey .xlsx
    :return: DataFrame of observed values
    """
    filepath = DATA_DIR / "private/raw/ner/abn/Données_ Niamey2005_2022.xlsx"
    return pd.read_excel(filepath, skiprows=[0, 1], index_col=0)


def load_abn_other() -> pd.DataFrame:
    filepath = DATA_DIR / "private/raw/ner/abn/Data_Stations_Amont Niamey.txt"
    df = pd.read_csv(
        filepath,
        header=None,
        sep="\t",
    )
    df = df.replace(" ", np.nan)
    df = df.dropna()
    df["station"] = df[0].apply(lambda x: x[11:40].strip())
    df["type"] = df[0].apply(lambda x: x[-1])
    df["date"] = pd.to_datetime(df[2], dayfirst=True)
    df[3] = pd.to_numeric(df[3])
    df = df.pivot(
        columns="type", index=["station", "date"], values=3
    ).reset_index()
    df = df.rename(columns={"C": "Water Level (cm)", "D": "Discharges (m3/s)"})
    df = df[["date", "station", "Water Level (cm)", "Discharges (m3/s)"]]
    df = df.sort_values(["station", "date"])
    return df


def read_raw_floodscan():
    filepath = FS_DIR / FLOODSCAN_FILENAME
    with xr.open_dataset(filepath) as ds:
        return ds


def process_floodscan(ds: xr.Dataset, gdf: gpd.GeoDataFrame):
    coords_transform = (
        ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        .rio.write_crs("EPSG:4326")
        .rio.transform()
    )

    percentile_list = [2, 4, 6, 8, 10, 20]

    # compute statistics on level in adm_path for all dates in ds
    df_list = []
    for date in ds.time.values:
        print(date)
        df = gdf[[ID_COL, "geometry"]]
        ds_date = ds.sel(time=date)

        df[["mean_cell", "max_cell", "min_cell"]] = pd.DataFrame(
            zonal_stats(
                vectors=df,
                raster=ds_date[DATA_VAR].values,
                affine=coords_transform,
                nodata=np.nan,
            )
        )[["mean", "max", "min"]]
        # TODO: the percentiles seem to always return 0,
        #  even if setting the p to 0.00001.
        #  Don't understand why yet..
        df[[f"percentile_{str(p)}" for p in percentile_list]] = pd.DataFrame(
            zonal_stats(
                vectors=df,
                raster=ds_date[DATA_VAR].values,
                affine=coords_transform,
                nodata=np.nan,
                stats=" ".join(
                    [f"percentile_{str(p)}" for p in percentile_list]
                ),
            )
        )[[f"percentile_{str(p)}" for p in percentile_list]]

        df["date"] = pd.to_datetime(date)

        df_list.append(df)
    df_hist = pd.concat(df_list)
    df_hist = df_hist.sort_values(by="date")
    # drop the geometry column, else csv becomes huge
    df_hist = df_hist.drop("geometry", axis=1)

    max_date = pd.to_datetime(ds.time.values.max()).strftime("%Y-%m-%d")
    min_date = pd.to_datetime(ds.time.values.min()).strftime("%Y-%m-%d")
    save_name = f"ner_floodscan_stats_adm3_sel_{min_date}_to_{max_date}.csv"
    df_hist.to_csv(PROC_DIR / save_name)

    return df_hist
