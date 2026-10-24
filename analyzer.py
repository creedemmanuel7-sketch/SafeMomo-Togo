"""Appels Gemma 4 et parsing JSON du verdict SafeMomo."""

from __future__ import annotations

import io
import json
import re

from PIL import Image
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

try:
    from google import genai
    from google.genai import types
except ImportError:  # Le mode démo de l'interface doit rester utilisable.
    genai = None
    types = None

GEMMA_FAST_MODEL = "gemma-4-26b-a4b-it"
GEMMA_PRECISE_MODEL = "gemma-4-31b-it"
GEMMA_MODELS = {
    "Gemma 4 26B A4B (rapide)": GEMMA_FAST_MODEL,
    "Gemma 4 31B (plus précis)": GEMMA_PRECISE_MODEL,
}

_MAX_EDGE = 1280
_JSON_KEYS = (
    "is_scam",
    "risk_score",
    "scene",
    "verdict_title",
    "spoken_sentence",
    "sender_analysis",
    "red_flags",
    "plain_advice",
    "whatsapp_alert",
)
_FALLBACK_SPOKEN = "Ne donne rien. Vérifie ton solde avec *145#."

SYSTEM_PROMPT = """
Tu es SafeMomo, à Lomé. On te montre la photo d'un écran : un reçu T-Money
ou Flooz, ou un message WhatsApp. La personne doit décider en dix secondes
si elle donne une marchandise ou si elle renvoie de l'argent.

Tu juges l'image, pas seulement le texte :
- Un vrai avis vient du canal TMONEY ou MOOV_MONEY. Un numéro personnel
  (+228) qui annonce un transfert est une arnaque.
- Une capture collée dans WhatsApp, une mention transféré, un montant
  recollé, une référence invraisemblable ou un solde absent : la preuve
  est une image, le compte n'a rien reçu.
- L'urgence (« erreur de transfert », hôpital, « renvoie vite ») pousse
  à agir avant de vérifier.

Choisis scene :
- boutique : quelqu'un montre un reçu pour emporter une marchandise.
- famille : quelqu'un demande de renvoyer de l'argent.
- autre : le reste.

spoken_sentence : UNE phrase de français simple, dite à voix haute.
Elle dit quoi faire. Elle ne dit jamais d'envoyer de l'argent.
Si tu doutes : dire de taper *145# avant toute action.

Réponds uniquement avec un objet JSON, sans markdown, avec exactement ces clés :
is_scam (booléen), risk_score (entier 0-100), scene (boutique, famille ou autre),
verdict_title (texte court), spoken_sentence (une phrase),
sender_analysis (texte), red_flags (liste de textes), plain_advice (texte),
whatsapp_alert (texte prêt à partager).
""".strip()

USER_PROMPT = (
    "Analyse cette capture. Réponds uniquement avec l'objet JSON demandé, "
    "sans texte autour."
)


class AnalysisError(Exception):
    """Erreur montrable à l'utilisateur, déjà rédigée en français."""


class ScamVerdict(BaseModel):
    is_scam: bool
    risk_score: int = Field(ge=0, le=100)
    scene: str = "autre"
    verdict_title: str
    spoken_sentence: str
    sender_analysis: str
    red_flags: list[str]
    plain_advice: str
    whatsapp_alert: str

    @model_validator(mode="before")
    @classmethod
    def fill_spoken_sentence(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        spoken = str(payload.get("spoken_sentence") or "").strip()
        if not spoken:
            spoken = str(payload.get("plain_advice") or "").strip()
        payload["spoken_sentence"] = spoken or _FALLBACK_SPOKEN
        if not str(payload.get("scene") or "").strip():
            payload["scene"] = "autre"
        return payload

    @field_validator("is_scam", mode="before")
    @classmethod
    def coerce_bool(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "vrai", "oui", "yes"}
        return value

    @field_validator("risk_score", mode="before")
    @classmethod
    def coerce_score(cls, value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("score booléen")
        if isinstance(value, str):
            digits = re.sub(r"[^\d]", "", value)
            if not digits:
                raise ValueError("score vide")
            value = int(digits)
        score = int(value)  # type: ignore[arg-type]
        return max(0, min(100, score))

    @field_validator("scene", mode="before")
    @classmethod
    def coerce_scene(cls, value: object) -> str:
        text = str(value or "").strip().lower()
        if text in {"boutique", "shop", "marche", "marché"}:
            return "boutique"
        if text in {"famille", "family"}:
            return "famille"
        return "autre"

    @field_validator("red_flags", mode="before")
    @classmethod
    def coerce_flags(cls, value: object) -> object:
        if isinstance(value, str):
            lines = [line.strip(" -\t•") for line in value.splitlines()]
            return [line for line in lines if line]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return value

    @field_validator(
        "verdict_title",
        "spoken_sentence",
        "sender_analysis",
        "plain_advice",
        "whatsapp_alert",
        mode="before",
    )
    @classmethod
    def coerce_text(cls, value: object) -> str:
        text = "" if value is None else str(value).strip()
        if not text:
            raise ValueError("texte vide")
        return text


def demo_verdict() -> ScamVerdict:
    """Verdict local quand le réseau ou la clé API manque."""
    return ScamVerdict.model_validate(
        {
            "is_scam": True,
            "risk_score": 98,
            "scene": "famille",
            "verdict_title": "Faux transfert montré en image",
            "spoken_sentence": (
                "Ne renvoie rien. Ce message n'est pas un vrai T-Money. Tape *145#."
            ),
            "sender_analysis": (
                "L'avis affiché vient d'un numéro personnel, pas du canal TMONEY. "
                "La preuve est une image dans la discussion."
            ),
            "red_flags": [
                "Le reçu est une capture, pas un SMS du canal TMONEY",
                "L'expéditeur visible est un numéro +228",
                "Le texte pousse à renvoyer l'argent tout de suite",
                "Aucune preuve que le solde du téléphone a changé",
            ],
            "plain_advice": (
                "Ne donne pas d'argent. Tape *145# et rappelle la personne "
                "sur son vrai numéro."
            ),
            "whatsapp_alert": (
                "ALERTE : on vous montre une photo de transfert T-Money pour "
                "vous faire renvoyer de l'argent ou donner une marchandise. "
                "Ne donnez rien avant d'avoir tapé *145#."
            ),
        }
    )


def image_to_jpeg(image: Image.Image) -> bytes:
    """Réduit la capture avant l'envoi pour limiter le temps d'analyse."""
    prepared = image.convert("RGB")
    prepared.thumbnail((_MAX_EDGE, _MAX_EDGE), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    prepared.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()


def parse_verdict(raw: str) -> ScamVerdict:
    payload = _extract_json(raw)
    try:
        return ScamVerdict.model_validate(payload)
    except ValidationError as exc:
        raise AnalysisError(
            "Gemma 4 a répondu, mais le verdict ne respecte pas le format attendu."
        ) from exc


def analyze_screenshot(
    api_key: str,
    image: Image.Image,
    model: str = GEMMA_FAST_MODEL,
) -> ScamVerdict:
    if genai is None or types is None:
        raise AnalysisError(
            "Le paquet google-genai est absent. Installez les dépendances "
            "avec pip install -r requirements.txt, ou cochez le mode démo."
        )
    if not api_key.strip():
        raise AnalysisError(
            "Ajoutez une clé API Google dans le menu latéral, "
            "ou cochez le mode démo hors-ligne."
        )
    if model not in GEMMA_MODELS.values():
        raise AnalysisError("Modèle Gemma 4 inconnu.")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=45_000),
    )
    image_part = types.Part.from_bytes(
        data=image_to_jpeg(image),
        mime_type="image/jpeg",
    )
    raw = _generate_raw(client, model, [image_part, USER_PROMPT])
    try:
        return parse_verdict(raw)
    except AnalysisError:
        repaired = _repair_json(client, model, raw)
        return parse_verdict(repaired)


def _generate_raw(client: object, model: str, contents: list[object]) -> str:
    assert types is not None
    fast_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
        max_output_tokens=1024,
        response_mime_type="application/json",
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
        thinking_config=types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.MINIMAL,
            include_thoughts=False,
        ),
    )
    try:
        response = client.models.generate_content(  # type: ignore[attr-defined]
            model=model,
            contents=contents,
            config=fast_config,
        )
    except Exception as exc:
        if _status_code(exc) != 400:
            raise AnalysisError(_friendly_api_error(exc)) from exc
        response = _generate_plain(client, model, contents, exc)

    text = getattr(response, "text", None) or ""
    if not text.strip():
        raise AnalysisError(
            "Gemma 4 n'a renvoyé aucun texte. Réessayez, ou cochez le mode démo."
        )
    return text


def _generate_plain(
    client: object,
    model: str,
    contents: list[object],
    original: Exception,
) -> object:
    assert types is not None
    plain_contents = list(contents)
    if plain_contents and isinstance(plain_contents[-1], str):
        plain_contents[-1] = f"{SYSTEM_PROMPT}\n\n{plain_contents[-1]}"
    try:
        return client.models.generate_content(  # type: ignore[attr-defined]
            model=model,
            contents=plain_contents,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
    except Exception as exc:
        raise AnalysisError(_friendly_api_error(exc)) from original


def _repair_json(client: object, model: str, raw: str) -> str:
    assert types is not None
    keys = ", ".join(_JSON_KEYS)
    prompt = (
        "Corrige le texte suivant pour qu'il devienne un seul objet JSON valide "
        f"avec les clés {keys}. N'ajoute aucun texte autour.\n\n{raw}"
    )
    try:
        response = client.models.generate_content(  # type: ignore[attr-defined]
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=1024,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.MINIMAL,
                    include_thoughts=False,
                ),
            ),
        )
    except Exception as exc:
        raise AnalysisError(_friendly_api_error(exc)) from exc
    text = getattr(response, "text", None) or ""
    if not text.strip():
        raise AnalysisError(
            "Le verdict JSON de Gemma 4 n'a pas pu être réparé. Réessayez."
        )
    return text


def _extract_json(raw: str) -> dict[str, object]:
    cleaned = raw.strip()
    fenced = re.search(
        r"```(?:json)?\s*(.*?)```",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        cleaned = fenced.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise AnalysisError(
            "La réponse de Gemma 4 ne contient pas de JSON exploitable."
        )
    blob = cleaned[start : end + 1]
    blob = re.sub(r",\s*([}\]])", r"\1", blob)
    try:
        payload = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise AnalysisError(
            "La réponse de Gemma 4 n'est pas un JSON lisible."
        ) from exc
    if not isinstance(payload, dict):
        raise AnalysisError("La réponse de Gemma 4 n'est pas un objet JSON.")
    return payload


def _status_code(exc: Exception) -> int | None:
    for attr in ("code", "status_code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    match = re.search(r"\b(400|401|403|404|429|500|503)\b", str(exc))
    if match:
        return int(match.group(1))
    return None


def _friendly_api_error(exc: Exception) -> str:
    text = str(exc).lower()
    code = _status_code(exc)
    if code in {401, 403} or "api key" in text or "permission" in text:
        return (
            "La clé API Google a été refusée. Vérifiez-la dans le menu latéral, "
            "ou cochez le mode démo."
        )
    if code == 429 or "quota" in text or "resource_exhausted" in text:
        return (
            "Le quota Gemma 4 est atteint. Patientez une minute, "
            "ou cochez le mode démo."
        )
    if code == 404 or "not found" in text:
        return (
            "Le modèle Gemma 4 est introuvable pour cette clé. "
            "Vérifiez l'accès à gemma-4-26b-a4b-it dans Google AI Studio."
        )
    if code in {500, 503} or "timeout" in text or "timed out" in text:
        return (
            "Le service Gemma 4 ne répond pas. Réessayez, "
            "ou cochez le mode démo hors-ligne."
        )
    return (
        "L'analyse Gemma 4 a échoué. Réessayez, "
        "ou cochez le mode démo hors-ligne."
    )
