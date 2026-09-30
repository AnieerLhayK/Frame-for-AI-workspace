from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.workspace import merge_safety as merge, task_records
from scripts.workspace import task_ledger
from argparse import Namespace


class MergeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.path = self.root / "records/2026/09/08/TASK-20260908-001.json"
        self.path.parent.mkdir(parents=True)
        self.record = task_records.initial_record("TASK-20260908-001", task_type="demo", started_at="2026-09-08T00:00:00Z", tokens_estimated=1, operations=["workspace_write"])
        self.write_record()
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("checkout", "-b", "dev")
        (self.root / "source.txt").write_text("complete work")
        self.git("add", ".")
        self.git("commit", "-m", "feature")
        for obj, attr, value in [(merge,"ROOT",self.root),(task_records,"ROOT",self.root),(task_records,"RECORD_ROOT",self.root/"records"),(task_ledger,"DESTINATION",self.root/"ledger")]:
            patcher=patch.object(obj,attr,value); patcher.start(); self.addCleanup(patcher.stop)
        policy={"git_branch_governance":{"development_branch":"dev","integration_branch":"main","allowed_one_shot_strategies":["ff-only"]}}
        for name,value in [("load_yaml",policy),("load_manifest",{}),("check_access",{"status":"ALLOW"})]:
            patcher=patch.object(merge,name,return_value=value); patcher.start(); self.addCleanup(patcher.stop)

    def git(self,*args):
        return subprocess.run(["git",*args],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()

    def write_record(self):
        self.path.write_text(json.dumps(self.record),encoding="utf-8")

    def receipt(self, **overrides):
        note={"kind":"merge_review","review_base":"main","status":"completed","source_branch":"dev","target_branch":"main","strategy":"ff-only","source_commit":self.git("rev-parse","dev"),"target_commit":self.git("rev-parse","main"),"validation":{"status":"passed","commands":["focused tests"]}}
        note.update(overrides)
        self.record["notes"].append(note); self.write_record()
        self.git("add", "."); self.git("commit","-m","review receipt")

    def assess(self):
        return merge.governed_assess("dev","main",agent="codex",record_id=self.record["task_id"],strategy="ff-only")

    def test_receipt_only_successor_is_safe(self):
        self.receipt()
        self.assertEqual(self.assess()["status"],"SAFE_TO_CONTINUE")

    def test_missing_and_skipped_reviews_stop(self):
        self.assertEqual(self.assess()["status"],"STOP")
        self.receipt(status="skipped_user_approved")
        self.assertEqual(self.assess()["status"],"STOP")

    def test_changed_source_stops(self):
        self.receipt()
        (self.root/"source.txt").write_text("unreviewed")
        self.git("add","."); self.git("commit","-m","unreviewed")
        self.assertEqual(self.assess()["status"],"STOP")

    def test_receipt_cannot_smuggle_source_changes(self):
        (self.root/"source.txt").write_text("unreviewed")
        self.receipt()
        self.assertEqual(self.assess()["status"],"STOP")

    def test_receipt_cannot_change_other_record_fields(self):
        self.record["task_type"]="changed"
        self.receipt()
        self.assertEqual(self.assess()["status"],"STOP")

    def test_stale_target_and_failed_validation_stop(self):
        self.receipt(target_commit="0"*40, validation={"status":"failed","commands":["test"]})
        self.assertEqual(self.assess()["status"],"STOP")

    def test_dirty_tree_stops(self):
        self.receipt(); (self.root/"unfinished.txt").write_text("pending")
        self.assertEqual(self.assess()["status"],"STOP")

    def test_divergence_stops(self):
        self.receipt(); self.git("checkout","main")
        (self.root/"other.txt").write_text("other")
        self.git("add","."); self.git("commit","-m","other")
        self.git("checkout","dev")
        self.assertEqual(self.assess()["status"],"STOP")

    def test_inactive_record_stops(self):
        self.receipt(); self.record["status"]="cancelled"; self.write_record()
        self.assertEqual(self.assess()["status"],"STOP")

    def test_other_unfinished_task_blocks_integration_not_editing(self):
        self.receipt()
        other = dict(self.record, task_id="TASK-20260908-002", notes=[])
        with patch.object(merge, "records", return_value=[self.record, other]):
            self.assertIn("unfinished", " ".join(self.assess()["errors"]))

    def test_ready_concurrent_tasks_share_one_batch(self):
        self.receipt(ready_tasks=["TASK-20260908-002"])
        other = dict(self.record, task_id="TASK-20260908-002", notes=[])
        with patch.object(merge, "records", return_value=[self.record, other]):
            self.assertEqual(self.assess()["status"], "SAFE_TO_CONTINUE")

    def close_task(self):
        self.receipt()
        self.git("checkout", "main"); self.git("merge", "--ff-only", "dev")
        self.git("checkout", "dev")
        self.record = task_records.finalize(Namespace(
            task_id=self.record["task_id"], status="successful", validation="passed",
            usability="usable", human_edit_rounds=0, command=["tests"], ended_at=None,
            tokens_actual=None, tokens_saved=None, currency_cost=None))
        self.git("add", "."); self.git("commit", "-m", "final audit")

    def closure_receipt(self):
        self.record = task_records.add_merge_review_note(Namespace(
            task_id=self.record["task_id"], status="completed", source_branch="dev",
            target_branch="main", strategy="ff-only", review_base="main", reason="audit reviewed",
            validation_command=["records validate"], ready_task=[], audit_close=True))
        self.git("add", "."); self.git("commit", "-m", "audit review receipt")

    def test_final_audit_delivery_terminates_without_a_new_task(self):
        self.close_task(); self.closure_receipt()
        self.assertEqual(self.assess()["status"], "SAFE_TO_CONTINUE")
        self.git("checkout", "main"); self.git("merge", "--ff-only", "dev")
        self.git("checkout", "dev")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.git("rev-parse", "main"), self.git("rev-parse", "dev"))
        self.assertEqual(len(task_records.records()), 1)
        self.assertEqual(task_records.records()[0]["status"], "successful")
        with self.assertRaisesRegex(ValueError, "already delivered"):
            self.closure_receipt()
        self.assertIn("already delivered", " ".join(self.assess()["errors"]))

    def test_final_audit_cannot_include_source_changes(self):
        self.close_task()
        (self.root / "source.txt").write_text("hidden development")
        self.git("add", "."); self.git("commit", "-m", "hidden code")
        self.closure_receipt()
        self.assertIn("only this TASK", " ".join(self.assess()["errors"]))

    def test_ordinary_remote_push_rejects_divergence(self):
        remote = self.root / "remote.git"
        self.git("init", "--bare", str(remote))
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "origin", "main", "dev")
        self.git("checkout", "main")
        (self.root / "remote-change.txt").write_text("new remote state")
        self.git("add", "remote-change.txt"); self.git("commit", "-m", "remote change")
        self.git("push", "origin", "main")
        result = subprocess.run(["git", "push", "origin", "dev:main"], cwd=self.root, capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_old_branch_ancestry_and_worktree_occupancy(self):
        self.git("branch", "codex", "main")
        self.git("merge-base", "--is-ancestor", "codex", "dev")
        other = self.root / "occupied"
        self.git("worktree", "add", str(other), "codex")
        self.assertIn("refs/heads/codex", self.git("worktree", "list", "--porcelain"))
        result = subprocess.run(["git", "branch", "-d", "codex"], cwd=self.root, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.git("worktree", "remove", str(other))

    def test_structured_overlap_stops(self):
        with patch.object(merge,"git",side_effect=["base","M\tconfig.yaml","M\tconfig.yaml"]):
            result=merge.assess("","left","right")
        self.assertEqual(result["status"],"STOP")


if __name__ == "__main__": unittest.main()
