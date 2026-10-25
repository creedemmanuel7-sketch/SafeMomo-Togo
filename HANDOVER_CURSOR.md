# 🚀 PROMPT DE RELAIS CURSOR — PROJET : SafeMomo Togo 🇹🇬

## 1. Contexte du Hackathon
- **Événement :** Hacktoberfest Hack Day Lomé 2026 × Python Togo (MLH).
- **Lieu :** Institut Polytechnique DEFITECH, Lomé.
- **Délai :** Sprint éclair de 2 heures. Équipe de 4 personnes.
- **Catégories ciblées :** 
  1. *Best Open-Source AI Project* (MIT, Repo public, standard `SKILL.md`).
  2. *Best Use of Gemma 4* (IA multimodale open-weight pour la protection citoyenne).

---

## 2. Objectif du Projet
Construire **SafeMomo Togo**, une application web (HTML, CSS, JavaScript) servie par `server.py`, propulsée par le modèle multimodal **Gemma 4**.
L'application regarde la **photo** d'un reçu ou d'un message WhatsApp et répond par **une phrase dite à voix haute** (voix Charon), avant qu'une marchandise parte ou qu'un argent soit renvoyé. L'écran à ouvrir est `web/`. `ui.py` reste l'écran d'équipe, pas la démo. Gemma reste dans `analyzer.py`.

---

## 3. Commandes d'Exécution Rapide

Dans le terminal de Cursor :
```bash
# 1. Installation des dépendances
pip install -r requirements.txt

# 2. Lancement immédiat de l'application (port 8000)
python server.py
```
Ouvrir `http://localhost:8000`. *(Si la clé API GEMINI_API_KEY n'est pas dans `.env`, la renseigner dans le menu Équipe, ou cocher le mode démo sans internet.)*
