"""SafeMomo : photo d'un reçu ou d'un message, puis une phrase à dire.

Le lead UI travaille dans ui.py. Gemma reste dans analyzer.py.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

from analyzer import AnalysisError, analyze_screenshot, demo_verdict
import ui

SAMPLE_PATH = Path("samples") / "fake_tmoney_sample.png"


def main() -> None:
    st.set_page_config(
        page_title="SafeMomo",
        page_icon="🛡️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    ui.inject_css()
    _remember_api_key()
    ui.render_intro()
    api_key, model, offline_demo = ui.render_sidebar()

    uploaded, use_sample = ui.render_capture(SAMPLE_PATH)
    _remember_source(uploaded, use_sample)

    source = st.session_state.get("source_bytes")
    if not source:
        ui.render_footer()
        return

    try:
        image = Image.open(io.BytesIO(source))
        image.load()
    except (UnidentifiedImageError, OSError):
        st.error("Cette photo est illisible. Choisis un fichier PNG ou JPEG.")
        ui.render_footer()
        return

    scan = ui.render_preview(image, st.session_state.get("source_name") or "")
    if scan:
        _scan(image, api_key, model, offline_demo)

    stored = st.session_state.get("verdict")
    if stored and st.session_state.get("verdict_for") == st.session_state.get("source_name"):
        ui.render_verdict(stored, demo=bool(st.session_state.get("verdict_demo")))
    ui.render_footer()


def _remember_api_key() -> None:
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    st.session_state.api_key_env = env_key


def _remember_source(uploaded: object, use_sample: bool) -> None:
    if "source_bytes" not in st.session_state:
        st.session_state.source_bytes = None
        st.session_state.source_name = None
    if uploaded is not None:
        name = getattr(uploaded, "name", "photo")
        data = uploaded.getvalue()
        if data != st.session_state.source_bytes:
            st.session_state.verdict = None
        st.session_state.source_bytes = data
        st.session_state.source_name = name
    if use_sample and SAMPLE_PATH.is_file():
        data = SAMPLE_PATH.read_bytes()
        if data != st.session_state.source_bytes:
            st.session_state.verdict = None
        st.session_state.source_bytes = data
        st.session_state.source_name = SAMPLE_PATH.name


def _scan(image: Image.Image, api_key: str, model: str, offline_demo: bool) -> None:
    if offline_demo:
        st.session_state.verdict = demo_verdict()
        st.session_state.verdict_demo = True
    elif not api_key:
        st.error(
            "Ajoute la clé API dans le menu Équipe, ou coche le mode démo."
        )
        return
    else:
        with st.spinner(ui.TEXTS["listening"]):
            try:
                st.session_state.verdict = analyze_screenshot(
                    api_key,
                    image,
                    model=model,
                )
            except AnalysisError as exc:
                st.error(str(exc))
                return
        st.session_state.verdict_demo = False
    st.session_state.verdict_for = st.session_state.get("source_name")


if __name__ == "__main__":
    main()
