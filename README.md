# SafeMomo Togo

Bouclier open source contre les faux reçus Mobile Money au Togo. Une photo, une phrase dite à voix haute, avant que l'argent ou la marchandise parte.

À Lomé, on donne un téléphone, un sac de ciment ou de l'argent parce qu'une image ressemble à un reçu T-Money ou Flooz. Le nom de l'opérateur est dessiné dans la photo. Le message est collé dans WhatsApp, parfois envoyé depuis un numéro personnel `+228`. Le canal officiel n'a rien envoyé. `*145#` dit si le solde a vraiment changé. Encore faut-il comprendre que l'écran montré n'est pas une preuve.

SafeMomo montre cette photo à **Gemma 4** et répond par une seule phrase, sur une carte pleine largeur. Le score reste derrière « Voir pourquoi ».

Construit pour le [Hacktoberfest Hack Day Lomé × Python Togo](https://www.mlh.com/events/hacktoberfest-hack-day-lome-x-python-togo).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gemma 4](https://img.shields.io/badge/AI-Gemma%204-0E5A58.svg)](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)

## Fonctionnalités

- Une photo, prise sur le moment ou choisie dans la galerie. **Voir l'exemple** envoie une image synthétique à Gemma 4.
- Une phrase en français, sur une carte rouge s'il faut s'arrêter, ou sur une carte sombre s'il faut quand même vérifier. Un message qui semble réel n'autorise jamais à envoyer de l'argent : la phrase dit de taper `*145#`.
- **Écouter** lit cette phrase avec la voix Charon, via `POST /api/speak`. Ce n'est pas la voix du navigateur.
- **Prévenir la famille** ouvre WhatsApp avec l'alerte déjà écrite.
- **Voir pourquoi** garde l'expéditeur, les signaux et le repère sur 100. Ce détail ne passe pas devant la phrase.
- Mode clair et mode sombre. Le bouton lune ou soleil, en haut à droite, mémorise le choix sur l'appareil.
- Mode démo sans réseau, réservé au bouton **Dis-moi quoi faire**. L'écran le dit. **Voir l'exemple** ignore ce mode et appelle le modèle.
- Deux scènes : la boutique, où un client montre « j'ai envoyé », et la famille, où l'on demande de renvoyer l'argent tout de suite.

## Prérequis

- Python 3.10 ou plus récent.
- Un navigateur moderne, sur l'ordinateur ou sur un téléphone du même Wi-Fi.
- Une clé [Google AI Studio](https://aistudio.google.com/apikey) pour l'appel réel à Gemma 4 et pour la voix. Sans clé, le mode démo reste utilisable.

## Installation et lancement

```bash
git clone https://github.com/creedemmanuel7-sketch/SafeMomo-Togo.git
cd SafeMomo-Togo
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine. Git l'ignore.

```text
GEMINI_API_KEY=ta_cle_ici
```

Pas de guillemets, pas d'espace autour du `=`. `GOOGLE_API_KEY` est accepté en secours.

Lancer le serveur. Il écoute sur le port 8000, sur toutes les interfaces.

```bash
python server.py
```

Ouvrir `http://localhost:8000`. Le terminal affiche aussi l'adresse à taper sur le téléphone. Dans le navigateur du téléphone : menu, puis « Ajouter à l'écran d'accueil ».

`GET /api/config` dit seulement si une clé est présente. Il ne renvoie jamais la clé.

## Utilisation de la démo

L'écran est l'interface web du dossier `web/` : HTML, CSS et JavaScript. `server.py` la sert et transmet la photo à Gemma 4. Il n'ajoute pas de règle de fraude.

1. **Voir l'exemple.** La photo `samples/fake_tmoney_sample.png` part vers Gemma 4.
2. Laisser la carte, puis **Écouter**. La voix vient de Gemini, voix Charon, en WAV.
3. S'il reste quelques secondes, ouvrir **Voir pourquoi**.

Si la clé ou le wifi manque : menu Équipe, cocher **Mode démo sans internet**, puis **Dis-moi quoi faire**. Phrase préparée : « Ne renvoie rien. Ce message n'est pas un vrai T-Money. Tape *145#. »

Le bouton lune, à gauche du menu Équipe, passe au mode sombre. Le bouton soleil revient au mode clair. Le choix reste après un rechargement.

Régénérer l'image d'exemple, qui ne contient aucun SMS réel :

```bash
python samples/generate_sample.py
```

Routes :

| Route | Rôle |
|---|---|
| `POST /api/analyze` | Corps = image brute. En-têtes optionnels `X-Api-Key` et `X-Model`. Réponse : `{"verdict": {...}}` |
| `GET /api/demo` | Verdict préparé, sans réseau |
| `GET /api/config` | Modèles Gemma 4, et si une clé est présente. Jamais la clé |
| `POST /api/speak` | Corps `{"text": "..."}`. Réponse audio WAV, voix Charon |

Une erreur revient sous `{"error": {"kind", "detail"}}`. L'écran la traduit en une phrase française avec une action.

Le verdict suit ce contrat. `spoken_sentence` est la seule phrase en grand, et la phrase lue.

```json
{
  "is_scam": true,
  "risk_score": 98,
  "scene": "famille",
  "verdict_title": "Faux transfert montré en image",
  "spoken_sentence": "Ne renvoie rien. Ce message n'est pas un vrai T-Money. Tape *145#.",
  "sender_analysis": "L'avis affiché vient d'un numéro personnel, pas du canal TMONEY.",
  "red_flags": ["Le reçu est une capture, pas un SMS du canal TMONEY"],
  "plain_advice": "Ne donne pas d'argent. Tape *145#.",
  "whatsapp_alert": "ALERTE : on vous montre une photo de transfert pour vous faire renvoyer de l'argent."
}
```

`scene` vaut `boutique`, `famille` ou `autre`. Les états d'écran sont décrits dans [UX.md](./UX.md).

## Structure du dépôt

```text
SafeMomo-Togo/
├── web/                  Interface de la démo
│   ├── index.html
│   ├── app.css
│   ├── app.js
│   ├── manifest.webmanifest
│   ├── sw.js
│   ├── fonts/            Atkinson Hyperlegible, licence OFL
│   └── icons/
├── server.py             Sert web/ et les routes /api/
├── analyzer.py           Appel Gemma 4, image JPEG, verdict validé
├── samples/              Photo synthétique et script qui la dessine
├── tests/                Parseur JSON, sans appel réseau
├── SKILL.md              Même raisonnement, au format Agent Skill
├── UX.md                 États, textes, ce que l'écran a le droit de montrer
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
└── requirements.txt
```

Le contrat à garder est `analyze_screenshot()` et `demo_verdict()` dans `analyzer.py`. Le prompt et le parseur ne se réécrivent pas dans `web/`.

## Stack technique

| Rôle | Choix |
|---|---|
| Interface | HTML, CSS et JavaScript dans `web/`. Pas de framework. Mode clair et mode sombre. Police Atkinson Hyperlegible. |
| Serveur | `server.py`, bibliothèque standard de Python, port 8000 |
| Lecture de l'image | Gemma 4 via l'API Gemini : `gemma-4-26b-a4b-it` par défaut, `gemma-4-31b-it` dans le menu Équipe |
| Voix | `POST /api/speak`, modèle `gemini-3.8-flash-tts`, voix Charon. Le navigateur joue le WAV. |
| Validation | Pydantic pour le verdict, Pillow pour la photo ramenée à 1280 px |
| Skill | [SKILL.md](./SKILL.md), [spécification Agent Skills](https://agentskills.io/specification) |

L'image est envoyée en JPEG. L'appel demande du JSON et retente une fois si la réponse n'est pas un objet. Une réponse entourée de markdown ou une virgule finale est rattrapée avant l'affichage.

Documentation utilisée :

- [Run Gemma with the Gemini API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
- [Image understanding](https://ai.google.dev/gemma/docs/capabilities/vision/image)
- [Google AI Studio, clés](https://aistudio.google.com/apikey)
- SDK [`google-genai`](https://github.com/googleapis/python-genai)

Prix visés : [Best Use of Gemma 4](https://www.mlh.com/events/hacktoberfest-hack-day-lome-x-python-togo/challenges/01a03b87-be22-9180-5e2d-b3beeb66666d) et [Best Open-Source AI Project](https://www.mlh.com/events/hacktoberfest-hack-day-lome-x-python-togo/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3).

## Licences

Le code de SafeMomo est sous [licence MIT](./LICENSE). Copyright (c) 2026 Python Togo Community Hackers. On peut l'utiliser, le modifier et le redistribuer. L'avis de licence doit rester avec les copies. Le logiciel est fourni sans garantie. Il aide à regarder une image. Il ne remplace pas `*145#`, ni un avis juridique.

| Ressource | Licence | Où c'est écrit |
|---|---|---|
| Ce dépôt, y compris [SKILL.md](./SKILL.md) | MIT | [LICENSE](./LICENSE) |
| Police Atkinson Hyperlegible, Braille Institute of America | SIL Open Font License 1.1 | [web/fonts/OFL.txt](./web/fonts/OFL.txt) |
| `google-genai` | Apache-2.0 | métadonnées du paquet installé |
| Pydantic | MIT | métadonnées du paquet installé |
| Pillow | HPND | métadonnées du paquet installé |

Les modèles Gemma 4 et la voix Charon sont appelés via l'API Gemini. Leurs conditions d'usage sont celles de Google. Elles ne sont pas recopiées dans ce dépôt.

## Contribuer

Le dépôt est public. Fork, branche, pull request vers `master`. Les textes visibles restent en français. Les noms de fichiers restent en anglais.

Les étapes, les tests et ce qu'il ne faut pas envoyer sont dans [CONTRIBUTING.md](./CONTRIBUTING.md).

```bash
python -m unittest tests.test_analyzer -v
```

Ces tests n'appellent pas l'API.

## Sécurité

Ne pas publier une clé, un SMS réel, un numéro réel ou un nom de client. `.env` n'est pas versionné. La marche à suivre est dans [SECURITY.md](./SECURITY.md).

## Code de conduite

Ce dépôt suit le code de conduite de Major League Hacking. Le texte court et le lien sont dans [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Équipe

Hacktoberfest Hack Day Lomé 2026 :

- **ADJIGNON K. Crédo** — Team Lead, Core AI Architect & Repo Maintainer
- **HEMAZRO Eloge** — Lead Frontend et UX, interface web HTML, CSS et JavaScript
- **AKOMAGBE E. Stéphane** — Lead QA, Datasets & Demo Specialist
- **HAMADOU Nassif** — Lead Product & Final Pitcher

## Attribution

Des assistants de code ont servi à accélérer l'architecture, le format du skill et la documentation : GitHub Copilot, Google Antigravity et Cursor. Les décisions produit, les règles T-Money / Flooz et les textes montrés à l'écran restent ceux de l'équipe.
