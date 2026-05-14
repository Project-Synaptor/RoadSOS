"""Language detection for multilingual triage.

Detects the user's preferred language from:
1. Unicode script analysis (Devanagari, Bengali, Tamil, etc.)
2. Keyword/phrase fallback for romanized text
3. Explicit language commands ("Hindi mein boliye")
4. MiMo STT response metadata
"""

from __future__ import annotations

import re
from typing import Optional

from app.config import settings


# ISO 639-1 language codes and their display names
LANGUAGE_CODES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "or": "Odia",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}

# Unicode script ranges for Indic languages
_SCRIPT_PATTERNS: list[tuple[str, str]] = [
    ("hi", r"[ऀ-ॿ]"),   # Devanagari (Hindi)
    ("bn", r"[ঀ-৿]"),   # Bengali
    ("or", r"[଀-୿]"),   # Odia
    ("ta", r"[஀-௿]"),   # Tamil
    ("te", r"[ఀ-౿]"),   # Telugu
    ("kn", r"[ಀ-೿]"),   # Kannada
    ("ml", r"[ഀ-ൿ]"),   # Malayalam
]

# Keyword patterns for romanized text detection
# Order matters: more specific languages first to avoid Hindi's generic words
# catching everything. Each language must have unique markers.
_KEYWORD_PATTERNS: list[tuple[str, list[str]]] = [
    ("or", ["odia", "oriya", "sahayata darkar", "mu tume", "kana darkar"]),
    ("ta", ["tamil", "udavi venum", "enakku", "neenga", "enna aachu"]),
    ("te", ["telugu", "sahayam kavali", "naku", "meeru", "emi aindi"]),
    ("kn", ["kannada", "sahayam beku", "nanu", "neenu", "yenu aaytu"]),
    ("ml", ["malayalam", "sahayam venam", "enikku", "ningal", "enth sambhavichu"]),
    ("bn", ["bangla", "bengali", "shahajjo koro", "ami", "tumi ki"]),
    ("hi", ["hindi mein", "hindi me", "madad karo", "mujhe madad", "bahut tej dard"]),
]

# Explicit language command patterns
_COMMAND_PATTERNS: list[tuple[str, list[str]]] = [
    ("hi", [r"hindi\s+mein\s+boliye", r"hindi\s+mein\s+bolo", r"speak\s+in\s+hindi", r"hindi\s+mein\s+reply", r"hindi\s+mein\s+jawab"]),
    ("bn", [r"bangla\s+te\s+bolen", r"speak\s+in\s+bengali", r"speak\s+in\s+bangla", r"bengali\s+mein\s+reply"]),
    ("or", [r"odia\s+re\s+kahantu", r"speak\s+in\s+odia", r"speak\s+in\s+oriya", r"odia\s+mein\s+reply"]),
    ("ta", [r"tamil\s+la\s+sollunga", r"speak\s+in\s+tamil", r"tamil\s+mein\s+reply"]),
    ("te", [r"telugu\s+lo\s+cheppandi", r"speak\s+in\s+telugu", r"telugu\s+mein\s+reply"]),
    ("kn", [r"kannada\s+daalli\s+heliri", r"speak\s+in\s+kannada", r"kannada\s+mein\s+reply"]),
    ("ml", [r"malayalam\s+il\s+parayoo", r"speak\s+in\s+malayalam", r"malayalam\s+mein\s+reply"]),
]


def detect_language_from_text(text: str) -> str:
    """Detect language from text using script analysis and keyword fallback.

    Tries Unicode script detection first (works for native scripts),
    then falls back to keyword matching for romanized text.

    Args:
        text: The text to analyze.

    Returns:
        ISO 639-1 language code (e.g. "hi", "bn", "ta"). Defaults to "en".
    """
    if not text or not text.strip():
        return "en"

    # Check explicit language commands first
    cmd_lang = _detect_explicit_command(text)
    if cmd_lang:
        return cmd_lang

    # Try Unicode script detection
    text_len = len(text.strip())
    for lang_code, pattern in _SCRIPT_PATTERNS:
        matches = len(re.findall(pattern, text))
        if matches > 0 and (matches / text_len) > 0.3:
            return lang_code

    # Fallback: keyword detection for romanized text
    text_lower = text.lower()
    for lang_code, keywords in _KEYWORD_PATTERNS:
        for keyword in keywords:
            if keyword in text_lower:
                return lang_code

    return "en"


def detect_language_from_stt_response(stt_response: dict) -> str:
    """Extract detected language from MiMo STT API response.

    Args:
        stt_response: The JSON response dict from MiMo STT.

    Returns:
        ISO 639-1 language code. Falls back to text-based detection.
    """
    # MiMo STT may return language in the response
    detected = stt_response.get("language", "")
    if detected and detected in LANGUAGE_CODES:
        return detected

    # Some STT APIs return language in a nested field
    detected = stt_response.get("detected_language", "")
    if detected and detected in LANGUAGE_CODES:
        return detected

    # Fall back to text-based detection on the transcript
    transcript = stt_response.get("text", "")
    return detect_language_from_text(transcript)


def _detect_explicit_command(text: str) -> Optional[str]:
    """Check if the user explicitly requested a language switch.

    Args:
        text: The user's message.

    Returns:
        ISO 639-1 code if an explicit command is found, else None.
    """
    text_lower = text.lower().strip()
    for lang_code, patterns in _COMMAND_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return lang_code
    return None


def get_language_name(code: str) -> str:
    """Get the display name for a language code.

    Args:
        code: ISO 639-1 language code.

    Returns:
        Language name (e.g. "Hindi"). Returns "English" for unknown codes.
    """
    return LANGUAGE_CODES.get(code, "English")


def is_supported(code: str) -> bool:
    """Check if a language code is in the supported list.

    Args:
        code: ISO 639-1 language code.

    Returns:
        True if the language is supported.
    """
    return code in settings.supported_languages
