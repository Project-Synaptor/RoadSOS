# File Map

Every file in the RoadSOS project and what it does.

## Root Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude Code project instructions (auto-loaded) |
| `system_state.md` | Living project status document |
| `docker-compose.yml` | Redis + app service definitions |
| `Dockerfile` | Python 3.12 + ffmpeg + uvicorn |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |
| `.env` | Actual secrets (git-ignored) |
| `tasks.html` | GIS/Maps upgrade task tracker |
| `tasks2.html` | Voice + multilingual task tracker |
| `summary.html` | Project summary page |

## `app/` — Application Code

### `app/main.py`
FastAPI app factory. CORS, lifespan (Redis connect/disconnect), health check endpoint.

### `app/config.py`
Settings via pydantic-settings. Loads from `.env`. Singleton `settings` object.
- Key settings: `mimo_api_base_url`, `redis_url`, `session_ttl`, `supported_languages`

### `app/routes/webhook.py`
Twilio WhatsApp webhook endpoint (`POST /webhook`).
- `_parse_twilio_form()` — Extract MessagePayload from Twilio form
- `whatsapp_webhook()` — Main handler: parse → STT → language → triage → TTS → TwiML
- `_format_dispatch_message()` — Format emergency services for WhatsApp

### `app/services/triage.py`
Core triage engine. 6-state conversation state machine.
- `process_message()` — Main entry point
- `_build_messages()` — Construct MiMo prompt with state + language context
- `_call_mimo()` — Chat completion to MiMo V2.5 Pro
- `format_dispatch_message()` — Golden Hour + hospital details
- `format_golden_hour()` — Countdown calculation

### `app/services/stt.py`
Speech-to-text via MiMo V2 Omni.
- `transcribe_audio(audio_url)` → `(transcript, language_code)`
- Downloads audio from Twilio URL, sends to MiMo API

### `app/services/tts.py`
Text-to-speech via MiMo V2.5 TTS.
- `synthesize_speech(text, language_code)` → base64 audio or empty string
- Returns empty for unsupported languages (fallback to text-only)

### `app/services/language.py`
Language detection service.
- `detect_language_from_text()` — Unicode script + keyword detection
- `detect_language_from_stt_response()` — Extract from MiMo response
- `_detect_explicit_command()` — "speak in X" parsing
- `LANGUAGE_CODES` — Dict of 8 supported languages

### `app/services/maps.py`
Local JSON-based emergency service lookup.
- `find_nearest_services(lat, lng)` — Hospitals + police sorted by distance
- `find_nearest_ambulance(lat, lng)` — Ambulance contacts for city
- `geocode_location(text)` — Text to coordinates (Nominatim + JSON fallback)
- `_haversine_km()` — Distance calculation
- `classify_trauma_level()` — Level 1/2/3 from data fields
- `get_city_from_coords()` — Bounding box city detection

### `app/services/session.py`
Redis session storage.
- `load_session(user_id)` — Load or create SessionState
- `save_session(session)` — Persist with TTL
- `get_redis()` / `close_redis()` — Connection management

### `app/models/schemas.py`
Pydantic v2 models: SessionState, MessagePayload, TriageResult, EmergencyService, TriageState.

### `app/utils/twilio_client.py`
Twilio helpers.
- `build_twiml_reply()` — Text-only TwiML
- `build_twiml_media_reply()` — Text + media TwiML
- `upload_media()` — Upload audio to Twilio, get hosted URL
- `send_whatsapp_message()` — Proactive text message
- `send_whatsapp_voice_note()` — Proactive voice note

### `app/utils/audio.py`
Audio format conversion via ffmpeg.
- `convert_to_ogg_opus()` — Convert to WhatsApp-compatible format
- `get_audio_duration_seconds()` — Get audio length

## `prompts/`

| File | Purpose |
|------|---------|
| `triage_system.txt` | System prompt for MiMo triage agent (6 states, rules, language instruction) |

## `data/`

| File | Purpose |
|------|---------|
| `hospitals.json` | Static hospital/police/ambulance data for Bhubaneswar + Chennai |

## `tests/`

| File | Tests | Count |
|------|-------|-------|
| `test_language.py` | Language detection (script, keyword, command, STT) | 34 |
| `test_voice.py` | STT tuple return, TTS language, session schema | 11 |
| `test_triage.py` | Golden Hour, dispatch message formatting | 16 |
| `test_maps.py` | Hospital data, haversine, trauma classification | 22 |

**Total: 83 tests passing.**

## Related Notes

- [[02-Architecture]] — How these files connect
- [[08-Environment-Setup]] — How to run the project
