# Anieer Skills

A generated collection of Codex skills. Portability and host requirements vary by skill; check each entry before installing.

## Related project

- [Frame-for-AI-workspace](https://github.com/AnieerLhayK/Frame-for-AI-workspace): the governed framework and source project for this collection.

## Included skills

{included_skills}

Each directory is a skill source package. Read its `SKILL.md`; do not edit generated copies when a managed source is available.

## Install and use

Copy one selected `skills/<category>/<id>/` directory into your Codex skill directory, then invoke it by its frontmatter name. Check the listed host requirements first; workspace-bound skills require their documented Workspace services and are not standalone portable tools. Keep the directory intact so its scripts and references remain available.

Skills marked `internal-only` are never eligible for this public collection. The registered contract is the explicit allowlist for all other releases.

## Maintenance

This repository is generated from its managed workspace source. Propose changes against that source, update the projection boundary and tests, then regenerate the collection. Do not patch the generated repository directly; direct changes will be replaced at the next synchronization.
