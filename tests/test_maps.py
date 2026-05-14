"""Tests for the maps service: data loading, haversine, nearest services, trauma classification."""

from __future__ import annotations

import math

import pytest

from app.services.maps import (
    _haversine_km,
    _load_hospital_data,
    classify_trauma_level,
    find_nearest_ambulance,
    find_nearest_services,
    get_city_from_coords,
    is_24x7,
)


class TestLoadHospitalData:
    """Tests for _load_hospital_data()."""

    def test_returns_list(self):
        data = _load_hospital_data()
        assert isinstance(data, list)

    def test_has_correct_counts(self):
        data = _load_hospital_data()
        bhub_hospitals = [s for s in data if s["city"] == "bhubaneswar" and s["service_type"] == "hospital"]
        bhub_police = [s for s in data if s["city"] == "bhubaneswar" and s["service_type"] == "police"]
        bhub_ambulance = [s for s in data if s["city"] == "bhubaneswar" and s["service_type"] == "ambulance"]
        chen_hospitals = [s for s in data if s["city"] == "chennai" and s["service_type"] == "hospital"]
        chen_police = [s for s in data if s["city"] == "chennai" and s["service_type"] == "police"]
        chen_ambulance = [s for s in data if s["city"] == "chennai" and s["service_type"] == "ambulance"]

        assert len(bhub_hospitals) == 8
        assert len(bhub_police) == 3
        assert len(bhub_ambulance) == 3
        assert len(chen_hospitals) == 8
        assert len(chen_police) == 3
        assert len(chen_ambulance) == 3

    def test_all_records_have_required_fields(self):
        data = _load_hospital_data()
        required = [
            "name", "city", "area", "landmark", "latitude", "longitude",
            "phone", "trauma_capable", "has_icu", "has_blood_bank",
            "is_24x7", "type", "service_type",
        ]
        for svc in data:
            for field in required:
                assert field in svc, f"Record '{svc.get('name')}' missing field: {field}"


class TestHaversine:
    """Tests for _haversine_km()."""

    def test_same_point_is_zero(self):
        assert _haversine_km(20.0, 85.0, 20.0, 85.0) == 0.0

    def test_known_distance_bhubaneswar_to_cuttack(self):
        # AIIMS Bhubaneswar to SCB Medical College Cuttack ~27km
        dist = _haversine_km(20.2312, 85.7751, 20.4730, 85.8912)
        assert 25 < dist < 30

    def test_symmetry(self):
        d1 = _haversine_km(20.0, 85.0, 21.0, 86.0)
        d2 = _haversine_km(21.0, 86.0, 20.0, 85.0)
        assert abs(d1 - d2) < 0.001


class TestGetCityFromCoords:
    """Tests for get_city_from_coords()."""

    def test_bhubaneswar_coords(self):
        # AIIMS Bhubaneswar
        assert get_city_from_coords(20.2312, 85.7751) == "bhubaneswar"

    def test_chennai_coords(self):
        # Stanley Medical College Chennai
        assert get_city_from_coords(13.1058, 80.2872) == "chennai"

    def test_unknown_coords(self):
        # Delhi
        assert get_city_from_coords(28.6139, 77.2090) is None


class TestClassifyTraumaLevel:
    """Tests for classify_trauma_level()."""

    def test_level_1_all_capabilities(self):
        svc = {"trauma_capable": True, "has_icu": True, "has_blood_bank": True}
        assert classify_trauma_level(svc) == "Level 1"

    def test_level_2_trauma_and_icu_only(self):
        svc = {"trauma_capable": True, "has_icu": True, "has_blood_bank": False}
        assert classify_trauma_level(svc) == "Level 2"

    def test_level_2_trauma_and_blood_only(self):
        svc = {"trauma_capable": True, "has_icu": False, "has_blood_bank": True}
        assert classify_trauma_level(svc) == "Level 2"

    def test_level_3_no_trauma(self):
        svc = {"trauma_capable": False, "has_icu": True, "has_blood_bank": True}
        assert classify_trauma_level(svc) == "Level 3"

    def test_level_3_trauma_no_icu_no_blood(self):
        svc = {"trauma_capable": True, "has_icu": False, "has_blood_bank": False}
        assert classify_trauma_level(svc) == "Level 3"


class TestIs24x7:
    """Tests for is_24x7()."""

    def test_true(self):
        assert is_24x7({"is_24x7": True}) is True

    def test_false(self):
        assert is_24x7({"is_24x7": False}) is False

    def test_missing_defaults_false(self):
        assert is_24x7({}) is False


class TestFindNearestServices:
    """Tests for find_nearest_services()."""

    def test_returns_sorted_results(self):
        # Near AIIMS Bhubaneswar
        results = find_nearest_services(20.2312, 85.7751, ["hospital"])
        assert len(results) > 0
        distances = [r.distance_km for r in results]
        assert distances == sorted(distances)

    def test_filters_by_service_type(self):
        results = find_nearest_services(20.2312, 85.7751, ["police"])
        for r in results:
            assert r.service_type == "police"

    def test_returns_emergency_service_objects(self):
        results = find_nearest_services(20.2312, 85.7751, ["hospital"])
        assert results[0].name
        assert results[0].phone
        assert results[0].distance_km is not None
        assert results[0].latitude is not None
        assert results[0].longitude is not None

    def test_trauma_level_populated(self):
        results = find_nearest_services(20.2312, 85.7751, ["hospital"])
        for r in results:
            assert r.trauma_level in ("Level 1", "Level 2", "Level 3")

    def test_24x7_populated(self):
        results = find_nearest_services(20.2312, 85.7751, ["hospital"])
        for r in results:
            assert r.is_24x7 is not None


class TestFindNearestAmbulance:
    """Tests for find_nearest_ambulance()."""

    def test_returns_ambulance_contacts(self):
        results = find_nearest_ambulance(20.2312, 85.7751)
        assert len(results) > 0
        for r in results:
            assert r.service_type == "ambulance"

    def test_chennai_ambulance(self):
        results = find_nearest_ambulance(13.1058, 80.2872)
        assert len(results) > 0
