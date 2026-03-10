import math
import time

import src.googleapi as googleapi

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

def haversine(lat1, lon1, lat2, lon2):
    """
    Returns the distance in meters between two lat/lon points.
    Uses the Haversine formula to account for Earth's curvature.
    @author: Claude
    """
    R = 6_371_000

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class BoundingBox:
    def __init__(self, lat_south, lat_north, lon_west, lon_east):
        self.lat_south = lat_south
        self.lat_north = lat_north
        self.lon_west = lon_west
        self.lon_east = lon_east

    def center(self):
        center_lat = (self.lat_south + self.lat_north) / 2
        center_lon = (self.lon_west + self.lon_east) / 2
        return center_lat, center_lon

    def radius_meters(self):
        """haversine distance from center to corners, to guarantee full coverage of bounding box"""
        center_lat, center_lon = self.center()
        return haversine(center_lat, center_lon, self.lat_north, self.lon_east)

    def split_bounding_box(self):
        """split into four equal quadrants: NW, NE, SW, SE.
        each bounding box is their own quadrant that might be further split
        core-logic of quadtrees!
        """
        mid_lat = (self.lat_south + self.lat_north) / 2
        mid_lon = (self.lon_west + self.lon_east) / 2
        return [
            BoundingBox(mid_lat, self.lat_north, self.lon_west, mid_lon),  # NW
            BoundingBox(mid_lat, self.lat_north, mid_lon, self.lon_east),  # NE
            BoundingBox(self.lat_south, mid_lat, self.lon_west, mid_lon),  # SW
            BoundingBox(self.lat_south, mid_lat, mid_lon, self.lon_east),  # SE
        ]


class Node:
    def __init__(self, bounding_box):
        self.bounding_box = bounding_box
        self.results = []
        self.children = []

    def is_leaf(self):
        return len(self.children) == 0


def build_quadtree(bounding_box, depth=0):
    """
    recursively builds a quadtree over the bounding box.
    splits a cell into 4 if the API returns 20 (meaning it's saturated).
    stops splitting when the cell contains < 20 results.
    """
    node = Node(bounding_box)
    indent = "  " * depth
    center_lat, center_lon = bounding_box.center()
    radius = bounding_box.radius_meters()

    print(f"{indent}Querying cell (depth={depth}): center={f"{center_lat}, {center_lon}"}, radius={radius:.0f}m")

    # buffer to respect API rate limits
    time.sleep(0.1)

    results = googleapi.search_nearby(center_lat, center_lon, radius)

    print(f"{indent}-> Got {len(results)} results")

    # cell is not saturated, we're done here
    if len(results) < 20:
        node.results = results
        return node

    # otherwise, cell is saturated, so we recursively split into 4 quadrants
    print(f"{indent}  Saturated — splitting into 4 quadrants")
    for child_bounding_box in bounding_box.split_bounding_box():
        # recursively build new quadtrees and append the children to the current node
        child_node = build_quadtree(child_bounding_box, depth + 1)
        node.children.append(child_node)

    return node


def collect_results(node):
    """
    walk the quadtree and collect all results from leaf nodes.
    deduplicates by place ID since restaurants near cell borders
    may appear in multiple overlapping queries.
    """
    seen_ids = set()
    restaurants = []

    def walk(n):
        if n.is_leaf():
            for place in n.results:
                place_id = place.get("id")
                if place_id and place_id not in seen_ids:
                    seen_ids.add(place_id)
                    restaurants.append(place)
        else:
            for child in n.children:
                walk(child)

    walk(node)
    return restaurants


def main():
    bounding_box = BoundingBox(
        lat_south=MINI_BOX["lat_south"],
        lat_north=MINI_BOX["lat_north"],
        lon_west=MINI_BOX["lon_west"],
        lon_east=MINI_BOX["lon_east"],
    )

    print("Starting quadtree search over Mini Box...")
    root = build_quadtree(bounding_box)

    restaurants = collect_results(root)
    print(f"\nDone! Found {len(restaurants)} unique restaurants.")

    googleapi.save_to_json(restaurants, "mini-box.json")

    for r in restaurants:
        name = r.get("displayName", {}).get("text", "Unknown")
        loc = r.get("location", {})
        print(f"  {name}: ({loc.get('latitude')}, {loc.get('longitude')})")

    return restaurants


if __name__ == "__main__":
    main()
