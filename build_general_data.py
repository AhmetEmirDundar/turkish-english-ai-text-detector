"""Add balanced, source-attributed everyday writing to the frozen English control."""
import csv
import hashlib
import html
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone

from build_50k_data import ARCHIVES, CTURAN, write_records
from build_education_data import DATA, ROOT, UUNAN, normalized, phrases, reference_texts


CACHE = ROOT / ".training_cache/general_v6"
BILCAT = "ea9f926b2114c6c6a0a1983ef45eb13557ed6188"
TINY = "f54c09fd23315a6f9c86f9dc80f725de7d8f9c64"
TOPICS = re.compile(r"\b(?:yemek|seyahat|gezi|tatil|mutfak|futbol|basketbol|spor|sinema|müzik|"
                    r"roman|edebiyat|masal|hikâye|tiyatro|festival|hobiler|bahçecilik)\b", re.I)


def make(text, lang, label, source, loc, group, genre, url, **metadata):
    text = " ".join(text.split())
    return dict(text=text, id=hashlib.sha256(normalized(text).encode()).hexdigest(), language=lang,
                label=label, source=source, source_record=loc, group_id=group, genre=genre,
                source_url=url, word_count=len(text.split()), **metadata)


def news():
    with zipfile.ZipFile(CACHE / f"bilcat-{BILCAT}.zip") as z:
        name = next(n for n in z.namelist() if n.endswith("BilCat-merged.tsv"))
        with z.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"), delimiter="\t",
                                    quoting=csv.QUOTE_NONE):
                if r["Class"] not in ("Spor", "KulturSanat", "Saglik", "Yazarlar", "Turkiye"):
                    continue
                group = f"bilcat:{r['Resource']}:{r['DocID']}"
                yield make(html.unescape(r["Text"]), "tr", 0, "BilCat", group, group, r["Class"],
                           f"https://github.com/BilkentInformationRetrievalGroup/BilCat/blob/{BILCAT}/BilCat-merged.tsv",
                           publisher=r["Resource"], source_revision=BILCAT)


def paragraphs(body):
    for i, p in enumerate(re.split(r"\n\s*\n", body)):
        if 50 <= len(p.split()) <= 450 and not re.search(r"\[Illustration|Project Gutenberg|https?://", p, re.I):
            yield i, p


def literature():
    for path in sorted(CACHE.glob("pg*.txt")):
        uid = path.stem[2:]
        text = path.read_bytes().decode("utf-8-sig").replace("\r", "")
        header, body = text.split("*** START OF", 1)
        body = body.split("***", 1)[1].split("*** END OF", 1)[0]
        def field(key):
            return re.search(rf"^{key}: *(.+)$", header, re.M)[1].strip()
        author, title = field("Author"), field("Title")
        if field("Language") != "English":
            raise ValueError(uid)
        genre = {"65061":"cooking", "245":"travel_memoir", "308":"travel_humour",
                 "205":"nature_essay"}.get(uid, "fiction")
        for i, p in paragraphs(body):
            yield make(p, "en", 0, "Project Gutenberg", f"{uid}:paragraph:{i}", "pg:"+author, genre,
                       f"https://www.gutenberg.org/ebooks/{uid}", authors=[author], title=title,
                       ebook_release=field("Release date"), book=uid)
    for path in sorted(CACHE.glob("ws-*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        rev = page["revisions"][0]
        text = rev["slots"]["main"]["*"]
        if not re.search(r"\|\s*eser\s*sahibi\s*=\s*Ömer Seyfettin", text) or rev["timestamp"] >= "2022":
            continue
        body = text.split("}}", 1)[1]
        body = re.split(r"(?mi)^==|^\[\[Kategori:", body)[0]
        body = re.sub(r"<ref\b[^>]*>.*?</ref>|\{\{[^{}]*\}\}", " ", body, flags=re.S|re.I)
        body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"\[\[(?:[^]|]+\|)?([^]]+)\]\]", r"\1", body)
        # Join short lines of dialogue into nonoverlapping passages.
        words = html.unescape(body.replace("''","")).split()
        for i in range(0, len(words), 125):
            p = " ".join(words[i:i+125])
            if re.search(r"https?://|\{\{|\[\[", p):
                continue
            yield make(p, "tr", 0, "Vikikaynak", f"{rev['revid']}:words:{i}", "ws:Ömer Seyfettin",
                       "fiction", f"https://tr.wikisource.org/w/index.php?oldid={rev['revid']}",
                       authors=["Ömer Seyfettin"], title=page["title"], revision_date=rev["timestamp"])


def conversations():
    for path in sorted(CACHE.glob("se-*.json")):
        site = path.stem.split("-")[1]
        for r in json.loads(path.read_text(encoding="utf-8"))["items"]:
            owner = r["owner"]
            if (not owner.get("account_id") or owner.get("user_type") != "registered" or r["score"] < 2
                    or max(r["last_activity_date"], r.get("last_edit_date", 0)) > 1514764799
                    or not r.get("content_license")):
                continue
            body = re.sub(r"<(blockquote|pre|table)\b[^>]*>.*?</\1>", " ", r["body"], flags=re.S|re.I)
            body = html.unescape(re.sub(r"<[^>]*>", " ", body))
            host = f"https://{site}.stackexchange.com"
            url = f"{host}/a/{r['answer_id']}"
            yield make(body, "en", 0, "Stack Exchange", url, f"{host}/q/{r['question_id']}", site, url,
                       authors=[html.unescape(owner["display_name"])], author_key=f"stackexchange:{owner['account_id']}",
                       author_url=owner["link"], license=r["content_license"],
                       publication_date=datetime.fromtimestamp(r["creation_date"], timezone.utc).date().isoformat())


def synthetic_tr():
    paths = [(ROOT / "kaynaklar/AI/cturan/turkish-synthetic-corpus/tr_corpus.jsonl","cturan",CTURAN),
             (ROOT / "kaynaklar/AI/Uunan/turkish-knowledge-sft/chatml_dataset.jsonl","Uunan",UUNAN)]
    for path, source, revision in paths:
        seen = set()
        with path.open("rb") as f:
            while line := f.readline():
                r = json.loads(line)
                if source == "cturan":
                    text, topic_text, key = r["text"], r["text"], r["id"]
                else:
                    msgs = r["messages"]
                    if len(msgs) < 2 or [m["role"] for m in msgs[:2]] != ["user","assistant"]:
                        continue
                    topic_text, text = (m["content"] for m in msgs[:2])
                    if not isinstance(topic_text, str) or not isinstance(text, str):
                        continue
                    key = hashlib.sha256(normalized(topic_text).encode()).hexdigest()
                if key in seen or not 50 <= len(text.split()) <= 1000 or "```" in text:
                    continue
                match = TOPICS.search(topic_text)
                if not match:
                    continue
                seen.add(key)
                slug = "cturan/turkish-synthetic-corpus" if source == "cturan" else "Uunan/turkish-knowledge-sft"
                yield make(text, "tr", 1, slug, f"byte:{f.tell()-len(line)}", key, match[0].lower(),
                           f"https://huggingface.co/datasets/{slug}/tree/{revision}", source_revision=revision)
                if len(seen) >= 4500:
                    break


def synthetic_en(base):
    prefix = (CACHE / "tiny-prefix.txt").read_bytes()
    for i, raw in enumerate(prefix.split(b"<|endoftext|>")[:-1]):
        yield make(raw.decode("utf-8-sig"), "en", 1, "TinyStories", f"prefix:story:{i}", f"tiny:{i}",
                   "short_story", f"https://huggingface.co/datasets/roneneldan/TinyStories/tree/{TINY}",
                   generator="GPT-4", source_file="TinyStoriesV2-GPT4-train.txt", source_revision=TINY)
    known_ids = {r["source_record"] for r in base if r["source"] == "RAID"}
    known_titles, best = set(), {}
    with (ARCHIVES / "raid_train_none.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["domain"], normalized(r["title"]))
            if r["id"] in known_ids:
                known_titles.add(key)
            if r["domain"] not in ("books","recipes","reviews","news") or not key[1] or r["model"]=="human" or r["attack"]!="none":
                continue
            if not 50 <= len(r["generation"].split()) <= 1000:
                continue
            if key not in best or r["id"] < best[key]["id"]:
                best[key] = r
    for key, r in best.items():
        if key not in known_titles:
            yield make(r["generation"], "en", 1, "RAID", r["id"], "raid:"+":".join(key), key[0],
                       "https://github.com/liamdugan/raid", generator=r["model"], title=r["title"])


def build():
    snapshot = json.loads((DATA / "general_v6_sources.json").read_bytes())
    for item in snapshot["cache_files"]:
        with (CACHE / item["file"]).open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != item["sha256"]:
                raise ValueError(f"Source snapshot differs: {item['file']}")
    for relative, digest in snapshot["existing_archives"].items():
        with (ROOT / relative).open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != digest:
                raise ValueError(f"Source archive differs: {relative}")
    with (DATA / "detector_v6_control.jsonl").open(encoding="utf-8") as f:
        base = list(map(json.loads,f))
    known_groups = {r.get("group_id") for r in base}
    known_authors = {r.get("author_key") for r in base}
    pool = []
    for source in (news(), literature(), conversations(), synthetic_tr(), synthetic_en(base)):
        for r in source:
            if (50 <= r["word_count"] <= 1000 and r["group_id"] not in known_groups
                    and (not r.get("author_key") or r["author_key"] not in known_authors)):
                pool.append(r)
    keys = {k for r in pool for k in phrases(r["text"])}
    blocked = set()
    for texts in (reference_texts(), (r["text"] for r in base),
                  (json.loads(line)["text"] for line in (DATA/"verified_english_academic_holdout.jsonl").read_text(encoding="utf-8").splitlines())):
        for text in texts:
            blocked.update(k for k in phrases(text) if k in keys)
    del keys
    buckets = defaultdict(list)
    for r in sorted(pool, key=lambda r:r["id"]):
        partition = r.get("author_key") or r["group_id"]
        reserve = int(hashlib.sha256(partition.encode()).hexdigest()[:8],16) % 5 == 0
        if r["source"]=="Project Gutenberg":
            reserve = r["book"] in ("1260","55")
        if r["source"]=="Vikikaynak":
            reserve = False
        buckets[reserve,r["source"]].append(r)
    quotas = {"en": [("Project Gutenberg",600),("Stack Exchange",400),("TinyStories",500),("RAID",500)],
              "tr": [("Vikikaynak",100),("BilCat",900),("cturan/turkish-synthetic-corpus",500),
                     ("Uunan/turkish-knowledge-sft",500)]}
    result = {False:[], True:[]}
    authors, threads = set(), set()
    for reserve, rows in result.items():
        for lang, specs in quotas.items():
            story_shortage = 0
            for src, n in specs:
                limit = n//10 if reserve else n
                if src=="BilCat":
                    limit += story_shortage
                added = 0
                for r in buckets[reserve,src]:
                    if r.get("author_key") in authors or (src=="Stack Exchange" and r["group_id"] in threads):
                        continue
                    sh = set(phrases(r["text"]))
                    if not blocked.isdisjoint(sh):
                        continue
                    blocked.update(sh)
                    if src=="Stack Exchange":
                        authors.add(r["author_key"])
                        threads.add(r["group_id"])
                    rows.append(r)
                    added += 1
                    if added==limit:
                        break
                if added < limit and src != "Vikikaynak":
                    raise ValueError(f"Insufficient records: {src} {reserve} {added}/{limit}")
                if src=="Vikikaynak":
                    story_shortage = limit-added
        assert Counter((r["language"],r["label"]) for r in rows) == {
            (lang,label): 100 if reserve else 1000 for lang in ("en","tr") for label in (0,1)}
    extra, holdout = result[False], result[True]
    assert {r["group_id"] for r in extra}.isdisjoint(r["group_id"] for r in holdout)
    write_records(DATA / "general_v6_train.jsonl", extra)
    write_records(DATA / "general_v6_holdout.jsonl", holdout)
    write_records(DATA / "detector_v6.jsonl", base + [dict(r,split="train",split_group=r["group_id"]) for r in extra])
    for name, digest in snapshot["output_sha256"].items():
        with (DATA / name).open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != digest:
                raise ValueError(f"Unexpected output snapshot: {name}")
    print(Counter(r["source"] for r in extra), flush=True)


if __name__ == "__main__":
    build()
