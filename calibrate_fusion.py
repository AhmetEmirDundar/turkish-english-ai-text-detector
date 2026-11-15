"""Fit a fixed blend on a reproducible, balanced sample of the validation split."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from detector import DEFAULT_MODEL, ROOT, Detector


def validation_sample(directory):
    groups = defaultdict(list)
    with (directory / "splits.jsonl").open(encoding="utf-8") as f:
        for row in map(json.loads, f):
            if row["split"] == "validation":
                groups[row["language"], row["label"]].append(row["id"])
    count = min(256, *(len(groups[lang, label]) for lang in ("tr", "en") for label in (0, 1)))
    if not count:
        raise ValueError("Doğrulama verisinde her dil ve sınıf bulunmalıdır.")
    ids = {uid for group in groups.values() for uid in sorted(group)[:count]}
    hashes = json.loads((directory / "metrics.json").read_bytes())["input_sha256"]
    rows = []
    for filename, digest in hashes.items():
        data = (ROOT / "data" / filename).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Veri dosyası eğitim sürümünden farklı: {filename}")
        for row in map(json.loads, data.splitlines()):
            if row["id"] in ids:
                rows.append(row)
    if len(rows) != len(ids) or {r["id"] for r in rows} != ids:
        raise ValueError("Doğrulama kayıtları eksik veya yinelenmiş.")
    return rows


def fit_style_weight(primary, style, labels):
    # Least squares (Brier loss), with the primary model retaining at least half the weight.
    delta = style - primary
    denom = np.dot(delta, delta)
    return float(np.clip(np.dot(delta, labels - primary) / denom, 0, 0.5)) if denom else 0.0


def calibrate_fusion(directory):
    rows = validation_sample(directory)
    model = Detector(directory)
    if model.style is None:
        raise ValueError("Üslup ağırlıkları eksik.")
    primary, style = [], []
    for row in rows:
        prediction = model.predict(row["text"], diagnostics=True)
        base = prediction["primary_score"]
        primary.append(base)
        style.append(prediction["style_analysis"].get("ai_score", base))
    weight = fit_style_weight(np.array(primary), np.array(style), np.array([r["label"] for r in rows]))
    model.settings.update(style_weight=weight, fusion_validation_count=len(rows))
    settings_path = directory / "detector.json"
    temporary = settings_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(model.settings, indent=2) + "\n", encoding="utf-8")
    temporary.replace(settings_path)
    print(directory.name, "validation:", len(rows), "style weight:", weight, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    calibrate_fusion(parser.parse_args().model_dir)
