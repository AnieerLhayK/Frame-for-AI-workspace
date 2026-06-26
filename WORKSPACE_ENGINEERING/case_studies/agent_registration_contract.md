# Case Study: Agent Registration Contract

- Date: 2026-06-20
- Evidence level: Validated locally
- Scope: Agent identity, lifecycle, authority, platform, and storage governance

## Problem

A workspace may expose Skills to several AI tools without having a reliable way
to distinguish Agent identity, host application, platform visibility, Role,
path scope, registration lifecycle, and runtime storage boundaries.

Treating Skill visibility as authority lets an unknown or partially configured
Agent infer permissions it was never granted.

## Design

The solution separated four contracts:

```text
Agent Registration Contract
-> Role, capability, and surface policy
-> Manifest-backed platform exposure
-> Runtime access check
```

Concrete identity and lifecycle live in a centralized registry. Roles,
capabilities, surfaces, and lease constraints remain in policy. Platform and
Skill exposure facts remain in the Manifest.

## Safe Fallback

Unknown, incomplete, invalid, proposed, suspended, and retired registrations
resolve to Consumer. Missing data never expands authority.

Testing registrations require explicit capabilities, exact low-risk paths, a
review owner, an expiry, and no structural or platform write authority.

## Candidate Classification

Cursor and Reasonix demonstrated why identity, host, and client must remain
separate concepts. Existing evidence showed MCP client configuration, but did
not prove autonomous Agent identity or workspace Skill exposure. They were
therefore registered as proposed host/client candidates with Consumer access.

## Verification

The implementation covered alias conflicts, invalid roles and capabilities,
Consumer escalation, lifecycle expiry, inactive registrations with active
leases, exact testing scopes, preservation of existing Agent permissions, and
all existing CLI behavior. The full workspace test suite and health checks
passed before merge.

## Reusable Lessons

1. Exposure is not authority.
2. Registration is not authentication.
3. Identity, host, platform, Role, and trust source are independent dimensions.
4. Invalid registration should fail closed to a useful low-privilege mode.
5. Lifecycle state must affect runtime access, not merely documentation.
6. Experimental access needs precise scopes and expiry.
7. External data should not be created merely because an Agent was registered.
8. Structural migrations must update executable boundary guards, not only
   documentation and indexes.

## Limits

The local registry cannot cryptographically prove which process or model is
calling the CLI. Strong identity assurance would require platform-supported
attestation or authenticated execution boundaries.
