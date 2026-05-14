# Architecture

## System Diagram

```
Victim (WhatsApp) --> Twilio Webhook --> FastAPI Backend --> MiMo V2.5 Pro (triage)
                                           |                     |
                                           |               MiMo V2 Omni (STT)
                                           |               MiMo V2.5 TTS (voice reply)
                                           |
                                           +--> Local JSON (nearest hospitals/police)
                                           +--> Redis (session state)
```

## Request Flow

1. Victim sends text/voice/location via WhatsApp
2. Twilio forwards to FastAPI webhook (`/webhook`)
3. Session state loaded from Redis (`roadsos:session:{user_id}`)
4. If voice note: MiMo V2 Omni transcribes audio → (transcript, language_code)
5. Language detected from text/transcript and stored in session
6. MiMo V2.5 Pro triages: asks follow-up questions, assesses severity
7. Once triage is complete, local JSON data finds nearest emergency services
8. Reply sent as text (and voice via TTS if input was voice)

## Component Interaction

```
webhook.py
    |
    +--> stt.py (if audio) --> language.py (detect language)
    |
    +--> triage.py
    |       |
    |       +--> _build_messages() (injects [LANGUAGE: xx] context)
    |       +--> _call_mimo() (MiMo V2.5 Pro chat completion)
    |       +--> maps.py (when triage complete)
    |               |
    |               +--> hospitals.json (local data)
    |               +--> haversine distance calculation
    |
    +--> tts.py (if voice input) --> twilio_client.py (upload media)
    |
    +--> session.py (save updated state to Redis)
```

## Data Flow

| Step | Component | Input | Output |
|------|-----------|-------|--------|
| 1 | webhook.py | Twilio POST form | MessagePayload |
| 2 | session.py | sender ID | SessionState |
| 3 | stt.py | audio URL | (transcript, language) |
| 4 | language.py | text/STT response | language_code |
| 5 | triage.py | payload + session | TriageResult |
| 6 | maps.py | lat/lng | list[EmergencyService] |
| 7 | tts.py | text + language | base64 audio |
| 8 | twilio_client.py | base64 audio | media URL |
| 9 | webhook.py | TriageResult | TwiML XML |

## Key Files

- [[07-File-Map]] — Complete file-by-file breakdown
- [[06-Session-And-State]] — Pydantic models and Redis session structure
- [[04-Triage-Flow]] — The 6-state triage state machine
