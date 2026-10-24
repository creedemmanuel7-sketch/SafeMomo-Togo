# Terrain UI — Eloge

SafeMomo ne montre plus un rapport. La personne montre une photo. L'écran répond par une couleur, une phrase, un bouton Écouter et un bouton WhatsApp.

## Le problème

À Lomé, on donne une marchandise ou on renvoie de l'argent parce qu'une **image** ressemble à un reçu T-Money ou Flooz. Le nom de l'opérateur est dessiné dans la photo. Le canal officiel n'a rien envoyé.

Deux scènes, un seul geste :

- **Boutique.** Le client est devant toi et te montre « j'ai envoyé ».
- **Famille.** Un message demande de renvoyer de l'argent tout de suite.

La maman ou la vendeuse n'ouvre pas un menu et ne lit pas un score. Quelqu'un à côté appuie. La phrase est dite à voix haute.

## Fichiers

| Fichier | Qui |
|---|---|
| `ui.py` | Eloge. Textes, couleurs, mise en page. |
| `app.py` | Crédo. Photo, session, appel au modèle. À laisser. |
| `analyzer.py` | Crédo. Gemma 4 et JSON. À laisser. |
| `samples/fake_tmoney_sample.png` | Stéphane. Image de démo. |

## Ce que l'écran reçoit

Objet `ScamVerdict` :

- `is_scam` — vrai : fond danger. Faux : fond « vérifie quand même », jamais « tu peux envoyer ».
- `scene` — `boutique`, `famille` ou `autre`. Le libellé visible est dans `SCENE_LABELS`.
- `spoken_sentence` — la seule phrase en grand. C'est elle qui est lue.
- `whatsapp_alert` — texte du bouton Prévenir la famille.
- `verdict_title`, `sender_analysis`, `red_flags`, `plain_advice`, `risk_score` — seulement dans « Voir pourquoi », pour le jury.

## États à dessiner

1. **Vide.** Titre, une consigne, prise de photo, bouton Voir l'exemple.
2. **Photo prête.** La photo, puis Dis-moi quoi faire.
3. **Attente.** Une ligne : « Je regarde la photo... »
4. **Danger.** Carte rouge, phrase, Écouter, Prévenir la famille.
5. **À vérifier.** Carte verte sombre, même boutons. La phrase dit de taper `*145#`.
6. **Démo.** Une ligne discrète : la phrase était préparée, le réseau a manqué.
7. **Erreur.** Une phrase française et une action. Pas de code.

Le menu latéral « Équipe » reste fermé au départ. Il contient la clé API, le modèle et le mode démo. Il n'est pas pour la vendeuse.

## Contraintes

- Une seule phrase en grand. Le score reste caché dans Voir pourquoi.
- Boutons d'au moins 48 px de haut, pleine largeur.
- Français simple. `*145#` reste écrit tel quel.
- La voix utilise `fr-FR` dans `_listen_button`. Si tu changes le bouton, garde `spoken_sentence` et `utterance.lang`.
- Couleurs dans les variables `--danger-*` et `--check-*` en tête de `inject_css`.
- Tous les libellés sont dans le dictionnaire `TEXTS`.

## Piste visuelle

Écran de téléphone, pas un tableau de bord. La carte du verdict occupe la largeur. Rouge lisible au soleil pour le danger. Le vert ne doit pas ressembler à une autorisation d'envoyer l'argent : c'est « regarde encore ». Pas de graphique, pas de liste devant la phrase.

Stéphane prépare deux photos : un faux reçu montré au marché, un message qui demande de renvoyer. L'écran n'a pas besoin de deux pages. La phrase change, la carte reste la même.
