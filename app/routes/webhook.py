"""Twilio WhatsApp webhook endpoint.

Parses incoming Twilio webhook payloads, dispatches to the triage engine,
and returns TwiML responses. Handles both text messages and voice notes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse

from app.models.schemas import MessagePayload, TriageState
from app.services import session as session_service
from app.services import stt, triage, tts
from app.services.language import detect_language_from_text
from app.utils.twilio_client import build_twiml_reply, build_twiml_media_reply, upload_media

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_twilio_form(form: dict[str, str]) -> MessagePayload:
    """Extract a MessagePayload from Twilio's webhook form data.

    Args:
        form: The decoded form data from Twilio's POST request.

    Returns:
        Parsed MessagePayload.
    """
    sender = form.get("From", "")
    body = form.get("Body", "").strip()
    num_media = int(form.get("NumMedia", "0"))
    media_url: Optional[str] = None
    media_type: Optional[str] = None

    if num_media > 0:
        media_url = form.get("MediaUrl0")
        media_type = form.get("MediaContentType0")

    # Twilio sends location pins as Latitude/Longitude fields
    lat: Optional[float] = None
    lng: Optional[float] = None
    if form.get("Latitude") and form.get("Longitude"):
        try:
            lat = float(form["Latitude"])
            lng = float(form["Longitude"])
        except ValueError:
            pass

    return MessagePayload(
        sender=sender,
        message_body=body,
        num_media=num_media,
        media_url=media_url,
        media_content_type=media_type,
        latitude=lat,
        longitude=lng,
    )


def _format_dispatch_message(
    services: list,  # list[EmergencyService]
) -> str:
    """Format emergency services into the dispatch message from the triage prompt.

    Args:
        services: List of EmergencyService objects.

    Returns:
        Formatted dispatch text.
    """
    hospital_lines = []
    police_lines = []
    ambulance_lines = []

    for svc in services[:6]:  # Cap at 6 to keep message short
        phone_str = f" — \U0001f4de {svc.phone}" if svc.phone else ""
        dist_str = f" — {svc.distance_km} km" if svc.distance_km else ""

        if svc.service_type == "hospital":
            hospital_lines.append(f"\U0001f3e5 {svc.name}{dist_str}{phone_str}")
        elif svc.service_type == "police":
            police_lines.append(f"\U0001f46e {svc.name}{dist_str}{phone_str}")
        elif svc.service_type == "fire":
            ambulance_lines.append(f"\U0001f692 {svc.name}{dist_str}{phone_str}")

    parts = ["\U0001f198 Nearest emergency services:"]
    parts.extend(hospital_lines[:2])
    parts.extend(ambulance_lines[:1])
    parts.extend(police_lines[:2])
    parts.append("")
    parts.append("\U0001f449 Call them RIGHT NOW.")
    parts.append("I'll stay with you and guide you until help arrives.")

    return "\n".join(parts)


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: Optional[str] = Form(default=None),
    MediaContentType0: Optional[str] = Form(default=None),
    Latitude: Optional[str] = Form(default=None),
    Longitude: Optional[str] = Form(default=None),
) -> Response:
    """Handle incoming Twilio WhatsApp webhook.

    Parses the message, loads session, runs triage, and returns TwiML.
    """
    form = await request.form()
    form_dict = dict(form)
    payload = _parse_twilio_form(form_dict)
    logger.info("Incoming message from %s: %s", payload.sender, payload.message_body[:80])

    # Load or create session
    session = await session_service.load_session(payload.sender)

    # Check for inactivity timeout (2+ minutes) — send follow-up
    # Only fire when user hasn't sent an actual message (empty/repeated idle ping)
    now = datetime.now(timezone.utc)
    last = session.last_activity
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    is_idle_content = not payload.message_body or payload.message_body.lower() in (
        "yes", "no", "ok", "hello", "hi", "hey",
    )
    if (
        is_idle_content
        and now - last > timedelta(minutes=2)
        and session.conversation_history
        and session.triage_state not in (TriageState.RESOLUTION,)
    ):
        followup = "Are you still there? \U0001f6a8"
        await session_service.save_session(session)
        return Response(
            content=build_twiml_reply(followup),
            media_type="application/xml",
        )

    # Handle voice notes: transcribe before triage
    if payload.num_media > 0 and payload.media_url:
        content_type = payload.media_content_type or ""
        if "audio" in content_type:
            try:
                transcript, detected_lang = await stt.transcribe_audio(payload.media_url)
                payload.message_body = transcript
                session.language_code = detected_lang
                session.input_modality = "voice"
                logger.info("Transcribed voice note (%s): %s", detected_lang, transcript[:80])
            except stt.STTError as exc:
                logger.error("STT failed: %s", exc)
                return Response(
                    content=build_twiml_reply(
                        "Sorry, I couldn't understand the voice note. Please type or send a text message."
                    ),
                    media_type="application/xml",
                )
    else:
        # Text message: detect language from text
        session.input_modality = "text"
        detected_lang = detect_language_from_text(payload.message_body)
        session.language_code = detected_lang

    # Run triage
    try:
        result = await triage.process_message(payload, session)
    except triage.TriageError as exc:
        logger.error("Triage failed: %s", exc)
        await session_service.save_session(session)
        return Response(
            content=build_twiml_reply(
                "Something went wrong. Please describe the situation and your location."
            ),
            media_type="application/xml",
        )

    # Update session with new state
    session.triage_state = result.new_state
    await session_service.save_session(session)

    # Build reply text
    reply_text = result.reply_text
    if result.emergency_services:
        dispatch_msg = _format_dispatch_message(result.emergency_services)
        reply_text = f"{reply_text}\n\n{dispatch_msg}"

    # Send voice reply if input was voice or triage requests it
    if session.input_modality == "voice" or result.send_as_voice:
        try:
            audio_base64 = await tts.synthesize_speech(reply_text, session.language_code)
            if audio_base64:
                media_url = await upload_media(audio_base64)
                return Response(
                    content=build_twiml_media_reply(reply_text, media_url),
                    media_type="application/xml",
                )
        except (tts.TTSError, ValueError) as exc:
            logger.warning("TTS or media upload failed, falling back to text: %s", exc)

    return Response(
        content=build_twiml_reply(reply_text),
        media_type="application/xml",
    )
