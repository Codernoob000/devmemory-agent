"""Incident Post-Mortem Reporter Module.

This module handles prompt synthesis, Pydantic schema validation, and rendering
for the SRE Post-Mortem Synthesis Agent.
"""

import json
from typing import List, Optional, Protocol
from pydantic import BaseModel, Field, ValidationError, field_validator


class ReportValidationError(Exception):
    """Raised when the LLM output violates schema or validation checks."""
    pass


class HistoricalContextMissing(Exception):
    """Raised when the required historical context is empty or missing."""
    pass


class ModelClient(Protocol):
    """Protocol for LLM clients to allow clean dependency injection."""

    def generate_text(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Generates text from the given prompt.

        Args:
            prompt: The instruction prompt for the model.
            system_instruction: Optional system instruction.

        Returns:
            The raw text response from the model.
        """
        ...


class HistoricalIncident(BaseModel):
    """Represents a matched historical incident retrieved from memory."""

    incident_id: str = Field(..., description="The unique ID of the past incident.")
    date: str = Field(..., description="The date the past incident occurred.")
    root_cause: str = Field(..., description="The root cause of the past incident.")
    resolution: str = Field(..., description="How the past incident was resolved.")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence similarity score between 0.0 and 1.0.",
    )


class SuggestedFix(BaseModel):
    """Represents a step in the actionable remediation plan."""

    step_number: int = Field(..., description="1-indexed step order.")
    action: str = Field(..., description="The specific SRE mitigation action.")


class IncidentReport(BaseModel):
    """Validated structured schema representing the SRE Post-Mortem."""

    incident_summary: str = Field(
        ..., description="High-level incident summary and impact description."
    )
    root_cause_analysis: str = Field(
        ..., description="Multi-paragraph detailed architectural root cause analysis."
    )
    historical_reference: Optional[HistoricalIncident] = Field(
        None, description="Matching historical incident if one exists."
    )
    suggested_fixes: List[SuggestedFix] = Field(
        ..., min_length=1, description="Non-empty list of remediation steps."
    )
    markdown_output: str = Field(
        default="", description="The rendered Markdown representation of the report."
    )


class IncidentReporter:
    """Orchestrates prompt building, LLM generation, validation, and rendering."""

    def __init__(self, model_client: ModelClient) -> None:
        """Initializes the reporter with a dependency-injected model client.

        Args:
            model_client: An instance conforming to the ModelClient protocol.
        """
        self.model_client = model_client

    def build_prompt(self, scrubbed_log: str, historical_context: str) -> str:
        """Synthesizes the prompt for the reasoning model.

        Args:
            scrubbed_log: The raw/scrubbed log payload from runtime errors.
            historical_context: Retrieved context logs/incidents from Hindsight.

        Returns:
            The formatted prompt string with isolated sections.
        """
        system_rules = (
            "You are a specialized Post-Mortem Synthesis SRE Agent.\n"
            "Your output must be a single, valid JSON object matching the JSON Schema of IncidentReport.\n"
            "Strict rules:\n"
            "1. Bounded Reasoning: Do not invent services or logs not present in the input.\n"
            "2. Zero Placeholders: Omit missing values or infer logically. Never output '<TODO>' or '[Insert Date]'.\n"
            "3. Anti-Hallucination: Do not fabricate historical reference data or similarity scores. "
            "If no matching historical incident is present in the context, set historical_reference to null.\n"
            "4. Empty fix lists are strictly forbidden. You must list at least one actionable fix step.\n"
            "5. Do not include markdown formatting or backticks around the JSON payload itself. "
            "Output ONLY raw valid JSON."
        )

        prompt = f"""### SRE INSTRUCTIONS
{system_rules}

### CURRENT INCIDENT LOG
{scrubbed_log}

---

### HISTORICAL CONTEXT RECORD
{historical_context}

---

### REQUIRED JSON SCHEMA FORMAT
Provide your response strictly in the following JSON format:
{{
  "incident_summary": "Description of current failure...",
  "root_cause_analysis": "Detailed architectural root cause breakdown...",
  "historical_reference": {{
    "incident_id": "Incident ID from Hindsight context...",
    "date": "Date of incident from context...",
    "root_cause": "Historical root cause...",
    "resolution": "Historical resolution...",
    "similarity_score": 0.85
  }},
  "suggested_fixes": [
    {{
      "step_number": 1,
      "action": "First remediation action..."
    }}
  ]
}}
If no relevant historical incident exists, set "historical_reference": null.
"""
        return prompt

    def validate_report(self, raw_output: str) -> IncidentReport:
        """Parses and validates the raw JSON response against the Pydantic schema.

        Args:
            raw_output: The raw JSON string returned by the model.

        Returns:
            An IncidentReport instance with validated fields.

        Raises:
            ReportValidationError: If parsing or schema validation fails.
        """
        # Clean any accidental markdown code fences
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            # Ensure markdown_output is cleared out to be populated by renderer
            data.pop("markdown_output", None)
            report = IncidentReport(**data)
            
            # Programmatically render the markdown output to ensure absolute consistency
            report.markdown_output = self.render_markdown(report)
            return report
        except (json.JSONDecodeError, ValidationError) as err:
            raise ReportValidationError(
                f"Failed to validate LLM post-mortem output: {str(err)}"
            ) from err

    def render_markdown(self, report: IncidentReport) -> str:
        """Renders the validated report data structure into the SRE template.

        Args:
            report: Validated IncidentReport model.

        Returns:
            Formatted SRE Markdown report string.
        """
        history_section = ""
        if report.historical_reference:
            ref = report.historical_reference
            history_section = (
                f"Incident ID: {ref.incident_id}\n"
                f"Date: {ref.date}\n"
                f"Similarity: {ref.similarity_score:.2f}\n\n"
                f"Root Cause: {ref.root_cause}\n"
                f"Resolution: {ref.resolution}"
            )
        else:
            history_section = "No relevant historical incident found."

        fixes_rendered = "\n".join(
            f"{fix.step_number}. {fix.action}" for fix in report.suggested_fixes
        )

        markdown = f"""# Incident Post-Mortem

## Incident Summary

{report.incident_summary}

## Root Cause Analysis

{report.root_cause_analysis}

## Matching Historical Incident

{history_section}

## Suggested Fix Steps

{fixes_rendered}"""
        return markdown

    def generate_report(
        self, scrubbed_log: str, historical_context: str
    ) -> IncidentReport:
        """Runs the post-mortem synthesis pipeline.

        Args:
            scrubbed_log: Scrubbed logs string.
            historical_context: Hindsight memory context string.

        Returns:
            The validated IncidentReport with rendered markdown output.

        Raises:
            HistoricalContextMissing: If the historical_context is empty.
            ReportValidationError: If the validation fail-safes trigger.
        """
        if not historical_context or not historical_context.strip():
            raise HistoricalContextMissing("Hindsight memory historical context cannot be empty.")

        prompt = self.build_prompt(scrubbed_log, historical_context)
        raw_response = self.model_client.generate_text(
            prompt, system_instruction="You are a JSON-only generating assistant."
        )
        return self.validate_report(raw_response)
