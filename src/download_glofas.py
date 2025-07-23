import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from ochanticipy import (  # GlofasForecast,; GlofasReanalysis,
    CodAB,
    GeoBoundingBox,
    GlofasReforecast,
    create_country_config,
)

load_dotenv()

PROC_DIR = Path(os.environ["OAP_DATA_DIR"]) / "public/processed/ner/glofas"

adm1_sel = ["Tillabéri", "Niamey", "Dosso", "Maradi"]
startdate = datetime.date(1900, 1, 1)
enddate = datetime.date(2023, 12, 31)

country_config = create_country_config(iso3="ner")
codab = CodAB(country_config=country_config)
# codab.download()
gdf_adm1 = codab.load(admin_level=1)
gdf_aoi = gdf_adm1[gdf_adm1["adm_01"].isin(adm1_sel)]
geobb = GeoBoundingBox.from_shape(gdf_aoi)

glofas_forecast = GlofasReforecast(
    country_config=country_config,
    geo_bounding_box=geobb,
    leadtime_max=15,
    start_date=startdate,
    end_date=enddate,
)

glofas_forecast.download()
