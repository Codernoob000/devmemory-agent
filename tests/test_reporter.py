"""Unit tests for the Incident Post-Mortem Reporter module."""

try:
    import pytest
except ImportError:
    # Minimal fallback to run without pytest installed
    class MockPytest:
        class raises:
            def __init__(self, expected_exception) -> None:
                self.expected_exception = expected_exception

            def __enter__(self) -> "MockPytest.raises":
                return self

            def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
                if exc_type is None:
                    raise AssertionError(f"Expected exception {self.expected_exception} was not raised.")
                return issubclass(exc_type, self.expected_exception)

    pytest = MockPytest()

from src.pipeline.reporter import (
    IncidentReporter,
    IncidentReport,
    HistoricalIncident,
    SuggestedFix,
    ReportValidationError,
    HistoricalContextMissing,
)


class MockModelClient:
    """Mock model client for dependency injection testing."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.last_prompt = None

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        self.last_prompt = prompt
        return self.response_text


def test_build_prompt() -> None:
    """Test that build_prompt correctly isolates logs and context."""
    client = MockModelClient("{}")
    reporter = IncidentReporter(client)

    log = "ERROR: connection refused"
    context = "INCIDENT-404: Database failure"

    prompt = reporter.build_prompt(log, context)

    assert "### CURRENT INCIDENT LOG" in prompt
    assert "ERROR: connection refused" in prompt
    assert "### HISTORICAL CONTEXT RECORD" in prompt
    assert "INCIDENT-404: Database failure" in prompt


def test_validate_report_success() -> None:
    """Test validate_report with clean and valid JSON."""
    client = MockModelClient("")
    reporter = IncidentReporter(client)

    valid_json = """
    {
        "incident_summary": "Database pool manager encountered connection exhaustion.",
        "root_cause_analysis": "The maximum connection pool limit of 100 was exceeded due to unreleased connections.",
        "historical_reference": {
            "incident_id": "DB-EXHAUST-2025",
            "date": "2025-11-12",
            "root_cause": "Leak in auth service session pool.",
            "resolution": "Increased pool capacity and deployed idle timeout fix.",
            "similarity_score": 0.88
        },
        "suggested_fixes": [
            {"step_number": 1, "action": "Reboot the Database Pool Manager container."},
            {"step_number": 2, "action": "Review auth connection lifecycle code for resource leaks."}
        ]
    }
    """

    report = reporter.validate_report(valid_json)

    assert report.incident_summary == "Database pool manager encountered connection exhaustion."
    assert report.historical_reference is not None
    assert report.historical_reference.incident_id == "DB-EXHAUST-2025"
    assert report.historical_reference.similarity_score == 0.88
    assert len(report.suggested_fixes) == 2
    assert report.suggested_fixes[0].step_number == 1

    # Verify programmatic markdown generation
    assert "# Incident Post-Mortem" in report.markdown_output
    assert "## Root Cause Analysis" in report.markdown_output
    assert "DB-EXHAUST-2025" in report.markdown_output
    assert "Reboot the Database Pool Manager container." in report.markdown_output


def test_validate_report_success_no_history() -> None:
    """Test validate_report with clean JSON and no historical match."""
    client = MockModelClient("")
    reporter = IncidentReporter(client)

    valid_json_no_history = """
    {
        "incident_summary": "Fatal out of memory error.",
        "root_cause_analysis": "Heap exhaustion on primary server.",
        "historical_reference": null,
        "suggested_fixes": [
            {"step_number": 1, "action": "Increase container heap limits to 4GB."}
        ]
    }
    """

    report = reporter.validate_report(valid_json_no_history)

    assert report.historical_reference is None
    assert "No relevant historical incident found." in report.markdown_output


def test_validate_report_validation_errors() -> None:
    """Test validate_report throws ReportValidationError on invalid schemas."""
    client = MockModelClient("")
    reporter = IncidentReporter(client)

    # Missing mandatory suggested_fixes field
    invalid_json_missing_fields = """
    {
        "incident_summary": "Summary only",
        "root_cause_analysis": "RCA only"
    }
    """
    with pytest.raises(ReportValidationError):
        reporter.validate_report(invalid_json_missing_fields)

    # Empty suggested_fixes list (not allowed by min_length=1 constraint)
    invalid_json_empty_fixes = """
    {
        "incident_summary": "Summary",
        "root_cause_analysis": "RCA",
        "historical_reference": null,
        "suggested_fixes": []
    }
    """
    with pytest.raises(ReportValidationError):
        reporter.validate_report(invalid_json_empty_fixes)

    # Similarity score out of bounds
    invalid_json_bad_similarity = """
    {
        "incident_summary": "Summary",
        "root_cause_analysis": "RCA",
        "historical_reference": {
            "incident_id": "DB-EXHAUST-2025",
            "date": "2025-11-12",
            "root_cause": "Leak.",
            "resolution": "Fixed.",
            "similarity_score": 1.25
        },
        "suggested_fixes": [
            {"step_number": 1, "action": "Fix it."}
        ]
    }
    """
    with pytest.raises(ReportValidationError):
        reporter.validate_report(invalid_json_bad_similarity)


def test_validate_report_json_syntax_error() -> None:
    """Test validate_report throws ReportValidationError on syntax errors."""
    client = MockModelClient("")
    reporter = IncidentReporter(client)

    bad_json = "{ invalid json content }"
    with pytest.raises(ReportValidationError):
        reporter.validate_report(bad_json)


def test_generate_report_missing_historical_context() -> None:
    """Test generate_report throws HistoricalContextMissing if context is empty."""
    client = MockModelClient("")
    reporter = IncidentReporter(client)

    with pytest.raises(HistoricalContextMissing):
        reporter.generate_report("Scrubbed logs...", "")

    with pytest.raises(HistoricalContextMissing):
        reporter.generate_report("Scrubbed logs...", "   ")


def test_generate_report_success() -> None:
    """Test generate_report end-to-end flow with mock client."""
    response_json = """
    {
        "incident_summary": "Major S3 connection failure.",
        "root_cause_analysis": "AWS API gateway routing error due to DNS resolution failure.",
        "historical_reference": null,
        "suggested_fixes": [
            {"step_number": 1, "action": "Flush local DNS caches."}
        ]
    }
    """
    client = MockModelClient(response_json)
    reporter = IncidentReporter(client)

    log = "ERROR 503 AWS S3 Gateway Timeout"
    context = "No matches from history database."

    report = reporter.generate_report(log, context)

    assert report.incident_summary == "Major S3 connection failure."
    assert "Flush local DNS caches." in report.markdown_output
    assert "AWS S3 Gateway Timeout" in client.last_prompt
