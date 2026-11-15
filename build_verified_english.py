"""Extract auditable English passages from Europe PMC articles and historical Python PEPs."""
import hashlib
import json
import re
import zipfile
import argparse
from datetime import datetime
from email.parser import Parser
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from openpyxl import load_workbook

from build_education_data import DATA, ROOT, normalized, phrases, reference_texts

CACHE = ROOT / ".training_cache/english_academic"
CC_BY = re.compile(r"https?://creativecommons\.org/licenses/by/(\d\.\d)/")
PEP_REV = "6905c6ce669f4792f08149102b87b9ea9ec339b4"


def plain(element):
    return " ".join("".join(element.itertext()).split())


def extract(source):
    pmcid = source["pmcid"]
    xml = (CACHE / f"{pmcid}.xml").read_bytes()
    root = ET.fromstring(xml)
    meta = root.find("./front/article-meta")
    if meta is None or root.get("article-type") != "research-article" or root.get(
            "{http://www.w3.org/XML/1998/namespace}lang") != "en":
        return []
    ids = {e.get("pub-id-type"): e.text for e in meta.findall("article-id")}
    if ids.get("pmcid") != pmcid or ids.get("doi", "").lower() != source["doi"].lower():
        return []
    dates = [int(e.text) for e in meta.findall("pub-date/year") if e.text and e.text.isdecimal()]
    if not dates or min(dates) != int(source["date"][:4]) or max(dates) > 2017:
        return []
    licenses = meta.find("permissions/license")
    if licenses is None or not (license_url := CC_BY.search(ET.tostring(licenses, encoding="unicode"))):
        return []
    authors = []
    for name in meta.findall(".//contrib[@contrib-type='author']/name"):
        surname, given = name.findtext("surname"), name.findtext("given-names")
        if given and surname:
            authors.append(f"{given} {surname}")
    title = meta.find("title-group/article-title")
    if not authors or title is None:
        return []
    result = []
    for i, p in enumerate(root.findall("./body//sec/p")):
        if any(p.find(".//" + tag) is not None for tag in ("table", "fig", "disp-formula", "disp-quote")):
            continue
        text = plain(p)
        if not 60 <= len(text.split()) <= 350:
            continue
        uid = hashlib.sha256(normalized(text).encode()).hexdigest()
        result.append({"id": uid, "language": "en", "label": 0, "text": text,
                       "word_count": len(text.split()), "source": "Europe PMC", "group_id": pmcid,
                       "title": plain(title), "authors": authors, "publication_date": source["date"],
                       "journal": source["journal"], "doi": source["doi"],
                       "source_url": f"https://europepmc.org/articles/{pmcid}",
                       "license_url": license_url.group(), "source_record": f"body//sec/p[{i}] (zero-based)",
                       "source_sha256": hashlib.sha256(xml).hexdigest(),
                       "authorship_evidence": "Named authors and original publication date in archival metadata"})
    return sorted(result, key=lambda r: r["id"])


def reference_passages():
    yield from reference_texts()
    for name in ("technical_education_v4_addition.jsonl", "balanced_v5_addition.jsonl"):
        with (DATA / name).open(encoding="utf-8") as f:
            for row in map(json.loads, f):
                yield row["text"]
    workbook = load_workbook(ROOT / "kaynaklar/gercek_yasam/bagimsiz_test/external_eng.xlsx", read_only=True)
    try:
        for text, *_ in workbook.active.iter_rows(min_row=2, values_only=True):
            if isinstance(text, str):
                yield text
    finally:
        workbook.close()


def pep_documents():
    with zipfile.ZipFile(CACHE / f"peps-{PEP_REV}.zip") as archive:
        for path in sorted(archive.namelist()):
            name = path.split("/")[-1]
            if not re.fullmatch(r"pep-\d{4}\.(?:rst|txt)", name):
                continue
            raw = archive.read(path)
            text = raw.decode("utf-8-sig", errors="replace")
            if "\ufffd" in text:
                continue
            headers = Parser().parsestr(text, headersonly=True)
            # Require a document-specific public-domain notice and named authors.
            notice = re.search(r"(?ims)^Copyright\s*\n[-=]*\s*\n([^\n]+public domain[^\n]*)", text)
            if not notice or not all(headers.get(k) for k in ("Author", "Created", "Title", "PEP")):
                continue
            names = re.sub(r"<[^>]+>|\([^)]*\)", "", headers["Author"])
            authors = [" ".join(n.split()) for n in re.split(r",|\s+and\s+", names) if n.strip()]
            if not authors or any(not re.fullmatch(r"[\w .'’-]+", n) or len(n.split()) < 2 for n in authors):
                continue
            try:
                created = datetime.strptime(headers["Created"].strip(), "%d-%b-%Y").date()
            except ValueError:
                continue
            if created.year > 2017:
                continue
            result = []
            for i, p in enumerate(re.split(r"\n\s*\n", text[:notice.start()])):
                if not 60 <= len(p.split()) <= 350 or any(line.startswith(
                        (" ", "\t", "..", ">>>", "#")) for line in p.splitlines()):
                    continue
                if re.search(r"https?://|\n[-=*]{3,}", p):
                    continue
                passage = " ".join(p.split())
                uid = hashlib.sha256(normalized(passage).encode()).hexdigest()
                url = f"https://github.com/python/peps/blob/{PEP_REV}/{name}"
                result.append({"id": uid, "language": "en", "label": 0, "text": passage,
                               "word_count": len(passage.split()), "source": "Python PEP",
                               "group_id": "pep:" + headers["PEP"], "title": headers["Title"],
                               "authors": authors, "creation_date": created.isoformat(), "source_url": url,
                               "license": notice[1].strip(), "source_record": f"paragraph:{i}",
                               "source_sha256": hashlib.sha256(raw).hexdigest(),
                               "authorship_evidence": "Named authors in a pinned pre-2018 source revision"})
            if result:
                yield sorted(result, key=lambda r: r["id"])


def build(download=False):
    manifest = json.loads((DATA / "verified_english_sources.json").read_bytes())
    if manifest["pep_revision"] != PEP_REV:
        raise ValueError("Unexpected PEP revision")
    CACHE.mkdir(parents=True, exist_ok=True)
    book = CACHE / f"peps-{PEP_REV}.zip"
    if download and not book.is_file():
        with urlopen(f"https://codeload.github.com/python/peps/zip/{PEP_REV}", timeout=60) as response:
            book.write_bytes(response.read())
    groups = []
    for row in manifest["europe_pmc"]:
        pmcid = row["pmcid"]
        if not re.fullmatch(r"PMC\d+", pmcid):
            raise ValueError("Invalid article identifier")
        path = CACHE / f"{pmcid}.xml"
        if download and not path.is_file():
            with urlopen(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", timeout=45) as response:
                raw = response.read()
            if hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError(f"{pmcid}: archive revision changed")
            path.write_bytes(raw)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"{pmcid}: source hash mismatch")
        groups.append(extract(row))
    groups.extend(pep_documents())
    keys = {k for group in groups for r in group for k in phrases(r["text"])}
    blocked = set()
    for text in reference_passages():
        blocked.update(k for k in phrases(text) if k in keys)
    by_split = {"train": [], "holdout": []}
    seen_names = set()
    for group in groups:
        if not group:
            continue
        names = {normalized(n) for n in group[0]["authors"]}
        if not seen_names.isdisjoint(names):
            continue
        accepted = []
        for row in group:
            shingles = set(phrases(row["text"]))
            if not shingles.isdisjoint(blocked):
                continue
            blocked.update(shingles)
            accepted.append(row)
            if len(accepted) == 8:
                break
        if accepted:
            seen_names.update(names)
            document_hash = hashlib.sha256(group[0]["group_id"].encode()).digest()
            split = "holdout" if int.from_bytes(document_hash[:4], "big") % 5 == 0 else "train"
            by_split[split].extend(accepted)
    if not all(by_split.values()):
        raise ValueError("Both article-disjoint partitions must contain passages.")
    for split, rows in by_split.items():
        dest = DATA / f"verified_english_academic_{split}.jsonl"
        temp = dest.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if hashlib.sha256(temp.read_bytes()).hexdigest() != manifest["output_sha256"][split]:
            raise ValueError(f"{split}: output does not match the verified snapshot")
        temp.replace(dest)
        print(split, len(rows), "passages from", len({r["group_id"] for r in rows}), "documents")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download missing source archives")
    build(parser.parse_args().download)
