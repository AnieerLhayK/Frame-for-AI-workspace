# Codex Harness Profile

Status: reference profile; DSH loading and enforcement are not yet verified.

## Workspace sources

- `AGENTS.md` at the Workspace root: startup, task, authority and delivery rules.
- `USAGE_GUIDES/QUICK_START/codex.md`: current registered discovery and source rules.
- `shared/governance/agent_registry.yaml` and
  `shared/governance/agent_governance_policy.md`: actor identity and authority.
- `workspace_manifest.yaml` and its referenced skill catalogs: registered sources
  and projections. Discoverability does not grant execution authority.
- `workspace task resolve <task-id>` and `workspace workflow check`: current
  task-specific context, validation and scope. Do not guess unresolved bindings.

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [OpenAI guidance on skill and instruction design](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

These references describe their own host. A DSH adaptation may reuse the
workflow concepts but must test its own loading, tool and security behavior.
In particular, a prompt, skill or host instruction is not a filesystem sandbox.
