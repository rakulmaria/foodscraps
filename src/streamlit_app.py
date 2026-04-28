import math

import numpy as np
import pandas as pd
import plotly.express as px
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


cph_df = get_df()
scatter_map = get_scatter_map(cph_df)
histogram_map = get_2d_hist(cph_df)
histogram_map_np = get_2d_hist_np(cph_df, 100)
primary_restaurant_top20 = get_primary_restaurant_top20(cph_df)

st.plotly_chart(scatter_map)
st.plotly_chart(histogram_map)
st.plotly_chart(histogram_map_np)
st.plotly_chart(primary_restaurant_top20)
