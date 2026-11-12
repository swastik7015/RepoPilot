import tempfile
import unittest
from pathlib import Path
from repopilot.analyzer import analyze_repository

class AnalyzerTests(unittest.TestCase):
    def test_empty_repository_has_zero_score(self):
        with tempfile.TemporaryDirectory() as folder:
            report = analyze_repository(folder)
            self.assertEqual(report["score"], 0)
            self.assertEqual(report["maximum_score"], 100)

    def test_complete_repository_scores_100(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("# Demo")
            (root / "LICENSE").write_text("MIT")
            (root / "CONTRIBUTING.md").write_text("# Contributing")
            (root / "pyproject.toml").write_text("[project]")
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("# test")
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "test.yml").write_text("name: test")

            report = analyze_repository(folder)
            self.assertEqual(report["score"], 100)
            self.assertEqual(report["rating"], "Excellent")

    def test_missing_directory_raises_error(self):
        with self.assertRaises(ValueError):
            analyze_repository("this-folder-does-not-exist-12345")

if __name__ == "__main__":
    unittest.main()
