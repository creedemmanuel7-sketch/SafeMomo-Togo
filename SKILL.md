---
name: safemomo-togo
version: 1.0.0
description: Togo-specific multimodal agent skill. Looks at a photo of a T-Money, Flooz, or WhatsApp screen and answers with one spoken sentence before money or goods change hands.
author: Python Togo Community Hackers
license: MIT
model_compatibility:
  - gemma-4-26b-a4b-it
  - gemma-4-31b-it
tags:
  - open-source-ai
  - fraud-detection
  - mobile-money
  - togo
  - multimodal
---

# SafeMomo Togo Agent Skill

## 1. Overview
`safemomo-togo` protects people in Lomé who are about to hand over goods or send money because a **picture** looks like a Mobile Money receipt. Gemma 4 reads that image and returns one short sentence meant to be spoken aloud.

## 2. Capabilities
- **Visual Sender Verification**: Inspects message header to distinguish official telco shortcodes (`TMONEY`, `MOOV_MONEY`) from spoofed personal mobile numbers (+228 9X/7X).
- **Transaction Syntax Audit**: Verifies transaction IDs, FCFA currency syntax, and balance disclosure consistency.
- **Social Engineering Detection**: Identifies psychological manipulation triggers (feigned urgency, false medical emergencies, fake recruitment offers).
- **Community Defense**: Generates localized, actionable safety guidance and broadcast warnings in plain French and local vernacular.

## 3. Protocol & Reasoning Steps
When presented with an image (screenshot of SMS or WhatsApp conversation):
1. **OCR & Visual Parsing**: Extract visible sender handle/number, date/timestamp, message body, and surrounding UI chrome.
2. **Gateway Check**:
   - IF sender matches an unverified MSISDN (e.g., `+228 90 XX XX XX`) claiming funds transfer -> Flag as **SCAM (Confidence > 95%)**.
   - IF sender matches verified sender ID (`TMONEY` / `MOOV_MONEY`) -> Proceed to structural syntax validation.
3. **Contextual Analysis**: Check for common Togolese social engineering patterns:
   - *"Pardon maman j'ai envoyé l'argent par erreur, renvoie-moi ça..."*
   - Unsolicited recruitment fees or fake government concours.
4. **Scene**: `boutique` if a buyer is showing a receipt to take goods. `famille` if someone asks to send money back. `autre` otherwise.
5. **Output Synthesis**: One `spoken_sentence` in plain French, plus a WhatsApp alert. Risk score and red flags stay available for a secondary "why" view. Never tell the user to send money. If unsure, tell them to dial `*145#` first.

## 4. Input & Output Contract

### Input
- `image`: Screenshot image (PNG/JPEG).

### Output Schema (JSON)
```json
{
  "is_scam": "boolean",
  "risk_score": "integer (0-100)",
  "scene": "boutique | famille | autre",
  "verdict_title": "string",
  "spoken_sentence": "string, one short sentence to read aloud",
  "sender_analysis": "string",
  "red_flags": ["string"],
  "plain_advice": "string",
  "whatsapp_alert": "string"
}
```

## 5. Open Source Compliance
This skill follows the open standard for Agent Skills and is released under the **MIT License** for the global and Togolese open-source developer communities.
