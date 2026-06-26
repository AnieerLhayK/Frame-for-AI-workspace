# Workflow Reference: Diagnose Runtime Drift

Use `style-doctor` on a platform where it is currently exposed.

Inputs:

- failed output excerpt;
- user feedback;
- expected style direction;
- source character;
- task type.

Result:

- diagnosis packet;
- optional handoff packet.

This workflow should not patch files directly.

It should also avoid patch notes, validation notes, generalization notes, patch-ledger updates, and maintainer decisions. Those belong to `character-maintainer`.
