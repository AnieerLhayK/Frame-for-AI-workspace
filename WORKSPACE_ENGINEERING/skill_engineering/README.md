# Skill Engineering

Skill Engineering is a subdomain of Workspace Engineering concerned with the
design, implementation, evaluation, maintenance, and evolution of reusable AI
Skills.

Use this layer for:

- Skill responsibility and authority boundaries;
- prompt and invocation design;
- runtime diagnosis and maintenance loops;
- drift prevention and style alignment;
- deciding when a local fix should become generator or framework behavior.

Workspace-level concerns such as Agent registration, Git boundaries, platform
projections, Session continuity, output routing, and repository governance
belong in the parent `WORKSPACE_ENGINEERING/` layer.

Current references:

- `skill_design_patterns.md`
- `prompt_engineering.md`
- `runtime_loop_patterns.md`
- `drift_patterns.md`
- `style_alignment.md`
- `evolution_patterns.md`
