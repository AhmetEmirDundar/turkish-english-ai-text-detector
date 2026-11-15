"""Evaluate the saved detector on unseen MAiDE-up hotel reviews without refitting."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from detector import DEFAULT_MODEL, ROOT, Detector
from train_detector import (BALANCED_ADDITION, EDUCATION_ADDITION, ENGLISH_ADDITION, FILES,
                            REALWORLD_ADDITION, metrics, normalize, training_windows, write_json)

SOURCE = "https://huggingface.co/datasets/MichiganNLP/MAiDE-up/blob/045e9933ba5c8c216a49c5efc69d07a766c38c3e/all_data.csv"
SHA256 = "ba7e6c05f81fe4c7d05cefb4b6ab8650a80020b4986156c14a9ed1aad0f81d5e"


def phrases(text):
    words = normalize(text).split()
    return (hash(tuple(words[i:i+18])) for i in range(len(words)-17))


def select_reviews(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise ValueError(f"Expected the benchmark revision at {SOURCE}")
    used = set()
    for filename in FILES:
        with (ROOT / "data" / filename).open(encoding="utf-8") as f:
            for line in f:
                for piece in training_windows(json.loads(line)["text"]):
                    used.update(phrases(piece))
    corpus = defaultdict(dict)
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            lang = {"Turkish": "tr", "English": "en"}.get(row["Review_Language"])
            if not lang:
                continue
            text = " ".join(v.strip() for v in (row["Upside_Review"], row["Downside_Review"]) if v.strip())
            if len(text.split()) < 50 or any(p in used for p in phrases(text)):
                continue
            uid = hashlib.sha256(normalize(text).encode()).hexdigest()
            corpus[(lang, int(row["source"]))][uid] = text
    n = min(200, min(len(corpus[lang, label]) for lang in ("tr","en") for label in (0,1)))
    if not n:
        raise ValueError("No balanced evaluation sample available.")
    return [(uid, lang, label, group[uid]) for (lang, label), group in sorted(corpus.items())
            for uid in sorted(group)[:n]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--data", type=Path, default=ROOT / ".training_cache/benchmark/all_data.csv")
    parser.add_argument("--output", type=Path, help="Write a separate report for the current analysis")
    args = parser.parse_args()
    reviews = select_reviews(args.data)
    # Freeze the v1 benchmark selection. New training data must pass an overlap
    # check instead of silently changing which reviews are evaluated.
    training_info = json.loads((args.model_dir / "metrics.json").read_bytes())
    version = training_info.get("dataset_version")
    if version in ("v2", "v3", "v4", "v5", "v6_control", "v6"):
        benchmark_phrases = {p for _, _, _, text in reviews for p in phrases(text)}
        additions = [ENGLISH_ADDITION]
        if version in ("v3", "v4", "v5"):
            additions.append(REALWORLD_ADDITION)
        if version in ("v4", "v5"):
            additions.append(EDUCATION_ADDITION)
        if version == "v5":
            additions.append(BALANCED_ADDITION)
        if version in ("v6_control", "v6"):
            additions = [f"detector_{version}.jsonl"]
        for filename in additions:
            extra = (ROOT / "data" / filename).read_bytes()
            if hashlib.sha256(extra).hexdigest() != training_info["input_sha256"][filename]:
                raise ValueError(f"{filename} differs from the training snapshot.")
            if any(p in benchmark_phrases for row in map(json.loads, extra.splitlines())
                   if row.get("split", "train") == "train" for p in phrases(row["text"])):
                raise ValueError(f"{filename} overlaps the frozen benchmark.")
    detector = Detector(args.model_dir)
    predictions = []
    for uid, lang, label, text in reviews:
        result = detector.predict(text, diagnostics=True)
        predictions.append({"id": uid, "language": lang, "label": label, "score": result["ai_score"],
                            "primary_score": result["primary_score"],
                            "primary_correct": (result["primary_score"] >= detector.settings["threshold"]) == bool(label),
                            "style": result.get("style_analysis")})
    report = {"dataset": SOURCE, "sha256": SHA256, "model": detector.settings["model"],
              "threshold": detector.settings["threshold"], "results": {}, "primary_results": {}}
    if detector.style:
        report["style_threshold"] = detector.style["threshold"]
        report["style_human_threshold"] = detector.style["human_threshold"]
        report["style_results"] = {}
    for lang in ("overall", "tr", "en"):
        group = [p for p in predictions if lang=="overall" or p["language"]==lang]
        labels = np.array([p["label"] for p in group])
        scores = np.array([p["score"] for p in group])
        report["results"][lang] = metrics(labels, scores, detector.settings["threshold"])
        report["primary_results"][lang] = metrics(labels, np.array([p["primary_score"] for p in group]),
                                                  detector.settings["threshold"])
        if detector.style:
            covered = [p for p in group if p["style"]["status"] == "ok"]
            decided = [p for p in covered if p["style"]["agreement"] is not None]
            result = {"insufficient_text": len(group) - len(covered), "uncertain": len(covered) - len(decided)}
            if decided:
                result["decided_metrics"] = metrics(np.array([p["label"] for p in decided]),
                                                    np.array([p["style"]["ai_score"] for p in decided]),
                                                    detector.style["threshold"])
            for name, agreement in (("agree", True), ("disagree", False)):
                subset = [p for p in covered if p["style"]["agreement"] == agreement]
                result[name] = {"n": len(subset), "primary_errors": sum(not p["primary_correct"] for p in subset)}
            report["style_results"][lang] = result
    write_json(args.output or args.model_dir / "external_test.json", report)
    print(json.dumps(report["results"], indent=2))


if __name__ == "__main__":
    main()
