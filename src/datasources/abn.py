import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ["AA_DATA_DIR"])


def load_abn_niamey() -> pd.DataFrame:
    """
    Load ABN Niamey .xlsx
    :return: DataFrame of observed values
    """
    filepath = DATA_DIR / "private/raw/ner/abn/Données_ Niamey2005_2022.xlsx"
    return pd.read_excel(filepath, skiprows=[0, 1], index_col=0)
