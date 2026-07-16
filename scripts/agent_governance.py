from __future__ import annotations

import argparse
import fnmatch
import json
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml

try:
    from scripts.task_records import active_registration
except ModuleNotFoundError:  # Direct execution
    from task_records import active_registration


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = WORKSPACE_ROOT / "shared" / "agent_governance.yaml"
REGISTRY_PATH = WORKSPACE_ROOT / "shared" / "agent_registry.yaml"
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
REQUEST_ROOT = WORKSPACE_ROOT / "reports" / "agent-requests"


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return payload


def load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("workspace manifest must be an object")
    return payload


def load_registry() -> dict[str, Any]:
    return load_yaml(REGISTRY_PATH)


def normalize_relative(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def is_absolute_path(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def absolute_path_is_within(value: str, root: str) -> bool:
    return absolute_path_relative_to(value, root) is not None


def absolute_paths_equal(left: str, right: str) -> bool:
    """Compare Windows or POSIX absolute paths without relying on this host."""
    return (
        absolute_path_relative_to(left, right) == ""
        and absolute_path_relative_to(right, left) == ""
    )


def absolute_path_relative_to(value: str, root: str) -> str | None:
    value_windows = PureWindowsPath(value)
    root_windows = PureWindowsPath(root)
    if value_windows.is_absolute() and root_windows.is_absolute():
        value_parts = tuple(part.casefold() for part in value_windows.parts)
        root_parts = tuple(part.casefold() for part in root_windows.parts)
        if value_parts[: len(root_parts)] == root_parts:
            return "/".join(value_windows.parts[len(root_windows.parts) :])
        return None

    value_posix = PurePosixPath(value)
    root_posix = PurePosixPath(root)
    if value_posix.is_absolute() and root_posix.is_absolute():
        if value_posix.parts[: len(root_posix.parts)] == root_posix.parts:
            return "/".join(value_posix.parts[len(root_posix.parts) :])
        return None
    return None


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def path_matches(value: str, pattern: str) -> bool:
    normalized = normalize_relative(value)
    expected = normalize_relative(pattern)
    if expected == "**":
        return True
    if expected.endswith("/**"):
        prefix = expected[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return fnmatch.fnmatchcase(normalized.casefold(), expected.casefold())


def role_capabilities(policy: dict[str, Any], role: str) -> set[str]:
    entry = policy.get("roles", {}).get(role, {})
    return {str(value) for value in entry.get("capabilities", [])}


def all_capabilities(policy: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for role in policy.get("roles", {}).values():
        values.update(str(value) for value in role.get("capabilities", []))
    values.update(
        str(value)
        for value in policy.get("lease_policy", {}).get("allowed_capabilities", [])
    )
    return values


def registration_alias_map(registry: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, str]]]:
    aliases: dict[str, str] = {}
    diagnostics: list[dict[str, str]] = []
    for agent_id, entry in registry.get("agents", {}).items():
        names = [str(agent_id), *[str(value) for value in entry.get("aliases", [])]]
        for name in names:
            key = name.strip().casefold()
            if not key:
                diagnostics.append(
                    diagnostic("ERROR", "empty_alias", f"{agent_id}: empty id or alias")
                )
            elif key in aliases and aliases[key] != str(agent_id):
                diagnostics.append(
                    diagnostic(
                        "ERROR",
                        "alias_conflict",
                        f"{name!r} resolves to both {aliases[key]} and {agent_id}",
                    )
                )
            else:
                aliases[key] = str(agent_id)
    return aliases, diagnostics


def find_registration(
    registry: dict[str, Any], name: str
) -> tuple[str | None, dict[str, Any] | None]:
    aliases, _ = registration_alias_map(registry)
    agent_id = aliases.get(name.strip().casefold())
    if not agent_id:
        return None, None
    entry = registry.get("agents", {}).get(agent_id)
    return agent_id, entry if isinstance(entry, dict) else None


def diagnostic(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def parse_datetime(
    value: Any,
    field: str,
    diagnostics: list[dict[str, str]],
    *,
    required: bool,
) -> datetime | None:
    if value in (None, ""):
        if required:
            diagnostics.append(
                diagnostic("ERROR", "missing_datetime", f"{field} is required")
            )
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "invalid_datetime",
                f"{field} must be an ISO-8601 datetime with timezone",
            )
        )
        return None
    if parsed.tzinfo is None:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "naive_datetime",
                f"{field} must include a timezone",
            )
        )
        return None
    return parsed


def resolve_manifest_ref(manifest: dict[str, Any], reference: str) -> Any:
    current: Any = manifest
    for part in reference.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(reference)
        current = current[part]
    return current


def declared_capabilities(
    policy: dict[str, Any], entry: dict[str, Any]
) -> set[str]:
    capability_contract = entry.get("capabilities", {})
    if not isinstance(capability_contract, dict):
        return set()
    values = (
        role_capabilities(policy, str(entry.get("role", "consumer")))
        if capability_contract.get("inherit_role") is True
        else set()
    )
    values.update(str(value) for value in capability_contract.get("allow", []))
    return values


def validate_registration(
    policy: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    agent_id: str,
    entry: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    clock = now or datetime.now().astimezone()
    required_fields = (
        "id",
        "display_name",
        "aliases",
        "identity_kind",
        "host",
        "status",
        "registration_type",
        "role",
        "trust_source",
        "capabilities",
        "path_scopes",
        "platforms",
        "skill_access",
        "storage",
        "session_store",
        "lifecycle",
    )
    for field in required_fields:
        if field not in entry:
            diagnostics.append(
                diagnostic("ERROR", "missing_field", f"{agent_id}: missing {field}")
            )
    if entry.get("id") != agent_id:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "id_mismatch",
                f"{agent_id}: registration id must match its registry key",
            )
        )

    _, alias_diagnostics = registration_alias_map(registry)
    diagnostics.extend(alias_diagnostics)

    statuses = set(str(value) for value in registry.get("allowed_statuses", []))
    registration_types = set(
        str(value) for value in registry.get("allowed_registration_types", [])
    )
    trust_sources = set(
        str(value) for value in registry.get("allowed_trust_sources", [])
    )
    status = str(entry.get("status", ""))
    registration_type = str(entry.get("registration_type", ""))
    trust_source = str(entry.get("trust_source", ""))
    role = str(entry.get("role", ""))
    identity_kind = str(entry.get("identity_kind", ""))

    if status not in statuses:
        diagnostics.append(
            diagnostic("ERROR", "invalid_status", f"{agent_id}: unsupported status {status!r}")
        )
    if registration_type not in registration_types:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "invalid_registration_type",
                f"{agent_id}: unsupported registration_type {registration_type!r}",
            )
        )
    if trust_source not in trust_sources:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "invalid_trust_source",
                f"{agent_id}: unsupported trust_source {trust_source!r}",
            )
        )
    if role not in policy.get("roles", {}):
        diagnostics.append(
            diagnostic("ERROR", "invalid_role", f"{agent_id}: unknown role {role!r}")
        )
    if identity_kind not in {
        "agent",
        "agent_host",
        "tool_client",
        "unknown_candidate",
    }:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "invalid_identity_kind",
                f"{agent_id}: unsupported identity_kind {identity_kind!r}",
            )
        )
    host = entry.get("host", {})
    if not isinstance(host, dict) or not host.get("id") or not host.get("kind"):
        diagnostics.append(
            diagnostic(
                "ERROR",
                "invalid_host",
                f"{agent_id}: host requires id and kind",
            )
        )

    capability_contract = entry.get("capabilities", {})
    if not isinstance(capability_contract, dict):
        diagnostics.append(
            diagnostic("ERROR", "invalid_capabilities", f"{agent_id}: capabilities must be an object")
        )
        capability_contract = {}
    allow = capability_contract.get("allow", [])
    if not isinstance(allow, list):
        diagnostics.append(
            diagnostic("ERROR", "invalid_capabilities", f"{agent_id}: capabilities.allow must be a list")
        )
        allow = []
    invalid_capabilities = sorted(
        set(str(value) for value in allow) - all_capabilities(policy)
    )
    if invalid_capabilities:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "unknown_capability",
                f"{agent_id}: unsupported capabilities: {', '.join(invalid_capabilities)}",
            )
        )

    scopes = entry.get("path_scopes", [])
    if not isinstance(scopes, list) or not scopes:
        diagnostics.append(
            diagnostic("ERROR", "missing_scopes", f"{agent_id}: path_scopes must be non-empty")
        )
        scopes = []
    for scope in scopes:
        normalized = normalize_relative(str(scope))
        if is_absolute_path(str(scope)) or ".." in Path(normalized).parts:
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "unsafe_scope",
                    f"{agent_id}: scope must stay workspace-relative: {scope}",
                )
            )
        if normalized == "**" and not (
            status == "active" and role == "structural_maintainer"
        ):
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "overbroad_scope",
                    f"{agent_id}: only active structural maintainers may use **",
                )
            )

    declared = declared_capabilities(policy, entry)
    high_risk = set(
        str(value)
        for value in policy.get("registration_policy", {}).get(
            "high_risk_capabilities", []
        )
    )
    if role == "consumer" and declared & high_risk:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "consumer_escalation",
                f"{agent_id}: consumer declares high-risk capabilities: "
                + ", ".join(sorted(declared & high_risk)),
            )
        )
    if status == "testing":
        if capability_contract.get("inherit_role") is True:
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "testing_inherits_role",
                    f"{agent_id}: testing registrations must enumerate an explicit subset",
                )
            )
        if "structural_write" in declared or "platform_write" in declared:
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "testing_high_risk",
                    f"{agent_id}: testing may not grant structural_write or platform_write",
                )
            )

    lifecycle = entry.get("lifecycle", {})
    if not isinstance(lifecycle, dict):
        diagnostics.append(
            diagnostic("ERROR", "invalid_lifecycle", f"{agent_id}: lifecycle must be an object")
        )
        lifecycle = {}
    owner = lifecycle.get("owner")
    reviewed_at = parse_datetime(
        lifecycle.get("reviewed_at"),
        f"{agent_id}.lifecycle.reviewed_at",
        diagnostics,
        required=status == "active",
    )
    expiry_required = status == "testing" or registration_type in {
        "experimental",
        "temporary",
    }
    expires_at = parse_datetime(
        lifecycle.get("expires_at"),
        f"{agent_id}.lifecycle.expires_at",
        diagnostics,
        required=expiry_required,
    )
    if status == "active" and not owner:
        diagnostics.append(
            diagnostic("ERROR", "missing_owner", f"{agent_id}: active registration needs owner")
        )
    if expires_at and expires_at <= clock:
        diagnostics.append(
            diagnostic("ERROR", "expired_registration", f"{agent_id}: registration has expired")
        )
    if reviewed_at and expires_at:
        duration_hours = (expires_at - reviewed_at).total_seconds() / 3600
        maximum = (
            float(
                policy.get("registration_policy", {}).get(
                    "testing_max_duration_hours", 168
                )
            )
            if status == "testing"
            else float(
                policy.get("registration_policy", {}).get(
                    "experimental_max_duration_hours", 720
                )
            )
        )
        if duration_hours > maximum:
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "registration_duration",
                    f"{agent_id}: registration duration exceeds {maximum:g} hours",
                )
            )

    for platform in entry.get("platforms", []):
        if not isinstance(platform, dict):
            diagnostics.append(
                diagnostic("ERROR", "invalid_platform", f"{agent_id}: platform entry must be an object")
            )
            continue
        reference = str(platform.get("manifest_ref", ""))
        try:
            resolve_manifest_ref(manifest, reference)
        except KeyError:
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "unsupported_platform",
                    f"{agent_id}: manifest does not support {reference!r}",
                )
            )

    for field in ("storage", "session_store"):
        contract = entry.get(field, {})
        if not isinstance(contract, dict):
            diagnostics.append(
                diagnostic("ERROR", f"invalid_{field}", f"{agent_id}: {field} must be an object")
            )
            continue
        if contract.get("boundary") != "external":
            diagnostics.append(
                diagnostic(
                    "ERROR",
                    "source_pollution_boundary",
                    f"{agent_id}: {field} must declare an external boundary",
                )
            )
        for key in ("data_root", "cache_root"):
            value = contract.get(key)
            if value and value != "unconfirmed":
                if not is_absolute_path(str(value)):
                    diagnostics.append(
                        diagnostic(
                            "ERROR",
                            "relative_external_storage",
                            f"{agent_id}: {field}.{key} must be absolute or unconfirmed",
                        )
                    )
                elif absolute_path_is_within(str(value), str(WORKSPACE_ROOT)):
                    diagnostics.append(
                        diagnostic(
                            "ERROR",
                            "source_pollution_boundary",
                            f"{agent_id}: {field}.{key} points inside workspace source",
                        )
                    )
        reference = contract.get("manifest_ref")
        if reference:
            try:
                resolve_manifest_ref(manifest, str(reference))
            except KeyError:
                diagnostics.append(
                    diagnostic(
                        "ERROR",
                        "invalid_manifest_ref",
                        f"{agent_id}: unresolved manifest reference {reference!r}",
                    )
                )

    lease_refs = entry.get("active_lease_refs", [])
    if status in {"suspended", "retired"} and lease_refs:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "inactive_active_lease",
                f"{agent_id}: {status} registration still lists active leases",
            )
        )
    if status == "proposed":
        diagnostics.append(
            diagnostic(
                "WARNING",
                "proposed_consumer",
                f"{agent_id}: proposed registration is restricted to Consumer",
            )
        )
    if entry.get("identity_kind") in {"agent_host", "tool_client", "unknown_candidate"}:
        diagnostics.append(
            diagnostic(
                "INFO",
                "identity_not_agent",
                f"{agent_id}: identity is classified as {entry.get('identity_kind')}",
            )
        )

    errors = [item for item in diagnostics if item["severity"] == "ERROR"]
    warnings = [item for item in diagnostics if item["severity"] == "WARNING"]
    status_value = "ERROR" if errors else "WARNING" if warnings else "PASS"
    return {
        "status": status_value,
        "agent": agent_id,
        "registration_status": status,
        "declared_role": role,
        "diagnostics": diagnostics,
    }


def effective_registration(
    policy: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    agent_id, entry = find_registration(registry, name)
    fallback = policy.get("unregistered_agent", {})
    if not agent_id or not entry:
        role = str(fallback.get("role", "consumer"))
        return {
            "agent": name.strip() or "unregistered",
            "registered": False,
            "registration_status": "unregistered",
            "role": role,
            "capabilities": role_capabilities(policy, role),
            "path_scopes": list(fallback.get("path_scopes", [])),
            "validation": {"status": "WARNING", "diagnostics": []},
            "degraded": True,
        }

    validation = validate_registration(policy, registry, manifest, agent_id, entry)
    lifecycle_status = str(entry.get("status", "proposed"))
    eligible = lifecycle_status in {"active", "testing"} and validation["status"] != "ERROR"
    role = str(entry.get("role", "consumer")) if eligible else str(
        fallback.get("role", "consumer")
    )
    capabilities = (
        declared_capabilities(policy, entry)
        if eligible
        else role_capabilities(policy, role)
    )
    scopes = (
        list(entry.get("path_scopes", []))
        if eligible
        else list(fallback.get("path_scopes", []))
    )
    return {
        "agent": agent_id,
        "registered": True,
        "registration_status": lifecycle_status,
        "role": role,
        "capabilities": capabilities,
        "path_scopes": scopes,
        "validation": validation,
        "degraded": not eligible,
    }


def managed_platform_publisher(
    policy: dict[str, Any], publisher_id: str
) -> dict[str, Any] | None:
    """Return one declared external platform publisher, if it is valid enough to use."""
    publishers = policy.get("managed_platform_publishers", {})
    if not isinstance(publishers, dict):
        return None
    publisher = publishers.get(publisher_id)
    if not isinstance(publisher, dict):
        return None
    return publisher


def classify_path(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    raw_path: str,
) -> dict[str, Any]:
    value = raw_path.strip().strip("\"'")
    for publisher_id, publisher in policy.get("managed_platform_publishers", {}).items():
        if not isinstance(publisher, dict):
            continue
        staging_path = str(publisher.get("staging_path", ""))
        if staging_path and absolute_path_relative_to(value, staging_path) is not None:
            return {
                "surface": "platform_projection",
                "required_capability": "platform_write",
                "path": value,
                "workspace_relative": "",
                "platform": "managed_public_publisher",
                "publisher": str(publisher_id),
                "requires_external_write": True,
            }
    for platform, root_value in manifest.get("platform_roots", {}).items():
        if absolute_path_relative_to(value, str(root_value)) is not None:
            return {
                "surface": "platform_projection",
                "required_capability": "platform_write",
                "path": value,
                "workspace_relative": "",
                "platform": str(platform),
                "publisher": "",
                "requires_external_write": False,
            }

    relative: str | None = None
    if is_absolute_path(value):
        workspace_roots = (
            str(manifest.get("workspace", {}).get("source_of_truth", "")),
            str(WORKSPACE_ROOT),
        )
        for root in workspace_roots:
            if not root:
                continue
            relative = absolute_path_relative_to(value, root)
            if relative is not None:
                break
        if relative is None:
            return {
                "surface": "external_environment",
                "required_capability": "environment_write",
                "path": value,
                "workspace_relative": "",
                "platform": "",
                "publisher": "",
                "requires_external_write": False,
            }
    else:
        absolute = (WORKSPACE_ROOT / Path(value)).resolve()
        if not is_within(absolute, WORKSPACE_ROOT):
            return {
                "surface": "external_environment",
                "required_capability": "environment_write",
                "path": str(absolute),
                "workspace_relative": "",
                "platform": "",
                "publisher": "",
                "requires_external_write": False,
            }
        relative = absolute.relative_to(WORKSPACE_ROOT).as_posix()

    relative = normalize_relative(relative or "")
    absolute = (WORKSPACE_ROOT / Path(relative)).resolve()
    if not is_within(absolute, WORKSPACE_ROOT):
        return {
            "surface": "external_environment",
            "required_capability": "environment_write",
            "path": str(absolute),
            "workspace_relative": "",
            "platform": "",
            "publisher": "",
            "requires_external_write": False,
        }

    for surface in policy.get("surface_classes", []):
        for pattern in surface.get("path_patterns", []):
            if path_matches(relative, str(pattern)):
                return {
                    "surface": str(surface.get("id", "")),
                    "required_capability": str(
                        surface.get("required_capability", "")
                    ),
                    "path": str(absolute),
                    "workspace_relative": relative,
                    "platform": "",
                    "publisher": "",
                    "requires_external_write": False,
                }
    raise ValueError(f"No surface classification for {relative}")


def check_managed_platform_publish(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    *,
    publisher_id: str,
    publisher_script: str,
    agent_name: str,
    record_id: str,
    staging_path: str,
    remote_url: str,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize an exact managed public-repository publication target."""
    publisher = managed_platform_publisher(policy, publisher_id)
    if publisher is None:
        return {
            "status": "DENY",
            "publisher": publisher_id,
            "reason": "publisher is not registered in agent_governance.yaml",
        }

    expected_staging = str(publisher.get("staging_path", ""))
    expected_script = normalize_relative(str(publisher.get("publisher_script", "")))
    allowed_remotes = {
        str(value) for value in publisher.get("remote_urls", []) if str(value)
    }
    if not expected_script or normalize_relative(publisher_script) != expected_script:
        return {
            "status": "DENY",
            "publisher": publisher_id,
            "reason": "publisher script does not match the registered publisher",
        }
    if not expected_staging or not absolute_paths_equal(staging_path, expected_staging):
        return {
            "status": "DENY",
            "publisher": publisher_id,
            "reason": "push staging path must exactly match the registered publisher",
        }
    if remote_url not in allowed_remotes:
        return {
            "status": "DENY",
            "publisher": publisher_id,
            "reason": "push remote URL is not registered for this publisher",
        }

    try:
        registration = active_registration(record_id, "external_write")
    except ValueError as error:
        return {
            "status": "DENY",
            "publisher": publisher_id,
            "reason": f"task registration denied: {error}",
        }

    authorization = check_access(
        policy,
        manifest,
        registry=registry,
        agent_name=agent_name,
        operation="write",
        raw_path=staging_path,
    )
    authorization["publisher"] = publisher_id
    authorization["task_registration"] = registration
    if authorization["status"] != "ALLOW":
        authorization["reason"] = (
            "managed publisher authorization denied: " + authorization["reason"]
        )
    return authorization


def validate_lease(
    policy: dict[str, Any],
    lease: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    required = (
        "lease_id",
        "agent",
        "issued_by",
        "capabilities",
        "path_scopes",
        "starts_at",
        "expires_at",
        "status",
        "isolation",
    )
    for field in required:
        if field not in lease:
            errors.append(f"missing field: {field}")

    lease_policy = policy.get("lease_policy", {})
    issuer = str(lease.get("issued_by", ""))
    if issuer not in lease_policy.get("trusted_issuers", []):
        errors.append(f"untrusted issuer: {issuer}")

    capabilities = lease.get("capabilities", [])
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty list")
        capabilities = []
    invalid_capabilities = sorted(
        set(str(value) for value in capabilities)
        - set(
            str(value)
            for value in lease_policy.get("allowed_capabilities", [])
        )
    )
    if invalid_capabilities:
        errors.append(f"unsupported capabilities: {', '.join(invalid_capabilities)}")

    scopes = lease.get("path_scopes", [])
    if not isinstance(scopes, list) or not scopes:
        errors.append("path_scopes must be a non-empty list")

    lease_diagnostics: list[dict[str, str]] = []
    starts_at = parse_datetime(
        lease.get("starts_at"), "starts_at", lease_diagnostics, required=True
    )
    expires_at = parse_datetime(
        lease.get("expires_at"), "expires_at", lease_diagnostics, required=True
    )
    errors.extend(item["message"] for item in lease_diagnostics)
    if starts_at and expires_at:
        if expires_at <= starts_at:
            errors.append("expires_at must be later than starts_at")
        maximum = float(lease_policy.get("maximum_duration_hours", 24))
        duration_hours = (expires_at - starts_at).total_seconds() / 3600
        if duration_hours > maximum:
            errors.append(f"lease duration exceeds {maximum:g} hours")

    isolation = lease.get("isolation", {})
    if not isinstance(isolation, dict):
        errors.append("isolation must be an object")
        isolation = {}
    isolation_mode = str(isolation.get("mode", ""))
    if "structural_write" in capabilities:
        allowed_modes = lease_policy.get(
            "structural_isolation_modes", ["worktree"]
        )
        if isolation_mode not in allowed_modes:
            errors.append("structural_write requires worktree isolation")
        if not isolation.get("branch") or not isolation.get("worktree_path"):
            errors.append(
                "structural_write requires isolation.branch and isolation.worktree_path"
            )

    clock = now or datetime.now().astimezone()
    active = (
        not errors
        and str(lease.get("status")) == "active"
        and starts_at is not None
        and expires_at is not None
        and starts_at <= clock <= expires_at
    )
    return {
        "status": "PASS" if not errors else "ERROR",
        "active": active,
        "lease_id": lease.get("lease_id"),
        "agent": lease.get("agent"),
        "errors": errors,
    }


def lease_allows(
    policy: dict[str, Any],
    registry: dict[str, Any],
    lease: dict[str, Any],
    *,
    agent: str,
    capability: str,
    target: dict[str, str],
) -> tuple[bool, dict[str, Any]]:
    validation = validate_lease(policy, lease)
    if not validation["active"]:
        return False, validation
    lease_agent, _ = find_registration(registry, str(lease.get("agent", "")))
    requested_agent, _ = find_registration(registry, agent)
    canonical_lease_agent = lease_agent or str(lease.get("agent", "")).casefold()
    canonical_requested = requested_agent or agent.casefold()
    if canonical_lease_agent != canonical_requested:
        validation["errors"].append("lease agent does not match requested agent")
        return False, validation
    if capability not in lease.get("capabilities", []):
        validation["errors"].append(f"lease does not grant {capability}")
        return False, validation
    comparable = target["workspace_relative"] or target["path"]
    if not any(
        path_matches(comparable, str(scope))
        for scope in lease.get("path_scopes", [])
    ):
        validation["errors"].append("target path is outside lease scopes")
        return False, validation
    return True, validation


def check_access(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    *,
    agent_name: str,
    operation: str,
    raw_path: str,
    acting_skill: str | None = None,
    lease: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    resolved = effective_registration(
        policy, registry, manifest, agent_name
    )
    target = classify_path(policy, manifest, raw_path)

    if operation == "read":
        allowed = target["surface"] != "external_environment"
        return {
            "status": "ALLOW" if allowed else "DENY",
            "agent": resolved["agent"],
            "role": resolved["role"],
            "registration_status": resolved["registration_status"],
            "degraded": resolved["degraded"],
            "operation": operation,
            **target,
            "reason": (
                "workspace reads are allowed"
                if allowed
                else "external paths are outside this policy"
            ),
        }

    required = target["required_capability"]
    allowed = required in resolved["capabilities"]
    comparable = target["workspace_relative"] or target["path"]
    scope_allowed = any(
        path_matches(comparable, str(scope))
        for scope in resolved["path_scopes"]
    )
    if allowed and not scope_allowed:
        allowed = False
        reason = "target is outside the effective registration path scopes"
    elif allowed:
        reason = (
            f"effective {resolved['registration_status']} registration grants "
            f"{required} inside scope"
        )
    else:
        reason = f"effective role {resolved['role']} does not grant {required}"

    lease_result: dict[str, Any] | None = None
    if not allowed and lease is not None:
        allowed, lease_result = lease_allows(
            policy,
            registry,
            lease,
            agent=resolved["agent"],
            capability=required,
            target=target,
        )
        if allowed:
            reason = f"active lease grants {required}"

    skill_authorization: dict[str, Any] | None = None
    if acting_skill:
        skill = next(
            (
                item
                for item in manifest.get("skills", [])
                if str(item.get("id", "")).casefold()
                == acting_skill.casefold()
            ),
            None,
        )
        if skill is None:
            allowed = False
            skill_authorization = {
                "skill": acting_skill,
                "status": "DENY",
                "reason": "acting skill is not registered in workspace_manifest.yaml",
            }
            reason = skill_authorization["reason"]
        else:
            required_mode = {
                "skill_source": "source_patch",
                "runtime_record": "record_write",
                "generated_snapshot": "record_write",
                "platform_projection": "source_patch",
                "governance_structure": "source_patch",
                "workspace_other": "source_patch",
            }.get(target["surface"])
            allowed_modes = {
                str(value)
                for value in skill.get("execution_modes", {}).get("allowed", [])
            }
            skill_allowed = required_mode is None or required_mode in allowed_modes
            skill_authorization = {
                "skill": skill.get("id"),
                "role": skill.get("role"),
                "required_mode": required_mode,
                "allowed_modes": sorted(allowed_modes),
                "status": "ALLOW" if skill_allowed else "DENY",
                "reason": (
                    "acting skill permits the required execution mode"
                    if skill_allowed
                    else (
                        f"acting skill {skill.get('id')} does not permit "
                        f"{required_mode}"
                    )
                ),
            }
            if not skill_allowed:
                allowed = False
                reason = skill_authorization["reason"]

    return {
        "status": "ALLOW" if allowed else "DENY",
        "agent": resolved["agent"],
        "role": resolved["role"],
        "registration_status": resolved["registration_status"],
        "degraded": resolved["degraded"],
        "operation": operation,
        **target,
        "reason": reason,
        "lease": lease_result,
        "acting_skill": skill_authorization,
        "next_action": (
            None
            if allowed
            else "Create a change request; structural work requires an active validated registration or valid temporary lease."
        ),
    }


def status_payload(
    policy: dict[str, Any], registry: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    agents = []
    for agent_id in registry.get("agents", {}):
        resolved = effective_registration(policy, registry, manifest, agent_id)
        entry = registry["agents"][agent_id]
        agents.append(
            {
                "agent": agent_id,
                "role": resolved["role"],
                "declared_role": entry.get("role"),
                "registration_status": entry.get("status"),
                "degraded": resolved["degraded"],
                "capabilities": sorted(resolved["capabilities"]),
                "path_scopes": resolved["path_scopes"],
            }
        )
    surfaces = [
        {
            "surface": entry.get("id"),
            "required_capability": entry.get("required_capability"),
            "path_patterns": entry.get("path_patterns", []),
        }
        for entry in policy.get("surface_classes", [])
    ]
    return {
        "status": "PASS",
        "agents": agents,
        "unregistered": policy.get("unregistered_agent"),
        "surfaces": surfaces,
        "lease_policy": policy.get("lease_policy"),
    }


def list_payload(
    policy: dict[str, Any], registry: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    agents = []
    for agent_id, entry in registry.get("agents", {}).items():
        resolved = effective_registration(policy, registry, manifest, agent_id)
        agents.append(
            {
                "agent": agent_id,
                "display_name": entry.get("display_name"),
                "identity_kind": entry.get("identity_kind"),
                "status": entry.get("status"),
                "registration_type": entry.get("registration_type"),
                "declared_role": entry.get("role"),
                "effective_role": resolved["role"],
                "degraded": resolved["degraded"],
                "owner": entry.get("lifecycle", {}).get("owner"),
                "expires_at": entry.get("lifecycle", {}).get("expires_at"),
            }
        )
    return {"status": "PASS", "agents": agents}


def show_payload(
    policy: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    agent_id, entry = find_registration(registry, name)
    if not agent_id or not entry:
        resolved = effective_registration(policy, registry, manifest, name)
        return {
            "status": "WARNING",
            "agent": name,
            "registered": False,
            "effective": {
                **resolved,
                "capabilities": sorted(resolved["capabilities"]),
            },
        }
    resolved = effective_registration(policy, registry, manifest, agent_id)
    return {
        "status": "PASS",
        "agent": agent_id,
        "registered": True,
        "contract": entry,
        "effective": {
            **resolved,
            "capabilities": sorted(resolved["capabilities"]),
        },
    }


def validate_payload(
    policy: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    agent_id, entry = find_registration(registry, name)
    if not agent_id or not entry:
        return {
            "status": "WARNING",
            "agent": name,
            "registration_status": "unregistered",
            "effective_role": "consumer",
            "diagnostics": [
                diagnostic(
                    "WARNING",
                    "unregistered_consumer",
                    f"{name}: no registration; Consumer fallback applies",
                )
            ],
        }
    validation = validate_registration(
        policy, registry, manifest, agent_id, entry
    )
    resolved = effective_registration(policy, registry, manifest, agent_id)
    return {
        **validation,
        "effective_role": resolved["role"],
        "effective_capabilities": sorted(resolved["capabilities"]),
        "degraded": resolved["degraded"],
    }


def doctor_payload(
    policy: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    payload = validate_payload(policy, registry, manifest, name)
    diagnostics = list(payload.get("diagnostics", []))
    agent_id, entry = find_registration(registry, name)
    if not agent_id or not entry:
        return payload

    if policy.get("agents"):
        diagnostics.append(
            diagnostic(
                "ERROR",
                "competing_identity_source",
                "agent_governance.yaml must not retain concrete agent identities",
            )
        )

    for platform in entry.get("platforms", []):
        reference = str(platform.get("manifest_ref", ""))
        try:
            root = Path(str(resolve_manifest_ref(manifest, reference)))
        except KeyError:
            continue
        if root.exists():
            diagnostics.append(
                diagnostic(
                    "INFO",
                    "platform_root_present",
                    f"{agent_id}: {reference} exists",
                )
            )
        else:
            severity = "ERROR" if entry.get("status") == "active" else "WARNING"
            diagnostics.append(
                diagnostic(
                    severity,
                    "platform_root_missing",
                    f"{agent_id}: {reference} does not exist",
                )
            )

    access_platforms = entry.get("skill_access", {}).get("platforms", [])
    declared_platforms = {
        str(item.get("id"))
        for item in entry.get("platforms", [])
        if isinstance(item, dict)
    }
    unsupported_access = sorted(
        set(str(value) for value in access_platforms) - declared_platforms
    )
    if unsupported_access:
        diagnostics.append(
            diagnostic(
                "ERROR",
                "skill_access_platform",
                f"{agent_id}: skill access lacks platform declarations: "
                + ", ".join(unsupported_access),
            )
        )
    for platform in access_platforms:
        exposed = any(
            any(
                exposure.get("platform") == platform
                for exposure in skill.get("exposures", [])
            )
            for skill in manifest.get("skills", [])
        )
        if not exposed:
            diagnostics.append(
                diagnostic(
                    "WARNING",
                    "no_skill_exposure",
                    f"{agent_id}: no manifest skill exposure for {platform}",
                )
            )

    storage = entry.get("storage", {})
    for key in ("data_root", "cache_root"):
        value = storage.get(key)
        if value == "unconfirmed":
            diagnostics.append(
                diagnostic(
                    "WARNING",
                    "unconfirmed_storage",
                    f"{agent_id}: storage.{key} is unconfirmed",
                )
            )
        elif value and not Path(str(value)).exists():
            diagnostics.append(
                diagnostic(
                    "INFO",
                    "storage_not_materialized",
                    f"{agent_id}: {key} is declared but not currently present",
                )
            )
    if entry.get("session_store", {}).get("mode") == "unconfirmed":
        diagnostics.append(
            diagnostic(
                "WARNING",
                "unconfirmed_session_store",
                f"{agent_id}: session store boundary is unconfirmed",
            )
        )

    errors = [item for item in diagnostics if item["severity"] == "ERROR"]
    warnings = [item for item in diagnostics if item["severity"] == "WARNING"]
    return {
        **payload,
        "status": "ERROR" if errors else "WARNING" if warnings else "PASS",
        "diagnostics": diagnostics,
    }


def create_request(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    *,
    agent: str,
    mode: str,
    summary: str,
    paths: list[str],
    output: str | None,
) -> dict[str, Any]:
    allowed_modes = policy.get("request_policy", {}).get("allowed_modes", [])
    if mode not in allowed_modes:
        raise ValueError(f"unsupported request mode: {mode}")
    if not paths:
        raise ValueError("at least one --path is required")

    classifications = [classify_path(policy, manifest, path) for path in paths]
    capabilities = sorted(
        {item["required_capability"] for item in classifications}
    )
    timestamp = datetime.now().astimezone()
    request_id = (
        f"REQ-{timestamp:%Y%m%d-%H%M%S}-{agent.casefold().replace('_', '-')}"
    )
    target = (
        (WORKSPACE_ROOT / output).resolve()
        if output
        else REQUEST_ROOT / f"{request_id}.md"
    )
    if not is_within(target, REQUEST_ROOT):
        raise ValueError("request output must stay under reports/agent-requests")
    if target.exists():
        raise FileExistsError(f"request already exists: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Agent Change Request",
        "",
        f"- Request ID: {request_id}",
        "- Status: requested",
        f"- Requested by: {agent}",
        f"- Requested mode: {mode}",
        f"- Created at: {timestamp.isoformat()}",
        f"- Summary: {summary}",
        "- Requested capabilities:",
        *[f"  - `{capability}`" for capability in capabilities],
        "- Requested paths:",
        *[
            f"  - `{item['workspace_relative'] or item['path']}` ({item['surface']})"
            for item in classifications
        ],
        "- Evidence:",
        "  - Add the missing registration, failure output, or task evidence here.",
        "- Proposed validation:",
        "  - Resolve the exact task and run its routed validation.",
        "- Structural reviewer: codex | claude | user",
        "- Decision: pending",
        "- Decision notes:",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return {
        "status": "CREATED",
        "request_id": request_id,
        "path": str(target),
        "capabilities": capabilities,
        "mode": mode,
    }


def render(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return
    if "agents" in payload:
        title = "Agent Registry" if payload["agents"] and "display_name" in payload["agents"][0] else "Agent Governance"
        print(title)
        for agent in payload["agents"]:
            if "display_name" in agent:
                print(
                    f"- {agent['agent']}: {agent['status']} / "
                    f"{agent['effective_role']} ({agent['identity_kind']})"
                )
            else:
                print(
                    f"- {agent['agent']}: {agent['registration_status']} / "
                    f"{agent['role']} ({', '.join(agent['capabilities'])})"
                )
        if title == "Agent Governance":
            print("- unregistered: consumer (read, invoke, proposal only)")
        return
    if "contract" in payload or payload.get("registered") is False:
        print(f"Agent registration: {payload['status']}")
        print(f"Agent: {payload['agent']}")
        print(f"Registered: {payload.get('registered', True)}")
        effective = payload.get("effective", {})
        if effective:
            print(f"Effective role: {effective.get('role')}")
            print(f"Degraded: {effective.get('degraded')}")
        if payload.get("contract"):
            print(yaml.safe_dump(payload["contract"], sort_keys=False, allow_unicode=True).rstrip())
        return
    if "diagnostics" in payload:
        print(f"Agent validation: {payload['status']}")
        print(f"Agent: {payload['agent']}")
        print(f"Effective role: {payload.get('effective_role')}")
        for item in payload["diagnostics"]:
            print(f"- {item['severity']} [{item['code']}]: {item['message']}")
        return
    if payload.get("request_id"):
        print(f"Agent request: {payload['status']}")
        print(f"Request: {payload['request_id']}")
        print(f"Path: {payload['path']}")
        return
    if "active" in payload:
        print(f"Lease validation: {payload['status']}")
        print(f"Active: {payload['active']}")
        for error in payload["errors"]:
            print(f"- {error}")
        return
    print(f"Access: {payload['status']}")
    print(f"Agent: {payload['agent']} ({payload['role']})")
    print(f"Registration: {payload.get('registration_status')}")
    print(f"Surface: {payload['surface']}")
    print(f"Required: {payload['required_capability']}")
    print(f"Reason: {payload['reason']}")
    if payload.get("next_action"):
        print(f"Next: {payload['next_action']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect and route workspace agent authority."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser(
        "status", help="Show effective agents and surface classes."
    )
    status.add_argument("--format", choices=("text", "json"), default="text")

    list_agents = commands.add_parser("list", help="List registration summaries.")
    list_agents.add_argument("--format", choices=("text", "json"), default="text")

    show = commands.add_parser("show", help="Show one resolved registration contract.")
    show.add_argument("agent_id")
    show.add_argument("--format", choices=("text", "json"), default="text")

    validate = commands.add_parser("validate", help="Validate one agent registration.")
    validate.add_argument("agent_id")
    validate.add_argument("--format", choices=("text", "json"), default="text")

    doctor = commands.add_parser(
        "doctor", help="Diagnose registration, policy, manifest, and storage consistency."
    )
    doctor.add_argument("agent_id")
    doctor.add_argument("--format", choices=("text", "json"), default="text")

    check = commands.add_parser(
        "check", help="Check whether an agent may read or write a path."
    )
    check.add_argument("--agent", required=True)
    check.add_argument("--operation", choices=("read", "write"), default="write")
    check.add_argument("--path", required=True)
    check.add_argument("--record-id")
    check.add_argument("--skill")
    check.add_argument("--lease")
    check.add_argument("--format", choices=("text", "json"), default="text")

    request = commands.add_parser("request", help="Create a reviewable change request.")
    request.add_argument("--agent", required=True)
    request.add_argument(
        "--mode",
        choices=("review_only", "temporary_lease", "worktree"),
        default="review_only",
    )
    request.add_argument("--summary", required=True)
    request.add_argument("--path", action="append", default=[])
    request.add_argument("--output")
    request.add_argument("--format", choices=("text", "json"), default="text")

    lease = commands.add_parser("lease", help="Validate an external capability lease.")
    lease_commands = lease.add_subparsers(dest="action", required=True)
    lease_validate = lease_commands.add_parser("validate")
    lease_validate.add_argument("lease_file")
    lease_validate.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_yaml(POLICY_PATH)
        registry = load_registry()
        manifest = load_manifest()
        if args.command == "status":
            payload = status_payload(policy, registry, manifest)
        elif args.command == "list":
            payload = list_payload(policy, registry, manifest)
        elif args.command == "show":
            payload = show_payload(policy, registry, manifest, args.agent_id)
        elif args.command == "validate":
            payload = validate_payload(policy, registry, manifest, args.agent_id)
        elif args.command == "doctor":
            payload = doctor_payload(policy, registry, manifest, args.agent_id)
        elif args.command == "check":
            lease = load_yaml(Path(args.lease)) if args.lease else None
            registration = None
            registration_error = None
            if args.operation == "write":
                target = classify_path(policy, manifest, args.path)
                if not args.record_id:
                    registration_error = "--record-id is required for a write check"
                else:
                    try:
                        registration = active_registration(
                            args.record_id,
                            (
                                "external_write"
                                if (
                                    target["surface"] == "external_environment"
                                    or target.get("requires_external_write")
                                )
                                else "workspace_write"
                            ),
                        )
                    except ValueError as error:
                        registration_error = str(error)
            payload = check_access(
                policy,
                manifest,
                agent_name=args.agent,
                operation=args.operation,
                raw_path=args.path,
                acting_skill=args.skill,
                lease=lease,
                registry=registry,
            )
            if registration:
                payload["task_registration"] = registration
            if registration_error:
                payload["status"] = "DENY"
                payload["reason"] = f"task registration denied: {registration_error}"
                payload["next_action"] = (
                    "Start an active task record with the required operation, "
                    "then pass it through --record-id."
                )
        elif args.command == "request":
            payload = create_request(
                policy,
                manifest,
                agent=args.agent,
                mode=args.mode,
                summary=args.summary,
                paths=args.path,
                output=args.output,
            )
        else:
            payload = validate_lease(policy, load_yaml(Path(args.lease_file)))
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        payload = {"status": "ERROR", "error": str(exc)}

    render(payload, args.format)
    if payload["status"] in {"PASS", "WARNING", "ALLOW", "CREATED"}:
        return 0
    return 2 if payload["status"] == "DENY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
