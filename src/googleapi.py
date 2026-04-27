import datetime as dt
import json
import logging
import os
from functools import partial

import requests
from timer import function_timer

from config import DATA_DIR
from logger import setup_logger

function_timer = partial(function_timer, decimals=5)


# --- logger
logger = logging.getLogger(__name__)

# --- global shared vars ---
API_KEY = os.getenv("MAPS_PLATFORM_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "*",  # what i want to be included in the respond
}

# bounds found from here: https://epsg.io/4693-area
COPENHAGEN_BOUNDS = {
    "lat_south": 55.51,
    "lat_north": 55.82,
    "lon_west": 12.23,
    "lon_east": 12.73,
}

# mini bounding box, used for testing purpose
MINI_BOX = {
    "lat_north": 55.669764,
    "lat_south": 55.667723,
    "lon_west": 12.542044,
    "lon_east": 12.554734,
}


# @function_timer()
def make_request(url, body, headers=HEADERS):
    """default request method"""
    response = requests.post(url, json=body, headers=HEADERS)
    response.raise_for_status
    return response.json()


# --- API calls to google maps
# @function_timer()
def nearby_search(lat, lon, radius):
    """uses Nearby Search from Placse API (New) to fetch restaurants near to a centerpoint"""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    body = {
        "includedTypes": ["restaurant"],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon,
                },
                "radius": radius,
            }
        },
    }

    response = make_request(url, body)

    return response.get("places", [])  # unwrap the places entry


# @function_timer()
def find_aggregated_places(coordinates):
    """uses Places Aggregated API to fetch aggregated count of restaurants in an area
    initially used to find total count of restaurants in CPH
    """
    url = "https://areainsights.googleapis.com/v1:computeInsights"

    body = {
        "insights": ["INSIGHT_COUNT"],
        "filter": {
            "locationFilter": {
                "customArea": {
                    "polygon": {
                        "coordinates": [
                            {  # NW
                                "latitude": coordinates["lat_north"],
                                "longitude": coordinates["lon_west"],
                            },
                            {  # SW
                                "latitude": coordinates["lat_south"],
                                "longitude": coordinates["lon_west"],
                            },
                            {  # SE
                                "latitude": coordinates["lat_south"],
                                "longitude": coordinates["lon_east"],
                            },
                            {  # NE
                                "latitude": coordinates["lat_north"],
                                "longitude": coordinates["lon_east"],
                            },
                            {  # NW: closes the loop
                                "latitude": coordinates["lat_north"],
                                "longitude": coordinates["lon_west"],
                            },
                        ]
                    }
                }
            },
            "typeFilter": {"includedTypes": "restaurant"},
        },
    }

    response = make_request(url, body)

    return response


# @function_timer()
def search_text(text_query):
    """ -- NIU --
    uses Text Search from Placse API (New) to fetch restaurants based on a prompt 
    ! needs to be handled with caution
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    body = { "textQuery" : text_query }

    response = make_request(url, body)
    return response


@function_timer()
def save_to_json(data, prefix="results"):
    """simple helper method to save the data to a json file"""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = DATA_DIR / f"{prefix}_{timestamp}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@function_timer()
def main():

    # save_to_json(place)
    results = find_aggregated_places(COPENHAGEN_BOUNDS)

    logger.info(results)


if __name__ == "__main__":
    setup_logger()
    main()
