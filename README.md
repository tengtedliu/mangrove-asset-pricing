# mangrove-asset-pricing

Replication code and data for **"Private Value of Mangrove Coastal Protection Benefits"** (Liu, Beck, Constantz, Reguero, and Hale, 2026).

The analysis values mangrove flood-protection benefits in seven coastal Florida counties using two complementary approaches: an engineering avoided-damages calculation and a consumption-based asset-pricing valuation calibrated to housing-market responses to major hurricanes.

## Repository structure

```
mangrove-asset-pricing/
├── README.md
├── CITATION.cff
├── requirements.txt
├── .gitignore
│
├── main.ipynb                            # main analysis: engineering + market valuations
├── robustness.ipynb                      # value-weighted robustness checks
├── figures.ipynb                         # publication figures
├── rentalyield.ipynb                     # rental-yield (delta) calibration from FRED
│
├── data/                                 # inputs read by the notebooks
│   ├── ALL_damages_by_county_florida.csv
│   ├── Florida_damage_dollar_stats_by_county_florida.csv
│   ├── Florida_fixed_building_sample_florida.csv
│   └── Florida_fixed_building_sample_florida_v3.csv
│
└── output/                               # empty placeholder; populated by running the notebooks
    └── .gitkeep
```

Running the notebooks writes `*.csv` result tables and `*.png` figures into `output/`. See [Reproduction steps](#reproduction-steps) for the run order.

## Notebook overview

| Notebook | Role |
|---|---|
| `rentalyield.ipynb` | Standalone calibration of the housing service-flow yield (δ) from FRED PCE series. Output: a single number used downstream. |
| `main.ipynb` | Main analysis. Reads damage tables and the building sample, computes engineering and market-based NPV of protection benefits per county and return period, writes most files in `output/`. |
| `robustness.ipynb` | Value-weighted variants of the main analysis; writes the `*_valueweighted.csv` outputs. |
| `figures.ipynb` | Generates publication figures from the result CSVs. |

## Reproduction steps

1. **Set up the environment.** Python 3.10 or newer.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **API key for FRED.** `rentalyield.ipynb` calls the FRED API. Replace `FRED_API_KEY = "YOUR API KEY"` with a key from <https://fred.stlouisfed.org/docs/api/api_key.html>. The other three notebooks read only local files in `data/` and `output/`.

   The CSVs in `data/` are committed; `output/` ships empty and is repopulated by running the notebooks (see step 3).

3. **Run the notebooks in this order, from the repo root:**

   ```bash
   jupyter lab
   ```

   All paths in the notebooks are relative to the repo root, so launch Jupyter from `mangrove-asset-pricing/` and run:

   1. `rentalyield.ipynb` — produces δ (a scalar pasted into `main.ipynb`). Quick.
   2. `main.ipynb` — main results; reads `data/*.csv`, writes most of `output/`. Runs ~5–10 min on a laptop with `N_SIMULATIONS = 1000` (the default in the storm-matrix cell).
   3. `robustness.ipynb` — value-weighted variants; reads `data/*.csv`, writes `output/*_valueweighted.csv`. Same order of magnitude as `main.ipynb`.
   4. `figures.ipynb` — figures from the result CSVs in `output/`. Quick.

   Each notebook is idempotent: re-running overwrites the corresponding CSVs and PNGs in `output/`. Together they regenerate paper Figures 2, 3, and 4 as `output/storm_timeline_combined.png`, `output/xiPA.png`, and `output/allresults_w.png` respectively. (Figure 1 is GIS work and is not produced by these notebooks.)

## Data sources

- `data/ALL_damages_by_county_florida.csv` — county-level damage table produced upstream from catastrophe-risk model runs (RMS/Hazus pipeline, see paper §2).
- `data/Florida_damage_dollar_stats_by_county_florida.csv` — county summary statistics.
- `data/Florida_fixed_building_sample_florida{,_v3}.csv` — fixed sample of buildings used for hedonic and engineering comparisons.
- All output files are reproducible from the inputs by running the notebooks above.

The notebooks additionally read several Google Sheets (e.g. `ResultsGH`, `xi_h_inputsMeanPA`) hosted on the authors' Drive. External Sheets access is required to refresh those values; pre-fetched CSVs are not committed here.

## Citation

See [`CITATION.cff`](./CITATION.cff). The canonical reference is:

> Liu, T., Beck, M., Constantz, B., Reguero, B., & Hale, G. (2026). *Private Value of Mangrove Coastal Protection Benefits*. 

## Contact

Galina Hale — <gbhale@ucsc.edu>
Teng Liu — <tedliu@ucsc.edu>
