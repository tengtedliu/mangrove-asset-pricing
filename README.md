# mangrove-asset-pricing

Replication code and data for **"Private Value of Mangrove Coastal Protection Benefits"** (Liu, Beck, Constantz, Reguero, Gutiérrez-Barceló, and Hale, 2026).

The analysis values mangrove flood-protection benefits in seven coastal Florida counties using two complementary approaches: an engineering avoided-damages calculation and a consumption-based asset-pricing valuation calibrated to housing-market responses to major hurricanes.

## Notebook overview

| Notebook | Role |
|---|---|
| `main.ipynb` | Main analysis. Reads damage tables and the building sample, computes engineering and market-based NPV of protection benefits per county and return period, writes most files in `output/`. |
| `figures.ipynb` | Generates the **non-map** publication figures (chart-style plots — e.g., the loss-parameter and storm-timeline charts) from the result CSVs. County *map* figures are produced separately by `maps/` (see "Map figures" below). |
| `robustness.ipynb` | Value-weighted variants of the main analysis; writes the `*_valueweighted.csv` outputs. |
| `rentalyield.ipynb` | Standalone calibration of the housing service-flow yield (δ) from FRED PCE series. Output: a single number used downstream. |

## Map figures

`maps/make_paper_figures.py` renders the county map figures used in the
manuscript — main-text Figure 4 and the two SI map figures — from the
notebook outputs. Run after `main.ipynb`:

```
python maps/make_paper_figures.py
```

Each figure is written to `output/` as PDF and PNG, in a titled version and
a `_lettersonly` version (panel descriptions are provided in the manuscript
captions). The script also writes `output/county_AEB_NPV_RP1anchor.csv`,
the per-county annual expected benefit and present value table underlying
the SI figure.

County geometry comes from `data/FL_counties_coastclipped_cb2023.gpkg`
(U.S. Census cartographic boundaries, clipped to the shoreline). Hillshade
terrain tiles (public domain) are downloaded and cached under
`output/basemap_cache/` on first run. Requires `geopandas`, `shapely`, and
`Pillow` (see `requirements.txt`).

## Citation

See [`CITATION.cff`](./CITATION.cff). The canonical reference is:

> Liu, T., Beck, M., Constantz, B., Reguero, B., Gutiérrez-Barceló, D., & Hale, G. (2026). *Private Value of Mangrove Coastal Protection Benefits*. 

## Contact

Galina Hale — <gbhale@ucsc.edu>
Teng Liu — <tedliu@ucsc.edu>
