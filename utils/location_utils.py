# utils/location_utils.py

from geopy.distance import geodesic
import json
from pathlib import Path

BRANCHES = Path(__file__).parent.parent.parent / "data" / "branches.json"

def get_branch_from_location(latitude, longitude):
    user_coords = (float(latitude), float(longitude))
    for branch_name, info in BRANCHES.items():
        coords = tuple(info["coordinates"])
        if geodesic(user_coords, coords).km <= 2:
            return branch_name
    return None