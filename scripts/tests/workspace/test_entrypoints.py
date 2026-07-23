from scripts.workspace.entrypoints import ENTRYPOINT_LIFECYCLE, ENTRYPOINT_MODULES


def test_retained_root_adapters_have_explicit_lifecycle() -> None:
    assert set(ENTRYPOINT_LIFECYCLE) == set(ENTRYPOINT_MODULES)
    assert ENTRYPOINT_LIFECYCLE["workspace_cli.py"] == "deprecated"
    assert ENTRYPOINT_LIFECYCLE["publish_public.py"] == "supported_until_replacement"


def test_retired_project_context_adapter_is_not_registered() -> None:
    assert "project_context_cli.py" not in ENTRYPOINT_MODULES
