"""Yerel Türkçe / İngilizce metin sınıflandırıcısı ve komut satırı aracı."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from document_text import DOCUMENT_EXTENSIONS, MAX_DOCUMENT_BYTES, extract_document
from style_analysis import FEATURES, style_prediction

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "models" / "detector_v6"
WINDOW_WORDS = 50
MAX_TOKENS = 160
BATCH_SIZE = 8


def windows(text):
    words = text.split()
    if len(words) < WINDOW_WORDS:
        raise ValueError(f"En az {WINDOW_WORDS} sözcük içeren Türkçe veya İngilizce metin girin.")
    return [" ".join(words[start:start + WINDOW_WORDS])
            for start in range(0, len(words), WINDOW_WORDS)]


def probability(logit, settings):
    value = settings["slope"] * float(logit) + settings["intercept"]
    return 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, value))))


def combine_scores(primary, support, style_weight):
    if support["status"] != "ok":
        return primary
    return primary + style_weight * (support["ai_score"] - primary)


class Detector:
    def __init__(self, directory=DEFAULT_MODEL, device=None):
        self.directory = Path(directory)
        self.settings = json.loads((self.directory / "detector.json").read_text(encoding="utf-8"))
        style_path = self.directory / "style.json"
        self.style = json.loads(style_path.read_text(encoding="utf-8")) if style_path.is_file() else None
        if self.style is not None and self.style["features"] != list(FEATURES):
            raise ValueError("Üslup modeli bu özellik sürümüyle uyumlu değil.")
        if self.settings["model"] == "tfidf":
            import joblib
            self.model = joblib.load(self.directory / "tfidf.joblib")
        else:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            folder = self.directory / "xlmr"
            self.tokenizer = AutoTokenizer.from_pretrained(
                folder, local_files_only=True, fix_mistral_regex=False)
            self.model = AutoModelForSequenceClassification.from_pretrained(folder, local_files_only=True)
            self.model.to(self.device).eval()

    def transformer_piece_logits(self, pieces):
        import torch

        # A 50-word piece may span multiple token sequences. Score every
        # continuation and average by its number of content tokens.
        tokens = self.tokenizer(pieces, padding=True, truncation=True, max_length=MAX_TOKENS,
                                return_overflowing_tokens=True, return_special_tokens_mask=True,
                                return_tensors="pt")
        owners = tokens.pop("overflow_to_sample_mapping").numpy()
        special = tokens.pop("special_tokens_mask")
        weights = (tokens["attention_mask"] * (1 - special)).sum(dim=1).clamp(min=1).numpy()
        margins = []
        with torch.inference_mode():
            for start in range(0, len(owners), BATCH_SIZE):
                batch = {key: value[start:start + BATCH_SIZE].to(self.device)
                         for key, value in tokens.items()}
                logits = self.model(**batch).logits.float()
                margins.extend((logits[:, 1] - logits[:, 0]).cpu().tolist())
        return np.bincount(owners, weights=weights * margins) / np.bincount(owners, weights=weights)

    def document_logit(self, pieces):
        weighted_sum = 0.0
        word_count = 0
        for start in range(0, len(pieces), BATCH_SIZE):
            batch = pieces[start:start + BATCH_SIZE]
            lengths = [len(piece.split()) for piece in batch]
            if self.settings["model"] == "tfidf":
                logits = self.model.decision_function(batch)
            else:
                logits = self.transformer_piece_logits(batch)
            weighted_sum += np.dot(logits, lengths)
            word_count += sum(lengths)
        return weighted_sum / word_count

    def predict(self, text, *, diagnostics=False):
        pieces = windows(text)
        logit = self.document_logit(pieces)
        primary = probability(logit, self.settings)
        threshold = self.settings["threshold"]
        score = primary
        support = None
        if self.style is not None:
            support = style_prediction(text, self.style, "AI" if primary >= threshold else "İnsan")
            score = combine_scores(primary, support, self.settings.get("style_weight", 0.0))
        result = {"label": "AI" if score >= threshold else "İnsan",
                "ai_score": round(score, 6), "threshold": self.settings["threshold"],
                "word_count": len(text.split()), "windows": len(pieces)}
        if diagnostics:
            result.update(primary_score=primary, style_analysis=support)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entry = parser.add_mutually_exclusive_group(required=True)
    entry.add_argument("--text", help="Analiz edilecek metin")
    entry.add_argument("--file", type=Path, help="TXT, Markdown, PDF, Word (.docx), Excel (.xlsx, .xls) veya PowerPoint (.pptx) dosyası")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    try:
        if args.file and args.file.suffix.lower() in DOCUMENT_EXTENSIONS:
            with args.file.open("rb") as source:
                text = extract_document(source.read(MAX_DOCUMENT_BYTES + 1), args.file.suffix.lower())
        else:
            text = args.file.read_text(encoding="utf-8-sig") if args.file else args.text
        windows(text)
        result = Detector(args.model_dir).predict(text)
    except (OSError, ValueError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
