# Project Overview

## What is RoadSOS?

RoadSOS is a WhatsApp-based AI emergency response agent for road accident victims. When someone sends "HELP" on WhatsApp, the bot:

1. Triages the situation (asks about injuries, consciousness, mobility)
2. Locates the nearest trauma-capable hospitals
3. Dispatches emergency service details
4. Guides the user through first aid until help arrives

All via WhatsApp — no app download, no website, just a message.

## The Problem: Dispatch Gap

Current emergency response systems route ambulances to the **nearest** hospital, not the **nearest capable** hospital. A Level 1 trauma centre 5km away is better than a general hospital 1km away for severe injuries. This "Dispatch Gap" costs lives during the Golden Hour (first 60 minutes after injury).

RoadSOS solves this by:
- Classifying hospitals by trauma capability (Level 1/2/3)
- Matching injury severity to the right facility
- Providing Golden Hour countdown to create urgency

## Target Users

- **Primary:** Accident victims who can still use their phone
- **Secondary:** Bystanders who witness an accident
- **Tertiary:** First responders coordinating from the scene

## Hackathon Context

- **Event:** National Road Safety Hackathon 2026
- **Organizers:** CoERS, RBG Labs, IIT Madras
- **Theme:** AI in Road Safety
- **See also:** [[12-Hackathon-Context]]

## What Makes It Different

| Feature | RoadSOS | Traditional 108/112 |
|---------|---------|---------------------|
| Channel | WhatsApp (no app needed) | Phone call |
| Hospital selection | Trauma-capability matched | Nearest available |
| Guidance | AI first-aid loop | Dispatcher instructions |
| Language | 8 Indian languages | Usually local language only |
| Golden Hour | Active countdown | No tracking |
