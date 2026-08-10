---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: pa-aa-ner-flooding
    language: python
    name: pa-aa-ner-flooding
---

# Process 2025 ANADIA

Just matching strings to assign PCODEs

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import unicodedata
import re

import ocha_stratus as stratus
import pandas as pd

from src.datasources import codab
from src.constants import *
```

```python
adm3 = codab.load_codab_from_blob(admin_level=3, aoi_only=False)
```

```python
adm3.plot()
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/anadia/traité_1998-2024_FréqMoyenne.xlsx"
df_anadia = pd.read_excel(stratus.load_blob_data(blob_name))
```

```python
def normalize_string(s):
    # Lowercase
    s = s.lower()
    # Remove accents
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Remove all non-alphanumeric characters
    s = re.sub(r"[^a-z0-9]", "", s)
    return s
```

```python
df_anadia["Communes_norm"] = df_anadia["Communes"].apply(normalize_string)
adm3["adm3_match"] = adm3["ADM3_FR"].apply(normalize_string)
```

```python
adm3[adm3.duplicated(subset="Communes_norm", keep=False)]
```

```python
def int_to_roman(num):
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = [
        "M",
        "CM",
        "D",
        "CD",
        "C",
        "XC",
        "L",
        "XL",
        "X",
        "IX",
        "V",
        "IV",
        "I",
    ]
    roman = ""
    for i in range(len(val)):
        count = num // val[i]
        roman += syms[i] * count
        num -= val[i] * count
    return roman


def int_to_roman_name_dict(name, max_int):
    return {
        f"{name}{x}": f"{name}{int_to_roman(x).lower()}"
        for x in range(1, max_int + 1)
    }
```

```python
correct_names = {
    "falenco": "falenko",
}
correct_names.update(int_to_roman_name_dict("niamey", 5))
correct_names.update(int_to_roman_name_dict("maradi", 3))
correct_names.update(int_to_roman_name_dict("tahoua", 2))
correct_names.update(int_to_roman_name_dict("zinder", 5))
correct_names.update(int_to_roman_name_dict("tombokoirey", 2))
correct_names.update(int_to_roman_name_dict("roumbou", 1))
df_anadia["adm3_match"] = df_anadia["Communes_norm"].replace(correct_names)
```

```python
specific_pcodes = {
    "tibirimaradi": "NE004005005",
    "tibiridoutchi": "NE003008004",
    "gangaratanout": "NE007009002",
    "gangaraaguie": "NE004004001",
}
```

```python
df_anadia_merge = df_anadia.merge(
    adm3[["adm3_match", "ADM3_PCODE"]], how="outer"
)
df_anadia_merge["ADM3_PCODE"] = df_anadia_merge["ADM3_PCODE"].fillna(
    df_anadia_merge["adm3_match"].map(specific_pcodes)
)
# df_anadia_merge.merge(adm3[["ADM3_PCODE", how="outer")
```

```python
df_anadia_merge[df_anadia_merge["ADM3_PCODE"].isnull()].sort_values("Communes")
```

```python
df_anadia_merge
```

```python
df_anadia_merge[df_anadia_merge["Communes"].isnull()].sort_values("ADM3_FR")
```

```python
adm3[adm3["ADM3_FR"].astype(str).str.contains("Tibiri")]
```

```python
df_anadia_merge["ADM3_PCODE"].fillna(
    df_anadia_merge["adm3_match"].replace(specific_pcodes)
)
```

```python
blob_name = f"{PROJECT_PREFIX}/processed/anadia/anadia_summary_2024.parquet"
stratus.upload_parquet_to_blob(
    df_anadia_merge.drop(columns=["adm3_match", "Communes_norm"]), blob_name
)
```

```python

```
