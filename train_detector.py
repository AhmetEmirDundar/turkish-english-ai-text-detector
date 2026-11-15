"""Train and evaluate the bilingual detector from the two project JSONL files."""
import argparse
import hashlib
import json
import random
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from detector import MAX_TOKENS, ROOT, WINDOW_WORDS, probability
from calibrate_fusion import calibrate_fusion
from style_analysis import FEATURES, style_features, style_label

SEED = 42
BASE_ID = "FacebookAI/xlm-roberta-base"
REVISION = "e73636d4f797dec63c3081bb6ed5c7b0bb3f2089"
FILES = ["ai_texts_tr_en_10000.jsonl", "human_texts_tr_en_10000.jsonl"]
ENGLISH_ADDITION = "human_texts_en_nonacademic_10000.jsonl"
REALWORLD_ADDITION = "realworld_v3_addition.jsonl"
EDUCATION_ADDITION = "technical_education_v4_addition.jsonl"
BALANCED_ADDITION = "balanced_v5_addition.jsonl"
V1_MODEL = ROOT / "models" / "detector_v1"
V2_MODEL = ROOT / "models" / "detector_v2"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def training_windows(text):
    """Reproduce the sampling used to train and calibrate the released models."""
    words = text.split()
    last = len(words) - WINDOW_WORDS
    if last < 0:
        raise ValueError(f"Eğitim metni en az {WINDOW_WORDS} sözcük içermeli.")
    return [" ".join(words[start:start + WINDOW_WORDS]) for start in sorted({0, last // 2, last})]


def split_records(rows, stratify_genre=False):
    # Connected components keep articles, shared named authors, and overlapping text together.
    parent = list(range(len(rows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    known, phrases = {}, {}
    for i, row in enumerate(rows):
        keys = ([("account", row["author_key"])] if row.get("author_key") else
                [("author", normalize(a)) for a in row.get("authors", [])])
        if row.get("group_id"):
            keys.append(("article", row["group_id"]))
        for key in keys:
            parent[root(i)] = root(known.setdefault(key, i))
        for part in row["pieces"]:
            words = normalize(part).split()
            for j in range(len(words) - 17):
                # Hash collisions conservatively put unrelated records in the same split.
                key = hash(tuple(words[j:j + 18]))
                parent[root(i)] = root(phrases.setdefault(key, i))
    groups = defaultdict(list)
    for i in range(len(rows)):
        groups[root(i)].append(i)
    strata = [(r["language"], r["source"], r["label"], r.get("genre")) if stratify_genre
              else (r["language"], r["source"]) for r in rows]
    sizes = Counter(strata)
    sets = {k: Counter() for k in ("train", "validation", "test")}
    ratios = {"train": .70, "validation": .15, "test": .15}
    components = list(groups.values())
    random.Random(SEED).shuffle(components)
    components.sort(key=len, reverse=True)
    for members in components:
        counts = Counter(strata[i] for i in members)
        def cost(name):
            return sum((2 * sets[name][k] * n + n * n) / (sizes[k] * ratios[name]) for k, n in counts.items())
        split = min(sets, key=cost)
        sets[split].update(counts)
        group = min(rows[i]["id"] for i in members)
        for i in members:
            rows[i].update(split=split, split_group=group)


def prepare(output, version):
    rows, hashes = [], {}
    legacy_test = []
    prior = {}
    if version in ("v6_control", "v6"):
        filename = f"detector_{version}.jsonl"
        data = (ROOT / "data" / filename).read_bytes()
        hashes[filename] = hashlib.sha256(data).hexdigest()
        rows = list(map(json.loads, data.splitlines()))
        if len(rows) != len({r["id"] for r in rows}):
            raise ValueError("Duplicate candidate record")
        with (ROOT / "models/detector_v5/splits.jsonl").open(encoding="utf-8") as f:
            frozen = {r["id"]:(r["split"],r["split_group"]) for r in map(json.loads,f) if r["split"] != "train"}
        if {r["id"]:(r["split"],r["split_group"]) for r in rows if r["split"] != "train"} != frozen:
            raise ValueError("Candidate evaluation split differs from V5")
        for row in rows:
            row["pieces"] = training_windows(row["text"])
        return save_splits(output, rows, hashes, legacy_test)
    if version != "v1":
        with (V1_MODEL / "splits.jsonl").open(encoding="utf-8") as f:
            prior = {r["id"]: r for r in map(json.loads, f)}
    parent_splits = {}
    filenames = list(FILES)
    if version != "v1":
        filenames.append(ENGLISH_ADDITION)
    if version in ("v3", "v4", "v5"):
        parent = V2_MODEL if version == "v3" else ROOT / "models/detector_v3"
        with (parent / "splits.jsonl").open(encoding="utf-8") as f:
            parent_splits = {r["id"]:r for r in map(json.loads, f)}
        filenames.append(REALWORLD_ADDITION)
    if version in ("v4", "v5"):
        filenames.append(EDUCATION_ADDITION)
    if version == "v5":
        filenames.append(BALANCED_ADDITION)
    for filename in filenames:
        path = ROOT / "data" / filename
        data = path.read_bytes()
        hashes[filename] = hashlib.sha256(data).hexdigest()
        for line in data.splitlines():
            row = json.loads(line)
            row["pieces"] = training_windows(row["text"])
            if version != "v1" and filename in FILES:
                prev = prior[row["id"]]
                assert (row["language"],row["label"]) == (prev["language"],prev["label"])
                row.update(split=prev["split"], split_group=prev["split_group"])
                if row["split"] == "test":
                    legacy_test.append(row)
                if row["language"] == "en" and row["label"] == 0:
                    continue
            if filename in (EDUCATION_ADDITION, BALANCED_ADDITION):
                row.update(split="train", split_group=row["group_id"])
            elif version in ("v4", "v5") or (version == "v3" and filename != REALWORLD_ADDITION):
                frozen = parent_splits[row["id"]]
                assert (frozen["language"],frozen["label"]) == (row["language"],row["label"])
                row.update(split=frozen["split"], split_group=frozen["split_group"])
            rows.append(row)
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate record ID")
    if version == "v5":
        counts = Counter((r["language"], r["label"]) for r in rows)
        if counts != {(lang, label): 12500 for lang in ("tr", "en") for label in (0, 1)}:
            raise ValueError(f"V5 sınıf sayıları beklenenden farklı: {counts}")
    split_records([r for r in rows if "split" not in r], stratify_genre=version == "v3")
    return save_splits(output, rows, hashes, legacy_test)


def save_splits(output, rows, hashes, legacy_test):
    splits = {s: [r for r in rows if r["split"] == s] for s in ("train", "validation", "test")}
    with (output / "splits.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps({k: row[k] for k in ("id", "split", "split_group", "language", "label")}) + "\n")
    assert sum(map(len, splits.values())) == len(rows)
    counts = {s: dict(Counter(f"{r['language']}:{r['label']}" for r in group)) for s, group in splits.items()}
    print("Split sizes", counts, flush=True)
    return splits, counts, hashes, legacy_test


def training_weights(rows, version):
    if version == "v1":
        return np.ones(len(rows))
    # Recent posts have account attribution and moderation, but no authorship declaration.
    reliability = np.array([.5 if r.get("period") == "recent" else 1. for r in rows])
    strata = [(r["language"], r["label"]) for r in rows]
    totals = Counter()
    for key, weight in zip(strata, reliability):
        totals[key] += weight
    return np.array([w * len(rows) / (len(totals) * totals[k]) for k,w in zip(strata,reliability)])


def metrics(labels, scores, threshold):
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(labels, pred, labels=[0, 1]).ravel().tolist()
    return {"n": len(labels), "accuracy": float(accuracy_score(labels, pred)),
            "macro_f1": float(f1_score(labels, pred, average="macro")),
            "ai_precision": float(precision_score(labels, pred, zero_division=0)),
            "ai_recall": float(recall_score(labels, pred, zero_division=0)),
            "human_false_positive_rate": fp / (fp + tn) if fp + tn else None,
            "tn": tn, "fp": fp, "fn": fn, "tp": tp,
            "brier_score": float(np.mean((scores - labels) ** 2))}


def evaluate(rows, logits, settings):
    labels = np.array([r["label"] for r in rows])
    scores = np.array([probability(v, settings) for v in logits])
    result = {"overall": metrics(labels, scores, settings["threshold"])}
    for lang in ("tr", "en"):
        mask = np.array([r["language"] == lang for r in rows])
        result[lang] = metrics(labels[mask], scores[mask], settings["threshold"])
    return result, scores


def calibrate(rows, logits):
    labels = np.array([r["label"] for r in rows])
    fit = LogisticRegression(C=100.0, max_iter=300).fit(logits.reshape(-1, 1), labels)
    settings = {"slope": float(fit.coef_[0, 0]), "intercept": float(fit.intercept_[0])}
    scores = np.array([probability(v, settings) for v in logits])
    floor = 0.
    for lang in ("tr", "en"):
        humans = sorted([s for r, s in zip(rows, scores) if r["language"] == lang and not r["label"]], reverse=True)
        floor = max(floor, float(np.nextafter(humans[int(.05 * len(humans))], np.inf)))
    thresholds = np.unique(np.r_[floor, np.linspace(floor, 1, 251)])
    threshold = max(thresholds, key=lambda t: f1_score(labels, scores >= t, average="macro"))
    settings["threshold"] = float(threshold)
    return settings


def train_style(splits, version, output):
    features, covered = {}, {}
    for split, rows in splits.items():
        covered[split], values = [], []
        for row in rows:
            vector = style_features(row["text"])
            if vector is not None:
                covered[split].append(row)
                values.append(vector)
        features[split] = np.array(values)
    weights = training_weights(covered["train"], version)
    scaler = StandardScaler().fit(features["train"], sample_weight=weights)
    classifier = LogisticRegression(max_iter=400, random_state=SEED)
    classifier.fit(scaler.transform(features["train"]), [r["label"] for r in covered["train"]],
                   sample_weight=weights)
    # Fold standardization and validation calibration into one linear function.
    coef = classifier.coef_[0] / scaler.scale_
    bias = classifier.intercept_[0] - np.dot(scaler.mean_, coef)
    logits = {s: features[s] @ coef + bias for s in ("validation", "test")}
    calibration = calibrate(covered["validation"], logits["validation"])
    validation_scores = [probability(v, calibration) for v in logits["validation"]]
    # Mirror the AI threshold's per-language error constraint for human calls.
    human_limit = min(0.5, calibration["threshold"])
    for lang in ("tr", "en"):
        ai = sorted(score for r, score in zip(covered["validation"], validation_scores)
                    if r["language"] == lang and r["label"] == 1)
        human_limit = min(human_limit, ai[int(.05 * len(ai))])
    settings = {
        "features": FEATURES, "weights": (coef * calibration["slope"]).tolist(),
        "intercept": bias * calibration["slope"] + calibration["intercept"],
        "threshold": calibration["threshold"],
        "human_threshold": float(np.nextafter(human_limit, -np.inf)),
    }
    write_json(output / "style.json", settings)
    report = {}
    for split in logits:
        labels = [style_label(probability(v, calibration), settings) for v in logits[split]]
        report[split] = {}
        for lang in ("overall", "tr", "en"):
            pairs = [(label, row["label"]) for row, label in zip(covered[split], labels)
                     if lang == "overall" or lang == row["language"]]
            report[split][lang] = {
                name: {"actual_ai": sum(label == name and actual == 1 for label, actual in pairs),
                       "actual_human": sum(label == name and actual == 0 for label, actual in pairs)}
                for name in ("AI", "İnsan", "Belirsiz")}
    report["excluded"] = {s: len(rows) - len(covered[s]) for s, rows in splits.items()}
    write_json(output / "style_metrics.json", report)
    print("Style test", report["test"]["overall"], flush=True)


def flatten(rows):
    texts = [p for r in rows for p in r["pieces"]]
    lengths = [len(r["pieces"]) for r in rows]
    return texts, lengths


def aggregate(pred, lengths):
    return np.add.reduceat(pred, np.cumsum([0] + lengths[:-1])) / lengths


def baseline(train, validation, out, weights):
    rng = random.Random(SEED)
    pipeline = make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=4,
                        max_features=45000, sublinear_tf=True, dtype=np.float32),
        LogisticRegression(C=4, max_iter=400, solver="liblinear", random_state=SEED))
    pipeline.fit([rng.choice(r["pieces"]) for r in train], [r["label"] for r in train],
                 logisticregression__sample_weight=weights)
    joblib.dump(pipeline, out / "tfidf.joblib", compress=3)
    def predict(rows):
        texts, lengths = flatten(rows)
        return aggregate(pipeline.decision_function(texts), lengths)
    logits = predict(validation)
    settings = calibrate(validation, logits)
    score = evaluate(validation, logits, settings)[0]
    print("Baseline validation", score["overall"], flush=True)
    return settings, score, predict


class Encoded:
    def __init__(self, rows, tokenizer):
        texts, self.lengths = flatten(rows)
        self.tokens = tokenizer(texts, truncation=True, padding="max_length", max_length=MAX_TOKENS, return_tensors="pt")
        self.offsets = np.cumsum([0] + self.lengths[:-1])
        self.labels = torch.tensor([r["label"] for r in rows])

    def batch(self, ids, device):
        mask = self.tokens["attention_mask"][ids]
        width = min(MAX_TOKENS, (int(mask.sum(1).max()) + 7) // 8 * 8)
        return {k: v[ids, :width].to(device) for k, v in self.tokens.items()}


@torch.inference_mode()
def transformer_logits(model, encoded, batch_size, device):
    model.eval()
    result = []
    total = sum(encoded.lengths)
    for start in range(0, total, batch_size):
        batch = encoded.batch(slice(start, start + batch_size), device)
        logits = model(**batch).logits
        result.extend((logits[:, 1] - logits[:, 0]).float().cpu().tolist())
    return aggregate(np.array(result), encoded.lengths)


def train_transformer(splits, base, out, args, device, weights):
    kwargs = {"local_files_only": True} if base.is_dir() else {"revision": REVISION}
    pretrained = str(base) if base.is_dir() else BASE_ID
    tok = AutoTokenizer.from_pretrained(pretrained, **kwargs)
    model = AutoModelForSequenceClassification.from_pretrained(pretrained, num_labels=2,
        id2label={0: "human", 1: "ai"}, label2id={"human": 0, "ai": 1}, **kwargs)
    model.roberta.requires_grad_(False)
    model.roberta.encoder.layer[-2:].requires_grad_(True)
    model.to(device)
    enc = {s: Encoded(splits[s], tok) for s in ("train", "validation")}
    train, validation = enc["train"], enc["validation"]
    weights = torch.as_tensor(weights, device=device, dtype=torch.float32)
    opt = torch.optim.AdamW([
        {"params": model.roberta.encoder.layer[-2:].parameters(), "lr": 2e-5},
        {"params": model.classifier.parameters(), "lr": 1e-4}], weight_decay=.01)
    batches = (len(train.labels) + args.batch_size - 1) // args.batch_size
    scheduler = get_linear_schedule_with_warmup(opt, int(.08 * batches * args.epochs), batches * args.epochs)
    use_bf16 = device.type == "cuda" and torch.cuda.is_bf16_supported()
    rng = np.random.default_rng(SEED)
    best = -1.
    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        # Frozen layers run without dropout; keep dropout in trainable layers and head.
        model.roberta.embeddings.eval()
        for layer in model.roberta.encoder.layer[:-2]:
            layer.eval()
        indices = rng.permutation(len(train.labels))
        start = time.monotonic()
        loss_sum = 0.
        for step, offset in enumerate(range(0, len(indices), args.batch_size), 1):
            docs = indices[offset:offset + args.batch_size]
            parts = train.offsets[docs] + np.array([rng.integers(train.lengths[i]) for i in docs])
            batch = train.batch(parts, device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16):
                logits = model(**batch).logits
                losses = torch.nn.functional.cross_entropy(logits, train.labels[docs].to(device), reduction="none")
                loss = (losses * weights[docs]).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
            scheduler.step()
            loss_sum += float(loss.detach())
            if step == 1 or step % 150 == 0 or step == batches:
                print(f"Epoch {epoch}/{args.epochs} batch {step}/{batches} mean loss {loss_sum/step:.4f} elapsed {time.monotonic()-start:.0f}s", flush=True)
        logits = transformer_logits(model, validation, args.batch_size, device)
        settings = calibrate(splits["validation"], logits)
        val = evaluate(splits["validation"], logits, settings)[0]
        history.append({"epoch": epoch, "loss": loss_sum/batches, "validation": val})
        print("XLM-R validation", epoch, val["overall"], flush=True)
        if val["overall"]["macro_f1"] > best:
            best = val["overall"]["macro_f1"]
            best_settings, best_val, best_epoch = settings, val, epoch
            model.save_pretrained(out / "xlmr")
            tok.save_pretrained(out / "xlmr")
    del model, opt, scheduler
    if device.type == "cuda":
        torch.cuda.empty_cache()
    model = AutoModelForSequenceClassification.from_pretrained(out / "xlmr", local_files_only=True).to(device)
    def predict(rows):
        return transformer_logits(model, Encoded(rows, tok), args.batch_size, device)
    return best_settings, best_val, predict, history, best_epoch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["v1","v2","v3","v4","v5","v6_control","v6"], default="v3")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--base-dir", type=Path, default=ROOT / ".training_cache" / "xlm-roberta-base")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--style-only", action="store_true", help="Train only the writing-style classifier")
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT / "models" / f"detector_{args.dataset}"
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Choose an empty output directory to keep earlier training runs intact.")
    args.output.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.set_num_threads(4)
    print("Device", torch.cuda.get_device_name(device) if device.type == "cuda" else device, flush=True)
    splits, counts, hashes, legacy_test = prepare(args.output, args.dataset)
    train_style(splits, args.dataset, args.output)
    if args.style_only:
        return
    weights = training_weights(splits["train"], args.dataset)
    val = splits["validation"]
    settings_b, val_b, predict_b = baseline(splits["train"], val, args.output, weights)
    settings_x, val_x, predict_x, history, epoch = train_transformer(splits, args.base_dir, args.output, args, device, weights)
    candidates = {"xlmr": (settings_x, val_x, predict_x), "tfidf": (settings_b, val_b, predict_b)}
    winner = max(candidates, key=lambda name: candidates[name][1]["overall"]["macro_f1"])
    report = {"dataset_version": args.dataset, "base": BASE_ID, "base_revision": REVISION, "seed": SEED, "input_sha256": hashes,
              "batch_size": args.batch_size, "epochs": args.epochs, "best_epoch": epoch,
              "split_counts": counts, "winner": winner, "training_history": history, "models": {}}
    tests = splits["test"]
    v2_test_ids = set()
    if args.dataset == "v3":
        with (V2_MODEL / "test_predictions.jsonl").open(encoding="utf-8") as f:
            v2_test_ids = {r["id"] for r in map(json.loads, f)}
    predictions = [{k: r[k] for k in ("id","language","label","source","split_group")} for r in tests]
    for name, (settings, validation, predict) in candidates.items():
        logits = predict(tests)
        metrics_test, scores = evaluate(tests, logits, settings)
        report["models"][name] = {"calibration": settings, "validation": validation, "test": metrics_test}
        if name == winner and legacy_test:
            report["legacy_v1_test"] = evaluate(legacy_test, predict(legacy_test), settings)[0]
            if v2_test_ids:
                keep = np.array([r["id"] in v2_test_ids for r in tests])
                assert keep.sum() == len(v2_test_ids)
                report["frozen_v2_test"] = evaluate([r for r,k in zip(tests,keep) if k], logits[keep], settings)[0]
            evidence = {}
            for period in ("historical","recent"):
                mask = np.array([r.get("period") == period for r in tests])
                fp = int((scores[mask] >= settings["threshold"]).sum())
                n = int(mask.sum())
                evidence[period] = {"human_texts": n, "false_positives": fp, "false_positive_rate": fp/n}
            report["english_nonacademic_test"] = evidence
        for row, score in zip(predictions, scores):
            row[name] = float(score)
    with (args.output/"test_predictions.jsonl").open("w", encoding="utf8") as f:
        for row in predictions:
            f.write(json.dumps(row)+"\n")
    write_json(args.output / "metrics.json", report)
    write_json(args.output / "detector.json", {"model": winner, **candidates[winner][0]})
    print("Selected", winner, "test", report["models"][winner]["test"], flush=True)
    del candidates, predict, predict_x
    calibrate_fusion(args.output)


if __name__ == "__main__":
    main()
