# Key Decisions

## 1. WhatsApp via Twilio (Not a Web App)

**Decision:** Build a WhatsApp bot, not a website or mobile app.

**Why:**
- Zero friction — no app download, no account creation
- Works on any phone with WhatsApp (90%+ smartphone penetration in India)
- Voice notes are native to WhatsApp
- Location pins are native to WhatsApp
- Twilio provides a reliable WhatsApp Business API

**Tradeoff:** Limited to Twilio's WhatsApp sandbox for development. Production needs approved WhatsApp Business account.

---

## 2. Static JSON Instead of Maps API

**Decision:** Use `data/hospitals.json` instead of Google Maps or Geoapify API.

**Why:**
- Hackathon demo — no need for real-time data
- No API costs (Google Maps is expensive)
- No latency (local file read vs API call)
- Full control over data quality
- Trauma classification requires custom fields not in standard APIs

**Tradeoff:** Limited to Bhubaneswar and Chennai. Adding cities requires manual data entry.

---

## 3. Redis for Session (No Database)

**Decision:** Store session state in Redis, not PostgreSQL or MongoDB.

**Why:**
- Sessions are ephemeral (1-hour TTL)
- Redis is fast (in-memory)
- Simple key-value pattern fits perfectly
- Docker-compose makes Redis trivial to deploy
- No schema migrations needed

**Tradeoff:** No persistent conversation history. Sessions expire after 1 hour.

---

## 4. Single Multilingual Prompt (Not 8 Separate)

**Decision:** One `triage_system.txt` with a `[LANGUAGE INSTRUCTION]` block, not 8 language-specific prompt files.

**Why:**
- MiMo V2.5 Pro handles translation natively
- 8x less maintenance (one file to update)
- Injecting `[LANGUAGE: hi]` is simpler than managing 8 files
- Language-specific prompts would need to stay in sync

**Tradeoff:** Less control over language-specific phrasing. MiMo's translations may not be perfect for emergency contexts.

---

## 5. Twilio Media Upload for TTS (Free, No ngrok)

**Decision:** Upload TTS audio to Twilio's Media API and use the Twilio-hosted URL.

**Why:**
- Free — part of existing Twilio account
- No extra infrastructure (no file server, no S3, no ngrok for audio)
- Twilio-hosted URLs are always accessible
- Works with WhatsApp's media requirements

**Tradeoff:** `upload_media()` needs testing for production reliability. May need a `/media/{id}` endpoint as fallback.

---

## 6. MiMo STT Language Field + Keyword Fallback

**Decision:** Use MiMo STT's `language` response field as primary detection, with keyword-based fallback for text messages.

**Why:**
- STT language field is free (already in the response)
- Zero extra latency for voice messages
- Keyword fallback handles text messages without STT
- Script detection handles native Indic scripts

**Tradeoff:** Keyword detection can have false positives (e.g., "hai" is common in both Hindi and other languages). Order of checking matters.

---

## 7. Trauma Level Classification from Data Fields

**Decision:** Classify hospitals as Level 1/2/3 based on `trauma_capable`, `has_icu`, `has_blood_bank` fields in JSON.

**Why:**
- Level 1 = trauma + ICU + blood bank (full capability)
- Level 2 = trauma + (ICU or blood bank) (partial)
- Level 3 = basic facility
- Data-driven, not hardcoded

**Tradeoff:** Classification is only as good as the data. Manual data entry may have errors.

---

## Related Notes

- [[09-Development-Log]] — When these decisions were made
- [[11-Known-Issues]] — Limitations of these choices
- [[02-Architecture]] — How these decisions shape the system
