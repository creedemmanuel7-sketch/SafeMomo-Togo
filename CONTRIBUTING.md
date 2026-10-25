# Contribuer à SafeMomo Togo

Le dépôt est public, licence MIT. Une modification utile est une pull request.

## Lancer

```bash
git clone https://github.com/creedemmanuel7-sketch/SafeMomo-Togo.git
cd SafeMomo-Togo
pip install -r requirements.txt
```

Clé, uniquement sur ta machine, dans `.env` :

```text
GEMINI_API_KEY=ta_cle_ici
```

```bash
python server.py
```

Écran : `http://localhost:8000`.

## Tester

```bash
python -m unittest tests.test_analyzer -v
```

Ces tests ne consomment pas de clé. Un changement du parseur ou de la taille d'image doit rester vert.

## Proposer un changement

1. Fork, puis une branche courte : `fix/phrase-demo`.
2. Les textes montrés à l'écran restent en français. Les noms de fichiers restent en anglais.
3. Le contrat à garder est `analyze_screenshot()` et `demo_verdict()` dans `analyzer.py`. Le front n'ajoute pas de règle de fraude.
4. Ouvre la pull request vers `master`. Dis ce que la photo change pour la personne qui décide.

## À ne pas envoyer

- `.env`, une clé, un jeton.
- Une capture de SMS réel, un numéro réel, un nom de client.
- Une phrase qui autorise à envoyer de l'argent sans `*145#`.

## Écran d'équipe

`streamlit run app.py` ouvre l'ancien écran, en général sur le port 8501. Ce n'est pas le parcours à montrer : **Écouter** y utilise encore la voix du navigateur. L'écran de la démo reste `python server.py`, port 8000.
