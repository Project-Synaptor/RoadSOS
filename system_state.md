# RoadSoS — System State.md

## 1. WHAT WE ARE BUILDING
RoadSoS is a WhatsApp-based AI emergency response 
agent for road accident victims, built for the 
National Road Safety Hackathon 2026 (CoERS, RBG 
Labs, IIT Madras) under the theme "AI in Road 
Safety."

A victim or bystander sends "HELP" on WhatsApp.
The bot triages the situation, locates nearby 
trauma-capable hospitals using GIS intelligence,
and guides the user with first-aid until help 
arrives. Built on MiMo V2.5 Pro (reasoning),
MiMo V2.5 TTS (voice), MiMo V2 Omni (STT),
Twilio (WhatsApp), FastAPI, Redis, Docker.

Developer: Tushar, 2nd year CSE, ITER SOA University
Dev tool: Claude Code (autonomous mode)
Hackathon: IIT Madras Road Safety Hackathon 2026

---

## 2. EXACT CURRENT STATE

### Infrastructure — WORKING ✅
- Docker running (Redis + FastAPI app on port 8000)
- Twilio WhatsApp sandbox connected
- MiMo API working (base URL fixed to:
  https://token-plan-sgp.xiaomimimo.com/v1)
- End-to-end flow tested and confirmed working
  on WhatsApp (HELP → triage → severity → 
  dispatch in progress)

### Files Built ✅
RoadSOS/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/webhook.py
│   ├── services/
│   │   ├── triage.py
│   │   ├── stt.py
│   │   ├── tts.py
│   │   ├── maps.py
│   │   ├── session.py
│   │   └── language.py ✅ NEW — multilingual detection
│   ├── models/schemas.py
│   └── utils/
│       ├── twilio_client.py
│       └── audio.py
├── prompts/triage_system.txt
├── data/hospitals.json
├── tasks.html
├── tasks2.html (voice + multilingual task tracker)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env

### Environment Variables in .env
TWILIO_ACCOUNT_SID=filled
TWILIO_AUTH_TOKEN=filled
TWILIO_WHATSAPP_NUMBER=filled
MIMO_API_KEY=filled
MIMO_API_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
REDIS_URL=redis://localhost:6379/0

GOOGLE_MAPS_API_KEY and GEOAPIFY_API_KEY 
— being removed entirely.

### MiMo Grant ✅
Tushar received Xiaomi MiMo Orbit 100T Token 
Grant — Max Tier — 1.6 billion credits.
Models available: MiMo-V2.5-Pro, MiMo-V2.5,
MiMo-V2.5-TTS, MiMo-V2.5-TTS-VoiceClone,
MiMo-V2.5-TTS-VoiceDesign, MiMo-V2-Pro,
MiMo-V2-Omni, MiMo-V2-TTS

---

## 3. IMPORTANT CONTEXT & RULES

### Architecture Decisions
- WhatsApp bot via Twilio (not a web app)
- Static hospitals.json instead of Maps API
  (hackathon demo/prototype only)
- Geoapify kept as commented plug-and-play 
  alternative in maps.py with TODO comments
- Redis for session state (stateless webhooks)
- No database needed beyond Redis

### GIS Intelligence Feature (IN PROGRESS)
Core insight from research: survival is determined
by trauma CAPABILITY not proximity. Current 
emergency systems suffer a "Dispatch Gap" — 
ambulances routed to nearest hospital, not nearest
capable trauma centre. Golden Hour = 60 mins.

Upgraded dispatch message format:
"⏱ Golden Hour: ~X mins remaining
🏥 [Name] — Xkm — Trauma Capable ✅
   📞 phone — Call ahead now
🏥 [Name] — Xkm — General Hospital ⚠️
   (Avoid for severe trauma)
🚑 Ambulance: 108
👮 Police: 100
🆘 National Emergency: 112"

### Triage Flow (6 States)
STATE 1: Activation (HELP → ask situation+location)
STATE 2: Severity check (conscious? breathing? bleeding?)
STATE 3: Triage complete trigger (location+severity confirmed)
STATE 4: Dispatch (send hospitals + emergency numbers)
STATE 5: First aid loop (one instruction at a time)
STATE 6: Resolution (help arrived confirmation)

### Development Rules (from CLAUDE.md)
1. No vibe coding
2. One component at a time
3. Docstrings on every public function
4. Type hints everywhere
5. Test before moving on
6. No hardcoded values — all via config.py
7. Fail explicitly
8. Prompts versioned in prompts/ folder

### Team
- Tushar: all core development
- Teammate: documentation, PPT, small tasks only

### Token Usage Rule ⚠️
Claude (this chat) must keep responses concise.
Ask before doing anything token-heavy.

---

## 4. COMPLETED: GIS + Maps Upgrade ✅

- data/hospitals.json created (Bhubaneswar + Chennai)
- maps.py rewritten with haversine distance, JSON-based lookup
- Trauma classification (Level 1/2/3) from data fields
- Golden Hour countdown in dispatch messages
- All Maps API keys removed
- 42 tasks completed, 38 tests passing

---

## 5. COMPLETED: Voice & Multilingual Integration ✅

### What was added
- `app/services/language.py` — Language detection service
  - Unicode script detection for 8 scripts (Devanagari, Bengali, Odia, Tamil, Telugu, Kannada, Malayalam)
  - Keyword fallback for romanized text
  - Explicit language command parsing ("Hindi mein boliye")
  - MiMo STT response language extraction
- STT (`stt.py`) updated to return `(transcript, language_code)` tuple
- TTS (`tts.py`) updated with `language_code` parameter and fallback for unsupported languages
- Session state now includes `language_code` and `input_modality` fields
- Triage prompt updated with `[LANGUAGE INSTRUCTION]` block
- Triage engine injects `[LANGUAGE: {code}]` context into MiMo messages
- Webhook handles voice → STT → language detect → triage → TTS → voice reply flow
- `twilio_client.py` updated with `upload_media()` for TTS audio serving
- `tasks2.html` — full task tracker for this integration

### Supported Languages
| Code | Language | STT | TTS | Script Detection |
|------|----------|-----|-----|-----------------|
| en | English | ✅ | ✅ | N/A |
| hi | Hindi | ✅ | ✅ | Devanagari |
| bn | Bengali | ✅ | ✅ | Bengali |
| or | Odia | ✅ | ⚠️ TODO | Odia |
| ta | Tamil | ✅ | ✅ | Tamil |
| te | Telugu | ✅ | ✅ | Telugu |
| kn | Kannada | ✅ | ✅ | Kannada |
| ml | Malayalam | ✅ | ✅ | Malayalam |

⚠️ Odia TTS: MiMo TTS support unverified. Falls back to text-only until confirmed.

### Tests Added
- `tests/test_language.py` — 34 tests (script detection, keyword fallback, explicit commands, STT response)
- `tests/test_voice.py` — 11 tests (STT tuple return, TTS language param, session schema, webhook flow)
- Full suite: 83 tests passing

---

## 6. IMMEDIATE NEXT STEP

Voice + multilingual integration is complete. 
Next priorities:
1. End-to-end WhatsApp test with voice notes in multiple languages
2. Confirm MiMo TTS support for Odia (or document text-only fallback)
3. Production deployment considerations (public webhook URL)
4. Teammate: documentation, PPT, demo prep
