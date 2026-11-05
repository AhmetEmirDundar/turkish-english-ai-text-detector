"""Compare two released detectors on identical, held-out texts without calibrating them."""
import hashlib
import json

import torch

from detector import Detector, ROOT, windows
from train_detector import evaluate, write_json, REALWORLD_ADDITION


def load_rows(path):
    with path.open(encoding="utf-8") as f:
        return list(map(json.loads, f))


def measure(detector, rows):
    logits = [detector.document_logit(r["pieces"]) for r in rows]
    return evaluate(rows, logits, detector.settings)[0]


if __name__ == "__main__":
    torch.set_num_threads(4)
    current = ROOT / "models/detector_v3"
    test_ids = {r["id"] for r in load_rows(current / "splits.jsonl") if r["split"] == "test"}
    blind_path = ROOT / "kaynaklar/gercek_yasam/bagimsiz_test/test_500.jsonl"
    blind = load_rows(blind_path)
    assert len(blind) == len({r["id"] for r in blind}) == 500
    additions = [r for r in load_rows(ROOT / "data" / REALWORLD_ADDITION) if r["id"] in test_ids]
    report = {"independent_source": "https://huggingface.co/datasets/aycabostancioglu/Arabic-English-Turkish-AI-Human-Text/tree/55ad8ab14b1bc2e2510a3d66903be95da1eae4b6",
              "independent_sha256": hashlib.sha256(blind_path.read_bytes()).hexdigest(), "models": {}}
    for r in additions + blind:
        r["pieces"] = windows(r["text"])
    for name in ("detector_v2", "detector_v3"):
        detector = Detector(ROOT / "models" / name)
        report["models"][name] = {"new_source_test": measure(detector, additions),
                                  "independent_test": measure(detector, blind)}
        print(name, report["models"][name]["independent_test"], flush=True)
        del detector
    write_json(current / "transfer_comparison.json", report)
