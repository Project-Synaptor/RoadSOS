# RoadSOS — Project Brain

> **WhatsApp-based AI emergency response agent for road accident victims.**
> Built for the National Road Safety Hackathon 2026, IIT Madras.

---

## If You're New, Read These in Order

1. [[01-Project-Overview]] — What is RoadSOS and why it exists
2. [[02-Architecture]] — How the system works
3. [[04-Triage-Flow]] — The 6-state emergency triage system
4. [[07-File-Map]] — Where everything lives in the codebase
5. [[09-Development-Log]] — What was built and when

---

## Quick Links

| Topic | Note |
|-------|------|
| What we're building | [[01-Project-Overview]] |
| System architecture | [[02-Architecture]] |
| Tech stack & APIs | [[03-Tech-Stack]] |
| Triage flow (6 states) | [[04-Triage-Flow]] |
| 8-language support | [[05-Language-Support]] |
| Session & state models | [[06-Session-And-State]] |
| File-by-file map | [[07-File-Map]] |
| How to run it | [[08-Environment-Setup]] |
| What's been built | [[09-Development-Log]] |
| Why we made these choices | [[10-Key-Decisions]] |
| Known issues & TODOs | [[11-Known-Issues]] |
| Hackathon & team | [[12-Hackathon-Context]] |

---

## Current Status

**Infrastructure:** Docker + Redis + FastAPI + Twilio + MiMo API — all working.

**Phase 1:** Initial build — FastAPI backend, WhatsApp webhook, MiMo triage, Redis sessions.
**Phase 2:** GIS/Maps upgrade — local hospitals.json, haversine distance, trauma classification. 42 tasks done.
**Phase 3:** Voice + Multilingual — language detection, STT/TTS with 8-language support. 34 tasks done.

**Tests:** 83 passing (language, voice, maps, triage).

**Next:** End-to-end WhatsApp voice test, confirm Odia TTS, production deployment.

---

## Project at a Glance

- **What:** WhatsApp bot that triages road accidents, finds nearest trauma-capable hospitals, guides first aid
- **How:** Twilio WhatsApp → FastAPI → MiMo V2.5 Pro (triage) + MiMo V2 Omni (STT) + MiMo V2.5 TTS
- **Where:** Bhubaneswar & Chennai (static hospital data)
- **Languages:** English, Hindi, Bengali, Odia, Tamil, Telugu, Kannada, Malayalam
- **Developer:** Tushar, 2nd year CSE, ITER SOA University
- **Tool:** Claude Code (autonomous mode)
