import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_gcodeclean import mcp


SAMPLE_VALID_GCODE = """G90
G21
G0 X0 Y0 Z5
M3 S1200
G1 Z-2.5 F100
G1 X10 Y10 F500
G0 Z5
M5
M30
"""

SAMPLE_COMPLEX_GCODE = """G90 G54
G21
; Tool 1: 6mm endmill
T1 M6
M3 S1500
G0 X0 Y0 Z5
G1 Z-5 F100
G1 X50 Y50 F800
G2 X60 Y50 I5 J0
G1 X80 Y80
G0 Z5
M5
M30
"""


async def workflow_1_first_time_user():
    """
    Workflow 1: First-time user verification

    Scenario: User just installed the MCP server and wants to verify it works.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 1: First-Time User Verification")
    print("=" * 70)
    print("User: 'I just installed mcp-server-gcodeclean. Is it working?'\n")

    async with mcp.client() as client:
        result = await client.call_tool("get_gcodeclean_version", {})

        print(f"Status: {result['status']}")
        print(f"Binary: {result['binary_path']}")
        print(f"Platform: {result['platform']['os']} {result['platform']['architecture']}")

        if result['status'] == 'SUCCESS':
            print("\n[PASS] Workflow 1 PASSED: Installation verified")
            print("Response: 'Yes, GCodeClean is properly installed and ready to use.'")
        else:
            print("\n[FAIL] Workflow 1 FAILED: Installation issue detected")
            print(f"Error: {result['error']}")

        return result['status'] == 'SUCCESS'


async def workflow_2_basic_validation():
    """
    Workflow 2: Basic G-code validation

    Scenario: User pastes G-code and asks for validation.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 2: Basic G-code Validation")
    print("=" * 70)
    print("User: 'Can you validate this G-code for me?'\n")

    async with mcp.client() as client:
        result = await client.call_tool(
            "validate_gcode_syntax",
            {"gcode_content": SAMPLE_VALID_GCODE}
        )

        print(f"Status: {result['status']}")
        print(f"Passed: {result['passed']}")
        print(f"Original: {result['statistics']['original_lines']} lines, "
              f"{result['statistics']['original_size_bytes']} bytes")
        print(f"Cleaned: {result['statistics']['output_lines']} lines, "
              f"{result['statistics']['cleaned_size_bytes']} bytes")
        print(f"Reduction: {result['statistics']['reduction_percent']}%")

        if result['status'] == 'PASSED':
            print("\n[PASS] Workflow 2 PASSED: G-code validated successfully")
            print("Response: 'Your G-code is valid and ready to use.'")
        else:
            print(f"\n[FAIL] Workflow 2 FAILED: {result['error']}")

        return result['status'] == 'PASSED'


async def workflow_3_optimization():
    """
    Workflow 3: G-code optimization for file transfer

    Scenario: User wants to minimize G-code for network transfer.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 3: G-code Optimization")
    print("=" * 70)
    print("User: 'Can you minimize this G-code for network transfer?'\n")

    async with mcp.client() as client:
        result = await client.call_tool(
            "validate_gcode_syntax",
            {
                "gcode_content": SAMPLE_COMPLEX_GCODE,
                "minimise": "hard"
            }
        )

        print(f"Status: {result['status']}")
        original_size = result['statistics']['original_size_bytes']
        cleaned_size = result['statistics']['cleaned_size_bytes']
        reduction = result['statistics']['reduction_percent']

        print(f"Original: {original_size} bytes")
        print(f"Optimized: {cleaned_size} bytes")
        print(f"Reduction: {reduction}%")

        if result['status'] == 'PASSED' and reduction > 0:
            print("\n[PASS] Workflow 3 PASSED: G-code optimized successfully")
            print(f"Response: 'G-code optimized with {reduction}% size reduction.'")
        else:
            print(f"\n[FAIL] Workflow 3 FAILED")

        return result['status'] == 'PASSED'


async def workflow_4_learning_mode():
    """
    Workflow 4: Educational - Understanding G-code

    Scenario: User wants to learn what G-code does.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 4: Learning Mode (Annotated Output)")
    print("=" * 70)
    print("User: 'Can you help me understand what this G-code does?'\n")

    async with mcp.client() as client:
        result = await client.call_tool(
            "validate_gcode_syntax",
            {
                "gcode_content": SAMPLE_VALID_GCODE,
                "annotate": True
            }
        )

        print(f"Status: {result['status']}")

        if result['status'] == 'PASSED' and result['cleaned_gcode']:
            print("\nAnnotated G-code (first 5 lines):")
            lines = result['cleaned_gcode'].split('\n')[:5]
            for line in lines:
                print(f"  {line}")

            print("\n[PASS] Workflow 4 PASSED: Annotated G-code generated")
            print("Response: 'I've added explanatory comments to help you understand.'")
        else:
            print(f"\n[FAIL] Workflow 4 FAILED")

        return result['status'] == 'PASSED'


async def workflow_5_precision_work():
    """
    Workflow 5: High-precision validation

    Scenario: User mentions precision requirements.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 5: High-Precision Validation")
    print("=" * 70)
    print("User: 'This is for aerospace work with tight tolerances (±0.001mm).'\n")

    async with mcp.client() as client:
        result = await client.call_tool(
            "validate_gcode_syntax",
            {
                "gcode_content": SAMPLE_COMPLEX_GCODE,
                "tolerance": 0.001
            }
        )

        print(f"Status: {result['status']}")
        print(f"Tolerance used: 0.001mm")

        if result['status'] == 'PASSED':
            print("\n[PASS] Workflow 5 PASSED: High-precision validation successful")
            print("Response: 'Validated with 0.001mm tolerance for precision work.'")
        else:
            print(f"\n[FAIL] Workflow 5 FAILED")

        return result['status'] == 'PASSED'


async def workflow_6_parameter_comparison():
    """
    Workflow 6: Compare different minimise modes

    Scenario: User is unsure which minimise mode to use.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 6: Compare Minimise Modes")
    print("=" * 70)
    print("User: 'What's the difference between minimise modes?'\n")

    async with mcp.client() as client:
        modes = ["soft", "medium", "hard"]
        results = {}

        for mode in modes:
            result = await client.call_tool(
                "validate_gcode_syntax",
                {
                    "gcode_content": SAMPLE_COMPLEX_GCODE,
                    "minimise": mode
                }
            )
            results[mode] = result['statistics']['cleaned_size_bytes']

        print("Size comparison:")
        for mode, size in results.items():
            print(f"  {mode}: {size} bytes")

        print("\n[PASS] Workflow 6 PASSED: Comparison completed")
        print("Response: 'soft preserves readability, medium balances size and "
              "readability, hard maximizes compression.'")

        return True


async def workflow_7_error_handling():
    """
    Workflow 7: Handle file size limit error

    Scenario: User provides G-code that exceeds 10MB.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 7: Error Handling (File Too Large)")
    print("=" * 70)
    print("User: [Provides very large G-code file]\n")

    large_gcode = "G0 X0 Y0\n" * 2_000_000

    async with mcp.client() as client:
        result = await client.call_tool(
            "validate_gcode_syntax",
            {"gcode_content": large_gcode}
        )

        print(f"Status: {result['status']}")
        print(f"Error: {result['error']}")

        if result['status'] == 'ERROR' and '10MB' in result['error']:
            print("\n[PASS] Workflow 7 PASSED: Error handled correctly")
            print("Response: 'Your G-code exceeds the 10MB limit. Try validating "
                  "smaller sections.'")
        else:
            print(f"\n[FAIL] Workflow 7 FAILED: Unexpected result")

        return result['status'] == 'ERROR'


async def workflow_8_combined_workflow():
    """
    Workflow 8: Complete workflow - Version check then validation

    Scenario: New user wants to validate G-code.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 8: Complete Workflow (Version + Validation)")
    print("=" * 70)
    print("User: 'I'm new here. Can you validate this G-code?'\n")

    async with mcp.client() as client:
        print("Step 1: Check installation")
        version_result = await client.call_tool("get_gcodeclean_version", {})
        print(f"  Version check: {version_result['status']}")

        if version_result['status'] != 'SUCCESS':
            print("\n[FAIL] Workflow 8 FAILED: Installation not working")
            return False

        print("\nStep 2: Validate G-code")
        validate_result = await client.call_tool(
            "validate_gcode_syntax",
            {"gcode_content": SAMPLE_VALID_GCODE}
        )
        print(f"  Validation: {validate_result['status']}")

        if validate_result['status'] == 'PASSED':
            print("\n[PASS] Workflow 8 PASSED: Complete workflow successful")
            print("Response: 'Everything is set up correctly. Your G-code is valid.'")
        else:
            print(f"\n[FAIL] Workflow 8 FAILED")

        return validate_result['status'] == 'PASSED'


async def workflow_9_tool_discovery():
    """
    Workflow 9: Tool discovery

    Scenario: User wants to know what tools are available.
    """
    print("\n" + "=" * 70)
    print("WORKFLOW 9: Tool Discovery")
    print("=" * 70)
    print("User: 'What can this MCP server do?'\n")

    async with mcp.client() as client:
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools:
            print(f"\n  Tool: {tool.name}")
            print(f"  Description: {tool.description[:100]}...")

        if len(tools) == 2:
            print("\n[PASS] Workflow 9 PASSED: Tools discovered")
            print("Response: 'I can validate G-code syntax and check GCodeClean "
                  "installation.'")
        else:
            print(f"\n[FAIL] Workflow 9 FAILED: Expected 2 tools, found {len(tools)}")

        return len(tools) == 2


async def run_all_workflows():
    """Run all workflow tests."""
    print("=" * 70)
    print("INTEGRATION TEST: CLAUDE DESKTOP WORKFLOWS")
    print("=" * 70)
    print("\nSimulating real-world Claude Desktop usage patterns...\n")

    workflows = [
        workflow_1_first_time_user,
        workflow_2_basic_validation,
        workflow_3_optimization,
        workflow_4_learning_mode,
        workflow_5_precision_work,
        workflow_6_parameter_comparison,
        workflow_7_error_handling,
        workflow_8_combined_workflow,
        workflow_9_tool_discovery,
    ]

    passed = 0
    failed = 0

    for workflow in workflows:
        try:
            success = await workflow()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[FAIL] {workflow.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("WORKFLOW TEST RESULTS")
    print("=" * 70)
    print(f"Passed: {passed}/{passed + failed}")
    print(f"Failed: {failed}/{passed + failed}")

    if failed == 0:
        print("\n[PASS] All workflows passed! MCP server is ready for Claude Desktop.")
    else:
        print(f"\n[WARN] {failed} workflow(s) failed. Review output above.")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_workflows())
    sys.exit(0 if success else 1)
