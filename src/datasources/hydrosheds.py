import os
from pathlib import Path

import geopandas as gpd

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
HS_RAW_DIR = DATA_DIR / "public" / "raw" / "glb" / "hydrosheds"
RIVERS_DIR = HS_RAW_DIR / "HydroRIVERS_v10_af_shp" / "HydroRIVERS_v10_af_shp"
HS_PROC_DIR = DATA_DIR / "public" / "processed" / "glb" / "hydrosheds"


def load_all_rivers():
    return gpd.read_file(RIVERS_DIR)


def load_niger_river():
    filename = "niger_river"
    return gpd.read_file(HS_PROC_DIR / filename)
