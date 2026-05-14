"""Pydantic v2 models for messages, sessions, triage results, and emergency services.

All data flowing through the system is validated here.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TriageState(str, Enum):
    """States the triage conversation can be in, matching prompts/triage_system.txt."""

    ACTIVATION = "activation"
    SEVERITY_CHECK = "severity_check"
    TRIAGE_COMPLETE = "triage_complete"
    DISPATCH = "dispatch"
    FIRST_AID = "first_aid"
    RESOLUTION = "resolution"


class EmergencyService(BaseModel):
    """A nearby emergency service returned from local JSON data."""

    name: str = Field(description="Name of the service (hospital, police, etc.)")
    service_type: str = Field(description="Type: hospital, ambulance, police, fire")
    phone: Optional[str] = Field(default=None, description="Phone number if available")
    distance_km: Optional[float] = Field(default=None, description="Distance in km from victim")
    address: Optional[str] = Field(default=None, description="Street address")
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    trauma_level: Optional[str] = Field(default=None, description="Trauma capability: Level 1, Level 2, or Level 3")
    is_24x7: Optional[bool] = Field(default=None, description="Whether the service operates 24/7")


class TriageResult(BaseModel):
    """Result from a single triage turn."""

    reply_text: str = Field(description="Text reply to send to the user")
    new_state: TriageState = Field(description="Updated triage state")
    is_triage_complete: bool = Field(default=False, description="Whether we have location + severity")
    emergency_services: list[EmergencyService] = Field(default_factory=list)
    send_as_voice: bool = Field(default=False, description="Whether to send reply as voice note")


class SessionState(BaseModel):
    """Per-user session stored in Redis."""

    user_id: str = Field(description="Twilio sender identifier (e.g. whatsapp:+1234567890)")
    triage_state: TriageState = Field(default=TriageState.ACTIVATION)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    location_text: Optional[str] = Field(default=None, description="Text description of location")
    location_lat: Optional[float] = Field(default=None, description="Latitude from WhatsApp pin")
    location_lng: Optional[float] = Field(default=None, description="Longitude from WhatsApp pin")
    severity_description: Optional[str] = Field(default=None, description="User's description of injuries")
    victim_conscious: Optional[bool] = Field(default=None)
    victim_can_move: Optional[bool] = Field(default=None)
    first_aid_step: int = Field(default=0, description="Current first aid instruction index")
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    triage_started_at: Optional[datetime] = Field(default=None, description="When triage began for Golden Hour tracking")
    language_code: str = Field(default="en", description="Preferred language ISO 639-1 code (en, hi, bn, or, ta, te, kn, ml)")
    input_modality: str = Field(default="text", description="How the user sent their last message: text or voice")


class MessagePayload(BaseModel):
    """Parsed incoming Twilio WhatsApp webhook payload."""

    sender: str = Field(description="Sender identifier (e.g. whatsapp:+1234567890)")
    message_body: str = Field(default="", description="Text content of the message")
    num_media: int = Field(default=0, description="Number of media attachments")
    media_url: Optional[str] = Field(default=None, description="URL of first media attachment")
    media_content_type: Optional[str] = Field(default=None, description="MIME type of media")
    latitude: Optional[float] = Field(default=None, description="Latitude from WhatsApp location pin")
    longitude: Optional[float] = Field(default=None, description="Longitude from WhatsApp location pin")
