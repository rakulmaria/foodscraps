import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

from data_cleaner import get_df


def get_ratings_label(rating):
    if math.isnan(rating):
        return "No rating"
    return f"{rating:.1f} ⭐"

def get_mid_price(price_range):
    try:
        low = int(price_range["startPrice"]["units"])
        high   = int(price_range["endPrice"]["units"])
        return (low + high) / 2
    except (TypeError, KeyError, ValueError):
        return None
    
def get_price_label(price_range):
    try:
        low = int(price_range["startPrice"]["units"])
        high   = int(price_range["endPrice"]["units"])
        return f"{low} - {high} DKK 💵"
    except (TypeError, KeyError, ValueError):
        return "Unknown price range"

def get_scatter_map(df):
    plot_df = df.copy()

    plot_df["priceLabel"] = plot_df["priceRange"].apply(get_price_label)
    plot_df["midPrice"] = plot_df["priceRange"].apply(get_mid_price)
    plot_df["ratingLabel"] = plot_df["rating"].apply(get_ratings_label)

    fig = px.scatter_map(
        plot_df,
        lat="lat",
        lon="lon",
        hover_name="displayName",
        hover_data={
            "primaryTypeDisplayName": True,
            "priceLabel": True,
            "ratingLabel": True,
            "lat": False,
            "lon": False,
        },
        color="midPrice",
        color_continuous_scale="RdYlGn_r",
        opacity=0.6,
        zoom=12,
        center={"lat": 55.6761, "lon": 12.5683},
        title="Copenhagen Restaurants – Google Maps Places API",
    )

    fig.update_layout(
        coloraxis=dict(
            colorscale="RdYlGn_r",
            colorbar_title="Mid Price (DKK)",
        ),
        map_style="light",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>"
                    "Primary Type: %{customdata[0]}<br>"
                    "Price Label: %{customdata[1]}<br>"
                    "Rating: %{customdata[2]}"
                    "<extra></extra>"
    )

    return fig

def get_2d_hist(df):
    plot_df = df.copy()
    fig = px.density_map(
        plot_df,
        lat="lat",
        lon="lon",
        radius=4,
        zoom=9,
        center={"lat": 55.6761, "lon": 12.5683},
        color_continuous_scale=px.colors.sequential.Viridis,
        title="Restaurant Density across Copenhagen",
    )

    fig.update_layout(
        coloraxis=dict(
            colorscale=px.colors.sequential.Viridis,
            colorbar_title="Density",
        ),
        map_style="light",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    fig.update_traces(hovertemplate=None, hoverinfo="skip")

    return fig

def get_2d_hist_np(df, bins=100):
    # bin lat/lon into a 2D grid
    plot_df = df.copy()
    lat_bins = np.linspace(plot_df["lat"].min(), plot_df["lat"].max(), bins + 1)
    lon_bins = np.linspace(plot_df["lon"].min(), plot_df["lon"].max(), bins + 1)

    counts, _, _ = np.histogram2d(plot_df["lat"], plot_df["lon"], bins=[lat_bins, lon_bins])

    # build one rectangle per bin as a GeoJSON feature
    features = []
    # loop over every cell in the grid
    for i in range(bins):
        for j in range(bins):
            count = int(counts[i, j])
            # skip empty cells so they don't render on the map
            if count == 0:
                continue
            # lookup the four corners of the cell 
            lat0, lat1 = float(lat_bins[i]), float(lat_bins[i + 1])
            lon0, lon1 = float(lon_bins[j]), float(lon_bins[j + 1])
            # and append it as a GeoJSON polygon feature
            features.append({
                "type": "Feature",
                "id": f"{i}-{j}",
                "properties": {"count": count},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon0, lat0], [lon1, lat0],
                        [lon1, lat1], [lon0, lat1],
                        [lon0, lat0],
                    ]],
                },
            })

    geojson = {"type": "FeatureCollection", "features": features}
    bin_df = pd.DataFrame([f["properties"] | {"id": f["id"]} for f in features])

    fig = px.choropleth_map(
        bin_df,
        geojson=geojson,
        locations="id",
        color="count",
        color_continuous_scale=px.colors.sequential.Viridis,
        opacity=0.6,
        zoom=10,
        hover_data={
            "id": True,
            "count": True,
        },
        center={"lat": 55.6761, "lon": 12.5683},
        title="Copenhagen Restaurants – 2D Histogram",
    )

    fig.update_layout(
        coloraxis=dict(
            colorbar_title="No. of Restaurants",
        ),
        map_style="light",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    fig.update_traces(
        hovertemplate="Bin ID: %{customdata[0]}<br>"
                    "Count: %{customdata[1]}<br>"
                    "<extra></extra>"
    )

    return fig

def get_primary_restaurant_top20(df):
    # calculate fraction % for each primaryTypeDisplayName
    type_counts_top20 = df["primaryTypeDisplayName"].value_counts().head(20)
    plot_df = (type_counts_top20 / len(df) * 100).reset_index().round(2)
    plot_df = plot_df.rename(columns={"count" : "fraction"})

    fig = px.bar(
        plot_df,
        x="primaryTypeDisplayName",
        y="fraction",
        title="Top 20 Restaurant Types in Copenhagen",
        labels={
            "primaryTypeDisplayName": "Restaurant Type",
            "fraction": "Fraction (%)"
        },
    )

    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        hovertemplate=None,
        hoverinfo="skip",
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis=dict(range=[0, plot_df["fraction"].max() * 1.15]),
        height=600,
        showlegend=False,
    )

    return fig

def collect_leaf_bboxes(restaurants, lat_s, lat_n, lon_w, lon_e):
    """Recursively split a cell if it holds >= SPLIT_THRESHOLD restaurants."""
    split_treshold = 10
    if len(restaurants) < split_treshold:
        return [(lat_s, lat_n, lon_w, lon_e)]

    mid_lat = (lat_s + lat_n) / 2
    mid_lon = (lon_w + lon_e) / 2

    quadrants = [
        (mid_lat, lat_n, lon_w, mid_lon),  # NW
        (mid_lat, lat_n, mid_lon, lon_e),  # NE
        (lat_s, mid_lat, lon_w, mid_lon),  # SW
        (lat_s, mid_lat, mid_lon, lon_e),  # SE
    ]

    leaves = []
    for s, n, w, e in quadrants:
        subset = [
            r for r in restaurants
            if s <= r["lat"] <= n
            and w <= r["lon"] <= e
        ]
        leaves.extend(collect_leaf_bboxes(subset, s, n, w, e))
    return leaves


def bbox_to_line(lat_s, lat_n, lon_w, lon_e):
    """Closed rectangle as (lats, lons) lists, terminated by None for batching."""
    lats = [lat_s, lat_n, lat_n, lat_s, lat_s, None]
    lons = [lon_w, lon_w, lon_e, lon_e, lon_w, None]
    return lats, lons

def get_quadtree(df):
    cph_bbox = {
        "lat_south": 55.51,
        "lat_north": 55.82,
        "lon_west": 12.23,
        "lon_east": 12.73,
    }

    restaurants = df[["lat", "lon"]].to_dict("records")

    leaf_bboxes = collect_leaf_bboxes(
        restaurants,
        cph_bbox["lat_south"],
        cph_bbox["lat_north"],
        cph_bbox["lon_west"],
        cph_bbox["lon_east"],
    )

    # batch all rectangles into one trace using None separators
    all_lats, all_lons = [], []
    for bbox in leaf_bboxes:
        lats, lons = bbox_to_line(*bbox)
        all_lats.extend(lats)
        all_lons.extend(lons)

    rest_lats = df["lat"].tolist()
    rest_lons = df["lon"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Scattermap(
        lat=all_lats,
        lon=all_lons,
        mode="lines",
        line=dict(color="royalblue", width=0.8),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.add_trace(go.Scattermap(
        lat=rest_lats,
        lon=rest_lons,
        mode="markers",
        marker=dict(size=3, color="black", opacity=0.45),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.update_layout(
        map=dict(
            style="carto-positron",
            center=dict(lat=55.665, lon=12.48),
            zoom=9,
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500,
    )

    return fig


def get_district(postal_code: str) -> str | None:
    # ── valid postal codes for Copenhagen + Frederiksberg municipalities ──────────
    # Source: worldpostalcode.com (Copenhagen municipality + Frederiksberg kommune)
    CPH_POSTAL_CODES = set([
        # København K — 1050–1473 (individual codes, not a solid range)
        *range(1050, 1474),
        # København V — 1500–1799
        *range(1500, 1800),
        # Frederiksberg C — 1800–1974
        *range(1800, 1975),
        # Frederiksberg — 2000
        2000,
        # København Ø — 2100
        2100,
        # Nordhavn — 2150
        2150,
        # København N — 2200
        2200,
        # København S — 2300
        2300,
        # København NV — 2400
        2400,
        # København SV — 2450
        2450,
        # Valby — 2500
        2500,
        # Brønshøj — 2700
        2700,
        # Vanløse — 2720
        2720,
    ])
    
    try:
        code = int(postal_code)
    except (ValueError, TypeError):
        return None

    if code not in CPH_POSTAL_CODES:
        return None

    if 1050 <= code <= 1473:
        return "København K (Center)"
    elif 1500 <= code <= 1799:
        return "København V (Vesterbro)"
    elif 1800 <= code <= 1999:
        return "Frederiksberg C"
    elif code == 2000:
        return "Frederiksberg"
    elif code == 2100:
        return "København Ø (Østerbro)"
    elif code == 2150:
        return "Nordhavn"
    elif code == 2200:
        return "København N (Nørrebro)"
    elif code == 2300:
        return "København S (Sundby/Amager)"
    elif code == 2400:
        return "København NV (Nordvest)"
    elif code == 2450:
        return "København SV (Sydhavn)"
    elif code == 2500:
        return "Valby"
    elif code == 2700:
        return "Brønshøj"
    elif code == 2720:
        return "Vanløse"

    return None


def get_vegetarian_bar(df):
    COLORS = {
        "Serves vegetarian food":         "#6e995f",
        "Does not serve vegetarian food":  "#ff6e6e",
        "No data":                         "#A2A2A2",
    }
    # ── extract postal code from dict ─────────────────────────────────────────
    df["postalCode"] = df["postalAddress"].apply(
        lambda x: x.get("postalCode", None) if isinstance(x, dict) else None
    )

    # ── map to district, drop rows outside CPH/Frederiksberg ─────────────────
    df["district"] = df["postalCode"].apply(get_district)
    plot_df = df[df["district"].notna()].copy()

    # ── normalise float64 boolean → readable label ────────────────────────────
    plot_df["veg_label"] = (
        plot_df["servesVegetarianFood"]
        .map({1.0: "Serves vegetarian food", 0.0: "Does not serve vegetarian food"})
        .fillna("No data")
    )

    # ── compute fractional breakdown + total n per district ───────────────────
    counts = (
        plot_df.groupby(["district", "veg_label"])
        .size()
        .reset_index(name="count")
    )
    district_totals = plot_df.groupby("district").size().rename("total")
    counts = counts.join(district_totals, on="district")
    counts["fraction"] = counts["count"] / counts["total"]

    # pivot fractions
    pivot = (
        counts.pivot(index="district", columns="veg_label", values="fraction")
        .fillna(0)
        .reset_index()
    )
    # attach total n per district
    pivot = pivot.join(district_totals, on="district")

    # ── sort by vegetarian fraction descending (ascending=True → top of h-bar) ─
    veg_col = "Serves vegetarian food"
    if veg_col in pivot.columns:
        pivot = pivot.sort_values(veg_col, ascending=True)

    districts  = pivot["district"].tolist()
    totals_per = pivot["total"].tolist()

    # ── build stacked horizontal bar traces ───────────────────────────────────
    category_order = [
        "Serves vegetarian food",
        "Does not serve vegetarian food",
        "No data",
    ]

    fig = go.Figure()

    for label in category_order:
        if label not in pivot.columns:
            continue

        fractions = pivot[label].tolist()
        text_labels = [f"{v:.0%}" if v >= 0.04 else "" for v in fractions]

        fig.add_trace(go.Bar(
            name=label,
            y=districts,
            x=fractions,
            orientation="h",
            marker_color=COLORS[label],
            text=text_labels,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="white", size=12, family="monospace"),
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"{label}: %{{x:.1%}}<br>"
                "n (district total): %{customdata}<br>"
                "<extra></extra>"
            ),
            customdata=totals_per,
        ))

    # ── n= annotations on the right edge of each bar ─────────────────────────
    annotations = [
        dict(
            x=1.01,
            y=district,
            text=f"n={n}",
            showarrow=False,
            xref="x",
            yref="y",
            xanchor="left",
            font=dict(size=11, color="#555555", family="monospace"),
        )
        for district, n in zip(districts, totals_per)
    ]

    # ── layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        barmode="stack",
        annotations=annotations,
        title=dict(
            text=(
                "<b>Vegetarian food availability by district (inner CPH only)</b>"
            ),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(
            tickformat=".0%",
            range=[0, 1.12],   # extra room for n= labels
            title="Share of restaurants",
            showgrid=True,
        ),
        yaxis=dict(
            type="category",
            title=None,
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        margin={"r": 60, "t": 80, "l": 20, "b": 40},
    )

    return fig

def get_rating_vs_price_box(df):
    bin_size = 100
    min_n = 30

    plot_df = df.copy()
    plot_df["midPrice"] = plot_df["priceRange"].apply(get_mid_price)
    plot_df = plot_df[plot_df["midPrice"].notna() & plot_df["rating"].notna()].copy()

    min_price = (plot_df["midPrice"].min() // bin_size) * bin_size
    max_price = (plot_df["midPrice"].max() // bin_size) * bin_size + bin_size

    bins   = np.arange(min_price, max_price + bin_size, bin_size)
    labels = [f"{int(b)}–{int(b + bin_size)} DKK" for b in bins[:-1]]

    plot_df["pricebin"] = pd.cut(
        plot_df["midPrice"],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )

    bin_counts    = plot_df["pricebin"].value_counts()
    valid_bins    = [lab for lab in labels if bin_counts.get(lab, 0) >= min_n]
    excluded_bins = [lab for lab in labels if 0 < bin_counts.get(lab, 0) < min_n]

    plot_df = plot_df[plot_df["pricebin"].astype(str).isin(valid_bins)]
    bin_counts_valid = plot_df["pricebin"].value_counts()

    total    = len(plot_df)
    excluded = len(df) - total

    fig = px.box(
        plot_df,
        x="pricebin",
        y="rating",
        category_orders={"pricebin": valid_bins},
        points="outliers",
        labels={"pricebin": "Mid-price bin (DKK)", "rating": "Rating"},
        title=(
            "<b>Restaurant rating by price range</b>"
            f"<br><sup>n = {total:,} restaurants · "
            + (f"excluded bins with n < {min_n}: {', '.join(excluded_bins)} · " if excluded_bins else "")
            + (f"{excluded:,} excluded (missing price or rating)" if excluded else "")
            + "</sup>"
        ),
    )

    fig.update_traces(boxmean=True)

    fig.update_layout(
        margin={"r": 20, "t": 80, "l": 20, "b": 60},
        yaxis=dict(range=[1, 5.4], dtick=0.5),
        annotations=[
            dict(
                x=bin_label,
                y=1,
                yref="paper",
                yanchor="top",
                text=f"n={bin_counts_valid.get(bin_label, 0)}",
                showarrow=False,
                font=dict(size=11, color="#555555", family="monospace"),
            )
            for bin_label in valid_bins
        ],
    )

    return fig

cph_df = get_df()
scatter_map = get_scatter_map(cph_df)
histogram_map = get_2d_hist(cph_df)
histogram_map_np = get_2d_hist_np(cph_df, 100)
primary_restaurant_top20 = get_primary_restaurant_top20(cph_df)
quadtree_fig = get_quadtree(cph_df)
vegetarian_map = get_vegetarian_bar(cph_df)
rating_vs_price_boxplot = get_rating_vs_price_box(cph_df)

st.plotly_chart(rating_vs_price_boxplot)
st.plotly_chart(vegetarian_map)
st.plotly_chart(histogram_map_np)
st.plotly_chart(primary_restaurant_top20)
st.plotly_chart(quadtree_fig)
st.plotly_chart(scatter_map)
st.plotly_chart(histogram_map)
