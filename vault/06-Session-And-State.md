# Session & State

## SessionState (Pydantic Model)

Per-user session stored in Redis as JSON.

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `user_id` | str | required | Twilio sender ID (e.g. `whatsapp:+1234567890`) |
| `triage_state` | TriageState | ACTIVATION | Current triage state |
| `conversation_history` | list[dict] | [] | Chat history (role + content) |
| `location_text` | str? | None | Text description of location |
| `location_lat` | float? | None | Latitude from WhatsApp pin |
| `location_lng` | float? | None | Longitude from WhatsApp pin |
| `severity_description` | str? | None | User's description of injuries |
| `victim_conscious` | bool? | None | Is victim conscious? |
| `victim_can_move` | bool? | None | Can victim move? |
| `first_aid_step` | int | 0 | Current first-aid instruction index |
| `last_activity` | datetime | utcnow() | For inactivity timeout (2 min) |
| `triage_started_at` | datetime? | None | For Golden Hour countdown |
| `language_code` | str | "en" | Preferred language (ISO 639-1) |
| `input_modality` | str | "text" | "text" or "voice" |

## TriageState (Enum)

```python
ACTIVATION = "activation"
SEVERITY_CHECK = "severity_check"
TRIAGE_COMPLETE = "triage_complete"
DISPATCH = "dispatch"
FIRST_AID = "first_aid"
RESOLUTION = "resolution"
```

See [[04-Triage-Flow]] for state transition rules.

## MessagePayload (Pydantic Model)

Parsed from Twilio webhook form data.

| Field | Type | Purpose |
|-------|------|---------|
| `sender` | str | Twilio sender ID |
| `message_body` | str | Text content (or STT transcript) |
| `num_media` | int | Number of media attachments |
| `media_url` | str? | URL of first media |
| `media_content_type` | str? | MIME type (e.g. audio/ogg) |
| `latitude` | float? | From WhatsApp location pin |
| `longitude` | float? | From WhatsApp location pin |

## TriageResult (Pydantic Model)

Returned by `triage.process_message()`.

| Field | Type | Purpose |
|-------|------|---------|
| `reply_text` | str | Text to send to user |
| `new_state` | TriageState | Updated triage state |
| `is_triage_complete` | bool | Location + severity confirmed? |
| `emergency_services` | list[EmergencyService] | Nearby hospitals/police |
| `send_as_voice` | bool | Whether to send as voice note |

## EmergencyService (Pydantic Model)

| Field | Type | Purpose |
|-------|------|---------|
| `name` | str | Hospital/police station name |
| `service_type` | str | "hospital", "ambulance", "police", "fire" |
| `phone` | str? | Phone number |
| `distance_km` | float? | Distance from victim |
| `address` | str? | Street address |
| `latitude` | float? | Coordinates |
| `longitude` | float? | Coordinates |
| `trauma_level` | str? | "Level 1", "Level 2", "Level 3" |
| `is_24x7` | bool? | 24/7 operation |

## Redis Storage

- **Key pattern:** `roadsos:session:{user_id}`
- **Value:** JSON string from `session.model_dump_json()`
- **TTL:** 3600 seconds (1 hour)
- **Last activity:** Updated on every save

## Related Notes

- [[04-Triage-Flow]] — How triage_state transitions work
- [[02-Architecture]] — Where session fits in the data flow
- [[07-File-Map]] — Location of schemas.py and session.py
