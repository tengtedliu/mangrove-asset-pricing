"""
Renders the county map figures used in the manuscript.

  Fig4_alt_climate_2x3 (+ _lettersonly)
      Main-text Figure 4. Rows: protection value per property (A-C) and
      county totals (D-F). Columns: market-based asset pricing (hedonic);
      risk-based asset pricing (catastrophic), present day; risk-based
      asset pricing, climate change 2050.

  FigSI_hydro_AEB_PV_1x3 (+ _lettersonly)
      SI: annual expected benefit (AEB) of mangroves from direct damages,
      present day (A) and climate change 2050 (B, shared color scale), and
      the 77-year present value at 5% per year (C). AEB is a trapezoidal
      integration of avoided damages over annual exceedance probability at
      return periods 10, 25, 50, and 100 years, extended to a zero-damage
      anchor at the 1-year return period.

  FigSI_expected_damages_vs_assetpricing_PV_1x2 (+ _lettersonly)
      SI appendix: present value of expected avoided damages vs the
      asset-pricing county totals, both restricted to the modeled storms
      (return periods 10-100, no anchor), on one shared color scale.

The _lettersonly variants carry panel letters only; panel descriptions are
provided in the manuscript captions. All figures are 7.1 in wide (PNAS
two-column) and are written to output/ as PDF and PNG at 400 dpi. The
script also writes output/county_AEB_NPV_RP1anchor.csv, the per-county
AEB and present-value table underlying the SI figure.

Inputs:
  output/assessment_results_long.csv     written by main.ipynb
  data/ALL_damages_by_county_florida_10m_v2.csv
  data/FL_counties_coastclipped_cb2023.gpkg
Terrain tiles for the hillshade are fetched automatically on first run and
cached under output/basemap_cache/ (public domain; see maps/basemap.py).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import MaxNLocator

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 7,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 400,
})

import basemap as bm  # noqa: E402  (rcParams must be set before first draw)

BASE = Path(__file__).resolve().parents[1]
ASSESS = BASE / "output" / "assessment_results_long.csv"
DAMAGES = BASE / "data" / "ALL_damages_by_county_florida_10m_v2.csv"
OUT = BASE / "output"

GREEN_CMAP = LinearSegmentedColormap.from_list(
    "benefit", ["#F7FBF4", "#CDE8C6", "#8ED08F", "#41A65C", "#0B5D32"])

RP_YEARS = {"RP010": 10, "RP025": 25, "RP050": 50, "RP100": 100}
R = 0.05
ann_due = lambda n: (1 - (1 + R) ** -n) / R * (1 + R)
trapezoid = getattr(np, "trapezoid", None) or getattr(np, "trapz")


def fmt_k(v):
    return f"(${v/1e3:,.0f}K)" if v >= 950 else f"(${v:,.0f})"


def fmt_busd(v):
    b = v / 1e9
    return f"(${b*1e3:,.0f}M)" if b < 1 else f"(${b:,.1f}B)"


def fmt_myr(v):
    return f"(${v/1e6:,.0f}M/yr)"


def add_row_cbar(fig, axes, norm, cmap, tickfmt, nticks=4, wfrac=0.42):
    boxes = [ax.get_position() for ax in axes]
    x0 = min(b.x0 for b in boxes)
    x1 = max(b.x1 for b in boxes)
    y0 = min(b.y0 for b in boxes)
    w = (x1 - x0) * wfrac
    cax = fig.add_axes([x0 + (x1 - x0 - w) / 2, y0 - 0.031, w, 0.013])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation="horizontal")
    ticks = [t for t in MaxNLocator(nticks).tick_values(norm.vmin, norm.vmax)
             if norm.vmin <= t <= norm.vmax]
    cb.set_ticks(ticks)
    cb.ax.set_xticklabels([tickfmt(t) for t in ticks])
    cb.ax.tick_params(labelsize=6.5, width=0.5, length=2)
    cb.outline.set_linewidth(0.5)


def load_assessment():
    a = pd.read_csv(ASSESS)
    if "ratio_type" in a.columns:
        a = a[a.ratio_type == "mean_ratio"]
    else:  # earlier export naming
        a = a[a.stat_type == "mean"]
    return a


def aeb_series(anchor_rp=None):
    """AEB per county and period from the damage table. anchor_rp=1 appends
    a zero-damage point at the 1-year return period; anchor_rp=None
    integrates the modeled storms (return periods 10-100) only."""
    al = pd.read_csv(DAMAGES)
    al["total_damage"] = al["total_damage"].replace(
        r"[\$, ]", "", regex=True).astype(float)
    pairs = {"historic": ("S1", "S2"), "climate": ("S1CC", "S2CC")}
    out = {}
    for period, (s_with, s_without) in pairs.items():
        vals = {}
        for cty, d in al.groupby("county"):
            piv = d.pivot_table(index="return_period", columns="scenario",
                                values="total_damage")
            av = piv[s_without] - piv[s_with]
            aep = np.array([1.0 / RP_YEARS[k] for k in av.index])
            o = np.argsort(aep)
            y, x = av.values[o], aep[o]
            if anchor_rp is not None:
                y = np.append(y, 0.0)
                x = np.append(x, 1.0 / anchor_rp)
            vals[cty] = float(trapezoid(y, x))
        out[period] = pd.Series(vals)
    return out


def fig4(path, journal=False, figwidth_in=7.1):
    a = load_assessment()
    sel = {}
    for key, assess, scen in [("mkt", "market", "baseline"),
                              ("eng", "engineering", "baseline"),
                              ("eng_cc", "engineering", "climate_change")]:
        sel[key] = a[(a.assessment == assess)
                     & (a.scenario == scen)].set_index("county")
    per_prop = {k: sel[k]["per_property_protection"].to_dict() for k in sel}
    totals = {k: sel[k]["aggregate_at_risk_protection"].to_dict() for k in sel}

    cols = [("Market-based asset pricing (hedonic)", "mkt"),
            ("Risk-based asset pricing (catastrophic)", "eng"),
            ("Risk-based asset pricing; climate change 2050", "eng_cc")]

    gdf, labels, view = bm.load()
    fig = plt.figure(figsize=(figwidth_in, figwidth_in * 0.80))
    gs = fig.add_gridspec(2, 3, wspace=0.02, hspace=0.46,
                          left=0.005, right=0.995, top=0.93, bottom=0.075)
    n_pp = Normalize(0, max(max(d.values()) for d in per_prop.values()))
    n_tot = Normalize(0, max(max(d.values()) for d in totals.values()))
    row_specs = [
        ("Mangrove protection value per property", per_prop, n_pp, fmt_k,
         lambda t: f"${t/1e3:g}K" if t else "$0"),
        ("Mangrove protection value, county total", totals, n_tot, fmt_busd,
         lambda t: f"${t/1e9:g}B" if t else "$0"),
    ]
    letters = "ABCDEF"
    n_panel = 0
    for irow, (row_title, data, norm, fmt, tickfmt) in enumerate(row_specs):
        axes = []
        for icol, (subtitle, key) in enumerate(cols):
            ax = fig.add_subplot(gs[irow, icol])
            bm.map_panel(ax, gdf, labels, view, data[key], norm, GREEN_CMAP,
                         letters[n_panel], "" if journal else subtitle, fmt)
            axes.append(ax)
            n_panel += 1
        if not journal:
            axes[0].annotate(row_title, (0, 1.0), xycoords="axes fraction",
                             xytext=(0, 24), textcoords="offset points",
                             fontsize=10, fontweight="bold", va="bottom",
                             annotation_clip=False, zorder=10)
        add_row_cbar(fig, axes, norm, GREEN_CMAP, tickfmt)
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(str(path).replace(".pdf", ".png"), bbox_inches="tight")
    plt.close(fig)


def si_hydro(path, journal=False, figwidth_in=7.1):
    aeb = aeb_series(anchor_rp=1)
    rows = []
    for period, s in aeb.items():
        for cty, v in s.items():
            rows.append(dict(county=cty, period=period,
                             convention="anchor_rp=1", discount_rate=R,
                             aeb=v, pv_aeb_30yr=v * ann_due(30),
                             pv_aeb_77yr=v * ann_due(77)))
    pd.DataFrame(rows).to_csv(OUT / "county_AEB_NPV_RP1anchor.csv",
                              index=False)

    aeb_h = aeb["historic"].to_dict()
    aeb_c = aeb["climate"].to_dict()
    pv77 = (aeb["historic"] * ann_due(77)).to_dict()
    n_aeb = Normalize(0, max(max(aeb_h.values()), max(aeb_c.values())))
    n_pv = Normalize(0, max(pv77.values()))

    gdf, labels, view = bm.load()
    fig = plt.figure(figsize=(figwidth_in, figwidth_in * 0.46))
    gs = fig.add_gridspec(1, 3, wspace=0.02, left=0.005, right=0.995,
                          top=0.90, bottom=0.13)
    panels = [("Annual benefit; present day", aeb_h, n_aeb, fmt_myr),
              ("Annual benefit; climate change 2050", aeb_c, n_aeb, fmt_myr),
              ("Present value, 77 yr; present day", pv77, n_pv, fmt_busd)]
    axes = []
    for i, (subtitle, vals, norm, fmt) in enumerate(panels):
        ax = fig.add_subplot(gs[0, i])
        bm.map_panel(ax, gdf, labels, view, vals, norm, GREEN_CMAP,
                     "ABC"[i], "" if journal else subtitle, fmt)
        axes.append(ax)
    if not journal:
        axes[0].annotate("Hydrodynamic mangrove benefit (avoided damages)",
                         (0, 1.0), xycoords="axes fraction", xytext=(0, 24),
                         textcoords="offset points", fontsize=10,
                         fontweight="bold", va="bottom",
                         annotation_clip=False, zorder=10)
    add_row_cbar(fig, axes[:2], n_aeb, GREEN_CMAP,
                 lambda t: f"${t/1e6:g}M" if t else "$0")
    add_row_cbar(fig, [axes[2]], n_pv, GREEN_CMAP,
                 lambda t: f"${t/1e9:g}B" if t else "$0")
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(str(path).replace(".pdf", ".png"), bbox_inches="tight")
    plt.close(fig)


def si_ed_vs_ap(path, journal=False, figwidth_in=7.1):
    pv77 = (aeb_series(anchor_rp=None)["historic"] * ann_due(77)).to_dict()
    a = load_assessment()
    ap = a[(a.assessment == "engineering")
           & (a.scenario == "baseline")].set_index("county")[
        "aggregate_at_risk_protection"].to_dict()

    n_usd = Normalize(0, max(max(pv77.values()), max(ap.values())))
    panels = [("Expected damages; present value 77 yr, 5%/yr", pv77),
              ("Asset pricing (Eq. 1); county total", ap)]

    gdf, labels, view = bm.load()
    fig = plt.figure(figsize=(figwidth_in, figwidth_in * 0.66))
    gs = fig.add_gridspec(1, 2, wspace=0.02, left=0.005, right=0.995,
                          top=0.90, bottom=0.13)
    axes = []
    for i, (subtitle, vals) in enumerate(panels):
        ax = fig.add_subplot(gs[0, i])
        bm.map_panel(ax, gdf, labels, view, vals, n_usd, GREEN_CMAP,
                     "AB"[i], "" if journal else subtitle, fmt_busd)
        axes.append(ax)
    if not journal:
        axes[0].annotate("Expected-damages valuation vs. asset pricing, "
                         "both using storms RP10/25/50/100 only",
                         (0, 1.0), xycoords="axes fraction", xytext=(0, 24),
                         textcoords="offset points", fontsize=10,
                         fontweight="bold", va="bottom",
                         annotation_clip=False, zorder=10)
    add_row_cbar(fig, axes, n_usd, GREEN_CMAP,
                 lambda t: f"${t/1e9:g}B" if t else "$0")
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(str(path).replace(".pdf", ".png"), bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    fig4(OUT / "Fig4_alt_climate_2x3.pdf")
    fig4(OUT / "Fig4_alt_climate_2x3_lettersonly.pdf", journal=True)
    si_hydro(OUT / "FigSI_hydro_AEB_PV_1x3.pdf")
    si_hydro(OUT / "FigSI_hydro_AEB_PV_1x3_lettersonly.pdf", journal=True)
    si_ed_vs_ap(OUT / "FigSI_expected_damages_vs_assetpricing_PV_1x2.pdf")
    si_ed_vs_ap(
        OUT / "FigSI_expected_damages_vs_assetpricing_PV_1x2_lettersonly.pdf",
        journal=True)
    print("wrote Fig4_alt_climate_2x3, FigSI_hydro_AEB_PV_1x3, "
          "FigSI_expected_damages_vs_assetpricing_PV_1x2 to output/ "
          "(.pdf/.png, each + _lettersonly), and "
          "county_AEB_NPV_RP1anchor.csv")


if __name__ == "__main__":
    main()
