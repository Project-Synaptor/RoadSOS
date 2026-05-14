"""Local JSON-based emergency service lookup with haversine distance.

Loads hospital, police, and ambulance data from data/hospitals.json.
Uses Nominatim for geocoding text locations (no API key required).

To switch back to a live API (e.g. Geoapify), see the commented-out
section at the bottom of this file and set GEOAPIFY_API_KEY in .env.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import EmergencyService

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
_USER_AGENT = "RoadSoS/1.0"

# City bounding boxes for coordinate-based city detection
_CITY_BOUNDS: dict[str, tuple[float, float, float, float]] = {
    "bhubaneswar": (20.20, 85.73, 20.50, 85.95),
    "chennai": (12.95, 80.10, 13.15, 80.32),
}

# Module-level cache for loaded hospital data
_hospital_data: Optional[list[dict]] = None


class MapsError(Exception):
    """Raised when a maps lookup or geocoding call fails."""


def _load_hospital_data() -> list[dict]:
    """Load emergency services data from the JSON file.

    Reads the file once and caches the result in a module-level variable.

    Returns:
        List of service dicts from data/hospitals.json.

    Raises:
        MapsError: If the file is missing or contains invalid JSON.
    """
    global _hospital_data
    if _hospital_data is not None:
        return _hospital_data

    data_path = Path(settings.hospital_data_path)
    if not data_path.exists():
        raise MapsError(f"Hospital data file not found: {data_path}")

    try:
        with open(data_path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise MapsError(f"Invalid JSON in hospital data file: {exc}") from exc

    _hospital_data = raw.get("services", [])
    return _hospital_data


def get_city_from_coords(lat: float, lng: float) -> Optional[str]:
    """Determine which city the given coordinates fall in.

    Uses bounding box checks for supported cities.

    Args:
        lat: Latitude.
        lng: Longitude.

    Returns:
        City name string (e.g. "bhubaneswar", "chennai") or None if
        coordinates don't match any supported city.
    """
    for city, (min_lat, min_lng, max_lat, max_lng) in _CITY_BOUNDS.items():
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return city
    return None


def classify_trauma_level(service: dict) -> str:
    """Classify a hospital's trauma capability level.

    Level 1: trauma_capable + ICU + blood bank (full trauma centre)
    Level 2: trauma_capable + (ICU or blood bank)
    Level 3: basic facility (no trauma capability)

    Args:
        service: A service dict from hospitals.json.

    Returns:
        Trauma level string: "Level 1", "Level 2", or "Level 3".
    """
    if not service.get("trauma_capable"):
        return "Level 3"

    has_icu = service.get("has_icu", False)
    has_blood = service.get("has_blood_bank", False)

    if has_icu and has_blood:
        return "Level 1"
    if has_icu or has_blood:
        return "Level 2"
    return "Level 3"


def is_24x7(service: dict) -> bool:
    """Check if a service operates 24/7.

    Args:
        service: A service dict from hospitals.json.

    Returns:
        True if the service is available 24 hours.
    """
    return service.get("is_24x7", False)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in kilometres using the Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def geocode_location(location_text: str) -> tuple[float, float]:
    """Convert a text location description to lat/lng.

    Primary: Nominatim geocoding (no API key).
    Fallback: searches JSON data by area/landmark text matching.

    Args:
        location_text: Free-text location like "Near Adyar Signal, Chennai".

    Returns:
        Tuple of (latitude, longitude).

    Raises:
        MapsError: If geocoding fails or returns no results.
    """
    # Try Nominatim first
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE}/search",
                params={"q": location_text, "format": "json", "limit": 1},
                headers={"User-Agent": _USER_AGENT},
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise MapsError(f"Geocoding request failed: {exc}") from exc

        results = response.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])

    # Fallback: text search in local data
    services = _load_hospital_data()
    query_lower = location_text.lower()
    for svc in services:
        area = (svc.get("area") or "").lower()
        landmark = (svc.get("landmark") or "").lower()
        if query_lower in area or query_lower in landmark or area in query_lower:
            return svc["latitude"], svc["longitude"]

    raise MapsError(f"Geocoding found no results for '{location_text}'")


def find_nearest_services(
    lat: float,
    lng: float,
    service_types: Optional[list[str]] = None,
) -> list[EmergencyService]:
    """Find nearby emergency services from local JSON data.

    Filters by service type and city, computes haversine distance,
    and returns results sorted by distance (nearest first).

    Args:
        lat: Victim's latitude.
        lng: Victim's longitude.
        service_types: List of service types to search for.
            Defaults to ["hospital", "police"].

    Returns:
        List of EmergencyService sorted by distance (nearest first).
    """
    if service_types is None:
        service_types = ["hospital", "police"]

    services = _load_hospital_data()
    city = get_city_from_coords(lat, lng)

    results: list[EmergencyService] = []
    for svc in services:
        # Filter by service type
        if svc.get("service_type") not in service_types:
            continue

        # Filter by city if detected
        if city and svc.get("city") != city:
            continue

        dist = _haversine_km(lat, lng, svc["latitude"], svc["longitude"])

        # Build address from area + landmark
        address_parts = [p for p in [svc.get("area"), svc.get("landmark")] if p]
        address = ", ".join(address_parts) if address_parts else None

        results.append(
            EmergencyService(
                name=svc["name"],
                service_type=svc.get("service_type", "hospital"),
                phone=svc.get("phone"),
                distance_km=round(dist, 1),
                address=address,
                latitude=svc["latitude"],
                longitude=svc["longitude"],
                trauma_level=classify_trauma_level(svc),
                is_24x7=is_24x7(svc),
            )
        )

    results.sort(key=lambda s: s.distance_km if s.distance_km is not None else float("inf"))
    return results


def find_nearest_ambulance(lat: float, lng: float) -> list[EmergencyService]:
    """Find ambulance contacts for the nearest city.

    Args:
        lat: Victim's latitude.
        lng: Victim's longitude.

    Returns:
        List of EmergencyService for ambulances in the victim's city.
    """
    services = _load_hospital_data()
    city = get_city_from_coords(lat, lng)

    results: list[EmergencyService] = []
    for svc in services:
        if svc.get("service_type") != "ambulance":
            continue
        if city and svc.get("city") != city:
            continue

        dist = _haversine_km(lat, lng, svc["latitude"], svc["longitude"])
        results.append(
            EmergencyService(
                name=svc["name"],
                service_type="ambulance",
                phone=svc.get("phone"),
                distance_km=round(dist, 1),
                address=svc.get("area"),
                latitude=svc["latitude"],
                longitude=svc["longitude"],
            )
        )

    results.sort(key=lambda s: s.distance_km if s.distance_km is not None else float("inf"))
    return results


# ---------------------------------------------------------------------------
# Geoapify plug-and-play alternative
# ---------------------------------------------------------------------------
# To switch from local JSON to live Geoapify API:
#
# 1. Add GEOAPIFY_API_KEY to .env and config.py
# 2. Uncomment the code below
# 3. Replace calls to find_nearest_services() with find_nearest_geoapify()
#
# GEOAPIFY_BASE = "https://api.geoapify.com/v2/places"
#
# async def find_nearest_geoapify(
#     lat: float,
#     lng: float,
#     service_types: Optional[list[str]] = None,
# ) -> list[EmergencyService]:
#     """Find nearby services using Geoapify Places API.
#
#     Requires GEOAPIFY_API_KEY in environment.
#     """
#     if service_types is None:
#         service_types = ["hospital", "police"]
#
#     # Geoapify categories mapping
#     category_map = {
#         "hospital": "healthcare.hospital",
#         "police": "service.police",
#         "ambulance": "healthcare.ambulance",
#     }
#     categories = ",".join(category_map.get(t, t) for t in service_types)
#
#     async with httpx.AsyncClient(timeout=15.0) as client:
#         response = await client.get(
#             GEOAPIFY_BASE,
#             params={
#                 "categories": categories,
#                 "filter": f"circle:{lng},{lat},10000",
#                 "limit": 20,
#                 "apiKey": settings.geoapify_api_key,
#             },
#         )
#         response.raise_for_status()
#         data = response.json()
#
#     results = []
#     for feature in data.get("features", []):
#         props = feature.get("properties", {})
#         coords = feature.get("geometry", {}).get("coordinates", [None, None])
#         if coords[0] is None:
#             continue
#         dist = _haversine_km(lat, lng, coords[1], coords[0])
#         results.append(EmergencyService(
#             name=props.get("name", "Unknown"),
#             service_type=props.get("categories", ["unknown"])[0],
#             phone=props.get("contact", {}).get("phone"),
#             distance_km=round(dist, 1),
#             address=props.get("formatted"),
#             latitude=coords[1],
#             longitude=coords[0],
#         ))
#
#     results.sort(key=lambda s: s.distance_km or float("inf"))
#     return results
