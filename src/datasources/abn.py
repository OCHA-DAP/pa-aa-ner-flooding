import os
from pathlib import Path

import pandas as pd

from src import blob_utils

DATA_DIR = Path(os.environ["AA_DATA_DIR"])


def load_abn_niamey(local: bool = False) -> pd.DataFrame:
    """
    Load ABN Niamey .xlsx
    :return: DataFrame of observed values
    """
    filename = "Données_ Niamey2005_2022.xlsx"
    if local:
        filepath = Path("temp") / filename
    else:
        filepath = (
            DATA_DIR / "private/raw/ner/abn/Données_ Niamey2005_2022.xlsx"
        )
    return pd.read_excel(filepath, skiprows=[0, 1], index_col=0)


def load_current_monitoring(year: int = 2024) -> pd.DataFrame:
    """Load current monitoring data as recorded from SATH-ABN site"""
    if year == 2024:
        blob_name = (
            f"{blob_utils.PROJECT_PREFIX}/raw/abn/"
            f"niger_flood_framework_monitoring - Sheet1.csv"
        )
    elif year == 2025:
        blob_name = (
            f"{blob_utils.PROJECT_PREFIX}/raw/abn/"
            f"niger_flood_framework_monitoring_2025 - Sheet1.csv"
        )
    else:
        raise ValueError("Year not supported")
    df = blob_utils.load_csv_from_blob(blob_name, parse_dates=["date"])
    cols = ["date", "level (cm)"]
    df = df[cols].rename(columns={"level (cm)": "level"}).dropna()
    return df
