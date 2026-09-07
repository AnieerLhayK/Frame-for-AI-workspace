# Skill release

Release `<target-skill>` from its authoritative Workspace source. Treat generated projections and remote checkouts as read-only outputs, never editable sources.

1. Bind the exact source and registered publisher. Create the required Workspace write record; add `external_write` only when an actual external write or push is explicitly authorized.
2. Generate into an approved staging path. Do not write directly to a registered target.
3. Validate the staged bundle, record the source revision, and calculate the publisher-defined checksums.
4. Publish only through the registered publisher to its registered target. Without external-write authority, stop after a verified dry run.
5. Return an audit receipt containing scope, mode, authority used, source revision, staging evidence, validation/checksum evidence, target result, and the stop or next-step condition.

Completion requires source/staging/target traceability. A successful local validation is not permission to push.
