# Skill Engineering Knowledge Base Setup Report

## Snapshot Header

- report_name: skill_engineering_setup_report
- generated_at: 2026-05-28
- generated_by: Codex
- source_root: ${WORKSPACE_ROOT}
- report_scope: SKILL_ENGINEERING knowledge layer setup
- report_is_snapshot: true
- truth_source: workspace_manifest.yaml, PROJECT_CONTEXT/, shared/, current Git state

## Added Files

- `SKILL_ENGINEERING/README.md`
- `SKILL_ENGINEERING/philosophy.md`
- `SKILL_ENGINEERING/architecture_patterns.md`
- `SKILL_ENGINEERING/skill_design_patterns.md`
- `SKILL_ENGINEERING/prompt_engineering.md`
- `SKILL_ENGINEERING/anti_patterns.md`
- `SKILL_ENGINEERING/runtime_loop_patterns.md`
- `SKILL_ENGINEERING/governance_patterns.md`
- `SKILL_ENGINEERING/portability_patterns.md`
- `SKILL_ENGINEERING/workspace_patterns.md`
- `SKILL_ENGINEERING/evolution_patterns.md`
- `SKILL_ENGINEERING/style_alignment.md`
- `SKILL_ENGINEERING/drift_patterns.md`
- `SKILL_ENGINEERING/case_studies/README.md`
- `SKILL_ENGINEERING/templates/README.md`
- `SKILL_ENGINEERING/experiments/README.md`
- `SKILL_ENGINEERING/reports/README.md`
- `SKILL_ENGINEERING/reports/skill_engineering_setup_report.md`

## File Roles

- `README.md`: defines the layer and its relationship to PROJECT_CONTEXT, shared, reports, runtime loop, and manifest.
- `philosophy.md`: records core design principles and tradeoffs.
- `architecture_patterns.md`: records reusable ecosystem architecture patterns.
- `skill_design_patterns.md`: separates generator, maintainer, diagnosis, runtime character, governance, and validator skill roles.
- `prompt_engineering.md`: captures prompt structures that reduce scope drift and dangerous automation.
- `anti_patterns.md`: lists high-risk mistakes and safer alternatives.
- `runtime_loop_patterns.md`: captures reusable runtime loop lessons.
- `governance_patterns.md`: records governance, validation, snapshot, and failure-policy patterns.
- `portability_patterns.md`: captures manifest and bootstrap portability lessons.
- `workspace_patterns.md`: explains reusable workspace layer boundaries.
- `evolution_patterns.md`: captures gradual skill evolution practices.
- `style_alignment.md`: records style drift and alignment observations.
- `drift_patterns.md`: names recurring drift classes.
- subdirectory README files: reserve space for future case studies, templates, experiments, and retrospectives.

## Difference From PROJECT_CONTEXT

`PROJECT_CONTEXT/` is the current workspace memory layer. It records this project's status, decisions, risks, todo items, and session handoff.

`SKILL_ENGINEERING/` is cross-project engineering memory. It records reusable lessons about building skills, validators, runtime loops, workspaces, and prompt governance.

## Difference From Shared

`shared/` contains protocol contracts that the current workspace can check or enforce.

`SKILL_ENGINEERING/` contains experience-based patterns. These are not automatically binding and may be replaced by future evidence.

## Future Maintenance

Keep this layer current when a real engineering lesson emerges from a new skill, workspace migration, runtime drift repair, validator change, or governance failure.

## Current Experience Limits

Much of this knowledge is drawn from the current character-skill ecosystem. It should be treated as strong local experience, not universal doctrine.

## Future Expansion

Add real case studies after runtime fixes, portability events, validator failures, or generator/maintainer evolution decisions. Add templates only after they prove reusable.

## Suggested Commit Message

Add long-term skill engineering knowledge base

