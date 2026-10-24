"""Pont mince entre l'app mobile (web/) et le cerveau SafeMomo (analyzer.py).

Aucune logique de fraude ici : on reçoit une image, on appelle
analyze_screenshot() ou demo_verdict(), on renvoie le verdict en JSON.

Lancer :  python server.py            (port 8000, toutes les interfaces)
          PORT=9000 python server.py
Clé API : variable GEMINI_API_KEY ou GOOGLE_API_KEY, sinon envoyée par
          le menu Équipe de l'app (en-tête X-Api-Key).
"""

from __future__ import annotations

import io
import json
import mimetypes
import os
import socket
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, UnidentifiedImageError

from analyzer import (
    GEMMA_FAST_MODEL,
    GEMMA_MODELS,
    AnalysisError,
    analyze_screenshot,
    demo_verdict,
)

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
SAMPLE_PATH = ROOT / "samples" / "fake_tmoney_sample.png"
MAX_UPLOAD = 15 * 1024 * 1024  # 15 Mo : une photo de téléphone tient largement.

mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/svg+xml", ".svg")


def _server_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


class Handler(BaseHTTPRequestHandler):
    server_version = "SafeMomo"

    # --- routes -----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (nom imposé par http.server)
        path = self.path.split("?", 1)[0]
        if path == "/api/config":
            self._json(
                {
                    "models": [{"label": k, "id": v} for k, v in GEMMA_MODELS.items()],
                    "default_model": GEMMA_FAST_MODEL,
                    "server_key": bool(_server_key()),
                }
            )
        elif path == "/api/demo":
            self._json({"verdict": demo_verdict().model_dump(), "demo": True})
        elif path == "/samples/fake_tmoney_sample.png":
            self._file(SAMPLE_PATH)
        else:
            self._static(path)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/analyze":
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Route inconnue.")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            self._error(HTTPStatus.BAD_REQUEST, "bad_image", "Aucune image reçue.")
            return
        if length > MAX_UPLOAD:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "bad_image", "Image trop lourde.")
            return
        data = self.rfile.read(length)

        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except (UnidentifiedImageError, OSError):
            self._error(HTTPStatus.BAD_REQUEST, "bad_image", "Image illisible.")
            return

        api_key = (self.headers.get("X-Api-Key") or "").strip() or _server_key()
        if not api_key:
            self._error(HTTPStatus.BAD_REQUEST, "no_key", "Aucune clé API Google.")
            return
        model = (self.headers.get("X-Model") or "").strip() or GEMMA_FAST_MODEL

        try:
            verdict = analyze_screenshot(api_key, image, model=model)
        except AnalysisError as exc:
            self._error(HTTPStatus.BAD_GATEWAY, "analysis", str(exc))
            return
        except Exception as exc:  # garde-fou : l'app doit toujours recevoir du JSON
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "server", type(exc).__name__)
            return
        self._json({"verdict": verdict.model_dump(), "demo": False})

    # --- réponses ---------------------------------------------------------
    def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, kind: str, detail: str) -> None:
        self._json({"error": {"kind": kind, "detail": detail}}, status)

    def _static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else unquote(path).lstrip("/")
        target = (WEB_DIR / relative).resolve()
        if WEB_DIR not in target.parents and target != WEB_DIR:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Fichier introuvable.")
            return
        self._file(target)

    def _file(self, target: Path) -> None:
        if not target.is_file():
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Fichier introuvable.")
            return
        body = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith(("json", "javascript")):
            ctype += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Le service worker et la page doivent toujours être frais.
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))


def _lan_address() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("10.255.255.255", 1))
            return probe.getsockname()[0]
    except OSError:
        return None


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    lan = _lan_address()
    print("\nSafeMomo est prêt.")
    print(f"  Sur cet ordinateur : http://localhost:{port}")
    if lan:
        print(f"  Sur le téléphone (même Wi-Fi) : http://{lan}:{port}")
    print("  Clé API côté serveur :", "oui" if _server_key() else "non (menu Équipe ou mode démo)")
    print("  Ctrl+C pour arrêter.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
