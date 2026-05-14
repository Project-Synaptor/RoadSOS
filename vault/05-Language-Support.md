# Language Support

RoadSOS supports 8 Indian languages for both input (STT) and output (triage responses + TTS).

## Supported Languages

| Code | Language | STT | TTS | Script Detection | Keyword Detection |
|------|----------|-----|-----|-----------------|-------------------|
| en | English | ✅ | ✅ | N/A | N/A |
| hi | Hindi | ✅ | ✅ | Devanagari (ऀ-ॿ) | "hindi mein", "madad karo" |
| bn | Bengali | ✅ | ✅ | Bengali (ঀ-৿) | "bangla", "shahajjo" |
| or | Odia | ✅ | ⚠️ | Odia (଀-୿) | "odia", "sahayata darkar" |
| ta | Tamil | ✅ | ✅ | Tamil (஀-௿) | "tamil", "udavi venum" |
| te | Telugu | ✅ | ✅ | Telugu (ఀ-౿) | "telugu", "sahayam kavali" |
| kn | Kannada | ✅ | ✅ | Kannada (ಀ-೿) | "kannada", "sahayam beku" |
| ml | Malayalam | ✅ | ✅ | Malayalam (ഀ-ൿ) | "malayalam", "sahayam venam" |

⚠️ = MiMo TTS support unverified. Falls back to text-only reply.

## Detection Methods

### 1. Unicode Script Detection (Primary)
Checks if >30% of characters belong to a specific Indic script. Works for native script input.

### 2. Keyword Fallback (Romanized Text)
Matches common words/phrases in romanized text. Languages are checked in order: Odia → Tamil → Telugu → Kannada → Malayalam → Bengali → Hindi (most specific first to avoid Hindi's generic words catching everything).

### 3. Explicit Language Command
Parses messages like "Hindi mein boliye", "speak in Tamil", "Telugu lo cheppandi".

### 4. MiMo STT Response
If MiMo STT returns a `language` or `detected_language` field, uses that directly.

## How Language Flows Through the System

```
Voice note → STT returns (transcript, language_code)
                ↓
Text message → detect_language_from_text(text)
                ↓
Session stores: language_code, input_modality
                ↓
Triage prompt gets: [LANGUAGE: hi]
                ↓
MiMo responds in Hindi
                ↓
If voice input → TTS generates Hindi audio
                ↓
Twilio sends text + voice reply
```

## TTS Fallback

If MiMo TTS doesn't support a language (currently only Odia is unverified), the system:
1. Returns empty string from `synthesize_speech()`
2. Webhook catches the empty result
3. Falls back to text-only reply
4. No error shown to the user

## Key Files

| File | Function | Purpose |
|------|----------|---------|
| `app/services/language.py` | `detect_language_from_text()` | Main detection function |
| `app/services/language.py` | `detect_language_from_stt_response()` | STT response parsing |
| `app/services/language.py` | `_detect_explicit_command()` | "speak in X" parsing |
| `app/services/stt.py` | `transcribe_audio()` | Returns (text, language_code) |
| `app/services/tts.py` | `synthesize_speech()` | Accepts language_code param |

## Related Notes

- [[04-Triage-Flow]] — How language context is injected into triage
- [[06-Session-And-State]] — language_code field in SessionState
- [[11-Known-Issues]] — Odia TTS TODO
