"""Triage logic powered by MiMo V2.5 Pro.

Manages the conversation state machine defined in prompts/triage_system.txt.
Each incoming message triggers a state transition and a MiMo call to generate
the next reply.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import (
    EmergencyService,
    MessagePayload,
    SessionState,
    TriageResult,
    TriageState,
)
from app.services import maps

_SYSTEM_PROMPT: Optional[str] = None

# Golden hour constant: 60 minutes from injury
_GOLDEN_HOUR_MINUTES = 60


def _load_system_prompt() -> str:
    """Load the triage system prompt from disk (cached after first read)."""
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        prompt_path = Path(settings.triage_prompt_path)
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Triage system prompt not found at {prompt_path.resolve()}"
            )
        _SYSTEM_PROMPT = prompt_path.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


class TriageError(Exception):
    """Raised when the triage engine encounters an error."""


async def _call_mimo(messages: list[dict[str, str]]) -> str:
    """Send a chat completion request to MiMo V2.5 Pro.

    Args:
        messages: Conversation messages in OpenAI-compatible format.

    Returns:
        The assistant's reply text.

    Raises:
        TriageError: If the API call fails or returns no content.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.mimo_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.mimo_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mimo-v2.5-pro",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 300,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TriageError(
                f"MiMo API returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise TriageError(f"MiMo API request failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise TriageError("MiMo API returned no choices")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise TriageError("MiMo API returned empty content")

        return content


def _build_messages(session: SessionState, user_message: str) -> list[dict[str, str]]:
    """Build the message list for MiMo: system prompt + conversation history + new message.

    Args:
        session: Current user session state.
        user_message: The new incoming message text.

    Returns:
        List of message dicts for the MiMo chat API.
    """
    system_prompt = _load_system_prompt()

    # Inject current state context so MiMo knows where we are
    state_context = (
        f"\n\n[CURRENT STATE: {session.triage_state.value}]\n"
        f"[LOCATION RECEIVED: {'yes' if session.location_text or session.location_lat else 'no'}]\n"
        f"[SEVERITY ASSESSED: {'yes' if session.severity_description else 'no'}]\n"
        f"[LANGUAGE: {session.language_code}]"
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt + state_context}
    ]

    # Add conversation history (last 20 turns to stay within context)
    for entry in session.conversation_history[-20:]:
        messages.append(entry)

    messages.append({"role": "user", "content": user_message})
    return messages


def _extract_location_info(
    payload: MessagePayload, session: SessionState
) -> SessionState:
    """Extract and store location data from the payload into the session.

    Args:
        payload: Incoming message payload.
        session: Session to update.

    Returns:
        Updated session.
    """
    if payload.latitude is not None and payload.longitude is not None:
        session.location_lat = payload.latitude
        session.location_lng = payload.longitude
    elif payload.message_body and not session.location_text:
        text = payload.message_body.strip()
        lower = text.lower()

        # Explicit "location: ..." prefix (user followed the prompt)
        if "location" in lower and ":" in text:
            loc_part = text.split(":", 1)[1].strip()
            if loc_part:
                session.location_text = loc_part
        # Keyword heuristic: message looks like a location description
        elif len(text) > 5 and any(
            kw in lower
            for kw in [
                "near", "road", "street", "signal", "junction", "highway",
                "km", "opp", "at ", "behind", "in front", "next to",
                "beside", "opposite", "cross", "area", "nagar", "mandi",
            ]
        ):
            session.location_text = text

    return session


def _extract_severity_info(payload: MessagePayload, session: SessionState) -> SessionState:
    """Extract severity indicators from the user's message.

    Updates session fields based on keywords in the message.

    Args:
        payload: Incoming message payload.
        session: Session to update.

    Returns:
        Updated session.
    """
    text = payload.message_body.lower()

    if "unconscious" in text or "not conscious" in text or "unresponsive" in text:
        session.victim_conscious = False
    elif "conscious" in text or "awake" in text or "responsive" in text:
        session.victim_conscious = True

    if "can't move" in text or "cannot move" in text or "paralyzed" in text:
        session.victim_can_move = False
    elif "can move" in text or "able to move" in text:
        session.victim_can_move = True

    if not session.severity_description and session.triage_state == TriageState.SEVERITY_CHECK:
        session.severity_description = payload.message_body

    return session


def _detect_help_arrival(message: str) -> bool:
    """Check if the user is saying help has arrived."""
    arrival_phrases = [
        "help arrived", "help has arrived", "they arrived", "ambulance here",
        "ambulance arrived", "police here", "police arrived", "doctor here",
        "hospital here", "people here", "someone here", "rescued",
    ]
    lower = message.lower()
    return any(phrase in lower for phrase in arrival_phrases)


def format_golden_hour(session: SessionState) -> str:
    """Calculate remaining time in the Golden Hour window.

    The Golden Hour is 60 minutes from when triage began. Returns a
    human-readable countdown string.

    Args:
        session: Current session with triage_started_at timestamp.

    Returns:
        String like "~42 min remaining" or "critical" if expired.
    """
    if not session.triage_started_at:
        return "~60 min remaining"

    now = datetime.now(timezone.utc)
    started = session.triage_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)

    elapsed = (now - started).total_seconds() / 60.0
    remaining = _GOLDEN_HOUR_MINUTES - elapsed

    if remaining <= 0:
        return "CRITICAL — Golden Hour expired"
    if remaining <= 15:
        return f"~{int(remaining)} min remaining — URGENT"
    return f"~{int(remaining)} min remaining"


def format_dispatch_message(
    services: list[EmergencyService],
    ambulances: list[EmergencyService],
    session: SessionState,
) -> str:
    """Build a formatted WhatsApp dispatch message.

    Includes Golden Hour countdown, trauma-capable labels, hospital
    details, and emergency contacts.

    Args:
        services: List of nearby hospitals and police stations.
        ambulances: List of ambulance contacts for the city.
        session: Current session for Golden Hour calculation.

    Returns:
        Formatted WhatsApp message string.
    """
    golden = format_golden_hour(session)

    lines = [
        f"⏱️ GOLDEN HOUR: {golden}",
        "",
        "🆘 Nearest emergency services:",
    ]

    # Separate hospitals and police
    hospitals = [s for s in services if s.service_type == "hospital"]
    police = [s for s in services if s.service_type == "police"]

    # Hospitals with trauma labels
    for h in hospitals[:3]:
        trauma_tag = ""
        if h.trauma_level:
            if h.trauma_level == "Level 1":
                trauma_tag = " [TRAUMA CENTRE]"
            elif h.trauma_level == "Level 2":
                trauma_tag = " [TRAUMA CAPABLE]"
        hours = " 24x7" if h.is_24x7 else ""
        dist = f"{h.distance_km} km" if h.distance_km is not None else "N/A"
        phone = h.phone or "N/A"
        lines.append(f"🏥 {h.name} — {dist}{trauma_tag}{hours}")
        lines.append(f"   📞 {phone}")

    # Ambulance contacts
    if ambulances:
        lines.append("")
        lines.append("🚑 Ambulance:")
        for a in ambulances[:3]:
            phone = a.phone or "N/A"
            lines.append(f"   {a.name} — 📞 {phone}")

    # Police
    if police:
        lines.append("")
        lines.append("👮 Police:")
        for p in police[:2]:
            dist = f"{p.distance_km} km" if p.distance_km is not None else "N/A"
            phone = p.phone or "N/A"
            lines.append(f"   {p.name} — {dist} — 📞 {phone}")

    # National emergency numbers
    lines.append("")
    lines.append("📞 National Emergency: 112")
    lines.append("")
    lines.append("👉 Call them RIGHT NOW.")
    lines.append("I'll stay with you and guide you until help arrives.")

    return "\n".join(lines)


async def process_message(
    payload: MessagePayload, session: SessionState
) -> TriageResult:
    """Process an incoming message through the triage state machine.

    This is the main entry point for the triage engine. It:
    1. Updates session with any new location/severity data
    2. Detects state transitions
    3. Calls MiMo to generate the next reply
    4. Fetches emergency services when triage is complete

    Args:
        payload: The incoming parsed message.
        session: The user's current session state.

    Returns:
        TriageResult with the reply text, updated state, and any services found.

    Raises:
        TriageError: If MiMo API or Maps API fails.
    """
    user_text = payload.message_body.strip()

    # --- Update session with incoming data ---
    session = _extract_location_info(payload, session)
    session = _extract_severity_info(payload, session)

    # --- State machine transitions ---

    # Check for help arrival (can happen from any active state)
    if session.triage_state in (
        TriageState.DISPATCH,
        TriageState.FIRST_AID,
    ) and _detect_help_arrival(user_text):
        session.triage_state = TriageState.RESOLUTION
        session.conversation_history.append({"role": "user", "content": user_text})
        session.conversation_history.append(
            {"role": "assistant", "content": "Help arrived confirmation"}
        )
        return TriageResult(
            reply_text=(
                "\U0001f64f Help has arrived. You did great.\n"
                "Stay with the victim until they are taken care of.\n"
                "Take care of yourself too. \U0001f6a8"
            ),
            new_state=TriageState.RESOLUTION,
        )

    # Detect activation from distress keywords
    distress_keywords = ["help", "accident", "emergency", "crash", "hurt", "injured", "bleeding"]
    if session.triage_state == TriageState.ACTIVATION and any(
        kw in user_text.lower() for kw in distress_keywords
    ):
        session.triage_state = TriageState.ACTIVATION  # Stay in activation, MiMo handles reply

    # Detect transition to severity check (location received)
    if session.triage_state == TriageState.ACTIVATION and (
        session.location_lat is not None or session.location_text
    ):
        session.triage_state = TriageState.SEVERITY_CHECK
        if session.triage_started_at is None:
            session.triage_started_at = datetime.now(timezone.utc)

    # Detect triage complete (location + severity both present)
    has_location = session.location_lat is not None or session.location_text is not None
    has_severity = session.severity_description is not None
    if (
        session.triage_state == TriageState.SEVERITY_CHECK
        and has_location
        and has_severity
    ):
        session.triage_state = TriageState.TRIAGE_COMPLETE

    # --- Build and call MiMo ---
    messages = _build_messages(session, user_text)
    reply_text = await _call_mimo(messages)

    # Record in history
    session.conversation_history.append({"role": "user", "content": user_text})
    session.conversation_history.append({"role": "assistant", "content": reply_text})

    # --- Handle triage complete → dispatch ---
    emergency_services: list[EmergencyService] = []
    ambulance_contacts: list[EmergencyService] = []
    if session.triage_state == TriageState.TRIAGE_COMPLETE:
        # Fetch emergency services
        if session.location_lat is not None and session.location_lng is not None:
            emergency_services = maps.find_nearest_services(
                session.location_lat, session.location_lng
            )
            ambulance_contacts = maps.find_nearest_ambulance(
                session.location_lat, session.location_lng
            )
        elif session.location_text:
            lat, lng = await maps.geocode_location(session.location_text)
            session.location_lat = lat
            session.location_lng = lng
            emergency_services = maps.find_nearest_services(lat, lng)
            ambulance_contacts = maps.find_nearest_ambulance(lat, lng)

        session.triage_state = TriageState.DISPATCH

    # Format dispatch message with golden hour, trauma labels, contacts
    if session.triage_state == TriageState.DISPATCH and emergency_services:
        reply_text = format_dispatch_message(
            emergency_services, ambulance_contacts, session
        )

    # Transition to first aid after dispatch
    if session.triage_state == TriageState.DISPATCH and not emergency_services:
        session.triage_state = TriageState.FIRST_AID

    return TriageResult(
        reply_text=reply_text,
        new_state=session.triage_state,
        is_triage_complete=has_location and has_severity,
        emergency_services=emergency_services,
    )
