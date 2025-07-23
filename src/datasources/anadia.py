import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ["AA_DATA_DIR"])


def load_processed_anadia() -> pd.DataFrame:
    filepath = (
        DATA_DIR / "public/processed/ner/anadia/ner_anadia_processed.csv"
    )
    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"])
    df["ADM3_PCODE"] = df["rowcacode3"].str.replace("R", "")
    return df
