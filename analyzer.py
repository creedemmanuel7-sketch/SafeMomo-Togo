"""Appels Gemma 4, lecture de l'écran, puis règles Python du verdict."""

from __future__ import annotations

import io
import json
import re
import unicodedata

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
    "sender_label",
    "message_text",
    "reply_blocked",
    "in_whatsapp",
    "asks_to_send_back",
)
_FALLBACK_SPOKEN = "Ne donne rien. Vérifie ton solde avec *145#."

SYSTEM_PROMPT = """
Tu lis une photo d'écran pour SafeMomo, à Lomé. Tu ne décides pas si c'est
une arnaque. Tu recopies seulement ce qui est visible.

Réponds uniquement avec un objet JSON, sans markdown, avec exactement ces clés :
- sender_label : le nom ou le numéro en haut du fil, tel qu'écrit.
  Exemples : MoovMoney, Movemoney, Mixx by Yas, Miss by Yas, Flooz, +228 90 12 34 56.
  Vide si aucun en-tête n'est visible.
- message_text : le texte des bulles, lignes conservées. Inclus montant,
  heure, référence, Txn ID, solde. N'invente aucun chiffre.
- reply_blocked : true si l'écran dit qu'on ne peut pas répondre
  (« ne peut pas accepter de réponses », « réponse non disponible »).
- in_whatsapp : true seulement si l'image est une discussion WhatsApp
  ou un message transféré, pas l'application SMS du téléphone.
- asks_to_send_back : true si le texte demande de renvoyer, rembourser
  ou redonner l'argent.

Ne mets pas is_scam. Ne juge pas l'expéditeur.
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


class ScreenReading(BaseModel):
    """Ce que Gemma a lu. Le verdict n'est pas dans cet objet."""

    sender_label: str = ""
    message_text: str = ""
    reply_blocked: bool = False
    in_whatsapp: bool = False
    asks_to_send_back: bool = False

    @field_validator("sender_label", "message_text", mode="before")
    @classmethod
    def coerce_optional_text(cls, value: object) -> str:
        return "" if value is None else str(value).strip()

    @field_validator("reply_blocked", "in_whatsapp", "asks_to_send_back", mode="before")
    @classmethod
    def coerce_flag(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "vrai", "oui", "yes"}
        return bool(value)


_OPERATOR_NAMES = (
    "movemoney",
    "moovmoney",
    "flooz",
    "mixxbyyas",
    "mixx",
    "missbyyas",
    "tmoney",
    "yas",
)
_MOOV_MARKS = ("movemoney", "moovmoney", "moov", "flooz")
_AMOUNT = re.compile(
    r"\d[\d\s.,]*\s*(?:fcfa|f\b|francs?)",
    re.IGNORECASE,
)
_REFERENCE = re.compile(
    r"(txn\s*id|r[ée]f[ée]rence|reference|\bref\b|id\s+de\s+transaction)",
    re.IGNORECASE,
)
_NOTICE = re.compile(
    r"(transfert|solde|alerte|re[çc]u|recu|montant|txn)",
    re.IGNORECASE,
)


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    stripped = "".join(char for char in stripped if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9+]", "", stripped.lower())


def _is_phone(label: str) -> bool:
    compact = re.sub(r"[\s.\-()]", "", label.strip())
    digits = re.sub(r"\D", "", compact)
    if compact.startswith("+") and len(digits) >= 8:
        return True
    if digits.startswith("228") and 11 <= len(digits) <= 13 and _fold(label).startswith("228"):
        return True
    return bool(re.fullmatch(r"\d{8}", compact))


def _is_operator_name(label: str) -> bool:
    if _is_phone(label):
        return False
    folded = _fold(label)
    return any(name in folded for name in _OPERATOR_NAMES)


def _looks_like_operator_notice(text: str) -> bool:
    if not _NOTICE.search(text):
        return False
    return bool(_AMOUNT.search(text) or _REFERENCE.search(text))


def _balance_code(sender: str, body: str) -> str:
    folded = _fold(sender + " " + body)
    if any(mark in folded for mark in _MOOV_MARKS):
        return "*155#"
    return "*145#"


def decide(reading: ScreenReading) -> ScamVerdict:
    """Applique les règles. Gemma ne fournit pas is_scam."""

    sender = reading.sender_label.strip()
    body = reading.message_text.strip()
    operator = _is_operator_name(sender)
    phone = _is_phone(sender)
    notice = _looks_like_operator_notice(body)
    code = _balance_code(sender, body)

    if reading.asks_to_send_back or (phone and notice) or (reading.in_whatsapp and notice):
        return ScamVerdict.model_validate(
            {
                "is_scam": True,
                "risk_score": 96,
                "scene": "famille" if reading.asks_to_send_back else "boutique",
                "verdict_title": "Avis imité depuis un numéro",
                "spoken_sentence": (
                    f"Ne renvoie rien. Cet avis ne vient pas de l'opérateur. Tape {code}."
                ),
                "sender_analysis": (
                    f"L'en-tête affiche « {sender or 'aucun nom'} ». "
                    "Un vrai avis MoovMoney, Flooz ou Mixx by Yas porte le nom "
                    "de l'opérateur, pas un numéro, et ne demande pas de renvoyer l'argent."
                ),
                "red_flags": _scam_flags(reading, phone, notice),
                "plain_advice": f"Ne donne rien. Tape {code} avant toute action.",
                "whatsapp_alert": (
                    "ALERTE : un message imite un avis de transfert Mobile Money. "
                    f"Ne renvoyez rien avant d'avoir tapé {code}."
                ),
            }
        )

    if operator and notice:
        shown = sender or "l'opérateur"
        return ScamVerdict.model_validate(
            {
                "is_scam": False,
                "risk_score": 20,
                "scene": "autre",
                "verdict_title": "Avis opérateur",
                "spoken_sentence": (
                    f"C'est un avis {shown}. Vérifie quand même le solde avec {code}."
                ),
                "sender_analysis": (
                    f"L'en-tête « {shown} » est un nom d'opérateur, pas un numéro. "
                    "Le texte a la forme d'un avis de transfert, de solde ou d'alerte."
                ),
                "red_flags": [],
                "plain_advice": (
                    f"Cet écran ressemble à un avis opérateur. Tape {code} "
                    "avant de donner une marchandise ou de l'argent."
                ),
                "whatsapp_alert": (
                    f"Un avis {shown} est affiché. "
                    f"Vérifiez le solde avec {code} avant d'agir."
                ),
            }
        )

    return ScamVerdict.model_validate(
        {
            "is_scam": False,
            "risk_score": 10,
            "scene": "autre",
            "verdict_title": "Pas un avis Mobile Money",
            "spoken_sentence": (
                "Ce n'est pas un avis Mobile Money. "
                "Ne te base pas dessus pour envoyer de l'argent."
            ),
            "sender_analysis": (
                f"L'en-tête « {sender or 'absent'} » n'est pas un canal opérateur "
                "annonçant un transfert."
            ),
            "red_flags": [],
            "plain_advice": "Rien à vérifier sur un compte Mobile Money dans cette image.",
            "whatsapp_alert": (
                "Le message montré n'est pas un avis Mobile Money. "
                "N'envoyez rien sur cette base."
            ),
        }
    )


def _scam_flags(reading: ScreenReading, phone: bool, notice: bool) -> list[str]:
    flags: list[str] = []
    if phone and notice:
        flags.append("Un numéro personnel annonce un transfert au format opérateur")
    if reading.asks_to_send_back:
        flags.append("Le texte demande de renvoyer l'argent")
    if reading.in_whatsapp and notice:
        flags.append("L'avis est montré dans WhatsApp, pas dans les SMS de l'opérateur")
    if not reading.reply_blocked and phone:
        flags.append("On peut répondre, comme à une personne")
    return flags or ["Le message imite un avis opérateur"]


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


def parse_reading(raw: str) -> ScreenReading:
    payload = _extract_json(raw)
    try:
        return ScreenReading.model_validate(payload)
    except ValidationError as exc:
        raise AnalysisError(
            "Gemma 4 a répondu, mais la lecture de l'écran est incomplète."
        ) from exc


def parse_verdict(raw: str) -> ScamVerdict:
    """Compatibilité : une lecture JSON devient un verdict par les règles."""

    return decide(parse_reading(raw))


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
        reading = parse_reading(raw)
    except AnalysisError:
        reading = parse_reading(_repair_json(client, model, raw))
    return decide(reading)


def _generate_raw(client: object, model: str, contents: list[object]) -> str:
    assert types is not None
    fast_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
        max_output_tokens=1024,
        response_mime_type="application/json",
        media_resolution=getattr(
            types.MediaResolution,
            "MEDIA_RESOLUTION_HIGH",
            types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
        ),
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
