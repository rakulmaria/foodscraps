import math

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DATA_DIR


def get_df():
    # possibly filter by cols-to-keep
    cols_to_keep = [
        "name", 
        "id", 
        "types", 
        "formattedAddress", 
        "location", 
        "rating", 
        "googleMapsUri",
        "websiteUri",
        "businessStatus",
        "priceLevel",
        "displayName",
        "takeout",
        "delivery",
        "dineIn",
        "servesBreakfast",
        "servesLunch",
        "servesDinner",
        "servesBrunch",
        "servesDessert",
        "primaryType",
        "reviews",
        "priceRange",
        "postalAddress",
        "editorialSummary",
        "servesVegetarianFood",
    ]

    cph_df = pd.read_json(DATA_DIR / "copenhagen-bounds-limit10_20260316_125502.json")
    cph_df = cph_df[cph_df["businessStatus"] == "OPERATIONAL"]

    # unwrap the dictionaries in the DF
    cph_df["lat"] = cph_df["location"].apply(lambda x: x["latitude"])
    cph_df["lon"] = cph_df["location"].apply(lambda x: x["longitude"])
    cph_df["displayName"] = cph_df["displayName"].apply(lambda x: x["text"] if isinstance(x, dict) else x)
    cph_df["primaryTypeDisplayName"] = cph_df["primaryTypeDisplayName"].apply(lambda x: x["text"] if isinstance(x, dict) else x)
    cph_df["priceLabel"] = cph_df["priceRange"].apply(get_price_label)
    cph_df["midPrice"] = cph_df["priceRange"].apply(get_mid_price)
    cph_df["ratingLabel"] = cph_df["rating"].apply(get_ratings_label)
    # cph_df["ratingLabel"] = cph_df.apply(
    #     lambda r: f"{r['rating']} ⭐ ({int(r['userRatingCount'])} reviews)"
    #     if pd.notna(r.get("rating")) and pd.notna(r.get("userRatingCount"))
    #     else "No rating",
    #     axis=1,
    # )

    return cph_df

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

def get_figure(df):
    fig = px.scatter_map(
        cph_df,
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

cph_df = get_df()
fig = get_figure(cph_df)

st.plotly_chart(fig)
