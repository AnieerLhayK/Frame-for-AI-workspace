# Character System Package

This package groups the related character-skill runtime and engineering tools.
Platform names do not define source ownership.

## Runtime

`runtime/` contains user-facing character skills that produce task output.

## Engineering

`engineering/` contains generation, diagnosis, and maintenance skills used to
build, inspect, and evolve runtime characters.

## Shared

`shared/` contains protocols, templates, and schemas that apply only to this
package. Workspace-wide path, discovery, failure, reporting, and portability
rules remain in the root `shared/` directory.

## Reports

`reports/runtime-loop/` stores durable diagnosis, handoff, patch, validation,
and generalization records for this package.
