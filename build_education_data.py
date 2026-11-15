"""Build the Turkish technical education addition from pinned local archives."""
import csv
import hashlib
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
YAZBEL = "af8ec45b868e4e3a17b183389c3d4749fb040a0a"
UUNAN = "ee6e20f207a9ef9cadc10b00072c6ef2a02f9817"
TECH = re.compile(r"\b(?:programlama|yazılım|python|javascript|algoritma|sunucu|internet|"
                  r"veritabanı|bilgisayar|bilişim|yönlendirici|protokol|html|css|donanım|işletim sistemi)\b", re.I)


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def phrases(text):
    words = normalized(text).split()
    return (hash(tuple(words[i:i + 18])) for i in range(len(words) - 17))


def record(text, label, source, revision, location, group):
    text = " ".join(text.split())
    return {"text": text, "label": label, "id": hashlib.sha256(normalized(text).encode()).hexdigest(),
            "language": "tr", "genre": "technical_education", "word_count": len(text.split()),
            "source": source, "source_revision": revision, "source_record": location, "group_id": group}


def human_passages():
    archive = ROOT / ".training_cache" / f"yazbel-{YAZBEL}.zip"
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            if "/source/" not in name or not name.endswith(".rst"):
                continue
            path = name.split("/", 1)[1]
            chapter = z.read(name).decode("utf-8-sig").replace("\r\n", "\n")
            passage = []
            start = 0
            for i, paragraph in enumerate(re.split(r"\n\s*\n", chapter)):
                if any(line.startswith((" ", "\t", "..", ">>>", ":")) for line in paragraph.splitlines()) or re.search(
                        r"(?m)^(.)\1{2,}\s*$|https?://|:[a-z]+:`|::", paragraph):
                    passage.clear()
                    continue
                text = " ".join(paragraph.replace("``", "").replace("**", "").split())
                if 50 <= len(text.split()) <= 900:
                    yield record(text, 0, "yazbel/python", YAZBEL, f"{path}#paragraph={i}", path)
                if not passage:
                    start = i
                passage.extend(text.split())
                if 250 <= len(passage) <= 900 and start < i:
                    yield record(" ".join(passage), 0, "yazbel/python", YAZBEL,
                                 f"{path}#paragraph={start}-{i}", path)
                if len(passage) >= 250:
                    passage.clear()


def ai_answers():
    source = ROOT / "kaynaklar/AI/Uunan/turkish-knowledge-sft/chatml_dataset.jsonl"
    seen_prompts = set()
    with source.open("rb") as f:
        while line := f.readline():
            messages = json.loads(line)["messages"]
            if len(messages) < 2:
                continue
            question, answer = messages[:2]
            prompt, text = question["content"], answer["content"]
            if question["role"] != "user" or answer["role"] != "assistant":
                continue
            if not isinstance(prompt, str) or not isinstance(text, str) or not TECH.search(prompt):
                continue
            if not 50 <= len(text.split()) <= 900 or "```" in text:
                continue
            key = hashlib.sha256(normalized(prompt).encode()).hexdigest()
            if key not in seen_prompts:
                seen_prompts.add(key)
                yield record(text.strip(), 1, "Uunan/turkish-knowledge-sft", UUNAN,
                             f"byte:{f.tell() - len(line)}", key)


def reference_texts():
    for path in (DATA / "detector_v3_40781.jsonl", DATA / "human_texts_tr_en_10000.jsonl",
                 ROOT / "kaynaklar/gercek_yasam/bagimsiz_test/test_500.jsonl"):
        with path.open(encoding="utf-8") as f:
            for row in map(json.loads, f):
                yield row["text"]
    with (ROOT / ".training_cache/benchmark/all_data.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["Review_Language"] in ("Turkish", "English"):
                yield " ".join((row["Upside_Review"], row["Downside_Review"]))


def build():
    groups = defaultdict(list)
    for candidates in (human_passages(), ai_answers()):
        for row in candidates:
            groups[row["word_count"] // 50, row["label"]].append(row)
    for rows in groups.values():
        rows.sort(key=lambda row: row["id"])
    selected = []
    for bucket in range(18, 0, -1):
        human = groups[bucket, 0]
        selected.extend(human + groups[bucket, 1][:4 * len(human)])
    candidates = {key for row in selected for key in phrases(row["text"])}
    used = set()
    for text in reference_texts():
        used.update(key for key in phrases(text) if key in candidates)
    eligible = defaultdict(list)
    for row in selected:
        keys = set(phrases(row["text"]))
        if keys.isdisjoint(used):
            eligible[row["word_count"] // 50, row["label"]].append(row)
            used.update(keys)
    result = []
    for bucket in range(1, 19):
        for pair in zip(eligible[bucket, 0], eligible[bucket, 1]):
            result.extend(pair)
    if not result:
        raise ValueError("Eşleşen yeni kayıt bulunamadı.")
    path = DATA / "technical_education_v4_addition.jsonl"
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as f:
        for row in sorted(result, key=lambda row: row["id"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp.replace(path)
    print(f"{len(result)} yeni eğitim kaydı: {path.name}")


if __name__ == "__main__":
    build()
