"""Construct the English replacement control and the general-text training variant."""
import hashlib
import json

from build_education_data import DATA, ROOT
from build_50k_data import write_records


def read(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(map(json.loads, f))


def build_control():
    base = {r["id"]: r for r in read("detector_v5_50000.jsonl")}
    with (ROOT / "models/detector_v5/splits.jsonl").open(encoding="utf-8") as f:
        order = list(map(json.loads, f))
    fresh = read("verified_english_academic_train.jsonl")
    manifest = json.loads((DATA / "verified_english_sources.json").read_bytes())
    if hashlib.sha256((DATA / "verified_english_academic_train.jsonl").read_bytes()).hexdigest() != manifest["output_sha256"]["train"]:
        raise ValueError("Verified passage snapshot differs")
    weak = sorted(s["id"] for s in order if s["split"] == "train" and s["language"] == "en"
                  and s["label"] == 0 and base[s["id"]].get("period") == "recent")
    if len(weak) < len(fresh) or len(fresh) != 631:
        raise ValueError("Unexpected replacement pool")
    replacements = dict(zip(weak[:len(fresh)], sorted(fresh, key=lambda r: r["id"]), strict=True))
    rows = []
    for s in order:
        r = replacements.get(s["id"], base[s["id"]])
        group = r["group_id"] if s["id"] in replacements else s["split_group"]
        rows.append(dict(r, split=s["split"], split_group=group))
    if len(rows) != 50000 or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Invalid control corpus")
    write_records(DATA / "detector_v6_control.jsonl", rows)
    write_records(DATA / "v6_replacements.jsonl", [{"removed_id": uid, "added_id": r["id"]}
                                                   for uid, r in replacements.items()])
    return rows


if __name__ == "__main__":
    build_control()
