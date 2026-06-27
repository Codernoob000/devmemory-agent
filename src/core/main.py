import os
import asyncio  # Resolves the runtime coroutine
from dotenv import load_dotenv
from pydantic import BaseModel
import json
import cascadeflow as cf

# Load local environment variables for model access
load_dotenv()

# Define the structured quality gate schema using Pydantic
class LogEvaluationSchema(BaseModel):
    is_true_bug: bool
    error_type: str
    severity: str
    rationale: str

def process_error_pipeline(raw_log_payload: str):
    print("🚀 [DevMemory Agent] Initializing Log Processing Ingestion...")
    
    # 1. Pipeline Pre-processing Hook (Handled downstream by Member 3)
    from src.pipeline.scrubber import deterministic_scrub
    clean_log = deterministic_scrub(raw_log_payload)
    
    print("🧠 [cascadeflow] Initializing Global Runtime Optimization Layer...")
    
    # Initialize cascadeflow core engine cleanly
    cf.init()
    
    # We append a structural instruction so the model reliably outputs our schema fields
    prompt = f"""
    Analyze the following system application log snippet.
    You must respond strictly with a valid JSON object matching this schema:
    {{
        "is_true_bug": bool,
        "error_type": string,
        "severity": string,
        "rationale": string
    }}
    
    LOG PAYLOAD:
    {clean_log}
    """
    
    print("⚡ [cascadeflow] Invoking Tier 1 Filter Engine (Cost-Optimized Auto-Routing)...")
    
    # Pass configuration inside the runtime orchestration selection tier
    agent = cf.get_cost_optimized_agent("groq/qwen3-32b")
    
    # FIX: Use native response_format json_object parameters instead of the unsupported response_model parameter
    evaluation_raw = asyncio.run(
        agent.run(
            prompt,
            response_format={"type": "json_object"}
        )
    )
    
    # Extract the text content from the agent's return profile
    if hasattr(evaluation_raw, "content"):
        raw_text = evaluation_raw.content
    elif isinstance(evaluation_raw, dict) and "content" in evaluation_raw:
        raw_text = evaluation_raw["content"]
    else:
        raw_text = str(evaluation_raw)

    # Parse and safely remap the JSON string into our structured Pydantic object
    try:
        parsed_json = json.loads(raw_text)
        evaluation = LogEvaluationSchema(**parsed_json)
    except Exception as e:
        print(f"⚠️ [Parsing Warning] Direct structural validation failed: {e}. Falling back to text wrapper parsing.")
        # Fallback block to safely extract values if structural formatting variations happen
        evaluation = LogEvaluationSchema(
            is_true_bug=True, 
            error_type="Runtime Error", 
            severity="HIGH", 
            rationale=raw_text[:200]
        )

    print(f"📋 [cascadeflow Audit Trail] Gate Evaluation Generated:")
    print(f"   - Is True Bug: {evaluation.is_true_bug}")
    print(f"   - Error Type: {evaluation.error_type}")
    print(f"   - Severity: {evaluation.severity}")
    print(f"   - Rationale: {evaluation.rationale}")
    
    # 2. Quality Gate Branch Routing Escalation
    if not evaluation.is_true_bug:
        print("🛑 [DevMemory Agent] Log classified as low-priority noise. Terminating pipeline loop to preserve API credits.")
        return {"status": "ignored", "reason": evaluation.rationale, "cost_saved": True}
        
    print("🔍 [Hindsight] Quality Gate cleared. Querying asynchronous vector memory storage...")
    
    # 3. Persistent Memory Retrieval Hook (Handled downstream by Member 2)
    from src.memory.manager import query_historical_context
    historical_fix_context = query_historical_context(clean_log)
    
    print("⚡ [cascadeflow] Escalating to Tier 2 Premium Reasoning Engine for Report Compilation...")
    
    # Switch to the high-tier agent when the quality gate requires it
    premium_agent = cf.get_quality_optimized_agent("openrouter/openai/gpt-4o")
    
    # 4. Final Output Synthesis Hook (Handled downstream by Member 5)
    from src.pipeline.reporter import synthesize_post_mortem
    final_report = synthesize_post_mortem(premium_agent, clean_log, historical_fix_context)
    
    # 5. Delivery Webhook Hook (Handled downstream by Member 3)
    from src.pipeline.notifier import send_slack_notification
    send_slack_notification(final_report)
    
    print("✅ [DevMemory Agent] Post-Mortem pipeline complete.")
    return {"status": "success", "report": final_report}

if __name__ == "__main__":
    # Test execution trace payload simulating a broken staging database connector
    mock_log = "ERROR 2026-06-27 11:59:05 Connection lost to PostgreSQL at 192.168.1.54:5432. Fatal Timeout Exception."
    process_error_pipeline(mock_log)