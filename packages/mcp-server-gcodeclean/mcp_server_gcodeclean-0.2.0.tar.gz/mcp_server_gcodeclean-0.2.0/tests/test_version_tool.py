import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_gcodeclean import mcp
import asyncio


async def test_version_tool():
    """Test the get_gcodeclean_version tool."""
    async with mcp.client() as client:
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        version_result = await client.call_tool("get_gcodeclean_version", {})
        print("\n=== GCodeClean Version Tool Output ===")
        print(f"Status: {version_result['status']}")
        print(f"Binary path: {version_result['binary_path']}")
        print(f"Bundled binary: {version_result['bundled_binary']}")
        print(f"Platform: {version_result['platform']}")
        print(f"Version output: {version_result['version_output']}")
        print(f"Exit code: {version_result['exit_code']}")
        print(f"Error: {version_result['error']}")

        assert version_result['status'] == 'SUCCESS', "Version tool should succeed"
        assert version_result['exit_code'] == 0, "Exit code should be 0"
        assert 'osx-arm64' in version_result['binary_path'], "Should use ARM64 binary"

        print("\n[PASS] Version tool test passed")


if __name__ == "__main__":
    asyncio.run(test_version_tool())
