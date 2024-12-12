import os
import shutil
from pathlib import Path

import geopandas as gpd
import requests

from src.constants import ADM1_AOI_PCODES

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
CODAB_PATH = DATA_DIR / "public" / "raw" / "ner" / "codab" / "ner.shp.zip"


def download_codab():
    url = "https://data.fieldmaps.io/cod/originals/ner.shp.zip"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(CODAB_PATH, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print(
            f"Failed to download file. "
            f"HTTP response code: {response.status_code}"
        )


def load_codab(admin_level: int = 3, aoi_only: bool = False):
    gdf = gpd.read_file(CODAB_PATH)
    if aoi_only:
        gdf = gdf[gdf["ADM1_PCODE"].isin(ADM1_AOI_PCODES)]
    if admin_level == 2:
        cols = [x for x in gdf.columns if "ADM3" not in x]
        gdf = gdf.dissolve("ADM2_PCODE").reset_index()[cols]
    elif admin_level == 1:
        cols = [x for x in gdf.columns if "ADM3" not in x and "ADM2" not in x]
        gdf = gdf.dissolve("ADM1_PCODE").reset_index()[cols]
    elif admin_level == 0:
        cols = [
            x
            for x in gdf.columns
            if "ADM3" not in x and "ADM2" not in x and "ADM1" not in x
        ]
        gdf = gdf.dissolve("ADM0_PCODE").reset_index()[cols]
    return gdf
