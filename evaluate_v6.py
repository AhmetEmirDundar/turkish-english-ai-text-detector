"""Compare frozen V5, English replacement control and general-writing detectors."""
import json
import hashlib
from collections import Counter

from build_education_data import DATA, ROOT, phrases
from detector import Detector
from evaluate_external import SHA256, select_reviews
from train_detector import write_json


def read(path):
    with path.open(encoding="utf-8") as f:
        return list(map(json.loads, f))


def measure(model, rows):
    results = {k: Counter() for k in ("overall", "tr", "en")}
    for row in rows:
        label = row["label"]
        predicted_ai = model.predict(row["text"])["label"] == "AI"
        for key in ("overall", row["language"]):
            counts = results[key]
            counts["human" if label == 0 else "ai"] += 1
            counts["false_ai"] += int(label == 0 and predicted_ai)
            counts["missed_ai"] += int(label == 1 and not predicted_ai)
    return {k: dict(v) for k, v in results.items() if v}


def main():
    reviews = select_reviews(ROOT / ".training_cache/benchmark/all_data.csv")
    sets = {
        "verified_human": read(DATA / "verified_english_academic_holdout.jsonl"),
        "general": read(DATA / "general_v6_holdout.jsonl"),
        "second_external": read(ROOT / "kaynaklar/gercek_yasam/bagimsiz_test/test_500.jsonl"),
        "hotel": [{"id": uid, "language": lang, "label": label, "text": text}
                  for uid, lang, label, text in reviews],
    }
    # Include the removed V5 records and every new candidate record in the leakage check.
    evaluation_keys = {k for rows in sets.values() for row in rows for k in phrases(row["text"])}
    matched = set()
    v5_train = {r["id"] for r in read(ROOT / "models/detector_v5/splits.jsonl") if r["split"] == "train"}
    for filename in ("detector_v6.jsonl", "detector_v5_50000.jsonl"):
        with (DATA / filename).open(encoding="utf-8") as f:
            for row in map(json.loads, f):
                if row.get("split") == "train" or row["id"] in v5_train:
                    matched.update(k for k in phrases(row["text"]) if k in evaluation_keys)
    report = {"hotel_archive_sha256": SHA256, "excluded_overlap": {}, "models": {}}
    for name, rows in sets.items():
        sets[name] = [r for r in rows if matched.isdisjoint(phrases(r["text"]))]
        report["excluded_overlap"][name] = len(rows) - len(sets[name])
    report["sample_sha256"] = {name: hashlib.sha256("\n".join(r["id"] for r in rows).encode()).hexdigest()
                               for name, rows in sets.items()}
    for version in ("v5","v6_control","v6"):
        directory = ROOT / "models" / f"detector_{version}"
        model = Detector(directory)
        if "style_weight" not in model.settings:
            raise ValueError("Model calibration incomplete")
        result = {name: measure(model, rows) for name, rows in sets.items()}
        report["models"][version] = result
        print(version, {k:v["overall"] for k,v in result.items()}, flush=True)
        del model
    write_json(ROOT / "models/detector_v6/comparison.json", report)


if __name__ == "__main__":
    main()
