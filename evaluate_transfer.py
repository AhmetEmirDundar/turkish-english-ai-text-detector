"""Compare two released detectors on identical, held-out texts without calibrating them."""
import hashlib
import json
import argparse

import numpy as np
import torch

from detector import Detector, ROOT
from train_detector import metrics, write_json, REALWORLD_ADDITION


def load_rows(path):
    with path.open(encoding="utf-8") as f:
        return list(map(json.loads, f))


def measure(detector, rows):
    scores = np.array([detector.predict(r["text"])["ai_score"] for r in rows])
    labels = np.array([r["label"] for r in rows])
    languages = np.array([r["language"] for r in rows])
    report = {"overall": metrics(labels, scores, detector.settings["threshold"])}
    for lang in ("tr", "en"):
        mask = languages == lang
        report[lang] = metrics(labels[mask], scores[mask], detector.settings["threshold"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("v3", "v5"), default="v3")
    args = parser.parse_args()
    torch.set_num_threads(4)
    current = ROOT / "models" / f"detector_{args.candidate}"
    test_ids = {r["id"] for r in load_rows(current / "splits.jsonl") if r["split"] == "test"}
    blind_path = ROOT / "kaynaklar/gercek_yasam/bagimsiz_test/test_500.jsonl"
    blind = load_rows(blind_path)
    assert len(blind) == len({r["id"] for r in blind}) == 500
    additions = [r for r in load_rows(ROOT / "data" / REALWORLD_ADDITION) if r["id"] in test_ids]
    report = {"independent_source": "https://huggingface.co/datasets/aycabostancioglu/Arabic-English-Turkish-AI-Human-Text/tree/55ad8ab14b1bc2e2510a3d66903be95da1eae4b6",
              "independent_sha256": hashlib.sha256(blind_path.read_bytes()).hexdigest(), "models": {}}
    for name in ("detector_v2", current.name):
        detector = Detector(ROOT / "models" / name)
        report["models"][name] = {"new_source_test": measure(detector, additions),
                                  "independent_test": measure(detector, blind)}
        print(name, report["models"][name]["independent_test"], flush=True)
        del detector
    write_json(current / "transfer_comparison.json", report)
