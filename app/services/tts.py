"""Text-to-speech via MiMo V2.5 TTS.

Converts reply text into audio that can be sent as a WhatsApp voice note.
Returns a base64-encoded OGG opus blob suitable for Twilio's WhatsApp API.
"""

from __future__ import annotations

import base64

import httpx

from app.config import settings


class TTSError(Exception):
    """Raised when text-to-speech processing fails."""


# Languages MiMo TTS supports natively. Others fall back to text-only.
_SUPPORTED_TTS_LANGUAGES = {"en", "hi", "bn", "ta", "te", "kn", "ml"}
# TODO: Confirm which languages MiMo V2.5 TTS actually supports natively.
# Odia ("or") is unverified — falls back to text-only until confirmed.


async def synthesize_speech(text: str, language_code: str = "en") -> str:
    """Convert text to speech using MiMo V2.5 TTS.

    Args:
        text: The text to synthesize. Should be short (under 500 chars).
        language_code: ISO 639-1 language code for the speech output.

    Returns:
        Base64-encoded audio bytes (OGG opus format), or empty string
        if the language is not supported by MiMo TTS.

    Raises:
        TTSError: If the TTS API call fails.
    """
    if language_code not in _SUPPORTED_TTS_LANGUAGES:
        # TODO: MiMo TTS does not natively support language '{language_code}'.
        # Falling back to text-only reply. Add support when MiMo adds this language.
        return ""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.mimo_api_base_url}/audio/speech",
                headers={
                    "Authorization": f"Bearer {settings.mimo_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mimo-v2.5-tts",
                    "input": text,
                    "voice": "alloy",
                    "response_format": "opus",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TTSError(
                f"MiMo TTS API returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise TTSError(f"MiMo TTS request failed: {exc}") from exc

        audio_bytes = response.content
        if not audio_bytes:
            raise TTSError("MiMo TTS returned empty audio")

        return base64.b64encode(audio_bytes).decode("ascii")
