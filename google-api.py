import json
import os
import requests

API_KEY = os.getenv("MAPS_PLATFORM_API_KEY")
# FIELD_MASK = 'places.id,places.types,places.displayName'

def find_place(query, api_key):    
    # Define the API endpoint
    url = 'https://places.googleapis.com/v1/places:searchText'

    # Define the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,  
        'X-Goog-FieldMask': '*'     # what i want to be included in the respond
    }

    # Define the data payload for the POST request
    data = {
        'textQuery': query
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=data)

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
    

    place = find_place(carlsberg_byen, API_KEY)
    save_to_json(place)