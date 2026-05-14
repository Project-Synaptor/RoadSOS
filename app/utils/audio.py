"""Audio format conversion helpers.

WhatsApp voice notes use OGG opus format. This module provides
conversion utilities when the source audio is in a different format.
"""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path


class AudioConversionError(Exception):
    """Raised when audio conversion fails."""


def convert_to_ogg_opus(audio_bytes: bytes, source_format: str = "mp3") -> bytes:
    """Convert audio bytes to OGG opus format using ffmpeg.

    Args:
        audio_bytes: Raw audio data.
        source_format: Format of the input audio (mp3, wav, m4a, etc.).

    Returns:
        OGG opus encoded audio bytes.

    Raises:
        AudioConversionError: If conversion fails.
    """
    with tempfile.NamedTemporaryFile(
        suffix=f".{source_format}", delete=False
    ) as infile:
        infile.write(audio_bytes)
        in_path = infile.name

    out_path = in_path.rsplit(".", 1)[0] + ".ogg"

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                in_path,
                "-c:a",
                "libopus",
                "-b:a",
                "32k",
                "-ar",
                "16000",
                "-ac",
                "1",
                out_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise AudioConversionError(
                f"ffmpeg failed: {result.stderr.decode('utf-8', errors='replace')}"
            )

        output = Path(out_path).read_bytes()
        if not output:
            raise AudioConversionError("ffmpeg produced empty output")

        return output
    except FileNotFoundError as exc:
        raise AudioConversionError(
            "ffmpeg not found. Install ffmpeg to enable audio conversion."
        ) from exc
    finally:
        Path(in_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)


def get_audio_duration_seconds(audio_bytes: bytes, source_format: str = "ogg") -> float:
    """Get the duration of an audio file in seconds using ffprobe.

    Args:
        audio_bytes: Raw audio data.
        source_format: Format of the audio.

    Returns:
        Duration in seconds.

    Raises:
        AudioConversionError: If probing fails.
    """
    with tempfile.NamedTemporaryFile(
        suffix=f".{source_format}", delete=False
    ) as infile:
        infile.write(audio_bytes)
        in_path = infile.name

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                in_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            raise AudioConversionError(
                f"ffprobe failed: {result.stderr}"
            )

        duration = float(result.stdout.strip())
        return duration
    except (ValueError, FileNotFoundError) as exc:
        raise AudioConversionError(f"Failed to get audio duration: {exc}") from exc
    finally:
        Path(in_path).unlink(missing_ok=True)
