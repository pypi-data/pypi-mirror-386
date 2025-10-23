from collections import defaultdict

import pandas as pd
from kumoapi.typing import Dtype, Stype

MAX_CAT = 100


def contains_multicategorical(
    ser: pd.Series,
    column_name: str,
    dtype: Dtype,
) -> bool:

    if not Stype.multicategorical.supports_dtype(dtype):
        return False

    if dtype == Dtype.stringlist:
        return True

    ser = ser.iloc[:500]
    ser = ser.dropna()

    num_unique: int = 0
    if dtype == Dtype.string:
        ser = ser.astype(str)
        text = '\n'.join(ser)

        white_list = {';', ':', '|', '\t'}
        candidates: dict[str, int] = defaultdict(int)
        for char in text:
            if char in white_list:
                candidates[char] += 1

        if len(candidates) == 0:
            return False

        num_unique = ser.nunique()

        sep = max(candidates, key=candidates.get)  # type: ignore
        ser = ser.str.split(sep)

    num_unique_multi = ser.explode().nunique()

    if dtype.is_list():
        return num_unique_multi <= MAX_CAT

    return num_unique > 1.5 * num_unique_multi and num_unique_multi <= MAX_CAT
