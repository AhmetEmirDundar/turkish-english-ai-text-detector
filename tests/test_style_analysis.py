import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from detector import Detector, combine_scores
from calibrate_fusion import fit_style_weight
from style_analysis import FEATURES, style_features, style_label, style_prediction


class StyleAnalysisTests(unittest.TestCase):
    def test_full_text_features_follow_repetitions_and_sentence_breaks(self):
        text = ("Çınar ağacı büyüyor. " * 50) + "Çınar ağacı gölge verdi!"
        features = dict(zip(FEATURES, style_features(text), strict=True))
        self.assertAlmostEqual(features["mean_sentence_length"], 154 / 51)
        self.assertAlmostEqual(features["repeated_opening_share"], 50 / 51)
        self.assertGreater(features["repeated_bigram_share"], 0.95)
        self.assertGreater(features["sentence_length_cv"], 0)

    def test_nonlinguistic_input_abstains(self):
        self.assertEqual(style_prediction("123 !!! " * 50, {}, "AI"), {"status": "insufficient_text"})
        self.assertIsNone(style_features("bir " * 49))
        self.assertIsNotNone(style_features("word " * 50))

    def test_style_support_changes_only_the_combined_result(self):
        text = "A short English sentence. " * 15
        with tempfile.TemporaryDirectory() as folder, patch("joblib.load") as load:
            path = Path(folder)
            settings = {"model": "tfidf", "threshold": 0.6, "slope": 1, "intercept": 0,
                        "style_weight": 0.15}
            (path / "detector.json").write_text(json.dumps(settings))
            load.return_value.decision_function.side_effect = lambda batch: np.ones(len(batch))
            original = Detector(path).predict(text)
            self.assertNotIn("style_analysis", original)
            style = {"features": FEATURES, "weights": [0] * len(FEATURES),
                     "intercept": -4, "human_threshold": 0.2, "threshold": 0.8}
            (path / "style.json").write_text(json.dumps(style))
            detector = Detector(path)
            result = detector.predict(text)
            self.assertEqual(result.keys(), original.keys())
            self.assertLess(result["ai_score"], original["ai_score"])
            self.assertLessEqual(original["ai_score"] - result["ai_score"], 0.15)
            detector.settings["threshold"] = 0.7
            self.assertEqual(detector.predict(text)["label"], "İnsan")
            detector.style["intercept"] = 4
            self.assertGreater(detector.predict(text)["ai_score"], original["ai_score"])
            detector.style["intercept"] = 0
            self.assertAlmostEqual(detector.predict(text)["ai_score"], 0.85 * original["ai_score"] + 0.15 * 0.5,
                                   places=5)
            self.assertEqual(detector.predict("123 " * 60)["ai_score"], original["ai_score"])

    def test_no_consensus_reported_between_thresholds(self):
        style = {"weights": [0] * len(FEATURES), "intercept": 0, "threshold": 0.8, "human_threshold": 0.2}
        support = style_prediction("bir " * 50, style, "AI")
        self.assertEqual(support["label"], "Belirsiz")
        self.assertIsNone(support["agreement"])
        self.assertEqual(style_label(0.2, style), "İnsan")
        self.assertEqual(style_label(0.8, style), "AI")

    def test_blend_is_symmetric_and_stays_on_the_same_scale(self):
        for primary in (0, 0.1, 0.5, 0.9, 1):
            for score in (0, 0.25, 0.5, 0.75, 1):
                result = combine_scores(primary, {"status": "ok", "ai_score": score}, 0.2)
                reverse = combine_scores(1 - primary, {"status": "ok", "ai_score": 1 - score}, 0.2)
                self.assertAlmostEqual(result, 1 - reverse)
                self.assertAlmostEqual(result, 0.8 * primary + 0.2 * score)

    def test_fit_minimizes_squared_error_with_primary_weight_at_least_half(self):
        base = np.array([0.25, 0.75])
        other = np.array([0.75, 0.25])
        self.assertAlmostEqual(fit_style_weight(base, other, np.array([0.35, 0.65])), 0.2)
        self.assertEqual(fit_style_weight(base, other, np.array([0, 1])), 0)
        self.assertEqual(fit_style_weight(base, other, np.array([1, 0])), 0.5)
        self.assertEqual(fit_style_weight(base, base, np.array([1, 0])), 0)
