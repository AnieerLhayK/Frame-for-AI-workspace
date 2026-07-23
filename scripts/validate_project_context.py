"""Compatibility entry point for PROJECT_CONTEXT validation."""

try:
    from _compat import load_legacy_module
except ModuleNotFoundError:
    from scripts._compat import load_legacy_module

_module = load_legacy_module("scripts.validation.validate_project_context", globals())


if __name__ == "__main__":
    raise SystemExit(_module.main())
