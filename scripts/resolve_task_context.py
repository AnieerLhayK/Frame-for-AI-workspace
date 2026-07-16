try:
    from _compat import load_legacy_module
except ModuleNotFoundError:
    from scripts._compat import load_legacy_module

_module = load_legacy_module("scripts.workspace.resolve_task_context", globals())

if __name__ == "__main__":
    _main = getattr(_module, "main", None)
    raise SystemExit(_main() if _main is not None else 0)
