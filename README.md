# 🛡️ SafeMomo Togo — AI Shield Against Mobile Money Fraud
> Built with Gemma 4 for Hacktoberfest Hack Day Lomé × Python Togo 🇹🇬

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Gemma 4](https://img.shields.io/badge/AI-Gemma%204%20Multimodal-purple.svg)]()
[![Agent Skill Standard](https://img.shields.io/badge/Standard-SKILL.md-green.svg)](./SKILL.md)

## 🚨 The Problem in Togo
In Lomé, people hand over goods or send money back because a **picture** looks like a T-Money or Flooz receipt. The operator name is drawn inside the image. The official channel never sent anything. A regex on the SMS inbox cannot see that photo, and the person in front of the counter has about ten seconds.

## 💡 The Solution: SafeMomo Togo
SafeMomo is an open-source witness for that moment. Someone photographs the screen they were just shown.
1. **Gemma 4** looks at the image: WhatsApp chrome, a pasted receipt, a personal number, a push to act now.
2. The screen answers with **one spoken sentence** and a full-color card. No score in front of the user.
3. One button reads the sentence aloud. Another opens WhatsApp with a warning the family can forward.
4. "Voir pourquoi" keeps the visual reasoning for the jury. The sidebar (API key, model, offline demo) stays collapsed.

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
├── app.py                # Photo, session, Gemma call
├── ui.py                 # Screen owned by the UX lead
├── UX.md                 # UI handoff: states, copy, colors
├── analyzer.py           # Gemma 4 vision call + JSON verdict parsing
├── server.py             # Thin bridge: phone app → analyzer.py (stdlib only)
├── web/                  # Installable mobile web app (camera, card, voice, WhatsApp)
├── requirements.txt      # Python dependencies
├── LICENSE               # Open-source MIT license
├── README.md             # Project documentation
├── HANDOVER_CURSOR.md    # Cursor IDE configuration & handover guide
├── samples/              # Synthetic scam screenshot for the demo
└── tests/                # Parser and image-prep checks
```

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/creedemmanuel7-sketch/SafeMomo-Togo.git
cd SafeMomo-Togo

# Install dependencies
pip install -r requirements.txt

# Run the application
export GEMINI_API_KEY="your-api-key"
streamlit run app.py
```

## 📱 Application mobile (web app installable)

L'écran pour la vendeuse et la famille : une photo, une carte pleine largeur, une phrase, Écouter, Prévenir la famille. Gemma 4 reste dans `analyzer.py` ; `server.py` ne fait que lui passer l'image.

```bash
pip install -r requirements.txt          # aucune dépendance en plus
export GEMINI_API_KEY="your-api-key"     # optionnel : sinon menu Équipe ou mode démo
python server.py
```

Le terminal affiche deux adresses :
- `http://localhost:8000` sur l'ordinateur ;
- `http://<ip-du-pc>:8000` à ouvrir sur le téléphone, **connecté au même Wi-Fi**.

Sur le téléphone : menu du navigateur › « Ajouter à l'écran d'accueil ». L'icône SafeMomo apparaît comme une app.

**Démo sans internet** : bouton réglages en haut à droite (menu Équipe) › cocher « Mode démo sans internet » › Voir l'exemple › Dis-moi quoi faire. Phrase attendue : « Ne renvoie rien. Ce message n'est pas un vrai T-Money. Tape *145#. »

Routes du pont : `POST /api/analyze` (corps = l'image brute, en-têtes optionnels `X-Api-Key`, `X-Model`) → `{"verdict": {...}}` ; `GET /api/demo` → `demo_verdict()` ; `GET /api/config` → modèles Gemma 4 disponibles. Les erreurs reviennent en `{"error": {"kind", "detail"}}` et l'app les traduit en une phrase française avec une action.

Le prototype Streamlit (`streamlit run app.py`) reste disponible pour l'équipe.

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
