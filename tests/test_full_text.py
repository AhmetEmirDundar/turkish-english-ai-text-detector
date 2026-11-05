import unittest
from types import SimpleNamespace

import numpy as np
import torch
from transformers import AutoTokenizer

from detector import BATCH_SIZE, DEFAULT_MODEL, MAX_TOKENS, Detector, windows


class FullTextTests(unittest.TestCase):
    def test_words_covered_in_order_including_remainder(self):
        for length in (50, 51, 99, 100, 151, 1234):
            words = [f"word{i}" for i in range(length)]
            pieces = windows(" \n".join(words))
            self.assertEqual(" ".join(pieces).split(), words)
            self.assertEqual(len(pieces), (length + 49) // 50)
        with self.assertRaises(ValueError):
            windows("short " * 49)

    def test_partial_window_has_proportional_weight(self):
        detector = Detector.__new__(Detector)
        detector.settings = {"model": "tfidf"}
        detector.model = SimpleNamespace(decision_function=lambda batch: np.array(
            [float("marker" in piece) for piece in batch]))
        pieces = windows("word " * (50 * BATCH_SIZE) + "marker")
        self.assertAlmostEqual(detector.document_logit(pieces), 1 / (50 * BATCH_SIZE + 1))

    def test_transformer_receives_every_content_token(self):
        detector = Detector.__new__(Detector)
        detector.device = "cpu"
        detector.tokenizer = AutoTokenizer.from_pretrained(
            DEFAULT_MODEL / "xlmr", local_files_only=True, fix_mistral_regex=False)
        seen = []

        def record(input_ids, attention_mask):
            self.assertLessEqual(len(input_ids), BATCH_SIZE)
            for ids, mask in zip(input_ids, attention_mask):
                self.assertLessEqual(int(mask.sum()), MAX_TOKENS)
                seen.extend(ids[mask.bool()][1:-1].tolist())
            return SimpleNamespace(logits=torch.zeros(len(input_ids), 2))

        detector.model = record
        pieces = windows("olağanüstüuzunbirsözcük " * 51)
        expected = detector.tokenizer(pieces, add_special_tokens=False)["input_ids"]
        self.assertGreater(len(expected[0]), MAX_TOKENS)
        np.testing.assert_array_equal(detector.transformer_piece_logits(pieces), [0, 0])
        self.assertEqual(seen, expected[0] + expected[1])


if __name__ == "__main__":
    unittest.main()
