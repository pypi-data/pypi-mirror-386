import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_gcodeclean.server import _validate_gcode_syntax_impl as validate_gcode_syntax


def check_gcodeclean_installed():
    """Check if GCodeClean is available."""
    gcc_path = os.environ.get("GCODECLEAN_PATH", "GCC")

    try:
        result = subprocess.run(
            [gcc_path, "--help"],
            capture_output=True,
            timeout=5
        )

        if "clean" in result.stdout.decode().lower() or "gcode" in result.stdout.decode().lower():
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return False


def test_basic_validation():
    """Test basic G-code validation."""
    gcode = """G90
G21
G0 X0 Y0
M3 S1000
G1 Z-5 F100
"""

    result = validate_gcode_syntax(gcode)

    assert result["status"] in ["PASSED", "FAILED", "ERROR", "TIMEOUT"]
    assert "passed" in result
    assert "statistics" in result
    assert "original_lines" in result["statistics"]
    assert "original_size_bytes" in result["statistics"]

    print("[PASS] Basic validation test passed")
    print(f"  Status: {result['status']}")
    print(f"  Passed: {result['passed']}")
    print(f"  Original lines: {result['statistics']['original_lines']}")
    print(f"  Original size: {result['statistics']['original_size_bytes']} bytes")


def test_file_size_limit():
    """Test that files exceeding 10MB are rejected."""
    large_gcode = "G0 X0 Y0\n" * 2_000_000

    result = validate_gcode_syntax(large_gcode)

    print(f"  Large file status: {result['status']}")
    print(f"  Large file size: {len(large_gcode.encode('utf-8'))} bytes")

    assert result["status"] == "ERROR", f"Expected ERROR but got {result['status']}: {result.get('error', 'no error')}"
    assert not result["passed"], f"Expected passed=False but got {result['passed']}"
    assert "10MB" in result["error"], f"Expected '10MB' in error but got: {result['error']}"

    print("[PASS] File size limit test passed")


def test_empty_input():
    """Test handling of empty input."""
    result = validate_gcode_syntax("")

    assert result["status"] in ["PASSED", "FAILED", "ERROR"]
    assert "statistics" in result

    print("[PASS] Empty input test passed")


def test_with_parameters():
    """Test validation with different parameters."""
    gcode = """G90
G21
G1 X10 Y10 F100
"""

    result = validate_gcode_syntax(
        gcode,
        tolerance=0.05,
        minimise="hard",
        annotate=True
    )

    assert result["status"] in ["PASSED", "FAILED", "ERROR", "TIMEOUT"]
    assert "statistics" in result

    print("[PASS] Parameter test passed")


if __name__ == "__main__":
    print("Running MCP Server GCodeClean Tests\n")

    if not check_gcodeclean_installed():
        print("[WARN] GCodeClean not found")
        print("  Install GCodeClean from: https://github.com/aersida/GCodeClean")
        print("  Set GCODECLEAN_PATH environment variable to the binary location")
        print("\nSkipping validation tests (GCodeClean required)")
        print("\nRunning tests that don't require GCodeClean:")
        try:
            test_file_size_limit()
            print()
            print("Basic tests passed!")
            print("Install GCodeClean to run full validation tests.")
        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            sys.exit(1)
        sys.exit(0)

    try:
        test_basic_validation()
        print()
        test_file_size_limit()
        print()
        test_empty_input()
        print()
        test_with_parameters()
        print()
        print("All tests passed!")
    except AssertionError as e:
        import traceback
        print(f"\n[FAIL] Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n[FAIL] Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
