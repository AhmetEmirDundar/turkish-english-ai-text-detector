"""A compact bilingual classifier based on document-level writing patterns."""
import math
import re
import unicodedata
from collections import Counter
from statistics import mean, pstdev


WORDS = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
SENTENCE_BREAK = re.compile(r"[.!?…]+|[\r\n]+")
MIN_STYLE_WORDS = 50
FEATURES = (
    "mean_word_length", "word_length_sd", "long_word_share",
    "mean_sentence_length", "sentence_length_cv", "repeated_opening_share",
    "local_vocabulary_diversity", "repeated_bigram_share",
    "commas_per_word", "other_punctuation_per_word", "questions_per_word",
)


def style_features(text):
    text = unicodedata.normalize("NFC", text)
    sentences = [tokens for part in SENTENCE_BREAK.split(text)
                 if (tokens := WORDS.findall(part))]
    words = [word.casefold() for sentence in sentences for word in sentence]
    if len(words) < MIN_STYLE_WORDS:
        return None
    n = len(words)
    lengths = [len(w) for w in words]
    sentence_lengths = [len(s) for s in sentences]
    openings = {s[0].casefold() for s in sentences}
    # Fixed-size blocks reduce the dependence of type/token ratios on text length.
    vocabulary_size = sum(len(set(words[i:i + 50])) for i in range(0, n, 50))
    pairs = Counter((a.casefold(), b.casefold()) for s in sentences for a, b in zip(s, s[1:]))
    pair_count = sum(pairs.values())
    return (
        mean(lengths), pstdev(lengths), sum(v >= 8 for v in lengths) / n,
        mean(sentence_lengths), pstdev(sentence_lengths) / mean(sentence_lengths),
        1 - len(openings) / len(sentences), vocabulary_size / n,
        (pair_count - len(pairs)) / max(1, pair_count),
        text.count(",") / n, sum(text.count(c) for c in ";:()—") / n, text.count("?") / n,
    )


def style_label(score, settings):
    if score >= settings["threshold"]:
        return "AI"
    if score <= settings["human_threshold"]:
        return "İnsan"
    return "Belirsiz"


def style_prediction(text, settings, primary_label):
    features = style_features(text)
    if features is None:
        return {"status": "insufficient_text"}
    logit = settings["intercept"] + sum(
        weight * value for weight, value in zip(settings["weights"], features, strict=True))
    score = 1 / (1 + math.exp(-max(-50, min(50, logit))))
    label = style_label(score, settings)
    return {"status": "ok", "ai_score": round(score, 6), "threshold": settings["threshold"],
            "human_threshold": settings["human_threshold"], "label": label,
            "agreement": None if label == "Belirsiz" else label == primary_label,
            "mean_sentence_length": round(features[FEATURES.index("mean_sentence_length")], 1)}
