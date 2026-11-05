import unittest
import summarize as s

ROWS = [
    {"rep": "R1", "event": "quiz_before", "value": "5", "note": ""},
    {"rep": "R1", "event": "quiz_after", "value": "8", "note": ""},
    {"rep": "R1", "event": "green_used", "value": "Tighten your draft", "note": ""},
    {"rep": "R2", "event": "green_used", "value": "tighten your draft", "note": ""},
    {"rep": "R2", "event": "slip_caught", "value": "x", "note": ""},
    {"rep": "R2", "event": "quiz_before", "value": "6", "note": ""},
]


class T(unittest.TestCase):
    def test_counts(self):
        r = s.summarize(ROWS)
        self.assertEqual((r["R1"]["before"], r["R1"]["after"]), (5, 8))
        self.assertEqual(r["R2"]["slips"], 1)

    def test_same_use_case_counted_once_across_reps(self):
        self.assertIn("Different green use cases tried (all reps): 1", s.report(s.summarize(ROWS)))

    def test_missing_after_score_not_invented(self):
        self.assertIn("R2: 6 -> n/a", s.report(s.summarize(ROWS)))

    def test_bad_score_rejected(self):
        with self.assertRaises(ValueError):
            s.summarize([{"rep": "R1", "event": "quiz_before", "value": "11", "note": ""}])


if __name__ == "__main__":
    unittest.main()
