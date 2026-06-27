"""Test runner using standard library to verify the test suite passes on systems without pytest."""
import sys
import os
# Add the project root and source directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tests.test_reporter import (
    test_build_prompt,
    test_validate_report_success,
    test_validate_report_success_no_history,
    test_validate_report_validation_errors,
    test_validate_report_json_syntax_error,
    test_generate_report_missing_historical_context,
    test_generate_report_success,
)
if __name__ == "__main__":
    tests = [
        test_build_prompt,
        test_validate_report_success,
        test_validate_report_success_no_history,
        test_validate_report_validation_errors,
        test_validate_report_json_syntax_error,
        test_generate_report_missing_historical_context,
        test_generate_report_success,
    ]
    print("Running SRE Reporter unit tests...")
    failed = False
    for test in tests:
        try:
            print(f"Running {test.__name__}...", end=" ")
            test()
            print("PASSED")
        except Exception as e:
            print("FAILED")
            import traceback
            traceback.print_exc()
            failed = True
    if failed:
        print("\nSome tests FAILED.")
        sys.exit(1)
    else:
        print("\nAll tests PASSED successfully!")
        sys.exit(0)