import json
import os

import requests

API_KEY = os.getenv("MAPS_PLATFORM_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "*",  # what i want to be included in the respond
}

# FIELD_MASK = 'places.id,places.types,places.displayName

def search_nearby(lat, lon, radius):
    url = "https://places.googleapis.com/v1/places:searchNearby"

    data = {
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

    response = requests.post(url, json=data, headers=HEADERS)
    
    if response.status_code == 200:
        print(f"Response OK: {response.status_code}")
    else:
        print(f"! ERROR: {response.status_code}")
        print(f"{response.text}")

    data = response.json()

    return data.get("places", [])



def find_aggregated_places():
    url = "https://areainsights.googleapis.com/v1:computeInsights"

    data = {
        "insights": ["INSIGHT_COUNT", "INSIGHT_PLACES"],
        "filter": {
            "locationFilter": {
                "region": {"place": "places/ChIJIz2AXDxTUkYRuGeU5t1-3QQ"} # copenhagen ID
            },
            "typeFilter": {"includedTypes": "restaurant"},
        },
    }
    response = requests.post(url, json=data, headers=HEADERS)

    if response.status_code == 200:
        print(f"Response OK: {response.status_code}")
    else:
        print(f"! ERROR: {response.status_code}")


    return json.loads(response.text)


def find_place(query):
    # Define the API endpoint
    url = "https://places.googleapis.com/v1/places:searchText"

    # Define the data payload for the POST request
    data = {"textQuery": query}

    # Make the POST request
    response = requests.post(url, json=data, headers=HEADERS)

    # Check if the request was successful
    if response.status_code == 200:
        print(f"Response OK: {response.status_code}")
    else:
        print(f"! ERROR: {response.status_code}")

    return json.loads(response.text)


def save_to_json(data, filename: str = "results.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {filename}")


if __name__ == "__main__":
    # prompts
    carlsberg_byen = "Restaurants in area Carlsberg Byen, Copenhagen"

    place = find_place(carlsberg_byen)
    save_to_json(place)
