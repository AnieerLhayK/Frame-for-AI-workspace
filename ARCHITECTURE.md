# Architecture

This repository is a framework template for a governed AI workspace. It is
organized around a small set of portable layers:

- `workspace_manifest.yaml`: source-of-truth registry for this template.
- `shared/`: reusable policies and contracts for bounded discovery and writes.
- `scripts/`: framework utilities for routing, health, setup, and validation.
- `skills/`: skills developed for your workspace.
- `external-skills/`: reviewed third-party skills.
- `PROJECT_CONTEXT/`: optional workspace memory and routing context.

Add domain packages after reviewing their source,
privacy, licensing, and deployment boundaries.

## Deployment Boundary

The first-run helper configures only template paths and performs read-only
checks. It does not install providers, create platform links, or grant extra
permissions. A healthy deployment means the framework CLI and tests run; a
platform-specific health warning is expected until that platform is configured.
