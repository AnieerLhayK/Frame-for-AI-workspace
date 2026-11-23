"""Load the Workspace manifest and its owner-maintained skill catalogs.

The root manifest remains the source for platform and package configuration.
Skill registrations are read only from the catalog indexes named there; this
module is the single aggregation point for runtime ``skills`` consumers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON-compatible Workspace catalog {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Workspace catalog must contain an object: {path}")
    return value


def _inside(root: Path, value: str, *, label: str) -> Path:
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes Workspace source: {value}") from exc
    return candidate


def _read_entries(path: Path, key: str) -> list[dict[str, Any]]:
    payload = _read_object(path)
    entries = payload.get(key)
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ValueError(f"{path} must contain a {key} array of objects")
    return entries


def _validate_skill_sources(root: Path, skills: list[dict[str, Any]], owner: str, category: str | None = None) -> None:
    for skill in skills:
        skill_id = skill.get("id")
        source = skill.get("source_path")
        if not isinstance(skill_id, str) or not skill_id:
            raise ValueError(f"catalog skill is missing a non-empty id in {owner}")
        if skill.get("status", "active") not in {"active", "development", "retired"}:
            raise ValueError(f"skill {skill_id} has an invalid catalog status")
        if "workspace_registered" in skill and not isinstance(skill["workspace_registered"], bool):
            raise ValueError(f"skill {skill_id} workspace_registered must be boolean")
        if not isinstance(source, str) or not source:
            raise ValueError(f"catalog skill {skill_id} is missing source_path")
        source_path = _inside(root, source, label=f"{owner} skill source")
        relative_parts = Path(source.replace("\\", "/")).parts
        if not source_path.is_dir():
            raise ValueError(f"catalog skill source is missing: {source}")
        if owner in {"skills", "external-skills"}:
            if not relative_parts or relative_parts[0] != owner:
                raise ValueError(f"skill {skill_id} is registered under the wrong catalog owner: {source}")
            if category is not None and (len(relative_parts) < 3 or relative_parts[1] != category):
                raise ValueError(f"skill {skill_id} source does not match category {category}: {source}")
        else:
            try:
                source_path.relative_to(_inside(root, owner, label="package source"))
            except ValueError as exc:
                raise ValueError(f"package skill {skill_id} escapes its package source: {source}") from exc
        required_files = skill.get("required_files", ["SKILL.md"])
        if not isinstance(required_files, list) or "SKILL.md" not in required_files:
            raise ValueError(f"skill {skill_id} required_files must include SKILL.md")
        for relative in required_files:
            if not isinstance(relative, str) or not relative:
                raise ValueError(f"skill {skill_id} has an invalid required file")
            required_path = _inside(source_path, relative, label=f"{skill_id} required file")
            if not required_path.is_file() or required_path.stat().st_size == 0:
                raise ValueError(f"skill {skill_id} required file is missing or empty: {relative}")


def load_manifest(path: Path) -> dict[str, Any]:
    """Load root manifest and aggregate catalog entries into ``skills``.

    Legacy manifests without ``skill_catalogs`` continue to return their root
    ``skills`` array unchanged, allowing consumers to migrate incrementally.
    """
    manifest = _read_object(path)
    root = path.resolve().parent
    catalog_roots = manifest.get("skill_catalogs")
    if catalog_roots is None:
        return manifest
    if not isinstance(catalog_roots, dict):
        raise ValueError("skill_catalogs must be an object")
    if set(catalog_roots) != {"skills", "external-skills"}:
        raise ValueError("skill_catalogs must declare exactly skills and external-skills")

    skills: list[dict[str, Any]] = []
    for owner, relative_root in catalog_roots.items():
        if not isinstance(relative_root, str):
            raise ValueError(f"skill catalog root for {owner!r} must be a path")
        catalog_root = _inside(root, relative_root, label=f"skill catalog root {owner}")
        index_path = _inside(root, f"{relative_root}/catalog.json", label="catalog index")
        index = _read_object(index_path)
        categories = index.get("categories")
        if not isinstance(categories, list) or any(not isinstance(item, str) for item in categories):
            raise ValueError(f"{index_path} must declare categories as string paths")
        if len(categories) != len(set(categories)):
            raise ValueError(f"{index_path} contains duplicate category registry paths")
        for relative_registry in categories:
            registry_path = _inside(catalog_root, relative_registry, label="category registry")
            category_skills = _read_entries(registry_path, "skills")
            registry = _read_object(registry_path)
            registry_parts = Path(relative_registry.replace("\\", "/")).parts
            if len(registry_parts) != 2 or registry_parts[1] != "registry.json":
                raise ValueError(f"category registry path must be <category>/registry.json: {relative_registry}")
            category = registry_parts[0]
            if registry.get("owner") != owner or registry.get("category") != category:
                raise ValueError(f"category registry ownership mismatch: {registry_path}")
            _validate_skill_sources(root, category_skills, owner, category)
            skills.extend(category_skills)

    for package in manifest.get("packages", []):
        if not isinstance(package, dict):
            raise ValueError("packages must contain objects")
        package_manifest = package.get("package_catalog")
        if package_manifest is None:
            raise ValueError(f"package {package.get('id', '<unknown>')} is missing package_catalog")
        package_path = _inside(root, str(package_manifest), label="package catalog")
        package_payload = _read_object(package_path)
        package_id = package.get("id")
        if package_payload.get("package_id") != package_id:
            raise ValueError(f"package catalog identity mismatch: {package_path}")
        for skill in _read_entries(package_path, "skills"):
            _validate_skill_sources(root, [skill], str(package["source_path"]))
            if skill.get("workspace_registered") is False or skill.get("status", "active") != "active":
                continue
            skills.append(skill)

    ids: set[str] = set()
    for skill in skills:
        skill_id = skill.get("id")
        if not isinstance(skill_id, str) or not skill_id:
            raise ValueError("catalog skill is missing a non-empty id")
        if skill_id in ids:
            raise ValueError(f"duplicate registered skill id: {skill_id}")
        ids.add(skill_id)
    manifest["skills"] = skills
    return manifest
