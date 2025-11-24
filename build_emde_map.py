from pathlib import Path

import pandas as pd
import geopandas as gpd
import folium


# =========================
# Paths
# =========================

ROOT = Path(__file__).resolve().parent      # ffrm_python/
DOCS = ROOT / "docs"

# Your CSV in docs/data/
DATA_CSV = DOCS / "data" / "EMDE_fossil-fuel_regimes___repopulated_inclusive_mapping.csv"

# Output HTML map
OUT_HTML = DOCS / "_static" / "emde_regime_map.html"


# =========================
# Load and prepare data
# =========================

print(f"Reading CSV from: {DATA_CSV}")
df = pd.read_csv(DATA_CSV)

print("Columns in CSV:", list(df.columns))

# Use PrimaryBucket for colouring; fallback to 'unknown'
df["DisplayBucket"] = df["PrimaryBucket"].fillna("unknown")

# Flag mixed systems: more than one of Has_Market / Has_PPA / Has_Regulated = True
def classify_mixed(row):
    flags = [
        bool(row.get("Has_Market", False)),
        bool(row.get("Has_PPA", False)),
        bool(row.get("Has_Regulated", False)),
    ]
    return "Yes" if sum(flags) > 1 else "No"

df["MixedSystem"] = df.apply(classify_mixed, axis=1)

print("Unique PrimaryBucket values:", df["PrimaryBucket"].dropna().unique())
print("Mixed system counts:", df["MixedSystem"].value_counts())


# =========================
# Load world geometry & join
# =========================

print("Loading Natural Earth world geometries...")
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

# Join on name (Natural Earth) vs Country (CSV)
gdf = world.merge(df, left_on="name", right_on="Country", how="inner")

print(f"Joined rows: {len(gdf)} (out of {len(df)} in CSV)")
missing = set(df["Country"]) - set(gdf["Country"])
if missing:
    print("Countries in CSV not matched in Natural Earth:", missing)

gdf = gpd.GeoDataFrame(gdf, crs=world.crs)


# =========================
# Build Folium map
# =========================

m = folium.Map(location=[10, 10], zoom_start=2, tiles="cartodbpositron")

colors = {
    "market": "#1f77b4",
    "ppa": "#ff7f0e",
    "regulated": "#2ca02c",
    "unknown": "#b0b0b0",   # unclassified
    "_default": "#e0e0e0",
}

def style_function(feature):
    bucket = feature["properties"].get("DisplayBucket", "_default")
    color = colors.get(bucket, colors["_default"])
    return {
        "fillColor": color,
        "color": "white",
        "weight": 0.5,
        "fillOpacity": 0.8,
    }

def highlight_function(_feature):
    return {
        "weight": 2,
        "color": "#000000",
        "fillOpacity": 0.9,
    }

# Hover: simple
tooltip = folium.GeoJsonTooltip(
    fields=["Country", "PrimaryBucket"],
    aliases=["Country:", "Electricity market regime:"],
    localize=True,
    sticky=True,
)

# Click popup: show mixed system + flags
popup = folium.GeoJsonPopup(
    fields=[
        "Country",
        "PrimaryBucket",
        "MixedSystem",
        "Has_Market",
        "Has_PPA",
        "Has_Regulated",
        "Notes",
    ],
    aliases=[
        "Country:",
        "Primary regime:",
        "Mixed system (multiple mechanisms):",
        "Has market?",
        "Has PPA?",
        "Has regulated tariffs?",
        "Notes:",
    ],
    localize=True,
    labels=True,
    parse_html=True,
)

geojson = folium.GeoJson(
    gdf,
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=tooltip,
    popup=popup,
)

geojson.add_to(m)

# Legend (no title, just colour → label)
legend_html = """
<div style="
    position: fixed;
    bottom: 30px;
    left: 30px;
    z-index: 9999;
    background: white;
    padding: 10px;
    border: 1px solid #ccc;
    font-size: 12px;
">
<span style="background:#1f77b4;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> Market-based<br>
<span style="background:#ff7f0e;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> PPA-based<br>
<span style="background:#2ca02c;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> Regulated<br>
<span style="background:#b0b0b0;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> Unclassified<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))


# =========================
# Save map
# =========================

OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
m.save(str(OUT_HTML))
print(f"Saved map to: {OUT_HTML}")
 