"""Extend V4 to 12,500 documents per language and authorship class."""
import csv
import heapq
import io
import json
import re
import tarfile
import zipfile
from collections import Counter, defaultdict

from build_education_data import DATA, ROOT, ai_answers, normalized, phrases, record, reference_texts

ARCHIVES = ROOT / "kaynaklar/gercek_yasam"
PROGIT = "61833a527c6ac0c44cc40793c034b81599c25efc"
CTURAN = "fa602a833012ba9390f573ab44828aade1a7609e"
TARGET = 12_500
BASE = ("detector_v3_40781.jsonl", "technical_education_v4_addition.jsonl")


def reviews(used_films):
    with zipfile.ZipFile(ARCHIVES / "turkish_movie_sentiment.zip") as z:
        with z.open("turkish_movie_sentiment_dataset.csv") as f:
            for i, r in enumerate(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")), 1):
                group = "tr-film:" + normalized(r["film_name"])
                if group not in used_films and 50 <= len(r["comment"].split()) <= 900:
                    yield record(r["comment"], 0, "Keskin", "archive_2019", f"csv:{i}", group)
    with tarfile.open(ARCHIVES / "product_reviews.tar.gz") as archive:
        for name in ("reviews.pos", "reviews.neg"):
            for i, line in enumerate(archive.extractfile(name), 1):
                text = line.decode("utf-8").strip()
                if 50 <= len(text.split()) <= 900:
                    yield record(text, 0, "Barmanbay", "archive_2018", f"{name}:{i}", f"{name}:{i}")


def book():
    with zipfile.ZipFile(ROOT / ".training_cache" / f"progit-{PROGIT}.zip") as archive:
        for name in sorted(archive.namelist()):
            if "/tr/" not in name or not name.endswith(".markdown"):
                continue
            path = name.split("/", 1)[1]
            sections = re.split(r"(?m)^#{1,6} .*$", archive.read(name).decode("utf-8"))
            for idx, section in enumerate(sections):
                paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section)
                              if p.strip() and not p.startswith((" ", "\t", "Insert ", "!["))]
                text = " ".join(paragraphs)
                if 50 <= len(text.split()) <= 2000:
                    yield record(text, 0, "progit/progit", PROGIT, f"{path}#section={idx}", path)


def narratives():
    path = ROOT / "kaynaklar/AI/cturan/turkish-synthetic-corpus/tr_corpus.jsonl"
    topic = re.compile(r"\b(?:film|sinema|ürün|alışveriş|müşteri|sipariş)\w*", re.I)
    with path.open("rb") as f:
        count = 0
        while line := f.readline():
            row = json.loads(line)
            text = row["text"]
            if 50 <= len(text.split()) <= 1500 and topic.search(text) and "```" not in text:
                yield record(text, 1, "cturan", CTURAN, f"byte:{f.tell()-len(line)}", row["id"])
                count += 1
                if count == 6500:
                    break


def raid():
    # These domains were absent from the RAID records in V3. Pick one generation
    # per title and label by stable content hash, independently of file order.
    best = {}
    with (ARCHIVES / "raid_train_none.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["domain"] not in ("wiki", "news", "abstracts") or r["attack"] != "none":
                continue
            text = r["generation"]
            if not r["title"].strip() or not 50 <= len(text.split()) <= 1500:
                continue
            group = f"raid:{r['domain']}:{normalized(r['title'])}"
            label = int(r["model"] != "human")
            key = group, label
            if key in best and best[key]["source_record"] <= r["id"]:
                continue
            row = record(text, label, "RAID", "train_none", r["id"], group)
            row.update(language="en", genre=r["domain"], generator=r["model"])
            best[key] = row
    yield from best.values()


def write_records(path, rows):
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp.replace(path)


def build():
    old = []
    for name in BASE:
        with (DATA / name).open(encoding="utf-8") as f:
            old.extend(map(json.loads, f))
    used_groups = {r["group_id"] for r in old if r.get("group_id")}
    pools = defaultdict(list)
    for source in (book(), reviews(used_groups), ai_answers(), narratives(), raid()):
        for row in source:
            if row["group_id"] not in used_groups:
                pools[row["language"], row["label"], row["source"]].append(row)
    # Bound the shingle index while keeping ample replacements for overlaps.
    pool = []
    for rows in pools.values():
        pool.extend(heapq.nsmallest(6500, rows, key=lambda r: r["id"]))
    keys = {k for r in pool for k in phrases(r["text"])}
    blocked = set()
    for text in reference_texts():
        blocked.update(k for k in phrases(text) if k in keys)
    with (DATA / BASE[1]).open(encoding="utf-8") as f:
        for r in map(json.loads, f):
            blocked.update(k for k in phrases(r["text"]) if k in keys)
    del keys
    counts = Counter((r["language"], r["label"]) for r in old)
    # Include available book sections first. Interleave the remaining sources
    # by hash so no single archive fills a language/class quota by file order.
    extra = []
    chosen_raid = set()
    for row in sorted(pool, key=lambda r: (r["source"] != "progit/progit", r["id"])):
        key = row["language"], row["label"]
        if counts[key] >= TARGET or row["group_id"] in chosen_raid:
            continue
        shingles = set(phrases(row["text"]))
        if not shingles.isdisjoint(blocked):
            continue
        blocked.update(shingles)
        if row["source"] == "RAID":
            chosen_raid.add(row["group_id"])
        elif row["source"] in ("Keskin", "Barmanbay", "cturan"):
            row["genre"] = {"Keskin":"movie_review", "Barmanbay":"product_review",
                            "cturan":"narrative"}[row["source"]]
        counts[key] += 1
        extra.append(row)
    if set(counts.values()) != {TARGET} or len(counts) != 4 or len({r["id"] for r in old + extra}) != 50_000:
        raise ValueError(f"Hedefe ulaşılmadı: {counts}")
    write_records(DATA / "balanced_v5_addition.jsonl", extra)
    write_records(DATA / "detector_v5_50000.jsonl", old + extra)
    print(len(extra), counts, Counter(r["source"] for r in extra), flush=True)


if __name__ == "__main__":
    build()
