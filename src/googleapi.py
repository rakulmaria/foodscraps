import datetime as dt
import json
import logging
import os

import requests

from config import DATA_DIR
from logger import setup_logger

# --- logger
logger = logging.getLogger(__name__)

# --- global shared vars ---
API_KEY = os.getenv("MAPS_PLATFORM_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "*",  # what i want to be included in the respond
}


def make_request(url, body, headers=HEADERS):
    """default request method"""
    response = requests.post(url, json=body, headers=HEADERS)
    response.raise_for_status
    return response.json()


# --- API calls to google maps
def search_nearby(lat, lon, radius):
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


def find_aggregated_places():
    """uses Places Aggregated API to fetch aggregated count of restaurants in an area
    initially used to find total count of restaurants in CPH
    """
    # "place": "places/ChIJIz2AXDxTUkYRuGeU5t1-3QQ"  # copenhagen ID
    url = "https://areainsights.googleapis.com/v1:computeInsights"
    body = {
        "insights": ["INSIGHT_COUNT", "INSIGHT_PLACES"],
        "filter": {
            "locationFilter": {
                "customArea": {
                    "polygon": {
                        "coordinates": [
                            { # NW
                                "latitude": 55.669764,
                                "longitude": 12.542044,
                            },
                            { # SW
                                "latitude": 55.667723,
                                "longitude": 12.542044,
                            },
                            { # SE
                                "latitude": 55.667723,
                                "longitude": 12.554734,
                            },
                            { # NE
                                "latitude": 55.669764,
                                "longitude": 12.554734,
                            },  
                            { # NW: closes the loop
                                "latitude": 55.669764,
                                "longitude": 12.542044,
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


def search_text(text_query):
    """uses Text Search from Placse API (New) to fetch restaurants based on a prompt
    ! needs to be handled with caution
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    body = {"textQuery": text_query}

    response = make_request(url, body)
    return response


def save_to_json(data, prefix="results"):
    """simple helper method to save the data to a json file"""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = DATA_DIR / f"{prefix}_{timestamp}.json"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # prompts
    # carlsberg_byen = "Restaurants in area Carlsberg Byen, Copenhagen"
    # place = search_text(carlsberg_byen)

    # save_to_json(place)
    results = find_aggregated_places()
    
    logger.info(results)


if __name__ == "__main__":
    setup_logger() 
    main()
