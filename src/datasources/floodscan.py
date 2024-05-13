import os
from pathlib import Path

import pandas as pd
import xarray as xr
from tqdm import tqdm

from src.datasources import codab, worldpop

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
RAW_FS_HIST_S_PATH = (
    DATA_DIR
    / "private"
    / "raw"
    / "glb"
    / "FloodScan"
    / "SFED"
    / "SFED_historical"
    / "aer_sfed_area_300s_19980112_20231231_v05r01.nc"
)
PROC_FS_DIR = DATA_DIR / "private" / "processed" / "ner" / "floodscan"


def clip_ner_from_glb():
    ds = xr.open_dataset(RAW_FS_HIST_S_PATH)
    da = ds["SFED_AREA"]
    da = da.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
    da = da.rio.write_crs(4326)
    adm0 = codab.load_codab(admin_level=0)
    lonmin, latmin, lonmax, latmax = adm0.total_bounds
    sfed_box = da.sel(lat=slice(latmax, latmin), lon=slice(lonmin, lonmax))
    sfed_box = sfed_box.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
    sfed_clip = sfed_box.rio.clip(adm0.geometry, all_touched=True)
    if "grid_mapping" in sfed_clip.attrs:
        del sfed_clip.attrs["grid_mapping"]
    filename = "ner_sfed_1998_2023.nc"
    if not PROC_FS_DIR.exists():
        PROC_FS_DIR.mkdir(parents=True)
    sfed_clip.to_netcdf(PROC_FS_DIR / filename)


def load_raw_ner_floodscan():
    filename = "ner_sfed_1998_2023.nc"
    ds = xr.open_dataset(PROC_FS_DIR / filename)
    da = ds["SFED_AREA"]
    da = da.rio.write_crs(4326).drop_vars("crs")
    return da


def calc_daily_exposure():
    """Calculate daily flood exposure by admin3.
    Takes about an hour.
    """
    adm3 = codab.load_codab(admin_level=3, aoi_only=True)
    pop = worldpop.load_raw_worldpop()
    da = load_raw_ner_floodscan()
    da_mask = da.where(da > 0)
    da_mask = da_mask.rio.write_crs(4326)
    da_mask = da_mask.transpose("time", "lat", "lon")
    dfs = []
    for year, da_y in tqdm(da_mask.groupby("time.year")):
        das = []
        for t in da_y.time.values:
            da_t = da_y.sel(time=t)
            da_t_rep = da_t.rio.reproject_match(pop)
            da_t_rep = da_t_rep.where(da_t_rep <= 1)
            exp_t = pop.squeeze(drop=True) * da_t_rep
            exp_t["time"] = t
            das.append(exp_t)
        exp = xr.concat(das, dim="time")
        for pcode, group in adm3.groupby("ADM3_PCODE"):
            exp_clip = exp.rio.clip(group.geometry)
            exp_clip = exp_clip.where(exp_clip >= 0)
            df_in = (
                exp_clip.sum(dim=["x", "y"])
                .to_dataframe(name="total_exposed")["total_exposed"]
                .astype(int)
                .reset_index()
            )
            df_in["ADM3_PCODE"] = pcode
            dfs.append(df_in)

    df = pd.concat(dfs)
    filename = "ner_adm3_totalexposed_daily_1998_2023.csv"
    df.to_csv(PROC_FS_DIR / filename, index=False)


def load_daily_exposure():
    filename = "ner_adm3_totalexposed_daily_1998_2023.csv"
    return pd.read_csv(PROC_FS_DIR / filename, parse_dates=["time"])


def load_ciblage():
    filename = "ner-ciblage-communes.xlsx"
    return pd.read_excel(PROC_FS_DIR / filename)
