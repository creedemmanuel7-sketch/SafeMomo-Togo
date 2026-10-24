# Sécurité

SafeMomo lit une image et propose une phrase. Il ne détient pas le compte Mobile Money.

## Ce qui ne doit jamais partir dans git

- `GEMINI_API_KEY` ou `GOOGLE_API_KEY`. Elles restent dans `.env`, ignoré par git.
- Un SMS réel, un reçu réel, un numéro `+228` réel, un nom de client.
- La réponse de `GET /api/config` ne contient pas la clé. Ne l'ajoute pas.

L'image de `samples/` est dessinée par `samples/generate_sample.py`. Elle est fausse, et elle le dit.

## Signaler

N'ouvre pas une issue avec une clé, un SMS réel ou une capture personnelle. Si le dépôt a publié un secret par erreur, dis-le au mainteneur en message privé et tourne la clé dans [Google AI Studio](https://aistudio.google.com/apikey).

Pour un défaut du dépôt : une issue GitHub, sans donnée personnelle. Décris le geste (photo montrée, phrase obtenue) et la version du fichier.

## Limite

Une phrase de SafeMomo ne remplace pas `*145#`, ni le canal de l'opérateur, ni un avis juridique. Le HTTP du Wi-Fi local n'est pas un secret : la clé de démo reste dans `.env` sur la machine qui sert, pas dans le navigateur du téléphone.
