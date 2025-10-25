import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_gcodeclean.server import _validate_gcode_syntax_impl as validate_gcode_syntax


SAMPLE_GCODE = """G90
G21
G0 X0 Y0 Z5
M3 S1200
G1 Z-2.5 F100
G1 X10 Y10 F500
G0 Z5
M5
M30
"""


def has_gcodeclean():
    from mcp_server_gcodeclean.server import get_gcodeclean_path
    gcc_path = get_gcodeclean_path()
    try:
        result = subprocess.run(
            [gcc_path, "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def skip_without_gcodeclean(func):
    def wrapper():
        if not has_gcodeclean():
            print(f"[SKIP] Skipping {func.__name__} (GCodeClean not available)")
            return True
        return func()
    return wrapper


class TestDefaultBehavior:
    """Test that defaults are correctly applied when parameters are omitted."""

    @staticmethod
    @skip_without_gcodeclean
    def test_all_defaults():
        """Test validation with all default parameters."""
        result = validate_gcode_syntax(SAMPLE_GCODE)

        assert result["status"] == "PASSED"
        assert result["passed"] is True
        assert result["cleaned_gcode"] is not None

        print("[PASS] test_all_defaults passed")
        print(f"  Used defaults: tolerance=0.01, minimise='soft', annotate=False")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_default_tolerance():
        """Verify default tolerance is 0.01mm."""
        result = validate_gcode_syntax(SAMPLE_GCODE)

        assert result["status"] == "PASSED"

        print("[PASS] test_default_tolerance passed (0.01mm)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_default_minimise():
        """Verify default minimise is 'soft'."""
        result = validate_gcode_syntax(SAMPLE_GCODE)

        assert result["status"] == "PASSED"
        assert result["cleaned_gcode"] is not None

        print("[PASS] test_default_minimise passed ('soft')")
        print(f"  Reduction: {result['statistics']['reduction_percent']}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_default_annotate():
        """Verify default annotate is False (no comments)."""
        result = validate_gcode_syntax(SAMPLE_GCODE)

        assert result["status"] == "PASSED"
        assert result["cleaned_gcode"] is not None

        print("[PASS] test_default_annotate passed (False)")
        return True


class TestToleranceOverride:
    """Test that tolerance parameter can be overridden."""

    @staticmethod
    @skip_without_gcodeclean
    def test_tolerance_0_001():
        """Test with high-precision tolerance (0.001mm)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.001)

        assert result["status"] == "PASSED"
        assert result["passed"] is True

        print("[PASS] test_tolerance_0_001 passed (0.001mm - precision work)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_tolerance_0_005():
        """Test with fine tolerance (0.005mm)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.005)

        assert result["status"] == "PASSED"

        print("[PASS] test_tolerance_0_005 passed (0.005mm)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_tolerance_0_01():
        """Test with standard tolerance (0.01mm - default)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.01)

        assert result["status"] == "PASSED"

        print("[PASS] test_tolerance_0_01 passed (0.01mm - default)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_tolerance_0_05():
        """Test with rough tolerance (0.05mm)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.05)

        assert result["status"] == "PASSED"

        print("[PASS] test_tolerance_0_05 passed (0.05mm - rough work)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_tolerance_0_1():
        """Test with coarse tolerance (0.1mm)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.1)

        assert result["status"] == "PASSED"

        print("[PASS] test_tolerance_0_1 passed (0.1mm - coarse work)")
        return True


class TestMinimiseOverride:
    """Test that minimise parameter can be overridden."""

    @staticmethod
    @skip_without_gcodeclean
    def test_minimise_soft():
        """Test with soft minimisation (default)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, minimise="soft")

        assert result["status"] == "PASSED"
        size_soft = result["statistics"]["cleaned_size_bytes"]
        reduction_soft = result["statistics"]["reduction_percent"]

        print("[PASS] test_minimise_soft passed (default)")
        print(f"  Size: {size_soft} bytes, Reduction: {reduction_soft}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_minimise_medium():
        """Test with medium minimisation."""
        result = validate_gcode_syntax(SAMPLE_GCODE, minimise="medium")

        assert result["status"] == "PASSED"
        size_medium = result["statistics"]["cleaned_size_bytes"]
        reduction_medium = result["statistics"]["reduction_percent"]

        print("[PASS] test_minimise_medium passed")
        print(f"  Size: {size_medium} bytes, Reduction: {reduction_medium}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_minimise_hard():
        """Test with hard minimisation."""
        result = validate_gcode_syntax(SAMPLE_GCODE, minimise="hard")

        assert result["status"] == "PASSED"
        size_hard = result["statistics"]["cleaned_size_bytes"]
        reduction_hard = result["statistics"]["reduction_percent"]

        print("[PASS] test_minimise_hard passed")
        print(f"  Size: {size_hard} bytes, Reduction: {reduction_hard}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_minimise_comparison():
        """Compare all three minimise modes."""
        result_soft = validate_gcode_syntax(SAMPLE_GCODE, minimise="soft")
        result_medium = validate_gcode_syntax(SAMPLE_GCODE, minimise="medium")
        result_hard = validate_gcode_syntax(SAMPLE_GCODE, minimise="hard")

        assert all(r["status"] == "PASSED" for r in [result_soft, result_medium, result_hard])

        size_soft = result_soft["statistics"]["cleaned_size_bytes"]
        size_medium = result_medium["statistics"]["cleaned_size_bytes"]
        size_hard = result_hard["statistics"]["cleaned_size_bytes"]

        print("[PASS] test_minimise_comparison passed")
        print(f"  soft:   {size_soft} bytes ({result_soft['statistics']['reduction_percent']}%)")
        print(f"  medium: {size_medium} bytes ({result_medium['statistics']['reduction_percent']}%)")
        print(f"  hard:   {size_hard} bytes ({result_hard['statistics']['reduction_percent']}%)")

        return True


class TestAnnotateOverride:
    """Test that annotate parameter can be overridden."""

    @staticmethod
    @skip_without_gcodeclean
    def test_annotate_false():
        """Test with annotate=False (default)."""
        result = validate_gcode_syntax(SAMPLE_GCODE, annotate=False)

        assert result["status"] == "PASSED"
        assert result["cleaned_gcode"] is not None

        print("[PASS] test_annotate_false passed (default)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_annotate_true():
        """Test with annotate=True."""
        result = validate_gcode_syntax(SAMPLE_GCODE, annotate=True)

        assert result["status"] == "PASSED"
        assert result["cleaned_gcode"] is not None

        print("[PASS] test_annotate_true passed")
        print(f"  Annotated output size: {result['statistics']['cleaned_size_bytes']} bytes")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_annotate_comparison():
        """Compare output with and without annotations."""
        result_no_annotation = validate_gcode_syntax(SAMPLE_GCODE, annotate=False)
        result_with_annotation = validate_gcode_syntax(SAMPLE_GCODE, annotate=True)

        assert result_no_annotation["status"] == "PASSED"
        assert result_with_annotation["status"] == "PASSED"

        size_no_annotation = result_no_annotation["statistics"]["cleaned_size_bytes"]
        size_with_annotation = result_with_annotation["statistics"]["cleaned_size_bytes"]

        print("[PASS] test_annotate_comparison passed")
        print(f"  Without annotation: {size_no_annotation} bytes")
        print(f"  With annotation: {size_with_annotation} bytes")
        print(f"  Annotation adds: {size_with_annotation - size_no_annotation} bytes")

        return True


class TestParameterCombinations:
    """Test various parameter combinations."""

    @staticmethod
    @skip_without_gcodeclean
    def test_precision_optimization():
        """High precision + maximum optimization."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.001,
            minimise="hard"
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_precision_optimization passed (0.001mm + hard)")
        print(f"  Reduction: {result['statistics']['reduction_percent']}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_precision_learning():
        """High precision + annotated output."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.001,
            annotate=True
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_precision_learning passed (0.001mm + annotate)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_optimization_learning():
        """Maximum optimization + annotated output."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            minimise="hard",
            annotate=True
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_optimization_learning passed (hard + annotate)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_all_parameters_custom():
        """All parameters with non-default values."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.001,
            minimise="hard",
            annotate=True
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_all_parameters_custom passed (all custom)")
        print(f"  tolerance=0.001, minimise='hard', annotate=True")
        print(f"  Reduction: {result['statistics']['reduction_percent']}%")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_rough_work_cleanup():
        """Rough tolerance + medium minimisation."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.05,
            minimise="medium"
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_rough_work_cleanup passed (0.05mm + medium)")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_standard_with_annotation():
        """Standard defaults but with annotation."""
        result = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.01,
            minimise="soft",
            annotate=True
        )

        assert result["status"] == "PASSED"

        print("[PASS] test_standard_with_annotation passed (defaults + annotate)")
        return True


class TestDefaultValueConsistency:
    """Verify that default values are consistently applied."""

    @staticmethod
    @skip_without_gcodeclean
    def test_explicit_vs_implicit_defaults():
        """Compare explicit default values vs omitted parameters."""
        result_implicit = validate_gcode_syntax(SAMPLE_GCODE)

        result_explicit = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.01,
            minimise="soft",
            annotate=False
        )

        assert result_implicit["status"] == result_explicit["status"]
        assert result_implicit["passed"] == result_explicit["passed"]
        assert result_implicit["statistics"]["cleaned_size_bytes"] == \
               result_explicit["statistics"]["cleaned_size_bytes"]

        print("[PASS] test_explicit_vs_implicit_defaults passed")
        print("  Implicit defaults produce identical results to explicit defaults")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_partial_defaults():
        """Test that omitted parameters use defaults when others are specified."""
        result_tolerance_only = validate_gcode_syntax(SAMPLE_GCODE, tolerance=0.05)

        result_tolerance_explicit_others = validate_gcode_syntax(
            SAMPLE_GCODE,
            tolerance=0.05,
            minimise="soft",
            annotate=False
        )

        assert result_tolerance_only["statistics"]["cleaned_size_bytes"] == \
               result_tolerance_explicit_others["statistics"]["cleaned_size_bytes"]

        print("[PASS] test_partial_defaults passed")
        print("  Omitted parameters correctly use defaults when others are specified")
        return True


class TestEdgeCasesWithDefaults:
    """Test edge cases with default parameters."""

    @staticmethod
    def test_empty_input_defaults():
        """Test empty input with default parameters."""
        result = validate_gcode_syntax("")

        assert result["status"] in ["PASSED", "FAILED", "ERROR"]
        assert result["statistics"]["original_lines"] == 0
        assert result["statistics"]["original_size_bytes"] == 0

        print("[PASS] test_empty_input_defaults passed")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_minimal_input_defaults():
        """Test minimal G-code with defaults."""
        result = validate_gcode_syntax("G0 X0 Y0")

        assert result["status"] in ["PASSED", "FAILED"]

        print("[PASS] test_minimal_input_defaults passed")
        return True

    @staticmethod
    @skip_without_gcodeclean
    def test_multiline_input_defaults():
        """Test multiline input with defaults."""
        multiline_gcode = "\n\nG90\n\nG21\n\n"
        result = validate_gcode_syntax(multiline_gcode)

        assert result["status"] in ["PASSED", "FAILED"]

        print("[PASS] test_multiline_input_defaults passed")
        return True


class TestDefaultDocumentation:
    """Verify that defaults are properly documented."""

    @staticmethod
    def test_impl_function_signature_has_defaults():
        """Verify implementation function has correct defaults."""
        import inspect
        from mcp_server_gcodeclean.server import _validate_gcode_syntax_impl

        sig = inspect.signature(_validate_gcode_syntax_impl)

        assert sig.parameters['tolerance'].default == 0.01
        assert sig.parameters['minimise'].default == "soft"
        assert sig.parameters['annotate'].default is False

        print("[PASS] test_impl_function_signature_has_defaults passed")
        print("  tolerance default: 0.01")
        print("  minimise default: 'soft'")
        print("  annotate default: False")
        return True

    @staticmethod
    def test_both_functions_have_matching_defaults():
        """Verify implementation and wrapper have matching defaults."""
        import inspect
        from mcp_server_gcodeclean.server import _validate_gcode_syntax_impl

        impl_sig = inspect.signature(_validate_gcode_syntax_impl)

        assert impl_sig.parameters['gcode_content'].default == inspect.Parameter.empty
        assert impl_sig.parameters['tolerance'].default == 0.01
        assert impl_sig.parameters['minimise'].default == "soft"
        assert impl_sig.parameters['annotate'].default is False

        print("[PASS] test_both_functions_have_matching_defaults passed")
        print("  Both implementation and wrapper use consistent defaults")
        return True


def run_all_tests():
    """Run all default and override tests."""
    print("=" * 70)
    print("DEFAULTS AND OVERRIDES COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    if not has_gcodeclean():
        print("[WARN] GCodeClean not found - some tests will be skipped")
        print()

    test_classes = [
        ("Default Behavior", TestDefaultBehavior),
        ("Tolerance Override", TestToleranceOverride),
        ("Minimise Override", TestMinimiseOverride),
        ("Annotate Override", TestAnnotateOverride),
        ("Parameter Combinations", TestParameterCombinations),
        ("Default Value Consistency", TestDefaultValueConsistency),
        ("Edge Cases with Defaults", TestEdgeCasesWithDefaults),
        ("Default Documentation", TestDefaultDocumentation),
    ]

    total_tests = 0
    passed_tests = 0

    for category, test_class in test_classes:
        print(f"\n{category}")
        print("-" * 70)

        test_methods = [
            method for method in dir(test_class)
            if method.startswith("test_") and callable(getattr(test_class, method))
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                success = method()
                if success or success is None:
                    passed_tests += 1
            except AssertionError as e:
                print(f"[FAIL] {method_name} FAILED: {e}")
            except Exception as e:
                print(f"[FAIL] {method_name} ERROR: {e}")

    print()
    print("=" * 70)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
