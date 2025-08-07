import pandas as pd
from ochanticipy import CodAB, create_country_config

import utils

pd.options.mode.chained_assignment = None

adm1s = ["Dosso", "Tillabéri", "Niamey"]
country_config = create_country_config("ner")
codab = CodAB(country_config=country_config)
codab = codab.load(admin_level=3)
codab = codab[codab["adm_01"].isin(adm1s)]

ds = utils.read_raw_floodscan()
df = utils.process_floodscan(ds, codab)
