# **FIRST:** Read `vault/00-Home.md` to understand the full project context before doing anything. Follow its links for deeper context.

# RoadSOS

WhatsApp-based AI emergency response agent for road accident victims.
Built for the National Road Safety Hackathon 2026, IIT Madras.

## Architecture

```
Victim (WhatsApp) --> Twilio Webhook --> FastAPI Backend --> MiMo V2.5 Pro (triage)
                                           |                     |
                                           |               MiMo V2 Omni (STT)
                                           |               MiMo V2.5 TTS (voice reply)
                                           |
                                           +--> Google Maps API (nearest hospitals/police)
                                           +--> Redis (session state)
```

**Request flow:**
1. Victim sends text/voice/location via WhatsApp
2. Twilio forwards to FastAPI webhook
3. Session state loaded from Redis
4. MiMo V2.5 Pro triages: asks follow-up questions, assesses severity
5. Voice notes transcribed via MiMo V2 Omni STT
6. Replies sent as text or synthesized voice via MiMo V2.5 TTS
7. Once triage is complete, Google Maps API locates nearest emergency services
8. Victim receives service details; optionally notifies emergency contacts

## Folder Structure

```
RoadSOS/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Settings via pydantic-settings
│   ├── routes/
│   │   └── webhook.py       # Twilio WhatsApp webhook endpoint
│   ├── services/
│   │   ├── triage.py        # MiMo V2.5 Pro triage logic & prompts
│   │   ├── stt.py           # MiMo V2 Omni speech-to-text
│   │   ├── tts.py           # MiMo V2.5 text-to-speech
│   │   ├── maps.py          # Local JSON-based nearest service lookup
│   │   ├── session.py       # Redis session read/write
│   │   └── language.py      # Multilingual language detection
│   ├── models/
│   │   └── schemas.py       # Pydantic models for messages, sessions
│   └── utils/
│       ├── twilio_client.py # Twilio WhatsApp send helpers + media upload
│       └── audio.py         # Audio format conversion helpers
├── prompts/
│   └── triage_system.txt    # System prompt for MiMo triage agent
├── tests/
│   ├── test_language.py     # Language detection tests (34 tests)
│   ├── test_voice.py        # STT/TTS pipeline tests (11 tests)
│   ├── test_triage.py       # Triage dispatch tests
│   └── test_maps.py         # Maps/haversine tests
├── docker-compose.yml       # Redis + app services
├── Dockerfile
├── requirements.txt
├── .env.example             # Template for required env vars
└── CLAUDE.md
```

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `main.py` | App factory, CORS, lifespan (Redis connect/disconnect), health check |
| `webhook.py` | Parse Twilio webhook payload, dispatch to triage service, handle voice+language, return TwiML |
| `triage.py` | Core logic: maintain conversation state, call MiMo for next action, decide when triage is complete |
| `stt.py` | Accept audio URL from Twilio, download, send to MiMo V2 Omni, return (transcript, language_code) |
| `tts.py` | Accept text + language_code, call MiMo V2.5 TTS, return base64 audio or empty string for unsupported |
| `language.py` | Detect language from text (Unicode scripts + keywords), STT responses, and explicit commands |
| `maps.py` | Given coordinates, lookup nearest hospitals/police/ambulance from local JSON data |
| `session.py` | Store/retrieve per-user session (conversation history, triage state, location, language) in Redis |
| `schemas.py` | MessagePayload, SessionState, TriageResult, EmergencyService Pydantic models |

## Environment Variables

```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
MIMO_API_KEY=
MIMO_API_BASE_URL=https://api.mimo.ai/v1
REDIS_URL=redis://localhost:6379/0
SUPPORTED_LANGUAGES=["en","hi","bn","or","ta","te","kn","ml"]
```

## Supported Languages

| Code | Language | STT | TTS | Script Detection |
|------|----------|-----|-----|-----------------|
| en | English | ✅ | ✅ | N/A |
| hi | Hindi | ✅ | ✅ | Devanagari |
| bn | Bengali | ✅ | ✅ | Bengali |
| or | Odia | ✅ | ⚠️ | Odia |
| ta | Tamil | ✅ | ✅ | Tamil |
| te | Telugu | ✅ | ✅ | Telugu |
| kn | Kannada | ✅ | ✅ | Kannada |
| ml | Malayalam | ✅ | ✅ | Malayalam |

⚠️ = MiMo TTS support unverified, falls back to text-only

## Development Rules

1. **No vibe coding.** Every function has a clear purpose tied to a specific requirement. If you can't explain why it exists, don't write it.
2. **One component at a time.** Build and test a single service end-to-end before touching the next. No parallel half-finished work.
3. **Always write docstrings.** Every public function and class gets a docstring explaining purpose, arguments, and return value.
4. **Type hints everywhere.** All function signatures must have full type annotations.
5. **Test before moving on.** Each component gets at least one test that exercises the happy path.
6. **No hardcoded values.** All config goes through `app/config.py` via pydantic-settings. No magic strings or numbers in business logic.
7. **Fail explicitly.** Raise specific exceptions with descriptive messages. No silent `except: pass`.
8. **Keep prompts versioned.** The triage system prompt lives in `prompts/triage_system.txt`, not inline in Python code.

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend framework | FastAPI |
| WhatsApp channel | Twilio WhatsApp Business API |
| Triage reasoning | MiMo V2.5 Pro |
| Speech-to-text | MiMo V2 Omni |
| Text-to-speech | MiMo V2.5 TTS |
| Location services | Google Maps Platform (Places, Geocoding) |
| Session store | Redis |
| Data validation | Pydantic v2 |
