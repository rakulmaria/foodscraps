"""
Google Maps Places API - Starter Kit
Restaurant Menu Data Research - Copenhagen

Setup:
    pip install requests

Usage:
    1. Set your API key: export GOOGLE_MAPS_API_KEY="your_key_here"
       OR paste it directly into API_KEY below
    2. Run: python places_api_starter.py
"""

import requests
import json
import os
import time

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
API_KEY = os.getenv("MAPS_PLATFORM_API_KEY")

BASE_URL = "https://maps.googleapis.com/maps/api"


# -------------------------------------------------------------------
# 1. FIND A SINGLE RESTAURANT BY NAME + LOCATION
#    Uses: Text Search
#    Docs: https://developers.google.com/maps/documentation/places/web-service/text-search
# -------------------------------------------------------------------
def find_restaurant(name: str, city: str = "Copenhagen") -> dict:
    """
    Search for a specific restaurant by name.
    Returns the top match with basic details.
    """
    url = f"{BASE_URL}/place/textsearch/json"
    params = {
        "query": f"{name} restaurant {city}",
        "key": API_KEY,
        "language": "en",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK":
        print(f"[!] API error: {data.get('status')} — {data.get('error_message', '')}")
        return {}

    results = data.get("results", [])
    if not results:
        print(f"[!] No results found for '{name}'")
        return {}

    place = results[0]
    print(f"[+] Found: {place.get('name')} — {place.get('formatted_address')}")
    print(f"    Place ID: {place.get('place_id')}")
    print(f"    Rating: {place.get('rating')} ({place.get('user_ratings_total')} reviews)")
    return place


# -------------------------------------------------------------------
# 2. GET FULL DETAILS FOR A RESTAURANT (by Place ID)
#    Uses: Place Details
#    Docs: https://developers.google.com/maps/documentation/places/web-service/details
#
#    Key fields for menu research:
#      - website (often links to menu)
#      - url (Google Maps link)
#      - opening_hours
#      - price_level (1=cheap, 4=expensive)
#      - types (cuisine categories)
# -------------------------------------------------------------------
def get_place_details(place_id: str, fields: list | None = None) -> dict:
    """
    Fetch detailed info for a restaurant using its Place ID.
    Customize `fields` to control cost (billed per field category).
    """
    if fields is None:
        fields = [
            # Basic (cheapest tier)
            "name", "place_id", "types", "price_level",
            # Contact
            "formatted_phone_number", "website", "url",
            # Atmosphere
            "rating", "user_ratings_total", "opening_hours",
            # Address
            "formatted_address", "geometry",
        ]

    url = f"{BASE_URL}/place/details/json"
    params = {
        "place_id": place_id,
        "fields": ",".join(fields),
        "key": API_KEY,
        "language": "en",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK":
        print(f"[!] API error: {data.get('status')} — {data.get('error_message', '')}")
        return {}

    result = data.get("result", {})
    print(f"\n--- Details: {result.get('name')} ---")
    print(f"  Address  : {result.get('formatted_address')}")
    print(f"  Website  : {result.get('website', 'N/A')}")
    print(f"  Phone    : {result.get('formatted_phone_number', 'N/A')}")
    print(f"  Price    : {'$' * result.get('price_level', 0) or 'N/A'}")
    print(f"  Types    : {', '.join(result.get('types', []))}")

    hours = result.get("opening_hours", {}).get("weekday_text", [])
    if hours:
        print("  Hours    :")
        for h in hours:
            print(f"    {h}")

    return result


# -------------------------------------------------------------------
# 3. SEARCH RESTAURANTS IN AN AREA
#    Uses: Nearby Search
#    Docs: https://developers.google.com/maps/documentation/places/web-service/nearby-search
#
#    Copenhagen city center coords: 55.6761, 12.5683
# -------------------------------------------------------------------
def search_restaurants_in_area(
    lat: float,
    lng: float,
    radius_meters: int = 1000,
    keyword: str | None = None,
    max_pages: int = 1,  # each page = up to 20 results; max 3 pages = 60 results
) -> list:
    """
    Search for all restaurants within a radius of a coordinate point.

    Tips:
    - radius_meters: max 50000, but smaller = more focused results
    - keyword: filter by cuisine e.g. "italian", "sushi", "smørrebrød"
    - max_pages: each extra page costs an additional API call (2s delay required between pages)
    """
    url = f"{BASE_URL}/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_meters,
        "type": "restaurant",
        "key": API_KEY,
        "language": "en",
    }
    if keyword:
        params["keyword"] = keyword

    all_results = []
    page = 1

    while page <= max_pages:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            print(f"[!] API error on page {page}: {status} — {data.get('error_message', '')}")
            break

        results = data.get("results", [])
        all_results.extend(results)
        print(f"[+] Page {page}: fetched {len(results)} restaurants (total: {len(all_results)})")

        next_page_token = data.get("next_page_token")
        if not next_page_token or page >= max_pages:
            break

        # Google requires a short delay before the next page token becomes valid
        time.sleep(2)
        params = {"pagetoken": next_page_token, "key": API_KEY}
        page += 1

    return all_results


# -------------------------------------------------------------------
# HELPER: Save results to JSON
# -------------------------------------------------------------------
def save_to_json(data, filename: str = "results.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved to {filename}")


# -------------------------------------------------------------------
# MAIN — Example usage (edit as needed)
# -------------------------------------------------------------------
if __name__ == "__main__":

    print("=" * 60)
    print("EXAMPLE 1: Find a single restaurant by name")
    print("=" * 60)

    restaurant = find_restaurant("Gasoline Grill", city="Copenhagen")

    if restaurant:
        place_id = restaurant["place_id"]

        print("\n" + "=" * 60)
        print("EXAMPLE 2: Get full details using Place ID")
        print("=" * 60)

        details = get_place_details(place_id)
        save_to_json(details, "noma_details.json")

    print("\n" + "=" * 60)
    print("EXAMPLE 3: Search restaurants near Copenhagen city center")
    print("=" * 60)

    # Coords: Rådhuspladsen (City Hall Square), Copenhagen
    nearby = search_restaurants_in_area(
        lat=55.6761,
        lng=12.5683,
        radius_meters=500,   # 500m radius — adjust freely
        keyword=None,        # Try: "sushi", "pizza", "smørrebrød"
        max_pages=1,         # Up to 3 pages for 60 results
    )

    print(f"\n[+] Total restaurants found: {len(nearby)}")
    for r in nearby:
        print(f"  - {r.get('name'):40s} | Rating: {r.get('rating', 'N/A')} | {r.get('vicinity', '')}")

    save_to_json(nearby, "copenhagen_restaurants.json")