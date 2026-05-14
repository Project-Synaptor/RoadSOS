"""Speech-to-text via MiMo V2 Omni.

Downloads audio from the Twilio media URL, converts if needed,
and sends it to MiMo for transcription.
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.services.language import detect_language_from_stt_response


class STTError(Exception):
    """Raised when speech-to-text processing fails."""


async def transcribe_audio(audio_url: str) -> tuple[str, str]:
    """Download audio from a URL and transcribe it via MiMo V2 Omni.

    Args:
        audio_url: Publicly accessible URL to the audio file (from Twilio webhook).

    Returns:
        Tuple of (transcribed_text, detected_language_code).

    Raises:
        STTError: If download or transcription fails.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Download the audio file
        try:
            audio_response = await client.get(audio_url)
            audio_response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise STTError(
                f"Failed to download audio from {audio_url}: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise STTError(f"Failed to download audio from {audio_url}: {exc}") from exc

        audio_bytes = audio_response.content
        content_type = audio_response.headers.get("content-type", "audio/ogg")

        # Determine file extension from content type
        ext_map = {
            "audio/ogg": "ogg",
            "audio/ogg; codecs=opus": "ogg",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/mp4": "m4a",
        }
        ext = ext_map.get(content_type, "ogg")
        filename = f"audio.{ext}"

        # Send to MiMo V2 Omni STT
        try:
            stt_response = await client.post(
                f"{settings.mimo_api_base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.mimo_api_key}"},
                files={"file": (filename, audio_bytes, content_type)},
                data={"model": "mimo-v2-omni"},
                timeout=60.0,
            )
            stt_response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise STTError(
                f"MiMo STT API returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise STTError(f"MiMo STT request failed: {exc}") from exc

        result = stt_response.json()
        transcript = result.get("text", "")
        if not transcript:
            raise STTError("MiMo STT returned empty transcript")

        language_code = detect_language_from_stt_response(result)

        return transcript, language_code
