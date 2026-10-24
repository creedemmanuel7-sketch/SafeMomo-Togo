---
name: safemomo-togo
version: 1.0.0
description: Togo-specific multimodal agent skill for detecting Mobile Money (T-Money & Flooz) fraud and social engineering scams from screenshots.
author: Python Togo Community Hackers
license: MIT
model_compatibility:
  - gemma-4
  - gemini-2.5-flash
tags:
  - open-source-ai
  - fraud-detection
  - mobile-money
  - togo
  - multimodal
---

# SafeMomo Togo Agent Skill

## 1. Overview
`safemomo-togo` is a specialized agent skill designed to protect citizens in Lomé and across Togo from Mobile Money phishing, fake transfer notifications, and social engineering scams using **Gemma 4 Multimodal**.

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
4. **Output Synthesis**: Produce structured JSON output with risk score, red flags, plain advice, and WhatsApp alert card.

## 4. Input & Output Contract

### Input
- `image`: Screenshot image (PNG/JPEG).

### Output Schema (JSON)
```json
{
  "is_scam": "boolean",
  "risk_score": "integer (0-100)",
  "verdict_title": "string",
  "sender_analysis": "string",
  "red_flags": ["string"],
  "plain_advice": "string",
  "whatsapp_alert": "string"
}
```

## 5. Open Source Compliance
This skill follows the open standard for Agent Skills and is released under the **MIT License** for the global and Togolese open-source developer communities.
