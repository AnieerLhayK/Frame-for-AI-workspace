from pathlib import Path
from tempfile import TemporaryDirectory
import json
import hashlib
import subprocess
import sys
import unittest

from scripts.workspace.harness_library import capture_candidates, check_sources


class HarnessLibraryTests(unittest.TestCase):
    def test_capture_keeps_candidate_unreviewed_and_preserves_sources(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'guide.md').write_text('local', encoding='utf-8')
            catalog = {'sources': [{'id': 'guide', 'kind': 'local', 'path': 'guide.md'},
                                   {'id': 'official', 'kind': 'url', 'url': 'https://developers.openai.com/example'}]}
            result = capture_candidates(catalog, root, fetcher=lambda _: 'remote')
            self.assertEqual(result['status'], 'pending_review')
            self.assertEqual(result['sources']['guide'], 'local')
            self.assertEqual(result['sources']['official'], 'remote')
            self.assertFalse(result['activation_performed'])

    def test_capture_rejects_unapproved_urls_and_duplicate_ids(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'guide.md').write_text('local', encoding='utf-8')
            bad = {'sources': [{'id': 'outside', 'kind': 'url', 'url': 'https://example.org/private'}]}
            with self.assertRaisesRegex(ValueError, 'unapproved harness source URL'):
                capture_candidates(bad, root, fetcher=lambda _: self.fail('unexpected network request'))
            duplicate = {'sources': [{'id': 'guide', 'kind': 'local', 'path': 'guide.md'}] * 2}
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                capture_candidates(duplicate, root)
    def write_review(self, baseline: Path, source_id: str, content: str) -> None:
        snapshot_content = (baseline / f"{source_id}.txt").read_bytes().decode("utf-8")
        self.assertEqual(snapshot_content.replace("\r\n", "\n"), content)
        (baseline / "review.json").write_text(json.dumps({"status": "reviewed", "sources": {
            source_id: hashlib.sha256(snapshot_content.encode("utf-8")).hexdigest()
        }}), encoding="utf-8")

    def test_changed_source_produces_diff_without_replacing_reviewed_baseline(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("before\n", encoding="utf-8")
            baseline = root / "reviewed"
            baseline.mkdir()
            (baseline / "guide.txt").write_text("before\n", encoding="utf-8")
            self.write_review(baseline, "guide", "before\n")
            (root / "guide.md").write_text("after\n", encoding="utf-8")
            result = check_sources({"sources": [{"id": "guide", "kind": "local", "path": "guide.md"}]}, root, baseline)
            self.assertEqual(result["status"], "CHANGED")
            self.assertIn("-before", result["sources"][0]["diff"])
            self.assertIn("+after", result["sources"][0]["diff"])
            self.assertEqual((baseline / "guide.txt").read_text(encoding="utf-8"), "before\n")

    def test_workspace_source_cannot_escape_through_parent_path(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            (root.parent / "private.txt").write_text("secret", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes workspace"):
                check_sources({"sources": [{"id": "escape", "kind": "local", "path": "../private.txt"}]}, root, root)

    def test_missing_reviewed_snapshot_never_marks_source_as_approved(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("current\n", encoding="utf-8")
            result = check_sources({"sources": [{"id": "guide", "kind": "local", "path": "guide.md"}]}, root, root / "absent")
            self.assertEqual(result["status"], "UNREVIEWED")
            self.assertFalse(result["baseline_modified"])

    def test_official_remote_source_is_compared_without_updating_baseline(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "official.txt").write_text("reviewed\n", encoding="utf-8")
            self.write_review(root, "official", "reviewed\n")
            source = {"id": "official", "kind": "url", "url": "https://developers.openai.com/example"}
            result = check_sources({"sources": [source]}, root, root, online=True, fetcher=lambda url: "changed\n")
            self.assertEqual(result["status"], "CHANGED")
            self.assertIn("-reviewed", result["sources"][0]["diff"])
            self.assertIn("+changed", result["sources"][0]["diff"])
            self.assertEqual((root / "official.txt").read_text(encoding="utf-8"), "reviewed\n")

    def test_remote_source_is_not_fetched_without_explicit_online_mode(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = {"id": "official", "kind": "url", "url": "https://developers.openai.com/example"}
            (root / "official.txt").write_text("reviewed\n", encoding="utf-8")
            self.write_review(root, "official", "reviewed\n")
            def no_fetch(_):
                raise AssertionError("offline check attempted a network request")
            result = check_sources({"sources": [source]}, root, root, fetcher=no_fetch)
            self.assertEqual(result["status"], "NOT_CHECKED")

    def test_remote_source_rejects_nonofficial_host_before_fetch(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = {"id": "outside", "kind": "url", "url": "https://example.org/private"}
            with self.assertRaisesRegex(ValueError, "unapproved harness source URL"):
                check_sources({"sources": [source]}, root, root, online=True, fetcher=lambda _: "unexpected")

    def test_check_command_reports_drift_without_mutating_sources(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("new\n", encoding="utf-8")
            (root / "guide.txt").write_text("reviewed\n", encoding="utf-8")
            self.write_review(root, "guide", "reviewed\n")
            catalog = root / "sources.yaml"
            catalog.write_text("sources:\n  - {id: guide, kind: local, path: guide.md}\n", encoding="utf-8")
            repo = Path(__file__).resolve().parents[3]
            result = subprocess.run([sys.executable, "-X", "utf8", "-B", "-m", "scripts.workspace.harness_library", "check", "--root", str(root), "--catalog", str(catalog), "--baseline", str(root), "--format", "json"], cwd=repo, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "CHANGED")
            self.assertEqual((root / "guide.txt").read_text(encoding="utf-8"), "reviewed\n")

    def test_empty_source_catalog_cannot_report_up_to_date(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "must contain sources"):
                check_sources({"sources": []}, root, root)

    def test_pending_candidate_is_not_reported_as_reviewed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("same\n", encoding="utf-8")
            (root / "guide.txt").write_text("same\n", encoding="utf-8")
            (root / "candidate.json").write_text('{"status":"pending_review"}', encoding="utf-8")
            result = check_sources({"sources": [{"id": "guide", "kind": "local", "path": "guide.md"}]}, root, root)
            self.assertEqual(result["status"], "UNREVIEWED")
            self.assertFalse(result["baseline_modified"])

    def test_pending_candidate_still_reports_a_source_diff(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'guide.md').write_text('new\n', encoding='utf-8')
            (root / 'guide.txt').write_text('old\n', encoding='utf-8')
            result = check_sources({'sources': [{'id': 'guide', 'kind': 'local', 'path': 'guide.md'}]}, root, root)
            self.assertEqual(result['status'], 'UNREVIEWED')
            self.assertTrue(result['sources'][0]['changed'])
            self.assertIn('+new', result['sources'][0]['diff'])

    def test_changed_snapshot_invalidates_review_marker(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("replacement\n", encoding="utf-8")
            (root / "guide.txt").write_text("reviewed\n", encoding="utf-8")
            self.write_review(root, "guide", "reviewed\n")
            (root / "guide.txt").write_text("replacement\n", encoding="utf-8")
            result = check_sources({"sources": [{"id": "guide", "kind": "local", "path": "guide.md"}]}, root, root)
            self.assertEqual(result["status"], "UNREVIEWED")
            self.assertFalse(result["sources"][0]["reviewed"])
