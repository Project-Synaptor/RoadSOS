"""Twilio WhatsApp send helpers.

Provides functions to send text messages and voice notes via the
Twilio WhatsApp Business API, and to build TwiML webhook responses.
"""

from __future__ import annotations

import base64
import logging

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from app.config import settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def _get_client() -> Client:
    """Return a shared Twilio REST client."""
    global _client
    if _client is None:
        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


def build_twiml_reply(text: str) -> str:
    """Build a TwiML XML string that replies with a text message.

    Used as the webhook response body so Twilio sends the message
    back to the user on WhatsApp.

    Args:
        text: The message text to send.

    Returns:
        TwiML XML string.
    """
    resp = MessagingResponse()
    resp.message(text)
    return str(resp)


def build_twiml_media_reply(text: str, media_url: str) -> str:
    """Build a TwiML XML string that replies with text + a media attachment.

    Args:
        text: Caption text.
        media_url: Public URL of the media to attach (e.g. audio file).

    Returns:
        TwiML XML string.
    """
    resp = MessagingResponse()
    msg = resp.message(text)
    msg.media(media_url)
    return str(resp)


async def send_whatsapp_message(to: str, body: str) -> str:
    """Send a WhatsApp text message via the Twilio REST API.

    Use this for proactive messages (e.g. inactivity follow-ups)
    where there is no webhook to respond to.

    Args:
        to: Recipient identifier (e.g. 'whatsapp:+1234567890').
        body: Message text.

    Returns:
        The Twilio message SID.
    """
    client = _get_client()
    message = client.messages.create(
        from_=f"whatsapp:{settings.twilio_whatsapp_number}",
        to=to,
        body=body,
    )
    return message.sid


async def upload_media(audio_base64: str, content_type: str = "audio/ogg") -> str:
    """Upload audio to Twilio and return a Twilio-hosted media URL.

    This is the free approach: Twilio hosts the media, no ngrok needed
    for serving audio back to the user.

    Args:
        audio_base64: Base64-encoded audio bytes.
        content_type: MIME type of the audio (default: audio/ogg).

    Returns:
        Publicly accessible Twilio media URL.

    Raises:
        ValueError: If upload fails.
    """
    client = _get_client()
    audio_bytes = base64.b64decode(audio_base64)

    # Create a temporary message to upload media to, then get the media URL
    # Twilio's Media resource requires a message SID. We create a minimal
    # message to attach the media to.
    try:
        # Upload media to the default messaging service
        media = client.messages.create(
            from_=f"whatsapp:{settings.twilio_whatsapp_number}",
            to=f"whatsapp:{settings.twilio_whatsapp_number}",  # Self-send (Twilio requires a To)
            body="",
            media_url=[],
        )
        # Upload the actual media bytes
        media_resource = client.messages(media.sid).media.create(
            content_type=content_type,
            filename="voice_reply.ogg",
        )
        # The media URL pattern for Twilio-hosted content
        media_url = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Messages/{media.sid}/Media/{media_resource.sid}.ogg"
        )
        logger.info("Uploaded TTS audio to Twilio: %s", media_url)
        return media_url
    except Exception as exc:
        logger.error("Failed to upload media to Twilio: %s", exc)
        # TODO: For production, consider serving audio from a /media/{id} endpoint
        # if Twilio direct upload proves unreliable. This would need a publicly
        # accessible URL (ngrok or hosted deployment).
        raise ValueError(f"Media upload failed: {exc}") from exc


async def send_whatsapp_voice_note(to: str, audio_url: str) -> str:
    """Send a WhatsApp voice note via the Twilio REST API.

    Args:
        to: Recipient identifier (e.g. 'whatsapp:+1234567890').
        audio_url: Public URL of the audio file.

    Returns:
        The Twilio message SID.
    """
    client = _get_client()
    message = client.messages.create(
        from_=f"whatsapp:{settings.twilio_whatsapp_number}",
        to=to,
        media_url=[audio_url],
    )
    return message.sid
