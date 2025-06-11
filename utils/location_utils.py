# utils/location_utils.py

from geopy.distance import geodesic
import json
from pathlib import Path

BRANCHES = json.loads((Path(__file__).parent.parent.parent / "data" / "branches.json").read_text())

def get_branch_from_location(latitude, longitude):
    user_coords = (float(latitude), float(longitude))
    for branch_name, info in BRANCHES.items():
        coords = tuple(info["coordinates"])
        dist_km = geodesic(user_coords, coords).km
        if dist_km <= 2:
            return branch_name
    return None