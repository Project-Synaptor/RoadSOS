# Development Log

## Phase 1: Initial Build

**What:** Core infrastructure — FastAPI backend, Twilio WhatsApp webhook, MiMo triage, Redis sessions.

**Built:**
- `app/main.py` — FastAPI app with CORS and lifespan
- `app/config.py` — Settings via pydantic-settings
- `app/routes/webhook.py` — Twilio webhook endpoint
- `app/services/triage.py` — MiMo V2.5 Pro triage engine
- `app/services/stt.py` — MiMo V2 Omni speech-to-text
- `app/services/tts.py` — MiMo V2.5 text-to-speech
- `app/services/session.py` — Redis session storage
- `app/models/schemas.py` — Pydantic models
- `app/utils/twilio_client.py` — Twilio send helpers
- `app/utils/audio.py` — ffmpeg audio conversion
- `prompts/triage_system.txt` — Triage system prompt
- Docker setup (Dockerfile + docker-compose.yml)

**Result:** Working end-to-end flow on WhatsApp. HELP → triage → severity → dispatch.

---

## Phase 2: GIS/Maps Upgrade

**What:** Replaced external Maps API with local JSON data + haversine distance calculation.

**Problem:** Google Maps API and Geoapify cost money and add latency. For a hackathon demo, static data is sufficient.

**Built:**
- `data/hospitals.json` — 8 hospitals + 3 police + ambulance per city (Bhubaneswar, Chennai)
- `app/services/maps.py` — Rewritten with haversine, JSON lookup, trauma classification
- `classify_trauma_level()` — Level 1/2/3 from data fields (trauma_capable, has_icu, has_blood_bank)
- `format_golden_hour()` — 60-minute countdown from triage start
- `format_dispatch_message()` — Rich WhatsApp message with trauma labels, 24x7 badges
- Updated `triage.py` dispatch flow
- Removed all Maps API keys from config

**Tasks:** 42 tasks completed.
**Tests:** 38 passing (test_maps.py, test_triage.py).

**Key insight:** Survival is determined by trauma CAPABILITY, not proximity. A Level 1 trauma centre 5km away beats a general hospital 1km away.

---

## Phase 3: Voice & Multilingual Integration

**What:** Added voice input/output support and 8-language triage.

**Built:**
- `app/services/language.py` — New language detection service
  - Unicode script detection for 7 Indic scripts
  - Keyword fallback for romanized text
  - Explicit language command parsing
  - MiMo STT response language extraction
- Updated `stt.py` — Returns `(transcript, language_code)` tuple
- Updated `tts.py` — Accepts `language_code` param, fallback for unsupported languages
- Updated `webhook.py` — Voice → STT → language detect → triage → TTS → voice reply
- Updated `triage.py` — Injects `[LANGUAGE: {code}]` context
- Updated `schemas.py` — Added `language_code`, `input_modality` to SessionState
- Updated `config.py` — Added `supported_languages` setting
- Updated `twilio_client.py` — Added `upload_media()` for TTS audio serving
- Updated `triage_system.txt` — Added LANGUAGE INSTRUCTION block

**Languages:** English, Hindi, Bengali, Odia, Tamil, Telugu, Kannada, Malayalam

**Tasks:** 34 tasks completed.
**Tests:** 83 total passing (34 language + 11 voice + 16 triage + 22 maps).

---

## Test Summary

| Test File | Tests | What's Tested |
|-----------|-------|---------------|
| `test_language.py` | 34 | Script detection, keyword fallback, explicit commands, STT response |
| `test_voice.py` | 11 | STT tuple return, TTS language param, session schema, webhook flow |
| `test_triage.py` | 16 | Golden Hour countdown, dispatch message formatting |
| `test_maps.py` | 22 | Hospital data loading, haversine distance, trauma classification |
| **Total** | **83** | **All passing** |

---

## Related Notes

- [[10-Key-Decisions]] — Why we made these architectural choices
- [[11-Known-Issues]] — What's still TODO
- [[01-Project-Overview]] — What RoadSOS is
