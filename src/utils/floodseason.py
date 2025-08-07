import datetime

import pandas as pd

FLOODSEASON_START = datetime.date(2000, 6, 1)
FLOODSEASON_START_DAYOFYEAR = FLOODSEASON_START.timetuple().tm_yday


def shift_to_floodseason_corrected(
    df: pd.DataFrame, date_col: str = "date"
) -> pd.DataFrame:
    df["year"] = df[date_col].dt.year
    df["dayofyear"] = df[date_col].dt.dayofyear
    df["dayofseason"] = (
        df["dayofyear"] - FLOODSEASON_START_DAYOFYEAR + 1
    ) % 365 + 1
    df["seasonyear"] = df["year"] - (
        df["dayofyear"] < FLOODSEASON_START_DAYOFYEAR
    ).astype(int)
    # add 0.5 for extra day from leap year
    df["dayofseason"] = df.apply(
        lambda x: x["dayofseason"] + 0.5
        if x["dayofyear"] == 366
        else x["dayofseason"],
        axis=1,
    )
    return df


def shift_to_floodseason(
    df: pd.DataFrame,
    date_col: str = "date",
    use_index: bool = False,
    season_startdate: datetime.date = FLOODSEASON_START,
) -> pd.DataFrame:
    """
    Calculate season year of flood
    (i.e., shift data to be centered on flood season)
    :param df: input DataFrame
    :param date_col: date column
    :param use_index: bool - if True, use index as date col
    :param season_startdate: date that season starts on (year doesn't matter)
    :return: DataFrame with columns indicating seasonyear and dayofseason
    """
    startdayofyear = season_startdate.timetuple().tm_yday
    if use_index:
        df["dayofseason"] = df.index.dayofyear - startdayofyear
        df["seasonyear"] = (
            pd.to_datetime(df.index.date) - pd.DateOffset(days=startdayofyear)
        ).year
    else:
        df["dayofseason"] = df[date_col].dt.dayofyear - startdayofyear + 2
        df["seasonyear"] = (
            df[date_col] - pd.DateOffset(days=startdayofyear + 2)
        ).dt.year + 1

    df["dayofseason"] = (
        df["dayofseason"].apply(lambda x: x + 365 if x < 1 else x).astype(int)
    )
    df = df.sort_values(["seasonyear", "dayofseason"])
    return df
