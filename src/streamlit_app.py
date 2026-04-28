import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_cleaner import get_df

SPLIT_THRESHOLD = 10

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
    df["priceLabel"] = df["priceRange"].apply(get_price_label)
    df["midPrice"] = df["priceRange"].apply(get_mid_price)
    df["ratingLabel"] = df["rating"].apply(get_ratings_label)

    fig = px.scatter_map(
        df,
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
    fig = px.density_map(
        df,
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
    lat_bins = np.linspace(df["lat"].min(), df["lat"].max(), bins + 1)
    lon_bins = np.linspace(df["lon"].min(), df["lon"].max(), bins + 1)

    counts, _, _ = np.histogram2d(df["lat"], df["lon"], bins=[lat_bins, lon_bins])

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
    type_counts_top20 = cph_df["primaryTypeDisplayName"].value_counts().head(20)
    type_frac_top20 = (type_counts_top20 / len(cph_df) * 100).reset_index().round(2)
    type_frac_top20 = type_frac_top20.rename(columns={"count" : "fraction"})

    fig = px.bar(
        type_frac_top20,
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
        yaxis=dict(range=[0, type_frac_top20["fraction"].max() * 1.15]),
        height=600,
        showlegend=False,
    )

    return fig

def collect_leaf_bboxes(restaurants, lat_s, lat_n, lon_w, lon_e):
    """Recursively split a cell if it holds >= SPLIT_THRESHOLD restaurants."""
    if len(restaurants) < SPLIT_THRESHOLD:
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
    COPENHAGEN_BOUNDS = {
        "lat_south": 55.51,
        "lat_north": 55.82,
        "lon_west": 12.23,
        "lon_east": 12.73,
    }

    restaurants = df[["lat", "lon"]].to_dict("records")

    leaf_bboxes = collect_leaf_bboxes(
        restaurants,
        COPENHAGEN_BOUNDS["lat_south"],
        COPENHAGEN_BOUNDS["lat_north"],
        COPENHAGEN_BOUNDS["lon_west"],
        COPENHAGEN_BOUNDS["lon_east"],
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
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
    )

    return fig

cph_df = get_df()
scatter_map = get_scatter_map(cph_df)
histogram_map = get_2d_hist(cph_df)
histogram_map_np = get_2d_hist_np(cph_df, 100)
primary_restaurant_top20 = get_primary_restaurant_top20(cph_df)
quadtree_fig = get_quadtree(cph_df)

st.plotly_chart(scatter_map)
st.plotly_chart(histogram_map)
st.plotly_chart(histogram_map_np)
st.plotly_chart(primary_restaurant_top20)
st.plotly_chart(quadtree_fig)
