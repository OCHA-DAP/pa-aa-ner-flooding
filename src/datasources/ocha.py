import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
COMMUNES_RAW_PATH = (
    DATA_DIR
    / "public"
    / "raw"
    / "ner"
    / "ocha"
    / "AA Inondations - Classification des communes potentielles_"
    "VF_résultat atelier_OIM.xlsx"
)


def load_communes() -> pd.DataFrame:
    return pd.read_excel(
        COMMUNES_RAW_PATH,
        sheet_name="Tillaberi + Dosso",
    )
