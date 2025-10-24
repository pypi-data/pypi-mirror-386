import argparse
import json
import io
import sys
import pytest
import subprocess
from rich.console import Console
from rich.pretty import pprint
import os
from .python_env_detector import detect_host_python_executable

console = Console()

class TestResultCollector:
    __test__ = False  # Prevent pytest from collecting this plugin as a test

    def __init__(self):
        self.failures = 0
        self.errors = 0
        self.warnings = 0
        self.passed = 0
        self.logs = io.StringIO()
        self.stdout = ""
        self.stderr = ""

    def pytest_runtest_logreport(self, report):
        """
        Treat any failing 'call' phase as a test failure (matching what Pytest calls 'failed'),
        and only count setup/teardown failures (or 'report.outcome == "error"') as errors.
        """
        # 'report.when' can be "setup", "call", or "teardown"
        if report.when == "call":
            if report.passed:
                self.passed += 1
            elif report.failed:
                # All exceptions that occur in the test body are 'failures'
                self.failures += 1
            elif report.outcome == "error":
                # Not frequently used, but included for completeness
                self.errors += 1
        elif report.when in ("setup", "teardown") and report.failed:
            # Setup/teardown failures are 'errors'
            self.errors += 1

    def pytest_sessionfinish(self, session):
        """Capture warnings from pytest session."""
        if hasattr(session.config, 'pluginmanager'):
            terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
            if terminal_reporter:
                self.warnings = len(terminal_reporter.stats.get("warnings", []))

    def capture_logs(self):
        """Redirect stdout and stderr to capture logs."""
        sys.stdout = self.logs
        sys.stderr = self.logs

    def get_logs(self):
        """Return captured logs and reset stdout/stderr."""
        self.stdout = self.logs.getvalue()
        self.stderr = self.logs.getvalue()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return self.stdout, self.stderr

def run_pytest_and_capture_output(test_file: str) -> dict:
    """
    Runs pytest on the given test file and captures the output.

    Args:
        test_file: The path to the test file.

    Returns:
        A dictionary containing the pytest output.
    """
    if not os.path.exists(test_file):
        console.print(f"[bold red]Error: Test file '{test_file}' not found.[/]")
        return {}

    if not test_file.endswith(".py"):
        console.print(
            f"[bold red]Error: Test file '{test_file}' must be a Python file (.py).[/]"
        )
        return {}

    # Use environment-aware Python executable for pytest execution
    python_executable = detect_host_python_executable()
    
    try:
        # Run pytest using subprocess with the detected Python executable
        result = subprocess.run(
            [python_executable, "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode
        
        # Parse the output to extract test results
        # Count passed, failed, and skipped tests from the output
        passed = stdout.count(" PASSED")
        failures = stdout.count(" FAILED") + stdout.count(" ERROR")
        errors = 0  # Will be included in failures for subprocess execution
        warnings = stdout.count("warning")
        
        # If return code is 2, it indicates a pytest error
        if return_code == 2:
            errors = 1
        
        return {
            "test_file": test_file,
            "test_results": [
                {
                    "standard_output": stdout,
                    "standard_error": stderr,
                    "return_code": return_code,
                    "warnings": warnings,
                    "errors": errors,
                    "failures": failures,
                    "passed": passed,
                }
            ],
        }
    except subprocess.TimeoutExpired:
        return {
            "test_file": test_file,
            "test_results": [
                {
                    "standard_output": "",
                    "standard_error": "Test execution timed out",
                    "return_code": -1,
                    "warnings": 0,
                    "errors": 1,
                    "failures": 0,
                    "passed": 0,
                }
            ],
        }
    except Exception as e:
        return {
            "test_file": test_file,
            "test_results": [
                {
                    "standard_output": "",
                    "standard_error": f"Error running pytest: {str(e)}",
                    "return_code": -1,
                    "warnings": 0,
                    "errors": 1,
                    "failures": 0,
                    "passed": 0,
                }
            ],
        }

def save_output_to_json(output: dict, output_file: str = "pytest.json"):
    """
    Saves the pytest output to a JSON file.

    Args:
        output: The dictionary containing the pytest output.
        output_file: The name of the output JSON file. Defaults to "pytest.json".
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        console.print(
            f"[green]Pytest output saved to '{output_file}'.[/green]"
        )
    except Exception as e:
        console.print(
            f"[bold red]Error saving output to JSON: {e}[/]"
        )

def main():
    """
    Main function for the pytest_output CLI tool.
    """
    parser = argparse.ArgumentParser(
        description="Capture pytest output and save it to a JSON file."
    )
    parser.add_argument(
        "test_file", type=str, help="Path to the test file."
    )
    parser.add_argument(
        "--json-only", action="store_true", help="Output only JSON to stdout."
    )
    args = parser.parse_args()

    pytest_output = run_pytest_and_capture_output(args.test_file)

    if args.json_only:
        # Print only valid JSON to stdout.
        print(json.dumps(pytest_output))
    else:
        console.print(f"Running pytest on: [blue]{args.test_file}[/blue]")
        pprint(pytest_output, console=console)  # Pretty print the output
        save_output_to_json(pytest_output)

if __name__ == "__main__":
    main()