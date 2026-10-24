"""Écran SafeMomo.

Lead UI : Eloge. Tout le visible est ici.
Le verdict arrive déjà calculé depuis analyzer.py : ne pas appeler Gemma.
Les textes sont dans TEXTS. Les couleurs sont les variables en tête de CSS.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from analyzer import GEMMA_FAST_MODEL, GEMMA_MODELS, ScamVerdict

TEXTS = {
    "title": "SafeMomo",
    "prompt": "Montre la photo du reçu ou du message.",
    "upload": "Prendre la photo",
    "sample": "Voir l'exemple",
    "sample_missing": "Exemple absent. Lance python samples/generate_sample.py.",
    "scan": "Dis-moi quoi faire",
    "listening": "Je regarde la photo...",
    "listen": "Écouter",
    "whatsapp": "Prévenir la famille",
    "why": "Voir pourquoi",
    "demo": "Démo sans réseau. La phrase est préparée à l'avance.",
    "footer": "SafeMomo Togo · Hacktoberfest Lomé 2026 · Python Togo · MIT",
    "sidebar_title": "Équipe",
    "api_key": "Clé API Google",
    "model": "Modèle",
    "demo_toggle": "Mode démo sans internet",
    "sender": "Expéditeur",
    "advice": "Détail",
    "score": "Repère pour le jury",
}

SCENE_LABELS = {
    "boutique": "Le client est devant toi",
    "famille": "Quelqu'un demande de renvoyer l'argent",
    "autre": "Message à vérifier",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --danger-bg: #7F1D1D;
          --danger-text: #FEF2F2;
          --check-bg: #14532D;
          --check-text: #F0FDF4;
          --ink: #14201F;
          --muted: #4A5B59;
        }
        .safemomo-title {
          text-align: center;
          color: var(--ink);
          font-weight: 800;
          font-size: 2.4rem;
          margin-bottom: 0.2rem;
        }
        .safemomo-prompt {
          text-align: center;
          color: var(--muted);
          font-size: 1.25rem;
          margin-bottom: 1.2rem;
        }
        .safemomo-card {
          border-radius: 28px;
          padding: 28px 22px;
          margin: 8px 0 16px;
        }
        .safemomo-danger { background: var(--danger-bg); color: var(--danger-text); }
        .safemomo-check { background: var(--check-bg); color: var(--check-text); }
        .safemomo-kicker {
          font-size: 0.95rem;
          letter-spacing: 0.02em;
          margin: 0 0 10px;
          opacity: 0.9;
        }
        .safemomo-spoken {
          font-size: 1.85rem;
          line-height: 1.35;
          font-weight: 700;
          margin: 0;
        }
        .stButton > button {
          width: 100%;
          min-height: 48px;
          border-radius: 16px;
          font-weight: 700;
          font-size: 1.05rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_intro() -> None:
    st.markdown(
        f"<h1 class='safemomo-title'>{html.escape(TEXTS['title'])}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p class='safemomo-prompt'>{html.escape(TEXTS['prompt'])}</p>",
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str, bool]:
    """Retourne la clé API, l'identifiant du modèle, et le mode démo."""
    api_key = st.session_state.get("api_key_env") or ""
    with st.sidebar:
        st.header(TEXTS["sidebar_title"])
        if not api_key:
            api_key = st.text_input(TEXTS["api_key"], type="password")
        model_label = st.selectbox(TEXTS["model"], list(GEMMA_MODELS), index=0)
        st.caption(GEMMA_MODELS[model_label])
        offline_demo = st.checkbox(
            TEXTS["demo_toggle"],
            value=False,
            help="Phrase préparée si la connexion manque devant le jury.",
        )
        st.caption(GEMMA_FAST_MODEL)
    return api_key, GEMMA_MODELS[model_label], offline_demo


def render_capture(sample_path: Path) -> tuple[object, bool]:
    """Affiche la prise de photo. Retourne le fichier choisi et le clic sur l'exemple."""
    uploaded = st.file_uploader(TEXTS["upload"], type=["png", "jpg", "jpeg"])
    use_sample = st.button(
        TEXTS["sample"],
        disabled=not sample_path.is_file(),
    )
    if not sample_path.is_file():
        st.caption(TEXTS["sample_missing"])
    return uploaded, use_sample


def render_preview(image: object, name: str) -> bool:
    st.image(image, width="stretch")
    st.caption(name)
    return st.button(TEXTS["scan"], type="primary")


def render_verdict(verdict: ScamVerdict, *, demo: bool) -> None:
    if demo:
        st.caption(TEXTS["demo"])
    kind = "danger" if verdict.is_scam else "check"
    scene = SCENE_LABELS.get(verdict.scene, SCENE_LABELS["autre"])
    st.markdown(
        (
            f"<section class='safemomo-card safemomo-{kind}'>"
            f"<p class='safemomo-kicker'>{html.escape(scene)}</p>"
            f"<p class='safemomo-spoken'>{html.escape(verdict.spoken_sentence)}</p>"
            "</section>"
        ),
        unsafe_allow_html=True,
    )
    _listen_button(verdict.spoken_sentence)
    st.link_button(
        TEXTS["whatsapp"],
        f"https://wa.me/?text={quote(verdict.whatsapp_alert)}",
        width="stretch",
    )
    with st.expander(TEXTS["why"]):
        st.write(f"**{verdict.verdict_title}**")
        st.caption(f"{TEXTS['score']} : {verdict.risk_score} / 100")
        st.write(f"**{TEXTS['sender']} :** {verdict.sender_analysis}")
        for flag in verdict.red_flags:
            st.markdown(f"- {flag}")
        st.info(f"**{TEXTS['advice']} :** {verdict.plain_advice}")


def render_footer() -> None:
    st.divider()
    st.caption(TEXTS["footer"])


def _listen_button(sentence: str) -> None:
    payload = json.dumps(sentence)
    components.html(
        f"""
        <button id="listen" style="width:100%;min-height:48px;border:0;
          border-radius:16px;font-size:1.05rem;font-weight:700;
          background:#0E5A58;color:#F4F7F6;cursor:pointer;">
          {html.escape(TEXTS["listen"])}
        </button>
        <script>
          const button = document.getElementById("listen");
          button.addEventListener("click", () => {{
            const utterance = new SpeechSynthesisUtterance({payload});
            utterance.lang = "fr-FR";
            utterance.rate = 0.92;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
          }});
        </script>
        """,
        height=64,
    )
