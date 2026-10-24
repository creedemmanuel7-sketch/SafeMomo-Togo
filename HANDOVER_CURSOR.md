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
Construire **SafeMomo Togo**, une application web interactive Python (Streamlit) propulsée par le modèle multimodal **Gemma 4**.
L'application regarde la **photo** d'un reçu ou d'un message WhatsApp et répond par **une phrase dite à voix haute**, avant qu'une marchandise parte ou qu'un argent soit renvoyé. Le lead UI travaille dans `ui.py` et `UX.md`. Gemma reste dans `analyzer.py`.

---

## 3. Commandes d'Exécution Rapide

Dans le terminal de Cursor :
```bash
# 1. Installation des dépendances
pip install -r requirements.txt

# 2. Lancement immédiat de l'application
streamlit run app.py
```
*(Si la clé API GEMINI_API_KEY n'est pas définie, vous pouvez la renseigner directement dans la barre latérale de l'application ou cocher le "Mode Démo de Secours" pour les tests sans connexion).*
