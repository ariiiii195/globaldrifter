"""
Figure D1 - where the drifters sampled (report Section 8, page 12).

Run from the project folder (next to data/):
    python data_coverage.py

Input:  data/gdp_cc_subset.pkl  (GDP hourly drifters; created automatically by
        06_RQ3_species_exposure.py, so run that script once first)
Output: figures/figD1_spatial_coverage.png
        figures/report/table_D1_coverage.csv  (observations and drifters per period)

The numbers in the text (565,818 observations from 124 drifters in the Blob,
304,126 from 85 drifters in 2019-20) are printed and saved in the table.
No random steps, so every run gives the same result.
"""

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                       # save to file, no pop-up window
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# ---------------- settings ----------------
HERE = os.path.dirname(os.path.abspath(__file__))
GDP_FILE = os.path.join(HERE, "data", "gdp_cc_subset.pkl")
OUT_DIR = os.path.join(HERE, "figures")
os.makedirs(OUT_DIR, exist_ok=True)

LON = (-135.0, -115.0)                      # study box
LAT = (25.0, 48.0)
CELL_DEG = 0.5                              # grid cell size (degrees) for counting observations
LON_SPLIT = -125.0                          # early coastal/offshore split (dashed line)
PERIODS = {                                 # the three map panels
    "All 2012-2021": ("2012-01-01", "2021-12-31 23:00"),
    "Blob 2013-16": ("2013-01-01", "2016-12-31 23:00"),
    "MHW 2019-20": ("2019-01-01", "2020-12-31 23:00"),
}

# Rough US West Coast outline (lat, lon), used only if cartopy is not installed
COAST = np.array([[32.53, -117.12], [33.00, -117.28], [33.45, -117.70], [33.75, -118.40], [34.03, -118.55],
                  [34.40, -119.50], [34.46, -120.47], [34.90, -120.65], [35.40, -120.90], [35.67, -121.30],
                  [36.30, -121.90], [36.60, -121.95], [36.95, -122.05], [37.50, -122.50], [37.80, -122.50],
                  [38.30, -123.05], [38.90, -123.70], [39.50, -123.80], [40.40, -124.40], [41.00, -124.10],
                  [41.75, -124.20], [42.80, -124.55], [43.40, -124.30], [44.60, -124.07], [45.50, -123.97],
                  [46.20, -124.05], [46.90, -124.10], [47.60, -124.40], [48.38, -124.70]])

try:                                        # nicer coastline and land if cartopy is available
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

# ---------------- load drifters ----------------
if not os.path.exists(GDP_FILE):
    raise SystemExit('data/gdp_cc_subset.pkl not found: run python 06_RQ3_species_exposure.py once first (it downloads the drifters).')
df = pd.read_pickle(GDP_FILE)               # one row per hourly observation
print(f"{len(df):,} hourly observations from {df.id.nunique()} drifters")

# ---------------- count observations per cell for each period ----------------
edges_x = np.arange(LON[0], LON[1] + 1e-9, CELL_DEG)
edges_y = np.arange(LAT[0], LAT[1] + 1e-9, CELL_DEG)
panels, rows = [], []
for name, (start, end) in PERIODS.items():
    p = df[(df.time >= start) & (df.time <= end)]
    counts = np.histogram2d(p.lon, p.lat, bins=[edges_x, edges_y])[0].T     # rows = latitude
    panels.append((name, p, counts))
    rows.append({"period": name, "hourly observations": len(p), "drifters": p.id.nunique(),
                 "cells with data": int((counts > 0).sum()), "cells in box": counts.size})
table = pd.DataFrame(rows).set_index("period")
print(table.to_string())
table.to_csv(os.path.join(OUT_DIR, "table_D1_coverage.csv"))

# ---------------- Figure D1: three maps on one colour scale ----------------
vmax = max(c.max() for _, _, c in panels)                                  # same scale on all maps
kw = {"projection": ccrs.PlateCarree()} if HAS_CARTOPY else {}
fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), subplot_kw=kw)
for ax, (name, p, counts) in zip(axes, panels):
    tx = {"transform": ccrs.PlateCarree()} if HAS_CARTOPY else {}
    mesh = ax.pcolormesh(edges_x, edges_y, np.ma.masked_equal(counts, 0),   # empty cells left blank
                         cmap="Blues", norm=LogNorm(1, vmax), **tx)
    ax.plot([LON_SPLIT] * 2, LAT, ls="--", color="k", lw=0.8, **tx)
    if HAS_CARTOPY:
        ax.set_extent([LON[0], LON[1], LAT[0], LAT[1]], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, fc="#efece6", zorder=0)
        ax.coastlines(linewidth=0.6)
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#bbbbbb", alpha=0.7)
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.plot(COAST[:, 1], COAST[:, 0], color="#777", lw=0.9)
        ax.set_xlim(*LON)
        ax.set_ylim(*LAT)
        ax.set_aspect(1 / np.cos(np.deg2rad(36)))    # degrees look the right shape at 36N
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    ax.set_title(f"{name}\n({len(p):,} obs, {p.id.nunique()} drifters)", fontsize=9.5)
fig.colorbar(mesh, ax=list(axes), shrink=0.75, label=f"hourly observations per {CELL_DEG:g}° cell")
fig.suptitle("Where drifters sampled (dashed line = exploratory coastal/offshore split)", y=1.02)
fig.savefig(os.path.join(OUT_DIR, "figD1_spatial_coverage.png"), dpi=200, bbox_inches="tight")
print("saved figures/figD1_spatial_coverage.png")
