"""
Output Parsers for Goby Framework.
Provides structured parsing of test runner output across multiple ecosystems
(pytest, jest, generic CLI). Transforms raw stdout/stderr into actionable
StructuredTestResult objects that GCA and LDE can analyze.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class TestFailureDetail:
    """Structured information about a single test failure."""
    test_name: str
    error_type: str
    message: str
    file_path: str
    line_number: Optional[int] = None


@dataclass
class StructuredTestResult:
    """Structured result from parsing test runner output."""
    runner: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    failures: List[TestFailureDetail] = field(default_factory=list)
    raw_stdout: str = ""
    raw_stderr: str = ""
    is_success: bool = True


# ---------------------------------------------------------------------------
# Base Parser
# ---------------------------------------------------------------------------

class BaseOutputParser:
    """Base class for test runner output parsers."""
    runner_name: str = "base"

    def parse(self, stdout: str, stderr: str, exit_code: int) -> StructuredTestResult:
        """Parse raw output into structured result. Override in subclasses."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Pytest / unittest Parser
# ---------------------------------------------------------------------------

class PytestParser(BaseOutputParser):
    """
    Parses pytest and Python unittest output.
    Handles summary lines like: '2 passed, 1 failed, 1 skipped in 0.45s'
    and 'FAILED test_file.py::test_name - ErrorType: message'
    """
    runner_name = "pytest"

    # Matches: '=== 1 failed, 2 passed, 1 skipped, 1 error in 1.20s ==='
    _SUMMARY_PATTERN = re.compile(
        r'(\d+)\s+(failed|passed|skipped|error|warnings?|deselected)',
        re.IGNORECASE,
    )

    # Matches: 'FAILED tests/test_math.py::test_divide - ZeroDivisionError: ...'
    _FAILURE_LINE_PATTERN = re.compile(
        r'FAILED\s+([\w/\\.]+)::(\w+)\s*-?\s*(.*)',
        re.IGNORECASE,
    )

    # Matches unittest-style: 'FAIL: test_name (test_module.TestClass)'
    _UNITTEST_FAIL_PATTERN = re.compile(
        r'(?:FAIL|ERROR):\s+(\w+)\s+\(([^)]+)\)',
    )

    def parse(self, stdout: str, stderr: str, exit_code: int) -> StructuredTestResult:
        combined = stdout + "\n" + stderr
        counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}

        # Extract summary counts
        for match in self._SUMMARY_PATTERN.finditer(combined):
            count = int(match.group(1))
            category = match.group(2).lower()
            if category in ("warning", "warnings", "deselected"):
                continue
            if category == "error":
                counts["error"] = count
            elif category in counts:
                counts[category] = count

        # Extract failure details
        failures: List[TestFailureDetail] = []
        for match in self._FAILURE_LINE_PATTERN.finditer(combined):
            file_path = match.group(1)
            test_name = match.group(2)
            error_info = match.group(3).strip()

            error_type = ""
            message = error_info
            if ":" in error_info:
                parts = error_info.split(":", 1)
                error_type = parts[0].strip()
                message = parts[1].strip() if len(parts) > 1 else ""

            failures.append(TestFailureDetail(
                test_name=test_name,
                error_type=error_type,
                message=message,
                file_path=file_path,
            ))

        # Also check for unittest-style failures
        for match in self._UNITTEST_FAIL_PATTERN.finditer(combined):
            test_name = match.group(1)
            module_path = match.group(2)
            failures.append(TestFailureDetail(
                test_name=test_name,
                error_type="TestFailure",
                message=f"Failed in {module_path}",
                file_path=module_path.replace(".", "/") + ".py",
            ))

        total = counts["passed"] + counts["failed"] + counts["skipped"] + counts["error"]

        return StructuredTestResult(
            runner="pytest",
            total=total,
            passed=counts["passed"],
            failed=counts["failed"],
            errors=counts["error"],
            skipped=counts["skipped"],
            failures=failures,
            raw_stdout=stdout,
            raw_stderr=stderr,
            is_success=(exit_code == 0 and counts["failed"] == 0 and counts["error"] == 0),
        )


# ---------------------------------------------------------------------------
# Jest / npm test Parser
# ---------------------------------------------------------------------------

class JestParser(BaseOutputParser):
    """
    Parses Jest (JavaScript/TypeScript) test runner output.
    Handles summary lines like: 'Tests: 1 failed, 2 passed, 3 total'
    and failure blocks starting with '●'
    """
    runner_name = "jest"

    # Matches: 'Tests:       1 failed, 2 passed, 3 total'
    _SUMMARY_PATTERN = re.compile(
        r'Tests:\s+(.+)',
        re.IGNORECASE,
    )
    _SUMMARY_COUNT = re.compile(
        r'(\d+)\s+(failed|passed|skipped|pending|todo|total)',
        re.IGNORECASE,
    )

    # Matches: '  ● test name'
    _FAILURE_BLOCK_PATTERN = re.compile(
        r'●\s+(.+)',
    )

    # Matches: '    TypeError: Cannot read property ...'
    _ERROR_TYPE_PATTERN = re.compile(
        r'^\s{4,}(\w+Error):\s+(.+)',
        re.MULTILINE,
    )

    # Matches: '      at Object.<anonymous> (src/auth.test.js:12:18)'
    _LOCATION_PATTERN = re.compile(
        r'at\s+\S+\s+\(([^:]+):(\d+):\d+\)',
    )

    # Matches: ' FAIL  src/auth.test.js'
    _FAIL_FILE_PATTERN = re.compile(
        r'FAIL\s+([\w./\\-]+\.(?:js|ts|jsx|tsx|mjs|cjs))',
    )

    def parse(self, stdout: str, stderr: str, exit_code: int) -> StructuredTestResult:
        combined = stdout + "\n" + stderr
        counts = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

        # Extract summary counts
        summary_match = self._SUMMARY_PATTERN.search(combined)
        if summary_match:
            summary_line = summary_match.group(1)
            for count_match in self._SUMMARY_COUNT.finditer(summary_line):
                count = int(count_match.group(1))
                category = count_match.group(2).lower()
                if category == "total":
                    counts["total"] = count
                elif category in ("pending", "todo"):
                    counts["skipped"] += count
                elif category in counts:
                    counts[category] = count

        # If total wasn't in summary, compute it
        if counts["total"] == 0:
            counts["total"] = counts["passed"] + counts["failed"] + counts["skipped"]

        # Extract failure details
        failures: List[TestFailureDetail] = []
        fail_files = self._FAIL_FILE_PATTERN.findall(combined)

        for match in self._FAILURE_BLOCK_PATTERN.finditer(combined):
            test_name = match.group(1).strip()
            # Look ahead for error type and location
            start_pos = match.end()
            region = combined[start_pos:start_pos + 500]

            error_type = ""
            message = ""
            error_match = self._ERROR_TYPE_PATTERN.search(region)
            if error_match:
                error_type = error_match.group(1)
                message = error_match.group(2)

            file_path = ""
            line_number = None
            loc_match = self._LOCATION_PATTERN.search(region)
            if loc_match:
                file_path = loc_match.group(1)
                line_number = int(loc_match.group(2))
            elif fail_files:
                file_path = fail_files[0]

            failures.append(TestFailureDetail(
                test_name=test_name,
                error_type=error_type,
                message=message,
                file_path=file_path,
                line_number=line_number,
            ))

        return StructuredTestResult(
            runner="jest",
            total=counts["total"],
            passed=counts["passed"],
            failed=counts["failed"],
            errors=0,
            skipped=counts["skipped"],
            failures=failures,
            raw_stdout=stdout,
            raw_stderr=stderr,
            is_success=(exit_code == 0 and counts["failed"] == 0),
        )


# ---------------------------------------------------------------------------
# Generic Parser (fallback for any CLI tool)
# ---------------------------------------------------------------------------

class GenericParser(BaseOutputParser):
    """
    Generic fallback parser for any test runner or compiler.
    Extracts error-like lines from output using common patterns.
    """
    runner_name = "generic"

    # Common error patterns across languages
    _ERROR_PATTERNS = [
        re.compile(r'^error(?:\[[\w]+\])?:\s+(.+)', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^\s*(\w+Error):\s+(.+)', re.MULTILINE),
        re.compile(r"^FAILED\b.*", re.MULTILINE),
        re.compile(r"^FAIL\b.*", re.MULTILINE),
        re.compile(r"panicked at '(.+)'", re.MULTILINE),
    ]

    # Location patterns: 'file:line', '--> file:line', 'at file:line'
    _LOCATION_PATTERNS = [
        re.compile(r'-->\s+([\w./\\-]+):(\d+)'),
        re.compile(r'at\s+([\w./\\-]+):(\d+)'),
        re.compile(r'([\w./\\-]+\.(?:py|js|ts|rs|go|java|c|cpp|rb)):(\d+)'),
    ]

    def parse(self, stdout: str, stderr: str, exit_code: int) -> StructuredTestResult:
        combined = stdout + "\n" + stderr
        failures: List[TestFailureDetail] = []
        seen_errors: set = set()

        for pattern in self._ERROR_PATTERNS:
            for match in pattern.finditer(combined):
                error_text = match.group(0).strip()
                if error_text in seen_errors:
                    continue
                seen_errors.add(error_text)

                error_type = ""
                message = error_text
                # Try to split "ErrorType: message"
                type_match = re.match(r'(\w+Error):\s+(.*)', error_text)
                if type_match:
                    error_type = type_match.group(1)
                    message = type_match.group(2)

                # Try to find location near this error
                start = max(0, match.start() - 200)
                end = min(len(combined), match.end() + 200)
                region = combined[start:end]

                file_path = ""
                line_number = None
                for loc_pattern in self._LOCATION_PATTERNS:
                    loc_match = loc_pattern.search(region)
                    if loc_match:
                        file_path = loc_match.group(1)
                        line_number = int(loc_match.group(2))
                        break

                failures.append(TestFailureDetail(
                    test_name=error_type or "unknown",
                    error_type=error_type,
                    message=message,
                    file_path=file_path,
                    line_number=line_number,
                ))

        is_success = exit_code == 0
        failed_count = len(failures) if not is_success else 0
        passed_count = 1 if is_success else 0

        return StructuredTestResult(
            runner="generic",
            total=max(passed_count + failed_count, 1),
            passed=passed_count,
            failed=failed_count,
            errors=0,
            skipped=0,
            failures=failures,
            raw_stdout=stdout,
            raw_stderr=stderr,
            is_success=is_success,
        )


# ---------------------------------------------------------------------------
# Auto-Detection & Factory
# ---------------------------------------------------------------------------

_RUNNER_KEYWORDS = {
    "pytest": ["pytest", "py.test", "python -m unittest", "python -m pytest"],
    "jest": ["jest", "npx jest", "npm test", "npm run test", "yarn test", "vitest"],
}


def detect_runner(command: str) -> str:
    """
    Auto-detect which test runner a command uses based on keyword matching.
    Returns 'pytest', 'jest', or 'generic'.
    """
    command_lower = command.lower()
    for runner, keywords in _RUNNER_KEYWORDS.items():
        for keyword in keywords:
            if keyword in command_lower:
                return runner
    return "generic"


_PARSER_REGISTRY = {
    "pytest": PytestParser,
    "jest": JestParser,
    "generic": GenericParser,
}


def get_parser(runner: str) -> BaseOutputParser:
    """Return parser instance for the specified runner."""
    parser_class = _PARSER_REGISTRY.get(runner, GenericParser)
    return parser_class()
