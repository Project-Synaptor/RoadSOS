"""Tests for triage dispatch formatting: golden hour and message builder."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.schemas import EmergencyService, SessionState, TriageState
from app.services.triage import format_dispatch_message, format_golden_hour


def _make_session(triage_started_at=None) -> SessionState:
    """Create a minimal session for testing."""
    return SessionState(
        user_id="whatsapp:+1234567890",
        triage_state=TriageState.DISPATCH,
        triage_started_at=triage_started_at,
    )


def _make_hospital(name="Test Hospital", trauma_level="Level 1", is_24x7=True, dist=2.5):
    """Create a test EmergencyService."""
    return EmergencyService(
        name=name,
        service_type="hospital",
        phone="0674-1234567",
        distance_km=dist,
        address="Test Area",
        latitude=20.0,
        longitude=85.0,
        trauma_level=trauma_level,
        is_24x7=is_24x7,
    )


def _make_ambulance(name="108 Ambulance"):
    """Create a test ambulance EmergencyService."""
    return EmergencyService(
        name=name,
        service_type="ambulance",
        phone="108",
        distance_km=None,
        address="Citywide",
        latitude=20.0,
        longitude=85.0,
    )


def _make_police(name="Test Police Station", dist=3.0):
    """Create a test police EmergencyService."""
    return EmergencyService(
        name=name,
        service_type="police",
        phone="0674-9999999",
        distance_km=dist,
        address="Test Area",
        latitude=20.0,
        longitude=85.0,
    )


class TestFormatGoldenHour:
    """Tests for format_golden_hour()."""

    def test_no_start_time_returns_60_min(self):
        session = _make_session(triage_started_at=None)
        result = format_golden_hour(session)
        assert "~60 min remaining" in result

    def test_30_min_elapsed(self):
        started = datetime.now(timezone.utc) - timedelta(minutes=30)
        session = _make_session(triage_started_at=started)
        result = format_golden_hour(session)
        assert "~29 min remaining" in result or "~30 min remaining" in result

    def test_50_min_elapsed_urgent(self):
        started = datetime.now(timezone.utc) - timedelta(minutes=50)
        session = _make_session(triage_started_at=started)
        result = format_golden_hour(session)
        assert "URGENT" in result

    def test_expired(self):
        started = datetime.now(timezone.utc) - timedelta(minutes=70)
        session = _make_session(triage_started_at=started)
        result = format_golden_hour(session)
        assert "CRITICAL" in result or "expired" in result.lower()


class TestFormatDispatchMessage:
    """Tests for format_dispatch_message()."""

    def test_includes_golden_hour(self):
        session = _make_session(triage_started_at=datetime.now(timezone.utc))
        msg = format_dispatch_message([], [], session)
        assert "GOLDEN HOUR" in msg

    def test_includes_hospitals(self):
        session = _make_session()
        hospitals = [_make_hospital("Apollo Hospital")]
        msg = format_dispatch_message(hospitals, [], session)
        assert "Apollo Hospital" in msg
        assert "🏥" in msg

    def test_includes_trauma_label_level1(self):
        session = _make_session()
        hospitals = [_make_hospital(trauma_level="Level 1")]
        msg = format_dispatch_message(hospitals, [], session)
        assert "TRAUMA CENTRE" in msg

    def test_includes_trauma_label_level2(self):
        session = _make_session()
        hospitals = [_make_hospital(trauma_level="Level 2")]
        msg = format_dispatch_message(hospitals, [], session)
        assert "TRAUMA CAPABLE" in msg

    def test_includes_24x7(self):
        session = _make_session()
        hospitals = [_make_hospital(is_24x7=True)]
        msg = format_dispatch_message(hospitals, [], session)
        assert "24x7" in msg

    def test_includes_ambulance(self):
        session = _make_session()
        ambulances = [_make_ambulance("108 Emergency")]
        msg = format_dispatch_message([], ambulances, session)
        assert "108 Emergency" in msg
        assert "🚑" in msg

    def test_includes_police(self):
        session = _make_session()
        police = [_make_police("Khandagiri PS")]
        msg = format_dispatch_message(police, [], session)
        assert "Khandagiri PS" in msg
        assert "👮" in msg

    def test_includes_national_emergency(self):
        session = _make_session()
        msg = format_dispatch_message([], [], session)
        assert "112" in msg

    def test_includes_call_to_action(self):
        session = _make_session()
        msg = format_dispatch_message([], [], session)
        assert "Call them RIGHT NOW" in msg

    def test_full_message_structure(self):
        session = _make_session(triage_started_at=datetime.now(timezone.utc))
        services = [
            _make_hospital("AIIMS Bhubaneswar", "Level 1", True, 1.5),
            _make_hospital("Capital Hospital", "Level 3", True, 3.2),
            _make_police("Khandagiri PS", 2.0),
        ]
        ambulances = [_make_ambulance("108 Emergency")]
        msg = format_dispatch_message(services, ambulances, session)

        assert "GOLDEN HOUR" in msg
        assert "AIIMS Bhubaneswar" in msg
        assert "Capital Hospital" in msg
        assert "108 Emergency" in msg
        assert "Khandagiri PS" in msg
        assert "112" in msg
