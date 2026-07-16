from __future__ import annotations
import unittest
from unittest.mock import patch
from scripts.merge_safety import assess

class MergeSafetyTests(unittest.TestCase):
    def test_disjoint_changes_are_safe(self) -> None:
        with patch("scripts.merge_safety.git", side_effect=["base", "M\ta.py", "A\tb.py"]):
            self.assertEqual(assess("", "left", "right")["status"], "SAFE_TO_CONTINUE")
    def test_structured_overlap_stops(self) -> None:
        with patch("scripts.merge_safety.git", side_effect=["base", "M\tconfig.yaml", "M\tconfig.yaml"]):
            result = assess("", "left", "right")
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(result["findings"][0]["category"], "structured_object")
if __name__ == "__main__": unittest.main()
