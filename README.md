# 🛡️ SafeMomo Togo — AI Shield Against Mobile Money Fraud
> Built with Gemma 4 for Hacktoberfest Hack Day Lomé × Python Togo 🇹🇬

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Gemma 4](https://img.shields.io/badge/AI-Gemma%204%20Multimodal-purple.svg)]()
[![Agent Skill Standard](https://img.shields.io/badge/Standard-SKILL.md-green.svg)](./SKILL.md)

## 🚨 The Problem in Togo
Every single day in Lomé, citizens, students, and small shopkeepers lose their hard-earned savings to sophisticated **fake T-Money & Flooz SMS transfers** and WhatsApp social engineering traps (*"Pardon maman, I sent the hospital money to your number by mistake, send it back immediately!"*). 

Traditional regex filters fail because modern scammers use screenshots of manipulated receipts and psychological urgency.

## 💡 The Solution: SafeMomo Togo
SafeMomo is an open-source AI guardian. Whenever a user suspects a message:
1. They take a **screenshot** of the SMS or WhatsApp message.
2. **Gemma 4 Multimodal** inspects the visual header, checks sender legitimacy (personal number vs. official gateway), audits the transaction structure, and analyzes social manipulation signals.
3. The app delivers a **high-confidence scam score**, a plain-language explanation in local context, and generates an **instant WhatsApp broadcast alert** to protect family and community members.

## ✨ Key Features
- 📸 **Visual & Multimodal Fraud Audit:** Analyzes phone screenshots without manual typing.
- 🇹🇬 **Togo-Specific Context:** Built around T-Money and Flooz transaction syntax and local scam patterns.
- 📢 **Community Defense:** Auto-generates WhatsApp warning cards for family groups.
- 🔒 **Privacy & Open Source:** Lightweight, open-weight ready, licensed under MIT.
- ⚡ **Offline Resilience:** Includes a zero-crash demonstration fallback mode.

## 🛠️ Project Structure
```text
SafeMomo-Togo/
├── SKILL.md              # Open Standard Agent Skill declaration
├── app.py                # Core Streamlit application + Gemma 4 vision
├── requirements.txt      # Python dependencies
├── LICENSE               # Open-source MIT license
├── README.md             # Project documentation
└── HANDOVER_CURSOR.md    # Cursor IDE configuration & handover guide
```

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/votre-user/SafeMomo-Togo.git
cd SafeMomo-Togo

# Install dependencies
pip install -r requirements.txt

# Run the application
export GEMINI_API_KEY="your-api-key"
streamlit run app.py
```

## 👥 The Team
Proudly built by **Team SafeMomo** for Hacktoberfest Hack Day Lomé 2026:
- **ADJIGNON K. Crédo** — *Team Lead, Core AI Architect & Repo Maintainer*
- **HEMAZRO Eloge** — *Lead Frontend & UX Engineer (Streamlit & Localisation)*
- **AKOMAGBE E. Stéphane** — *Lead QA, Datasets & Demo Specialist*
- **HAMADOU Nassif** — *Lead Product & Final Pitcher*

## 🏆 Target Hackathon Challenges
- **Best Use of Gemma 4** (Multimodal image + text reasoning for community protection)
- **Best Open-Source AI Project** (MIT License, Agent Skill open standard, community-oriented code)

## 🤖 AI Assistance Attribution
As per Hacktoberfest Hack Day guidelines, AI assistants (Google Antigravity, GitHub Copilot) were utilized for rapid scaffolding, agent skill formatting, and architecture optimization.
