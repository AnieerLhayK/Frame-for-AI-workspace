"""The JavaScript bridge must fail closed if its guard cannot answer."""
import subprocess
from pathlib import Path


def test_bridge_denies_when_guard_is_unavailable():
    module = (Path(__file__).parents[2] / "platform" / "deepseek-workspace-bridge.mjs").as_uri()
    script = f"import {{ checkTool }} from '{module}'; console.log(checkTool({{name:'write',arguments:{{file_path:'x'}}}}));"
    result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    assert "unavailable" in result.stdout
