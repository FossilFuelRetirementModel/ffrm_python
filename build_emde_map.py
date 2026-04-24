from pathlib import Path

import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Search


# =========================
# Paths
# =========================

ROOT = Path(__file__).resolve().parent  # ffrm_python/
DOCS = ROOT / "docs"

# Your CSV in docs/data/
DATA_CSV = DOCS / "data" / "ffrm_market_structure.csv"

# Output HTML map
OUT_HTML = DOCS / "_static" / "emde_regime_map.html"


# =========================
# Load and prepare data
# =========================

print(f"Reading CSV from: {DATA_CSV}")
df = pd.read_csv(DATA_CSV)

print("Columns in CSV:", list(df.columns))

# --- Use World Bank terminology columns if present (fallback to PrimaryBucket) ---
if "WB_Family_Code" in df.columns:
    bucket_col = "WB_Family_Code"  # e.g., VIU / SBM / WC (and maybe RC)
    bucket_label_col = "WB_Family_Label" if "WB_Family_Label" in df.columns else "WB_Family_Code"
    unknown_value = "unclassified"
else:
    bucket_col = "PrimaryBucket"  # fallback
    bucket_label_col = "PrimaryBucket"
    unknown_value = "unknown"

df["DisplayBucket"] = df[bucket_col].fillna(unknown_value)

# Country label for display (required for tooltips/search)
if "Country" not in df.columns:
    raise ValueError("CSV must contain a 'Country' column for labels/popups.")

# Flag mixed systems: more than one of Has_Market / Has_PPA / Has_Regulated = True (if those columns exist)
def classify_mixed(row):
    flags = [
        bool(row.get("Has_Market", False)),
        bool(row.get("Has_PPA", False)),
        bool(row.get("Has_Regulated", False)),
    ]
    return "Yes" if sum(flags) > 1 else "No"


df["MixedSystem"] = df.apply(classify_mixed, axis=1)

print(f"Using bucket column: {bucket_col}")
print("Unique DisplayBucket values:", df["DisplayBucket"].dropna().unique())
print("Mixed system counts:", df["MixedSystem"].value_counts(dropna=False))


# =========================
# Load world geometry & join
# =========================

print("Loading Natural Earth world geometries...")
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

# Prefer Natural Earth harmonized name column if present
join_right = "Country_NE" if "Country_NE" in df.columns else "Country"

# LEFT join keeps the full world map
gdf = world.merge(df, left_on="name", right_on=join_right, how="left")

# Fill unclassified where no match / no bucket
gdf["DisplayBucket"] = gdf["DisplayBucket"].fillna(unknown_value)

# Country label for tooltips/search/popups:
gdf["CountryLabel"] = gdf["Country"].fillna(gdf["name"])

print(f"World polygons: {len(world)}; joined polygons: {len(gdf)}")
matched = set(gdf[join_right].dropna().astype(str))
missing = sorted(set(df[join_right].dropna().astype(str)) - matched)
if missing:
    print(f"Rows in CSV not matched in Natural Earth by {join_right}: {len(missing)}")
    print("First few unmatched:", missing[:25])

gdf = gpd.GeoDataFrame(gdf, crs=world.crs)


# =========================
# Build Folium map
# =========================

m = folium.Map(location=[10, 10], zoom_start=2, tiles="cartodbpositron")

# Colors keyed to WB codes if present; fallback supports old buckets too
colors = {
    # World Bank family codes
    "VIU": "#2ca02c",
    "SBM": "#ff7f0e",
    "WC": "#1f77b4",
    "RC": "#9467bd",  # optional if you use it
    # Legacy buckets
    "market": "#1f77b4",
    "ppa": "#ff7f0e",
    "regulated": "#2ca02c",
    # Unknowns
    "unknown": "#b0b0b0",
    "unclassified": "#b0b0b0",
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


# Hover tooltip
tooltip_fields = (
    ["CountryLabel", bucket_label_col] if bucket_label_col in gdf.columns else ["CountryLabel", "DisplayBucket"]
)
tooltip_aliases = ["Country:", "Market structure:"]

tooltip = folium.GeoJsonTooltip(
    fields=tooltip_fields,
    aliases=tooltip_aliases,
    localize=True,
    sticky=True,
)

# Click popup
popup_fields = ["CountryLabel"]
popup_aliases = ["Country:"]

if "WB_Family_Label" in gdf.columns:
    popup_fields += ["WB_Family_Label", "WB_Family_Code"]
    popup_aliases += ["WB structure:", "WB code:"]
else:
    popup_fields += ["PrimaryBucket"]
    popup_aliases += ["Primary regime:"]

for col, alias in [
    ("MixedSystem", "Mixed system (multiple mechanisms):"),
    ("Has_Market", "Has market?"),
    ("Has_PPA", "Has PPA?"),
    ("Has_Regulated", "Has regulated tariffs?"),
#    ("Notes", "Notes:"),
]:
    if col in gdf.columns:
        popup_fields.append(col)
        popup_aliases.append(alias)

popup = folium.GeoJsonPopup(
    fields=popup_fields,
    aliases=popup_aliases,
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
    name="Market structure",
)
geojson.add_to(m)

# ---- Search control in bottom-right (bigger via CSS below) ----
Search(
    layer=geojson,
    search_label="CountryLabel",
    placeholder="Search country...",
    collapsed=False,
    search_zoom=5,
    position="bottomright",
).add_to(m)

# ---- CSS to make the search bar bigger + give padding from the edges ----
search_css = """
<style>
/* Add spacing from the map edges */
.leaflet-bottom.leaflet-right .leaflet-control {
  margin-right: 20px !important;
  margin-bottom: 20px !important;
}

/* Make the input bigger */
.leaflet-control-search .search-input {
  width: 420px !important;   /* adjust as you like */
  height: 40px !important;
  font-size: 16px !important;
  padding: 6px 12px !important;
}

/* Make the search button match the input height */
.leaflet-control-search .search-button {
  width: 40px !important;
  height: 40px !important;
}
</style>
"""
m.get_root().header.add_child(folium.Element(search_css))

# Legend
legend_html_wb = """
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
<span style="background:#2ca02c;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> VIU (Vertically Integrated Utility)<br>
<span style="background:#ff7f0e;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> SBM (Single Buyer Model)<br>
<span style="background:#1f77b4;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> WC (Wholesale Competition)<br>
<span style="background:#9467bd;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> RC (Retail Competition)<br>
<span style="background:#b0b0b0;width:12px;height:12px;display:inline-block;margin-right:4px;"></span> Unclassified<br>
</div>
"""

legend_html_legacy = """
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

m.get_root().html.add_child(
    folium.Element(legend_html_wb if "WB_Family_Code" in df.columns else legend_html_legacy)
)

folium.LayerControl(collapsed=True).add_to(m)


# =========================
# Save map
# =========================

OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
m.save(str(OUT_HTML))
print(f"Saved map to: {OUT_HTML}")
  