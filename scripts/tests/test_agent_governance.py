from __future__ import annotations

import copy
import unittest
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from scripts.agent_governance import (
    WORKSPACE_ROOT,
    absolute_path_is_within,
    check_access,
    classify_path,
    create_request,
    doctor_payload,
    effective_registration,
    is_absolute_path,
    list_payload,
    load_manifest,
    load_registry,
    load_yaml,
    show_payload,
    validate_lease,
    validate_payload,
    validate_registration,
)


POLICY_PATH = WORKSPACE_ROOT / "shared" / "agent_governance.yaml"


class AgentGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_yaml(POLICY_PATH)
        cls.registry = load_registry()
        cls.manifest = load_manifest()
        cls.now = datetime.fromisoformat("2026-06-20T20:00:00+08:00")

    def test_manifest_is_structural(self) -> None:
        result = classify_path(self.policy, self.manifest, "workspace_manifest.yaml")
        self.assertEqual(result["surface"], "governance_structure")
        self.assertEqual(result["required_capability"], "structural_write")

    def test_windows_workspace_paths_classify_on_any_host(self) -> None:
        diagnosis = classify_path(
            self.policy,
            self.manifest,
            (
                r"${WORKSPACE_ROOT}\packages\character-system\reports"
                r"\runtime-loop\diagnoses\DIAG-demo.md"
            ),
        )
        external = classify_path(
            self.policy,
            self.manifest,
            r"${WORKSPACE_ROOT}\out\hermes\document.docx",
        )
        self.assertEqual(diagnosis["surface"], "runtime_record")
        self.assertEqual(
            diagnosis["workspace_relative"],
            (
                "packages/character-system/reports/runtime-loop/"
                "diagnoses/DIAG-demo.md"
            ),
        )
        self.assertEqual(external["surface"], "external_environment")

    def test_external_path_detection_is_cross_platform(self) -> None:
        self.assertTrue(is_absolute_path(r"${DATA_ROOT}/codex"))
        self.assertTrue(is_absolute_path("${DATA_ROOT}/codex"))
        self.assertTrue(is_absolute_path(r"\\server\share\agent"))
        self.assertTrue(is_absolute_path("/var/lib/agent"))
        self.assertFalse(is_absolute_path("reports/agent-experiments/demo"))

    def test_absolute_path_containment_is_cross_platform(self) -> None:
        self.assertTrue(
            absolute_path_is_within(
                "${WORKSPACE_ROOT}/reports",
                r"${WORKSPACE_ROOT}",
            )
        )
        self.assertFalse(
            absolute_path_is_within(
                "${DATA_ROOT}/codex",
                r"${WORKSPACE_ROOT}",
            )
        )
        self.assertTrue(absolute_path_is_within("/srv/work/reports", "/srv/work"))
        self.assertFalse(absolute_path_is_within("${DATA_ROOT}/codex", "/srv/work"))

    def test_windows_storage_is_external_to_posix_workspace(self) -> None:
        with patch(
            "scripts.agent_governance.WORKSPACE_ROOT",
            PurePosixPath("/home/runner/work/workspace/workspace"),
        ):
            result = validate_registration(
                self.policy,
                self.registry,
                self.manifest,
                "codex",
                self.registry["agents"]["codex"],
                now=self.now,
            )
        self.assertEqual(result["status"], "PASS")

    def test_four_existing_agents_preserve_effective_permissions(self) -> None:
        expected = {
            "codex": "structural_maintainer",
            "claude": "structural_maintainer",
            "opencode": "record_producer",
            "hermes": "record_producer",
        }
        for agent_id, role in expected.items():
            with self.subTest(agent=agent_id):
                resolved = effective_registration(
                    self.policy, self.registry, self.manifest, agent_id
                )
                self.assertEqual(resolved["registration_status"], "active")
                self.assertEqual(resolved["role"], role)
                self.assertFalse(resolved["degraded"])

    def test_hermes_can_write_diagnosis_but_not_manifest(self) -> None:
        diagnosis = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="hermes",
            operation="write",
            raw_path="packages/character-system/reports/runtime-loop/diagnoses/DIAG-demo.md",
        )
        manifest = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="hermes",
            operation="write",
            raw_path="workspace_manifest.yaml",
        )
        self.assertEqual(diagnosis["status"], "ALLOW")
        self.assertEqual(manifest["status"], "DENY")

    def test_unregistered_agent_degrades_to_consumer(self) -> None:
        resolved = effective_registration(
            self.policy, self.registry, self.manifest, "unknown-agent"
        )
        self.assertEqual(resolved["role"], "consumer")
        self.assertTrue(resolved["degraded"])
        request = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="unknown-agent",
            operation="write",
            raw_path="reports/agent-requests/REQ-demo.md",
        )
        source = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="unknown-agent",
            operation="write",
            raw_path="skills/demo/SKILL.md",
        )
        self.assertEqual(request["status"], "ALLOW")
        self.assertEqual(source["status"], "DENY")

    def test_proposed_agents_receive_no_new_permissions(self) -> None:
        for agent_id in ("cursor",):
            with self.subTest(agent=agent_id):
                resolved = effective_registration(
                    self.policy, self.registry, self.manifest, agent_id
                )
                self.assertEqual(resolved["role"], "consumer")
                self.assertTrue(resolved["degraded"])
                self.assertNotIn("record_write", resolved["capabilities"])

    def test_testing_agent_is_limited_to_explicit_scope(self) -> None:
        registry = copy.deepcopy(self.registry)
        now = datetime.now().astimezone()
        registry["agents"]["test-agent"] = {
            "id": "test-agent",
            "display_name": "Test Agent",
            "aliases": [],
            "identity_kind": "agent",
            "host": {"id": "test", "kind": "cli"},
            "status": "testing",
            "registration_type": "temporary",
            "role": "record_producer",
            "trust_source": "user_approved",
            "capabilities": {
                "inherit_role": False,
                "allow": ["read", "invoke", "proposal_write", "record_write"],
            },
            "path_scopes": ["reports/agent-experiments/test-agent/**"],
            "platforms": [],
            "skill_access": {"mode": "none", "platforms": []},
            "storage": {
                "boundary": "external",
                "data_root": "${DATA_ROOT}/test-agent",
                "cache_root": "${DATA_ROOT}/test-agent/cache",
            },
            "session_store": {"mode": "platform_managed", "boundary": "external"},
            "lifecycle": {
                "owner": "user",
                "reviewed_at": (now - timedelta(hours=1)).isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            },
            "active_lease_refs": [],
        }
        allowed = check_access(
            self.policy,
            self.manifest,
            registry=registry,
            agent_name="test-agent",
            operation="write",
            raw_path="reports/agent-experiments/test-agent/result.md",
        )
        denied = check_access(
            self.policy,
            self.manifest,
            registry=registry,
            agent_name="test-agent",
            operation="write",
            raw_path="reports/hermes/result.md",
        )
        self.assertEqual(allowed["status"], "ALLOW")
        self.assertEqual(denied["status"], "DENY")

    def test_alias_conflict_is_an_error(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["agents"]["reasonix"]["aliases"] = ["codex-cli"]
        result = validate_registration(
            self.policy,
            registry,
            self.manifest,
            "reasonix",
            registry["agents"]["reasonix"],
            now=self.now,
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("alias_conflict", {item["code"] for item in result["diagnostics"]})

    def test_invalid_role_and_capability_are_errors(self) -> None:
        registry = copy.deepcopy(self.registry)
        entry = registry["agents"]["cursor"]
        entry["role"] = "administrator"
        entry["capabilities"]["allow"] = ["root_write"]
        result = validate_registration(
            self.policy, registry, self.manifest, "cursor", entry, now=self.now
        )
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("invalid_role", codes)
        self.assertIn("unknown_capability", codes)

    def test_invalid_active_registration_degrades_to_consumer(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["agents"]["codex"]["role"] = "administrator"
        resolved = effective_registration(
            self.policy, registry, self.manifest, "codex"
        )
        self.assertEqual(resolved["role"], "consumer")
        self.assertTrue(resolved["degraded"])

    def test_consumer_cannot_declare_high_risk_capability(self) -> None:
        registry = copy.deepcopy(self.registry)
        entry = registry["agents"]["cursor"]
        entry["capabilities"]["allow"] = ["structural_write"]
        result = validate_registration(
            self.policy, registry, self.manifest, "cursor", entry, now=self.now
        )
        self.assertIn(
            "consumer_escalation",
            {item["code"] for item in result["diagnostics"]},
        )

    def test_active_registration_requires_owner_review_and_identity(self) -> None:
        registry = copy.deepcopy(self.registry)
        entry = registry["agents"]["codex"]
        entry["lifecycle"]["owner"] = None
        entry["lifecycle"]["reviewed_at"] = None
        del entry["identity_kind"]
        result = validate_registration(
            self.policy, registry, self.manifest, "codex", entry, now=self.now
        )
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("missing_field", codes)
        self.assertIn("missing_owner", codes)
        self.assertIn("missing_datetime", codes)

    def test_temporary_registration_requires_bounded_expiry(self) -> None:
        registry = copy.deepcopy(self.registry)
        entry = registry["agents"]["cursor"]
        entry["status"] = "testing"
        entry["registration_type"] = "temporary"
        entry["role"] = "record_producer"
        entry["capabilities"] = {
            "inherit_role": False,
            "allow": ["record_write"],
        }
        entry["path_scopes"] = ["reports/cursor/**"]
        entry["lifecycle"]["reviewed_at"] = "2026-06-20T20:00:00+08:00"
        entry["lifecycle"]["expires_at"] = None
        result = validate_registration(
            self.policy, registry, self.manifest, "cursor", entry, now=self.now
        )
        self.assertIn(
            "missing_datetime",
            {item["code"] for item in result["diagnostics"]},
        )

    def test_suspended_or_retired_agents_degrade_and_cannot_hold_active_lease(self) -> None:
        for status in ("suspended", "retired"):
            registry = copy.deepcopy(self.registry)
            entry = registry["agents"]["codex"]
            entry["status"] = status
            entry["active_lease_refs"] = ["LEASE-demo"]
            validation = validate_registration(
                self.policy, registry, self.manifest, "codex", entry, now=self.now
            )
            resolved = effective_registration(
                self.policy, registry, self.manifest, "codex"
            )
            self.assertIn(
                "inactive_active_lease",
                {item["code"] for item in validation["diagnostics"]},
            )
            self.assertEqual(resolved["role"], "consumer")

    def test_cursor_candidate_and_reasonix_active_classification(self) -> None:
        cursor = self.registry["agents"]["cursor"]
        reasonix = self.registry["agents"]["reasonix"]
        self.assertEqual(cursor["identity_kind"], "agent_host")
        self.assertEqual(reasonix["identity_kind"], "agent")
        self.assertEqual(cursor["status"], "proposed")
        self.assertEqual(reasonix["status"], "active")
        self.assertEqual(reasonix["role"], "record_producer")

    def test_list_show_validate_and_doctor_payloads(self) -> None:
        listed = list_payload(self.policy, self.registry, self.manifest)
        shown = show_payload(self.policy, self.registry, self.manifest, "claude-code")
        validated = validate_payload(self.policy, self.registry, self.manifest, "codex")
        doctor = doctor_payload(self.policy, self.registry, self.manifest, "cursor")
        self.assertEqual(len(listed["agents"]), 6)
        self.assertEqual(shown["agent"], "claude")
        self.assertEqual(validated["status"], "PASS")
        self.assertEqual(doctor["status"], "WARNING")

    def test_structural_lease_requires_worktree(self) -> None:
        lease = {
            "lease_id": "LEASE-20260620-001",
            "agent": "hermes",
            "issued_by": "user",
            "capabilities": ["structural_write"],
            "path_scopes": ["workspace_manifest.yaml"],
            "starts_at": "2026-06-20T10:00:00+08:00",
            "expires_at": "2026-06-20T18:00:00+08:00",
            "status": "active",
            "isolation": {"mode": "branch", "branch": "agent/hermes/demo"},
        }
        result = validate_lease(self.policy, lease, now=self.now)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("worktree", " ".join(result["errors"]))

    def test_valid_structural_lease_can_authorize_exact_scope(self) -> None:
        lease = {
            "lease_id": "LEASE-20260620-001",
            "agent": "hermes",
            "issued_by": "user",
            "capabilities": ["structural_write"],
            "path_scopes": ["workspace_manifest.yaml"],
            "starts_at": "2026-06-20T00:00:00+08:00",
            "expires_at": "2026-06-21T00:00:00+08:00",
            "status": "active",
            "isolation": {
                "mode": "worktree",
                "branch": "agent/hermes/demo",
                "worktree_path": "${WORKSPACE_ROOT}/worktrees/hermes-demo",
            },
        }
        with patch(
            "scripts.agent_governance.datetime"
        ) as clock:
            clock.now.return_value = self.now
            clock.fromisoformat.side_effect = datetime.fromisoformat
            result = check_access(
                self.policy,
                self.manifest,
                registry=self.registry,
                agent_name="hermes",
                operation="write",
                raw_path="workspace_manifest.yaml",
                lease=lease,
            )
        self.assertEqual(result["status"], "ALLOW")

    def test_runtime_character_cannot_authorize_source_patch(self) -> None:
        result = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="codex",
            operation="write",
            raw_path=(
                "packages/character-system/runtime/characters/zyc/"
                "references/voice_card.md"
            ),
            acting_skill="zyc",
        )
        self.assertEqual(result["status"], "DENY")
        self.assertEqual(result["acting_skill"]["required_mode"], "source_patch")

    def test_style_doctor_can_authorize_diagnosis_record(self) -> None:
        result = check_access(
            self.policy,
            self.manifest,
            registry=self.registry,
            agent_name="hermes",
            operation="write",
            raw_path=(
                "packages/character-system/reports/runtime-loop/"
                "diagnoses/DIAG-demo.md"
            ),
            acting_skill="style-doctor",
        )
        self.assertEqual(result["status"], "ALLOW")
        self.assertEqual(result["acting_skill"]["status"], "ALLOW")

    def test_request_output_must_stay_in_request_root(self) -> None:
        with self.assertRaises(ValueError):
            create_request(
                self.policy,
                self.manifest,
                agent="hermes",
                mode="review_only",
                summary="Demo",
                paths=["workspace_manifest.yaml"],
                output="README.md",
            )

    def test_request_can_be_created_in_bounded_request_root(self) -> None:
        request_root = WORKSPACE_ROOT / "reports" / "agent-requests"
        with (
            patch("scripts.agent_governance.REQUEST_ROOT", request_root),
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
            patch.object(Path, "write_text") as write_text,
        ):
            result = create_request(
                self.policy,
                self.manifest,
                agent="hermes",
                mode="worktree",
                summary="Register a missing skill",
                paths=["workspace_manifest.yaml"],
                output=None,
            )
        self.assertEqual(result["status"], "CREATED")
        self.assertIn("structural_write", result["capabilities"])
        write_text.assert_called_once()


if __name__ == "__main__":
    unittest.main()
