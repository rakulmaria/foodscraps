import pandas as pd

from config import DATA_DIR


def get_df():
    """
    load and clean the Copenhagen places dataset for analysis.
    """
    cph_df = pd.read_json(DATA_DIR / "copenhagen-bounds-limit10_20260316_125502.json")
    
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
        "primaryTypeDisplayName",
        "reviews",
        "priceRange",
        "postalAddress",
        "editorialSummary",
        "servesVegetarianFood",
    ]
    cph_df = cph_df[cols_to_keep]

    # only keep restaurants that are operational
    cph_df = cph_df[cph_df["businessStatus"] == "OPERATIONAL"]

    # unwrap the dictionaries in the DF
    cph_df["lat"] = cph_df["location"].apply(lambda x: x["latitude"])
    cph_df["lon"] = cph_df["location"].apply(lambda x: x["longitude"])
    cph_df["displayName"] = cph_df["displayName"].apply(lambda x: x["text"] if isinstance(x, dict) else x)
    cph_df["primaryTypeDisplayName"] = cph_df["primaryTypeDisplayName"].apply(lambda x: x["text"] if isinstance(x, dict) else x)

    return cph_df
