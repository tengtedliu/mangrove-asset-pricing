"""
Shared basemap for the county map figures.

- County geometry: U.S. Census cartographic boundary counties (cb_2023,
  1:500,000), clipped to the shoreline so no legal boundaries extend into
  open water (data/FL_counties_coastclipped_cb2023.gpkg).
- Terrain: AWS Terrain Tiles (terrarium encoding, public domain), zoom 9,
  decoded to meters and hillshaded with high vertical exaggeration. The
  shade layer is shadow-only (an alpha overlay that darkens slopes and
  leaves flats untouched) so choropleth colors render true. Tiles are
  fetched automatically on first run and cached under
  output/basemap_cache/.
- CRS: EPSG:3857 throughout, so the DEM mosaic aligns natively.

County label positions are hand-placed for this specific map view.
"""

import io
import math
import urllib.request
from pathlib import Path

import numpy as np
import geopandas as gpd
import matplotlib.patheffects as pe
from matplotlib.colors import LightSource
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle
from shapely.geometry import Point

BASE = Path(__file__).resolve().parents[1]
ASSETS = BASE / "output" / "basemap_cache"
GPKG = BASE / "data" / "FL_counties_coastclipped_cb2023.gpkg"

LABELS = {
    "Hillsborough": (-82.35, 28.22, "center", "bottom"),
    "Pinellas":     (-83.02, 27.86, "right", "center"),
    "Manatee":      (-82.88, 27.44, "right", "center"),
    "Charlotte":    (-82.48, 26.80, "right", "center"),
    "Lee":          (-82.30, 26.40, "right", "center"),
    "Collier":      (-81.70, 25.68, "right", "center"),
    "Miami-Dade":   (-80.04, 25.58, "left", "center"),
}
VIEW_LONLAT = dict(lon=(-84.49, -78.72), lat=(24.32, 28.68))
Z = 9
PIX_M = 274  # ground meters per pixel at z9, ~26N


def build_dem():
    """Fetch terrarium tiles for the view bbox and save the mosaic + extent."""
    def tile_xy(lon, lat):
        n = 2 ** Z
        return ((lon + 180) / 360 * n,
                (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)

    from PIL import Image
    lon, lat = VIEW_LONLAT["lon"], VIEW_LONLAT["lat"]
    x0, y1 = tile_xy(lon[0], lat[0])
    x1, y0 = tile_xy(lon[1], lat[1])
    xs = range(int(x0), int(x1) + 1)
    ys = range(int(y0), int(y1) + 1)
    mosaic = np.zeros((len(ys) * 256, len(xs) * 256), dtype=np.float32)
    for j, ty in enumerate(ys):
        for i, tx in enumerate(xs):
            url = ("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/"
                   f"{Z}/{tx}/{ty}.png")
            with urllib.request.urlopen(url, timeout=30) as r:
                img = np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"),
                                 dtype=np.float32)
            mosaic[j*256:(j+1)*256, i*256:(i+1)*256] = (
                img[:, :, 0] * 256 + img[:, :, 1] + img[:, :, 2] / 256 - 32768)

    n = 2 ** Z
    R = 6378137.0
    def merc(lon_, lat_):
        return (R * math.radians(lon_),
                R * math.log(math.tan(math.pi / 4 + math.radians(lat_) / 2)))
    lon_a = min(xs) / n * 360 - 180
    lon_b = (max(xs) + 1) / n * 360 - 180
    lat_t = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * min(ys) / n))))
    lat_b = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (max(ys) + 1) / n))))
    xa, yt = merc(lon_a, lat_t)
    xb, yb = merc(lon_b, lat_b)
    ASSETS.mkdir(parents=True, exist_ok=True)
    np.save(ASSETS / "fl_dem_mercator_z9.npy", mosaic)
    np.save(ASSETS / "fl_dem_extent_3857.npy", np.array([xa, xb, yb, yt]))


def _shade():
    if not (ASSETS / "fl_dem_mercator_z9.npy").exists():
        build_dem()
    dem = np.load(ASSETS / "fl_dem_mercator_z9.npy")
    ext = np.load(ASSETS / "fl_dem_extent_3857.npy")
    z = np.where(dem < 0, 0, dem)
    hs = LightSource(azdeg=315, altdeg=45).hillshade(
        z, vert_exag=60, dx=PIX_M, dy=PIX_M)
    shade = np.zeros((*hs.shape, 4))
    shade[..., 3] = np.clip((0.86 - hs) * 1.1, 0, 0.32)
    return shade, ext


_SHADE, _EXT = None, None
_LAND = None


def load():
    global _SHADE, _EXT, _LAND
    g = gpd.read_file(GPKG).to_crs(3857)
    g["NAME"] = g["NAME"].str.strip()
    g["geometry"] = g.geometry.simplify(200, preserve_topology=True)
    to_3857 = lambda d: gpd.GeoSeries([Point(xy) for xy in d.values()],
                                      index=list(d), crs=4326).to_crs(3857)
    labels = to_3857({k: (v[0], v[1]) for k, v in LABELS.items()})
    lo, la = VIEW_LONLAT["lon"], VIEW_LONLAT["lat"]
    corners = {f"c{i}": (x, y) for i, (x, y) in enumerate(
        [(lo[0], la[0]), (lo[1], la[0]), (lo[0], la[1]), (lo[1], la[1])])}
    if _SHADE is None:
        _SHADE, _EXT = _shade()
        _LAND = g.union_all()
    return g, labels, to_3857(corners)


def _geom_patch(geom, ax):
    verts, codes = [], []
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            xy = np.asarray(ring.coords)
            verts.extend(xy)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2)
                         + [MplPath.CLOSEPOLY])
    return PathPatch(MplPath(verts, codes), transform=ax.transData)


OCEAN = "#DCEAF2"


def map_panel(ax, gdf, labels, view, values, norm, cmap, title, subtitle, fmt):
    xs_v = [p.x for p in view]
    ys_v = [p.y for p in view]
    # The ocean rectangle overhangs the axes slightly (clip_on=False) so
    # panel content that reaches the edge is framed in blue rather than
    # merging into the page background.
    pad_x = (max(xs_v) - min(xs_v)) * 0.0025
    pad_y = (max(ys_v) - min(ys_v)) * 0.0025
    ax.add_patch(Rectangle((min(xs_v) - pad_x, min(ys_v) - pad_y),
                           max(xs_v) - min(xs_v) + 2 * pad_x,
                           max(ys_v) - min(ys_v) + 2 * pad_y, facecolor=OCEAN,
                           edgecolor="none", zorder=0.4, clip_on=False))
    study = list(values)
    gdf[~gdf.NAME.isin(study)].plot(ax=ax, facecolor="#F1EFEA",
                                    edgecolor="none", zorder=1)
    sub = gdf[gdf.NAME.isin(study)].copy()
    sub.plot(ax=ax, color=[cmap(norm(values[n])) for n in sub.NAME],
             edgecolor="none", zorder=2)

    im = ax.imshow(_SHADE, extent=list(_EXT), origin="upper", zorder=3,
                   interpolation="bilinear")
    im.set_clip_path(_geom_patch(_LAND, ax))

    gdf.boundary.plot(ax=ax, color="#FFFFFF", lw=0.45, zorder=4)
    sub.boundary.plot(ax=ax, color="#5A5A5A", lw=0.6, zorder=4.5)

    halo = [pe.withStroke(linewidth=2.0, foreground="white")]
    for cty, pt in labels.items():
        _, _, ha, va = LABELS[cty]
        ax.annotate(f"{cty}\n{fmt(values[cty])}", (pt.x, pt.y),
                    ha=ha, va=va, fontsize=6.2, linespacing=1.25,
                    color="#1A1A1A", zorder=6, clip_on=False,
                    path_effects=halo)

    xs = [p.x for p in view]
    ys = [p.y for p in view]
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=11,
                 zorder=10)
    ax.annotate(subtitle, (0, 1.0), xycoords="axes fraction", xytext=(0, 2),
                textcoords="offset points", fontsize=7.0, color="#555555",
                va="bottom", linespacing=1.35, zorder=10)
