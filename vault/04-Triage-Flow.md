# Triage Flow

The triage engine is a 6-state conversation state machine powered by MiMo V2.5 Pro. Each incoming message triggers a state transition and an LLM call.

## The 6 States

### STATE 1 — ACTIVATION
**Trigger:** User sends "HELP", "accident", "emergency", "crash", or any distress message.
**Action:** Bot asks for situation description and location (pin or text).

### STATE 2 — SEVERITY CHECK
**Trigger:** Location received (WhatsApp pin or text description).
**Action:** Bot asks: Is the victim conscious? Can they move?

### STATE 3 — TRIAGE COMPLETE
**Trigger:** Both location AND severity confirmed.
**Action:** System fetches nearest emergency services from local JSON data.

### STATE 4 — DISPATCH
**Trigger:** Emergency services found.
**Action:** Bot sends formatted dispatch message with:
- Golden Hour countdown
- Hospital names with trauma level labels
- Ambulance and police contacts
- National emergency number 112

### STATE 5 — FIRST AID LOOP
**Trigger:** After dispatch, if help hasn't arrived.
**Action:** Bot sends one first-aid instruction at a time. Waits for "OK" before next step.
- **Unconscious victim:** Keep airway clear, check breathing
- **Conscious victim:** Move to safety, apply pressure to bleeding

### STATE 6 — RESOLUTION
**Trigger:** User says help has arrived.
**Action:** Reassuring farewell message.

## State Transitions

```
ACTIVATION --> SEVERITY_CHECK (when location received)
SEVERITY_CHECK --> TRIAGE_COMPLETE (when severity assessed)
TRIAGE_COMPLETE --> DISPATCH (when services fetched)
DISPATCH --> FIRST_AID (when no services found)
DISPATCH --> RESOLUTION (when user says help arrived)
FIRST_AID --> RESOLUTION (when user says help arrived)
```

## Golden Hour

- **Duration:** 60 minutes from triage start (SEVERITY_CHECK entry)
- **Display:** "~42 min remaining" or "CRITICAL — Golden Hour expired"
- **Urgency:** Under 15 min → "URGENT" label
- **Purpose:** Creates urgency for the victim and responders

## Dispatch Message Format

```
⏱ GOLDEN HOUR: ~42 min remaining

🏥 AIIMS Bhubaneswar — 3.2 km [TRAUMA CENTRE] 24x7
   📞 0674-2302302

🚑 Ambulance:
   108 Emergency — 📞 108

👮 Police:
   Capital Police Station — 1.5 km — 📞 0674-2345678

📞 National Emergency: 112

👉 Call them RIGHT NOW.
I'll stay with you and guide you until help arrives.
```

## Language in Triage

The triage prompt includes a `[LANGUAGE INSTRUCTION]` block. The webhook injects `[LANGUAGE: {code}]` into the context so MiMo responds in the user's language.

- [[05-Language-Support]] — How language detection works
- [[06-Session-And-State]] — SessionState fields that track triage progress

## Key Functions

| Function | File | Purpose |
|----------|------|---------|
| `process_message()` | triage.py | Main entry point — state machine + MiMo call |
| `_build_messages()` | triage.py | Constructs MiMo prompt with state context |
| `format_dispatch_message()` | triage.py | Formats hospital/police/ambulance details |
| `format_golden_hour()` | triage.py | Calculates remaining Golden Hour time |
