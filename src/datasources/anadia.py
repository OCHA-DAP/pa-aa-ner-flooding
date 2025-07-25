import os
from pathlib import Path

import ocha_stratus as stratus
import pandas as pd

from src.blob_utils import PROJECT_PREFIX

DATA_DIR = Path(os.environ["AA_DATA_DIR"])


def load_processed_anadia(from_blob: bool = False) -> pd.DataFrame:
    if from_blob:
        blob_name = (
            f"{PROJECT_PREFIX}/processed/anadia/ner_anadia_processed.csv"
        )
        df = stratus.load_csv_from_blob(blob_name, stage="dev")
    else:
        filepath = (
            DATA_DIR / "public/processed/ner/anadia/ner_anadia_processed.csv"
        )
        df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"])
    df["ADM3_PCODE"] = df["rowcacode3"].str.replace("R", "")
    return df
