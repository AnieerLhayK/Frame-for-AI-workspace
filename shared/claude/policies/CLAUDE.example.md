# Project Model-Tiering Examples

Claude Code resolves relative imports from the `CLAUDE.md` file containing
them. Use forward slashes in import paths for portability.

## Example A: Normal Project

The project inherits the user-level Model Tiering Principle and needs no
model-specific project configuration:

```markdown
# Project Instructions

Follow this project's build, test, review, and safety requirements.
```

## Example B: Project Explicitly Enables the Shared Policy

Import the current detailed implementation, then add only project-specific
differences:

```markdown
# Project Instructions

@shared/claude/policies/model-routing-policy.md

Follow this project's build, test, review, and safety requirements.
```

If the shared source is outside the project and the host cannot read it, copy
the policy into `.claude/policies/model-routing-policy.md` and use:

```text
@.claude/policies/model-routing-policy.md
```

## Example C: Project Disables Escalation Recommendations

A project rule overrides the user-level principle and any imported shared
policy:

```markdown
# Project Instructions

This project disables model escalation recommendations.

Always remain on the default model unless the user explicitly asks otherwise.
```

## Future Policy Imports

Keep policies separate so projects can adopt or override them independently:

```text
@shared/claude/policies/model-routing-policy.md
@shared/claude/policies/security-review-policy.md
@shared/claude/policies/release-policy.md
```
