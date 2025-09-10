import os
from pathlib import Path
from typing import Literal

import numpy as np
import ocha_stratus as stratus
import pandas as pd
import xarray as xr
from tqdm.auto import tqdm

from src.constants import PROJECT_PREFIX
from src.utils import cds_utils

GF_STATIONS = {
    "garbekourou": {
        "lon": 1.625,
        "lat": 13.72,
    },
    "niamey": {
        "lon": 2.075,
        "lat": 13.52,
    },
}


def get_blob_name(
    data_type: Literal["raw", "processed"],
    dataset: Literal["reanalysis", "reforecast", "forecast"],
    station_name: str,
    year: int = None,
) -> str:
    if year is None and data_type == "raw":
        raise ValueError("Year must be provided for raw data")
    if data_type == "raw":
        return f"{PROJECT_PREFIX}/{data_type}/glofas/{dataset}/glofas_{data_type}_{dataset}_{station_name}_{year}.grib"  # noqa
    return f"{PROJECT_PREFIX}/{data_type}/glofas/glofas_{dataset}_{station_name}.parquet"  # noqa


def get_glofas_grid_coords(lon, lat):
    grid_lat = np.arange(-90.025, 90, 0.05)
    grid_lon = np.arange(-180.025, 180, 0.05)
    nearest_lat_idx = (np.abs(grid_lat - lat)).argmin()
    nearest_lon_idx = (np.abs(grid_lon - lon)).argmin()
    return round(grid_lon[nearest_lon_idx], 3), round(
        grid_lat[nearest_lat_idx], 3
    )


def download_reanalysis_year(
    year: int,
    station_name: str = None,
    lon: float = None,
    lat: float = None,
    pitch: float = 0.001,
    clobber: bool = False,
    glofas_version: str = "version_4_0",
    centered: bool = False,
):
    if station_name is None and (lat is None or lon is None):
        raise ValueError("Either station_name or lat and lon must be provided")
    if station_name is not None and (lat is not None or lon is not None):
        raise ValueError(
            "Only one of station_name or lat and lon should be provided"
        )
    if station_name is None:
        # Create a dummy station name based on lat and lon
        station_name = f"lat{lat}_lon{lon}"
        glofas_lon, glofas_lat = get_glofas_grid_coords(lon, lat)
    else:
        if station_name not in GF_STATIONS:
            raise ValueError(
                f"Station name {station_name} not found in GF_STATIONS"
            )
        else:
            station = GF_STATIONS[station_name]
            glofas_lon, glofas_lat = get_glofas_grid_coords(
                station["lon"], station["lat"]
            )
    if centered:
        N = glofas_lat + pitch / 2
        S = glofas_lat - pitch / 2
        E = glofas_lon + pitch / 2
        W = glofas_lon - pitch / 2
    else:
        N = glofas_lat + pitch
        S = glofas_lat
        E = glofas_lon + pitch
        W = glofas_lon
    dataset = "cems-glofas-historical"
    request = {
        "system_version": [glofas_version],
        "hydrological_model": ["lisflood"],
        "product_type": ["consolidated"],
        "variable": ["river_discharge_in_the_last_24_hours"],
        "hyear": [f"{year}"],
        "hmonth": [f"{x:02}" for x in range(1, 13)],
        "hday": [f"{x:02}" for x in range(1, 32)],
        "data_format": "grib2",
        "download_format": "unarchived",
        "area": [N, W, S, E],
    }
    blob_name = get_blob_name("raw", "reanalysis", station_name, year)
    # check if blob exists
    if (
        not clobber
        and stratus.get_container_client().get_blob_client(blob_name).exists()
    ):
        print(f"{blob_name} already exists in blob storage")
        return
    return cds_utils.download_raw_cds_api_to_blob(dataset, request, blob_name)


def load_reanalysis_year(
    data_type: Literal["raw", "processed"],
    station_name: str = None,
    lat: float = None,
    lon: float = None,
    year: int = None,
):
    if station_name is None and (lat is None or lon is None):
        raise ValueError("Either station_name or lat and lon must be provided")
    if station_name is not None and (lat is not None or lon is not None):
        raise ValueError(
            "Only one of station_name or lat and lon should be provided"
        )
    if station_name is None:
        # Create a dummy station name based on lat and lon
        station_name = f"lat{lat}_lon{lon}"
    blob_name = get_blob_name(data_type, "reanalysis", station_name, year)
    if data_type == "raw":
        local_filepath = "temp" / Path(blob_name)
        if not local_filepath.exists():
            blob_data = stratus.load_blob_data(blob_name)
            print(f"Downloading {blob_name} to {local_filepath}")
            if not local_filepath.parent.exists():
                os.makedirs(local_filepath.parent)
            with open(local_filepath, "wb") as file:
                file.write(blob_data)
        return xr.load_dataset(
            local_filepath, backend_kwargs={"decode_timedelta": True}
        )
    elif data_type == "processed":
        return stratus.load_parquet_from_blob(blob_name)


def process_reanalysis(station_name: str):
    raw_blob_dir = "/".join(
        get_blob_name("raw", "reanalysis", station_name, year=0).split("/")[
            :-1
        ]
    )
    blob_names = [
        x
        for x in stratus.list_container_blobs(name_starts_with=raw_blob_dir)
        if x.endswith(".grib") and station_name in x
    ]
    dfs = []
    for blob_name in tqdm(blob_names):
        year = int(blob_name.split(".")[0].split("_")[-1])
        ds = load_reanalysis_year(
            data_type="raw", station_name=station_name, year=year
        )
        da = ds["dis24"]
        df_in = da.to_dataframe().reset_index()[["time", "dis24"]]
        dfs.append(df_in)
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("time")
    blob_name = get_blob_name("processed", "reanalysis", station_name)
    stratus.upload_parquet_to_blob(df, blob_name)


def load_reanalysis(station_name: str):
    blob_name = get_blob_name("processed", "reanalysis", station_name)
    return stratus.load_parquet_from_blob(blob_name)
