# mangrove-asset-pricing

Replication code and data for **"Private Value of Mangrove Coastal Protection Benefits"** (Liu, Beck, Constantz, Reguero, and Hale, 2026).

The analysis values mangrove flood-protection benefits in seven coastal Florida counties using two complementary approaches: an engineering avoided-damages calculation and a consumption-based asset-pricing valuation calibrated to housing-market responses to major hurricanes.

## Notebook overview

| Notebook | Role |
|---|---|
| `main.ipynb` | Main analysis. Reads damage tables and the building sample, computes engineering and market-based NPV of protection benefits per county and return period, writes most files in `output/`. |
| `figures.ipynb` | Generates publication figures from the result CSVs. |
| `robustness.ipynb` | Value-weighted variants of the main analysis; writes the `*_valueweighted.csv` outputs. |
| `rentalyield.ipynb` | Standalone calibration of the housing service-flow yield (δ) from FRED PCE series. Output: a single number used downstream. |

## Citation

See [`CITATION.cff`](./CITATION.cff). The canonical reference is:

> Liu, T., Beck, M., Constantz, B., Reguero, B., & Hale, G. (2026). *Private Value of Mangrove Coastal Protection Benefits*. 

## Contact

Galina Hale — <gbhale@ucsc.edu>
Teng Liu — <tedliu@ucsc.edu>
