import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP


mcp = FastMCP(
    name="GCodeClean Validator",
)


def _count_lines(content: str) -> int:
    """Count lines in text content."""
    if not content:
        return 0
    return content.count('\n') + (0 if content.endswith('\n') else 1)


def _get_version_info() -> dict:
    """Load version info from version.json."""
    package_dir = Path(__file__).parent

    version_file = package_dir / "resources" / "gcodeclean" / "version.json"
    if not version_file.exists():
        version_file = package_dir.parent.parent / "resources" / "gcodeclean" / "version.json"

    if not version_file.exists():
        return {"version": "1.4.2"}

    try:
        with open(version_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {"version": "1.4.2"}


def detect_bundled_binary() -> str | None:
    """Detect bundled GCodeClean binary for current platform."""
    package_dir = Path(__file__).parent
    version_info = _get_version_info()
    version = version_info.get("version", "1.4.2")

    resources_dir = package_dir / "resources" / "gcodeclean" / version
    if not resources_dir.exists():
        resources_dir = package_dir.parent.parent / "resources" / "gcodeclean" / version

    if not resources_dir.exists():
        return None

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if "arm" in machine or "aarch64" in machine:
            binary_path = resources_dir / "linux-arm" / "GCC"
        else:
            binary_path = resources_dir / "linux-x64" / "GCC"
    elif system == "darwin":
        if machine == "arm64":
            arm_binary = resources_dir / "osx-arm64" / "GCC"
            if arm_binary.exists():
                binary_path = arm_binary
            else:
                binary_path = resources_dir / "osx-x64" / "GCC"
        else:
            binary_path = resources_dir / "osx-x64" / "GCC"
    elif system == "windows":
        binary_path = resources_dir / "win-x64" / "GCC.exe"
    else:
        return None

    return str(binary_path) if binary_path.exists() else None


def get_gcodeclean_path() -> str:
    """Get GCodeClean binary path with priority: env var > bundled > system PATH."""
    if path := os.environ.get("GCODECLEAN_PATH"):
        return path

    if bundled := detect_bundled_binary():
        return bundled

    return "GCC"


def _validate_gcode_syntax_impl(
    gcode_content: str,
    tolerance: float = 0.01,
    minimise: Literal["soft", "medium", "hard"] = "soft",
    annotate: bool = False,
) -> dict:
    """
    Validate G-code syntax using GCodeClean.

    Processes G-code through GCodeClean for syntax validation and cleaning.
    Returns validation status, cleaned code, and processing statistics.

    Args:
        gcode_content: Raw G-code text to validate
        tolerance: Clipping tolerance in mm (default: 0.01)
        minimise: Token removal strategy - 'soft', 'medium', or 'hard' (default: 'soft')
        annotate: Add explanatory comments to output (default: False)

    Returns:
        Dictionary containing:
        - status: PASSED, FAILED, ERROR, or TIMEOUT
        - passed: Boolean validation result
        - cleaned_gcode: Processed G-code or None on failure
        - statistics: Processing metrics (line counts, file sizes, reduction %)
        - error: Error message if applicable
        - stdout: GCodeClean stdout output
    """

    if tolerance <= 0 or tolerance > 10:
        return {
            "status": "ERROR",
            "passed": False,
            "cleaned_gcode": None,
            "statistics": {
                "original_lines": _count_lines(gcode_content),
                "output_lines": 0,
                "original_size_bytes": len(gcode_content.encode('utf-8')),
                "cleaned_size_bytes": 0,
                "reduction_percent": 0.0,
            },
            "error": "Invalid tolerance: must be between 0 and 10mm",
            "stdout": "",
        }

    original_size = len(gcode_content.encode('utf-8'))
    original_lines = _count_lines(gcode_content)

    if original_size > 10 * 1024 * 1024:
        return {
            "status": "ERROR",
            "passed": False,
            "cleaned_gcode": None,
            "statistics": {
                "original_lines": original_lines,
                "output_lines": 0,
                "original_size_bytes": original_size,
                "cleaned_size_bytes": 0,
                "reduction_percent": 0.0,
            },
            "error": "Input exceeds 10MB limit",
            "stdout": "",
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.gcode"
        input_file.write_text(gcode_content, encoding='utf-8')

        output_file = Path(tmpdir) / "input-gcc.gcode"

        gcc_path = get_gcodeclean_path()

        cmd = [
            gcc_path,
            "clean",
            "--filename", str(input_file),
            "--minimise", minimise,
            "--tolerance", str(tolerance),
        ]

        if annotate:
            cmd.append("--annotate")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tmpdir,
            )
            elapsed = time.time() - start_time

            if result.returncode == 0 and output_file.exists():
                cleaned_content = output_file.read_text(encoding='utf-8')
                cleaned_size = len(cleaned_content.encode('utf-8'))
                cleaned_lines = _count_lines(cleaned_content)
                reduction = ((original_size - cleaned_size) / original_size * 100) if original_size > 0 else 0.0

                return {
                    "status": "PASSED",
                    "passed": True,
                    "cleaned_gcode": cleaned_content,
                    "statistics": {
                        "original_lines": original_lines,
                        "output_lines": cleaned_lines,
                        "original_size_bytes": original_size,
                        "cleaned_size_bytes": cleaned_size,
                        "reduction_percent": round(reduction, 2),
                    },
                    "error": None,
                    "stdout": result.stdout,
                }
            else:
                if result.stderr:
                    error_msg = result.stderr
                elif result.returncode != 0:
                    error_msg = f"GCodeClean exited with code {result.returncode}. The G-code may contain syntax errors or unsupported commands."
                else:
                    error_msg = "GCodeClean completed but did not produce output file"

                return {
                    "status": "FAILED",
                    "passed": False,
                    "cleaned_gcode": None,
                    "statistics": {
                        "original_lines": original_lines,
                        "output_lines": 0,
                        "original_size_bytes": original_size,
                        "cleaned_size_bytes": 0,
                        "reduction_percent": 0.0,
                    },
                    "error": error_msg,
                    "stdout": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "passed": False,
                "cleaned_gcode": None,
                "statistics": {
                    "original_lines": original_lines,
                    "output_lines": 0,
                    "original_size_bytes": original_size,
                    "cleaned_size_bytes": 0,
                    "reduction_percent": 0.0,
                },
                "error": "Validation timed out after 30 seconds",
                "stdout": "",
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "passed": False,
                "cleaned_gcode": None,
                "statistics": {
                    "original_lines": original_lines,
                    "output_lines": 0,
                    "original_size_bytes": original_size,
                    "cleaned_size_bytes": 0,
                    "reduction_percent": 0.0,
                },
                "error": f"Unexpected error: {str(e)}",
                "stdout": "",
            }


@mcp.tool
def get_gcodeclean_version() -> dict:
    """
    Verify GCodeClean installation and get configuration details.

    This diagnostic tool checks that GCodeClean is properly installed and
    accessible. Use this tool to troubleshoot installation issues or verify
    which binary (bundled vs. custom) is being used.

    When to use:
    - First-time setup verification
    - User asks "Is GCodeClean working?" or "What version do I have?"
    - Troubleshooting validation errors
    - Confirming binary path or platform detection

    Returns:
        Dictionary containing:
        - status: "SUCCESS" if binary is accessible, "ERROR" otherwise
        - binary_path: Path to the GCodeClean binary being used
        - bundled_binary: Path to bundled binary (if available)
        - platform: Operating system, architecture, and Python version
        - version_output: Raw output from GCC --version command
        - exit_code: Process exit code (0 = success)
        - error: Error message if binary is not accessible

    Example usage:
        When user asks: "Can you check if GCodeClean is installed?"
        Response: "Yes, GCodeClean v1.4.2 is working. You're using the bundled
                  ARM64 binary optimized for Apple Silicon."
    """
    gcc_path = get_gcodeclean_path()
    bundled = detect_bundled_binary()

    system_info = {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }

    try:
        result = subprocess.run(
            [gcc_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return {
            "status": "SUCCESS",
            "binary_path": gcc_path,
            "bundled_binary": bundled,
            "platform": system_info,
            "version_output": result.stdout if result.returncode == 0 else result.stderr,
            "exit_code": result.returncode,
            "error": None if result.returncode == 0 else "Non-zero exit code",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "ERROR",
            "binary_path": gcc_path,
            "bundled_binary": bundled,
            "platform": system_info,
            "version_output": "",
            "exit_code": None,
            "error": "Command timed out after 5 seconds",
        }

    except FileNotFoundError:
        return {
            "status": "ERROR",
            "binary_path": gcc_path,
            "bundled_binary": bundled,
            "platform": system_info,
            "version_output": "",
            "exit_code": None,
            "error": f"GCodeClean binary not found at: {gcc_path}",
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "binary_path": gcc_path,
            "bundled_binary": bundled,
            "platform": system_info,
            "version_output": "",
            "exit_code": None,
            "error": f"Unexpected error: {str(e)}",
        }


@mcp.tool
def validate_gcode_syntax(
    gcode_content: str,
    tolerance: float = 0.01,
    minimise: Literal["soft", "medium", "hard"] = "soft",
    annotate: bool = False,
) -> dict:
    """
    Validate and clean G-code programs for CNC machining.

    This tool checks G-code syntax against NIST standards, detects errors, and
    produces a cleaned, optimized version. Use this as the primary tool for all
    G-code validation, cleaning, and optimization tasks.

    When to use:
    - User provides G-code for validation or review
    - User asks to "check", "validate", "clean", or "optimize" G-code
    - User reports G-code errors or controller rejections
    - User wants to reduce file size or standardize formatting

    Args:
        gcode_content: Raw G-code text to validate (required)

        tolerance: Clipping tolerance in millimeters (default: 0.01)
            - 0.001: High-precision work (aerospace, medical devices)
            - 0.01: Standard machining (default - suitable for most work)
            - 0.05: Rough operations (woodworking, prototypes)
            - 0.1: Coarse work (foam cutting, artistic applications)

        minimise: File size optimization strategy (default: "soft")
            - "soft": Remove F/Z codes only, preserve readability (10-20% reduction)
                     Best for code that will be manually reviewed or edited
            - "medium": Remove all codes except IJK, keep some readability (30-50% reduction)
                       Good balance for storage and occasional editing
            - "hard": Maximum compression, remove all codes except IJK + spaces (50-70% reduction)
                     Best for production code, network transfer, or storage

            Selection guide:
            - Use "soft" by default unless user specifies otherwise
            - Use "hard" when user asks to "minimize", "compress", or "optimize"
            - Use "medium" when user mentions "clean" or "standardize"

        annotate: Add explanatory comments to output (default: False)
            - True: Add comments explaining each G-code command
                   Use when user is learning or asks to "explain" G-code
            - False: No comments, cleaner output
                    Use for production code or when user wants minimal output

    Returns:
        Dictionary containing:
        - status: Validation outcome
            "PASSED": G-code is syntactically valid and ready to use
            "FAILED": Syntax errors detected (see error field for details)
            "ERROR": Processing error (file too large, binary not found, etc.)
            "TIMEOUT": Validation exceeded 30 second limit (file too complex)

        - passed: Boolean indicating if validation succeeded

        - cleaned_gcode: Cleaned and optimized G-code (None if validation failed)

        - statistics: Processing metrics
            original_lines: Line count in input G-code
            output_lines: Line count in cleaned G-code
            original_size_bytes: Input file size in bytes
            cleaned_size_bytes: Output file size in bytes
            reduction_percent: File size reduction percentage

        - error: Error message if status is FAILED or ERROR (None on success)

        - stdout: Raw output from GCodeClean (for debugging)

    Response guidance:
        When status is "PASSED":
            - Confirm validation success clearly
            - Mention size reduction if significant (>20%)
            - Offer to show cleaned G-code
            Example: "Your G-code passed validation. The cleaned version is 25%
                     smaller while preserving all functionality."

        When status is "FAILED":
            - Explain errors from the error field in simple terms
            - Parse line numbers if present
            - Suggest specific corrections
            - Offer to help fix the issues
            Example: "Found syntax error on line 15: G2 arc command is missing
                     the I and J parameters. Would you like me to help fix this?"

        When status is "ERROR":
            - Explain the error clearly
            - Provide actionable solution
            Example: "Your G-code file exceeds the 10MB limit. Try validating
                     smaller sections or breaking it into multiple programs."

        When status is "TIMEOUT":
            - Explain that the file is very large or complex
            - Suggest breaking into smaller sections
            Example: "Validation timed out after 30 seconds. This is a very large
                     program. Try validating it in smaller sections."

    Limitations:
        - Maximum file size: 10MB (returns ERROR if exceeded)
        - Validation timeout: 30 seconds (returns TIMEOUT if exceeded)
        - Validates syntax only (no machine-specific limits or tool availability)
        - Uses NIST G-code standards (some machine-specific codes may not be recognized)

    Example workflows:
        1. Basic validation:
           User: "Check this G-code: G90\\nG21\\nG0 X0 Y0"
           → Call with default parameters
           → Report "Valid G-code" with statistics

        2. Optimization:
           User: "Minimize this G-code for network transfer"
           → Call with minimise="hard"
           → Show before/after size comparison

        3. Learning:
           User: "Help me understand this G-code"
           → Call with annotate=True
           → Explain the annotated output

        4. Error diagnosis:
           User: "My controller rejects this program"
           → Call with default parameters
           → Parse error messages and suggest fixes
    """
    return _validate_gcode_syntax_impl(gcode_content, tolerance, minimise, annotate)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
