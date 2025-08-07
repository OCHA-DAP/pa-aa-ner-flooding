import fsspec
import ocha_stratus as stratus
import xarray as xr

from src.constants import PROJECT_PREFIX


def load_grdc(station_id: int, cols: list = None) -> xr.Dataset:
    blob_name = f"{PROJECT_PREFIX}/raw/grdc/GRDC-Daily.nc"
    url = stratus.get_container_client().get_blob_client(blob_name).url
    fs = fsspec.filesystem("https")
    ds = xr.open_dataset(fs.open(url), engine="h5netcdf", chunks={})
    if cols is None:
        cols = ["time", "runoff_mean"]
    return ds.sel(id=station_id).to_dataframe().reset_index()[cols].copy()
