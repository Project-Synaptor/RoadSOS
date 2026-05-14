# Known Issues & TODOs

## Critical

### Odia TTS Unverified
**Status:** ⚠️ Not confirmed
**Issue:** MiMo V2.5 TTS may not support Odia (`or`) natively.
**Current behavior:** Falls back to text-only reply (no error shown).
**TODO:** Test MiMo TTS with Odia text. If unsupported, document as permanent limitation.
**File:** `app/services/tts.py` — `_SUPPORTED_TTS_LANGUAGES` set

### Production Webhook URL
**Status:** ⚠️ Not resolved
**Issue:** Twilio needs a publicly accessible URL to send webhooks. Local development uses ngrok or Twilio's sandbox.
**TODO:** Deploy to a hosted environment (Railway, Render, EC2) or set up persistent ngrok.
**File:** `app/utils/twilio_client.py` — TODO comment in `upload_media()`

---

## Medium

### `upload_media()` Needs Production Testing
**Status:** ⚠️ Untested
**Issue:** The Twilio Media upload function creates a self-send message to attach media. This approach may have rate limits or reliability issues in production.
**TODO:** Test with real Twilio sandbox. Consider fallback to `/media/{id}` endpoint.
**File:** `app/utils/twilio_client.py`

### End-to-End WhatsApp Voice Test
**Status:** ⚠️ Not done
**Issue:** Voice pipeline (voice note → STT → triage → TTS → voice reply) has not been tested end-to-end on WhatsApp.
**TODO:** Send a Hindi voice note to the bot, verify it responds in Hindi with both text and voice.

### Hospital Data Limited to 2 Cities
**Status:** Known limitation
**Issue:** `data/hospitals.json` only has data for Bhubaneswar and Chennai.
**TODO:** Add more cities as needed. Data entry is manual.

---

## Low

### No Persistent Conversation History
**Status:** By design
**Issue:** Redis sessions expire after 1 hour. No database for long-term storage.
**Decision:** Acceptable for hackathon demo. Production would need a database.

### No Authentication on Webhook
**Status:** By design
**Issue:** The `/webhook` endpoint accepts any POST request. Twilio provides request validation but it's not implemented.
**TODO:** Add Twilio request signature validation for production.

### `_extract_location_info()` Keyword Heuristic
**Status:** Working but fragile
**Issue:** Location detection from text uses simple keyword matching ("near", "road", "street"). May have false positives.
**TODO:** Consider using MiMo to extract location from text instead of regex.

---

## Resolved

### ~~GIS/Maps API Costs~~
**Resolved:** Replaced with local JSON + haversine. Phase 2.

### ~~Voice Notes Not Handled~~
**Resolved:** STT pipeline added. Phase 3.

### ~~English-Only~~
**Resolved:** 8-language support added. Phase 3.

---

## Related Notes

- [[09-Development-Log]] — What's been built
- [[10-Key-Decisions]] — Why we made these choices
- [[05-Language-Support]] — Odia TTS details
