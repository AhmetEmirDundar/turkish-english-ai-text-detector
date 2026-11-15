"""Türkçe ve İngilizce metinler için yerel analiz arayüzü."""
import argparse
import json
import math
import re
import socket
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from detector import ROOT, WINDOW_WORDS, windows
from document_text import DOCUMENT_EXTENSIONS, MAX_DOCUMENT_BYTES, extract_document
from gradio_client import Client

WEB = Path(__file__).resolve().parent / "web"
DEFAULT_WEB_MODEL = ROOT / "models" / "detector_v6"
ASSETS = {"/": ("index.html", "text/html"), "/app.css": ("app.css", "text/css"),
          "/app.js": ("app.js", "text/javascript")}
MAX_CHARS = 100_000
HF_SPACE_ID = "AhmetEmirDundar/ai-text-detector"
EXTRACT_ROUTES = {"/api/extract/" + ext[1:]: ext for ext in DOCUMENT_EXTENSIONS}


class LocalServer(ThreadingHTTPServer):
    # Windows'ta ikinci bir süreç istekleri eski sunucuyla paylaşmasın.
    allow_reuse_address = not hasattr(socket, "SO_EXCLUSIVEADDRUSE")

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, port, model_dir=DEFAULT_WEB_MODEL):
        super().__init__(("127.0.0.1", port), Handler)
        self.model_dir = model_dir
        self.lock = threading.Lock()
        self.client = None

    def predict(self, text):
        with self.lock:
            if self.client is None:
                self.client = Client(HF_SPACE_ID, verbose=False)
            output = self.client.predict(text, api_name="/analyze")

        if not isinstance(output, (list, tuple)) or len(output) < 3:
            raise RuntimeError("Hugging Face Space beklenmeyen bir yanıt döndürdü.")
        score_text, label, details = (str(value) for value in output[:3])
        score_match = re.search(r"([\d.,]+)\s*/\s*100", score_text)
        threshold_match = re.search(r"karar eşiği\s+([\d.,]+)", details, re.IGNORECASE)
        if not score_match or not threshold_match:
            raise RuntimeError("Hugging Face Space yanıtı okunamadı.")

        score = float(score_match.group(1).replace(",", ".")) / 100
        threshold = float(threshold_match.group(1).replace(",", ".")) / 100
        word_count = len(text.split())
        return {"label": label, "ai_score": round(score, 6), "threshold": threshold,
                "word_count": word_count, "windows": math.ceil(word_count / WINDOW_WORDS)}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)

    def json(self, status, value):
        self.respond(status, json.dumps(value, ensure_ascii=False).encode(), "application/json")

    def local_request(self):
        hosts = {f"{name}:{self.server.server_port}" for name in ("localhost","127.0.0.1")}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (origin is None or origin in {"http://" + h for h in hosts})

    def do_GET(self):
        if not self.local_request():
            return self.json(403, {"error": "Yalnızca yerel bağlantı desteklenir."})
        path = urlsplit(self.path).path
        if path == "/api/model":
            try:
                settings = json.loads((self.server.model_dir / "detector.json").read_bytes())
            except (OSError, ValueError):
                return self.json(503, {"error": "Model ayarları okunamadı."})
            return self.json(200, {"name": "XLM-RoBERTa" if settings["model"] == "xlmr" else "TF-IDF",
                                   "version": self.server.model_dir.name.split("_")[-1], "threshold": settings["threshold"],
                                   "style_weight": settings.get("style_weight", 0) if (self.server.model_dir / "style.json").is_file() else 0,
                                   "min_words": WINDOW_WORDS, "max_chars": MAX_CHARS,
                                   "document_extensions": sorted(DOCUMENT_EXTENSIONS)})
        if path not in ASSETS:
            return self.json(404, {"error": "Sayfa bulunamadı."})
        name, mime = ASSETS[path]
        self.respond(200, (WEB / name).read_bytes(), mime)

    def extract_upload(self, extension):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_DOCUMENT_BYTES:
                return self.json(413, {"error": "Belge dosyaları en fazla 20 MB olabilir."})
            if length <= 0:
                raise ValueError("Dosya boş veya okunamadı.")
            text = extract_document(self.rfile.read(length), extension, MAX_CHARS)
        except ValueError as exc:
            return self.json(400, {"error": str(exc)})
        except RuntimeError as exc:
            return self.json(503, {"error": str(exc)})
        self.json(200, {"text": text})

    def do_POST(self):
        if not self.local_request():
            return self.json(403, {"error": "Yalnızca yerel bağlantı desteklenir."})
        if self.path in EXTRACT_ROUTES:
            return self.extract_upload(EXTRACT_ROUTES[self.path])
        if self.path != "/api/analyze":
            return self.json(404, {"error": "İşlem bulunamadı."})
        if self.headers.get_content_type() != "application/json":
            return self.json(415, {"error": "JSON biçiminde metin bekleniyor."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_CHARS * 6 + 100:
                return self.json(413, {"error": "Gönderilen metin boyut sınırının dışında."})
            body = json.loads(self.rfile.read(length))
            text = body.get("text") if isinstance(body, dict) else None
            if not isinstance(text, str):
                raise ValueError("Analiz edilecek metni girin.")
            if len(text) > MAX_CHARS:
                return self.json(413, {"error": "En fazla 100.000 karakter girilebilir."})
            windows(text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self.json(400, {"error": "Metin okunamadı."})
        except ValueError as exc:
            return self.json(400, {"error": str(exc)})
        try:
            result = self.server.predict(text)
        except Exception:
            traceback.print_exc()
            return self.json(503, {"error": "Hugging Face analiz servisine ulaşılamadı. Space'in çalıştığını ve internet bağlantısını kontrol edin."})
        self.json(200, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metin Dedektörü yerel arayüzü")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model-version", choices=("v6",), default="v6")
    args = parser.parse_args()
    try:
        server = LocalServer(args.port, DEFAULT_WEB_MODEL.parent / ("detector_" + args.model_version))
    except OSError as exc:
        parser.exit(1, f"Sunucu başlatılamadı ({exc}). --port ile başka bir port seçebilirsiniz.\n")
    with server:
        print(f"Metin Dedektörü: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
