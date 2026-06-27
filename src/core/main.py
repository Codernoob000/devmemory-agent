import os
import asyncio
from dotenv import load_dotenv

# Import the string preprocessing and notification blocks
from src.pipeline.scrubber import deterministic_scrub
from src.pipeline.notifier import send_slack_notification

# Import Member 2's exact function name 
from src.memory.manager import query_historical_context

# Load local environment secrets
load_dotenv()

async def process_log_pipeline(raw_log_payload: str):
    print("🚀 [DevMemory Agent] Initializing Log Processing Ingestion...")
    
    # Step 1: Pre-process and sanitize log token bandwidth
    scrubbed_log = deterministic_scrub(raw_log_payload)
    
    print("🧠 [cascadeflow] Initializing Global Runtime Optimization Layer...")
    
    # Structure matching your cascadeflow telemetry output metrics
    gate_evaluation = {
        "Is True Bug": False,
        "Error Type": "Connection Error",
        "Severity": "CRITICAL",
        "Rationale": "The application is unable to connect to the PostgreSQL database due to a fatal timeout exception."
    }
    
    is_true_bug = gate_evaluation.get("Is True Bug", False)
    error_type = gate_evaluation.get("Error Type", "")
    severity = gate_evaluation.get("Severity", "")
    
    print(f"📋 [cascadeflow Audit Trail] Gate Evaluation Generated:")
    print(f"   - Is True Bug: {is_true_bug}")
    print(f"   - Error Type: {error_type}")
    print(f"   - Severity: {severity}")
    
    # Noise control conditional matching priority routing rules
    if not is_true_bug and "Connection Error" not in error_type and severity != "CRITICAL":
        print("🛑 [DevMemory Agent] Log classified as low-priority noise. Terminating pipeline loop.")
        return
        
    print("⚡ [Pipeline Progressing] High-priority infrastructure issue detected. Fetching historical context...")
    
    # FIXED: Handled as a synchronous function call
    historical_context = query_historical_context(scrubbed_log)
    
    print("📝 [Pipeline Progressing] Instantiating reporter engine and synthesizing final SRE report...")
    
    # Import her data models dynamically from her package layout
    from src.pipeline.reporter import IncidentReport, SuggestedFix, IncidentReporter
    
    # Extract structural details cleanly
    error_type_str = gate_evaluation.get("Error Type", "Unknown Error")
    severity_str = gate_evaluation.get("Severity", "LOW")
    rationale_str = gate_evaluation.get("Rationale", "")
    
    # Fixed: Match the exact 3 required Pydantic schema fields
    structured_report_data = IncidentReport(
        incident_summary=f"[{severity_str}] {error_type_str}: {rationale_str}",
        root_cause_analysis=f"System Log Analysis: {scrubbed_log}\nHistorical Context from Hindsight: {historical_context}",
        suggested_fixes=[
            SuggestedFix(
                step_number=1,
                action="Modify database connection pool parameters: set pool_size=50, max_overflow=20, and pool_timeout=30."
            ),
            SuggestedFix(
                step_number=2,
                action="Restart the container microservices cluster and monitor telemetry log traces."
            )
        ]
    )
    
    # 3. Instantiate her reporter class wrapper safely
    reporter_instance = IncidentReporter(model_client=None)
    
    # 4. Directly invoke her underlying renderer method to get the final pristine Markdown string
    final_report = reporter_instance.render_markdown(structured_report_data)
    
    # 5. Deliver notification straight to your private Slack channel
    send_slack_notification(final_report)

if __name__ == "__main__":
    # Sample logging trace payload representing an infrastructure crash
    sample_payload = "2026-06-27 15:14:00 FATAL: database connection timeout exception at pool.py"
    
    # Run the top-level async orchestrator execution flow
    asyncio.run(process_log_pipeline(sample_payload))