# Tech Stack

## Core Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Backend framework | FastAPI | Async Python web framework |
| WhatsApp channel | Twilio WhatsApp Business API | Message sending/receiving |
| Triage reasoning | MiMo V2.5 Pro | Conversational AI for emergency triage |
| Speech-to-text | MiMo V2 Omni | Transcribe voice notes |
| Text-to-speech | MiMo V2.5 TTS | Generate voice replies |
| Location services | Local JSON + haversine | Nearest hospital lookup |
| Session store | Redis | Per-user conversation state |
| Data validation | Pydantic v2 | Schema validation |
| Containerization | Docker + docker-compose | Deployment |

## MiMo Models

| Model | Role | Endpoint |
|-------|------|----------|
| mimo-v2.5-pro | Triage reasoning (chat completions) | `/chat/completions` |
| mimo-v2-omni | Speech-to-text | `/audio/transcriptions` |
| mimo-v2.5-tts | Text-to-speech | `/audio/speech` |

**API Base URL:** `https://token-plan-sgp.xiaomimimo.com/v1`
**Grant:** MiMo Orbit 100T Token Grant — Max Tier — 1.6 billion credits

## Twilio Integration

- **Webhook:** `POST /webhook` receives WhatsApp messages
- **Message parsing:** Form data with From, Body, NumMedia, MediaUrl0, MediaContentType0, Latitude, Longitude
- **Reply format:** TwiML XML (text + optional media URL)
- **Media upload:** `POST .../Messages/{sid}/Media` for TTS audio serving

## Redis Usage

- **Key pattern:** `roadsos:session:{user_id}`
- **Format:** JSON string (Pydantic model serialized)
- **TTL:** 3600 seconds (1 hour, configurable)
- **Library:** `redis[hiredis]` with async support

## Dependencies

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
redis[hiredis]>=5.0.0
httpx>=0.27.0
twilio>=9.0.0
python-multipart>=0.0.9
```

## Related Notes

- [[08-Environment-Setup]] — How to configure and run
- [[02-Architecture]] — How these components connect
- [[10-Key-Decisions]] — Why we chose this stack
