import os
import sys
import io
import time
import json
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# pyrefly: ignore [missing-import]
import litellm

# --- Fix Windows console encoding for emoji/Unicode output ---
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

# Import the downstream modules
from src.pipeline.ingest import ingest_raw_log
from src.pipeline.scrubber import deterministic_scrub
from src.pipeline.notifier import send_slack_notification
from src.memory.manager import query_historical_context
from src.pipeline.reporter import IncidentReport, SuggestedFix, IncidentReporter

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DevMemoryCore")

# FastAPI setup
app = FastAPI(
    title="DevMemory Agent API",
    description="SRE Log Management Agent - Ingestion & Processing Pipeline",
    version="4.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogPayload(BaseModel):
    payload: str

# Cost constants (Standardized Groq pricing)
QWEN_INPUT_COST = 0.07 / 1e6
QWEN_OUTPUT_COST = 0.10 / 1e6
LLAMA_INPUT_COST = 0.59 / 1e6
LLAMA_OUTPUT_COST = 0.79 / 1e6

class GroqModelClient:
    """Model client wrapper conforming to the ModelClient protocol for IncidentReporter."""
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.latency_ms = 0.0

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        start = time.perf_counter()
        response = litellm.completion(
            model=f"groq/{self.model_name}",
            messages=messages,
            temperature=0.1
        )
        end = time.perf_counter()
        
        self.latency_ms = (end - start) * 1000.0
        self.prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
        self.completion_tokens = getattr(response.usage, "completion_tokens", 0)
        self.total_tokens = getattr(response.usage, "total_tokens", 0)
        return response.choices[0].message.content

async def process_log_pipeline(raw_log_payload: str) -> dict:
    """
    Core pipeline function that runs log ingestion, scrubbing, CascadeFlow classification,
    Hindsight memory check, high-tier report synthesis, and notifications.
    """
    logger.info("Initializing Log Ingestion and Processing Pipeline...")
    
    # 1. Ingest
    clean_log = ingest_raw_log(raw_log_payload)
    if not clean_log:
        return {
            "status": "skipped",
            "reason": "Empty log payload.",
            "report_markdown": "## ℹ️ Empty Log Payload\n\nNo log was provided for ingestion.",
            "latency_ms": 0.0,
            "financial_savings_delta": 0.0
        }

    # 2. Scrub
    scrubbed_log = deterministic_scrub(clean_log)

    # 3. CascadeFlow Classification (Draft Model Pass)
    classifier_model = "qwen/qwen3-32b"
    classification_prompt = f"""You are an SRE log triage assistant. Analyze this log payload:
{scrubbed_log}

Determine if this log payload contains a true runtime crash, database error, out of memory (OOM), deadlock, or timeout that needs engineering resolution.
If it is just formatting warnings, heartbeat logs, system startup info, or cosmetic noise, classify it as noise.

You must respond with a JSON object in this exact format:
{{
  "is_crash": true/false,
  "error_type": "Connection Error/OOM/Timeout/Deadlock/None/etc",
  "severity": "CRITICAL/HIGH/MEDIUM/LOW/NONE",
  "rationale": "Short explanation of the classification decision."
}}
Do not include any other text or markdown wrapping. Output only raw valid JSON.
"""
    
    logger.info(f"Routing to draft classifier model ({classifier_model}) for crash check...")
    class_start = time.perf_counter()
    response = litellm.completion(
        model=f"groq/{classifier_model}",
        messages=[{"role": "user", "content": classification_prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    class_end = time.perf_counter()
    
    class_latency_ms = (class_end - class_start) * 1000.0
    class_prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
    class_completion_tokens = getattr(response.usage, "completion_tokens", 0)
    class_total_tokens = getattr(response.usage, "total_tokens", 0)
    
    classification_content = response.choices[0].message.content
    try:
        classification = json.loads(classification_content)
    except Exception as e:
        logger.error(f"Failed to parse classification JSON: {e}. Fallback to regex.")
        is_crash = "true" in classification_content.lower()
        classification = {
            "is_crash": is_crash,
            "error_type": "Log Exception" if is_crash else "None",
            "severity": "HIGH" if is_crash else "NONE",
            "rationale": "Regex fallback parsing."
        }

    is_crash = classification.get("is_crash", False)
    error_type = classification.get("error_type", "Unknown")
    severity = classification.get("severity", "LOW")
    rationale = classification.get("rationale", "")

    # Calculate classification costs
    class_cost = (class_prompt_tokens * QWEN_INPUT_COST) + (class_completion_tokens * QWEN_OUTPUT_COST)
    class_direct_cost = (class_prompt_tokens * LLAMA_INPUT_COST) + (class_completion_tokens * LLAMA_OUTPUT_COST)

    # Initialize variables for escalation path
    report_prompt_tokens = 0
    report_completion_tokens = 0
    report_total_tokens = 0
    report_latency_ms = 0.0
    report_cost = 0.0
    hindsight_match = False
    hindsight_score = 0.0
    slack_success = False
    final_report_md = ""
    escalated = False
    report_data = None

    # Noise control conditional matching
    if not is_crash and "Connection" not in error_type and severity != "CRITICAL":
        logger.info("Log classified as noise. Terminating pipeline.")
        final_report_md = f"## ℹ️ Log Classified as Noise\n\n**Reason:** {rationale}\n\n**Analysis Details:** Early termination occurred to optimize resource use. No runtime crash was detected."
        savings_delta = class_direct_cost - class_cost
        report_data = {
            "incident_summary": f"Log Classified as Noise: {rationale}",
            "root_cause_analysis": "No crash/exception patterns detected in the raw log stream. Early termination applied to save token costs.",
            "historical_reference": None,
            "suggested_fixes": [
                {"step_number": 1, "action": "No actions required. Log is normal telemetry noise."}
            ]
        }
    else:
        # Escalation Gate Triggered!
        escalated = True
        logger.info("High-priority SRE crash detected. Escalating to high-tier model...")
        
        # 4. Hindsight Memory Query
        historical_context = query_historical_context(scrubbed_log)
        
        # Check if match was found in context string
        if "Match Found:" in historical_context:
            hindsight_match = True
            score_match = re.search(r'Similarity:\s*([\d\.]+)', historical_context)
            if score_match:
                try:
                    hindsight_score = float(score_match.group(1))
                except ValueError:
                    hindsight_score = 0.8
            else:
                hindsight_score = 0.8
        
        # 5. Report Synthesis Engine (High-Tier Model Pass)
        logger.info("Escalating SRE report synthesis to LLaMA-3.3-70B-Versatile...")
        client = GroqModelClient(model_name="llama-3.3-70b-versatile")
        reporter = IncidentReporter(model_client=client)
        
        try:
            report = reporter.generate_report(scrubbed_log, historical_context)
            final_report_md = report.markdown_output
            report_data = report.model_dump()
        except Exception as e:
            logger.error(f"Failed to generate structured report via reporter: {e}")
            final_report_md = f"# Incident Post-Mortem (Fallback)\n\n## Incident Summary\n[{severity}] {error_type}: {rationale}\n\n## Root Cause Analysis\n{scrubbed_log}\n\n## Historical Reference\n{historical_context}\n\n## Suggested Fix Steps\n1. Review connection pool settings."
            
            # Extract historical details safely for UI matching
            hist_id = "Unknown"
            if hindsight_match:
                id_match = re.search(r'Match Found:\s*([^\s\n]+)', historical_context)
                if id_match:
                    hist_id = id_match.group(1)
            
            report_data = {
                "incident_summary": f"[{severity}] {error_type}: {rationale}",
                "root_cause_analysis": f"The raw application log traces indicate a fatal anomaly: {scrubbed_log}",
                "historical_reference": {
                    "incident_id": hist_id,
                    "date": "2025-11-12",
                    "root_cause": "Unresolved historical incident lookup failure.",
                    "resolution": "Check the suggested patch options below to remediate.",
                    "similarity_score": hindsight_score
                },
                "suggested_fixes": [
                    {"step_number": 1, "action": "Review database and server connection settings."}
                ]
            }
            
        report_prompt_tokens = client.prompt_tokens
        report_completion_tokens = client.completion_tokens
        report_total_tokens = client.total_tokens
        report_latency_ms = client.latency_ms
        
        # Calculate report costs
        report_cost = (report_prompt_tokens * LLAMA_INPUT_COST) + (report_completion_tokens * LLAMA_OUTPUT_COST)
        
        # Savings is the classification difference (we saved on using Qwen for classification)
        savings_delta = class_direct_cost - class_cost

        # 6. Notifier Workflow (Slack Webhook)
        logger.info("Dispatching post-mortem report to Slack...")
        slack_success = send_slack_notification(final_report_md)

    # Compile tracking telemetry record
    total_latency = class_latency_ms + report_latency_ms
    total_prompt_tokens = class_prompt_tokens + report_prompt_tokens
    total_completion_tokens = class_completion_tokens + report_completion_tokens
    total_tokens = class_total_tokens + report_total_tokens
    total_cost = class_cost + report_cost

    audit_record = {
        "timestamp": datetime.now().isoformat(),
        "raw_log_length": len(raw_log_payload),
        "scrubbed_log_length": len(scrubbed_log),
        "is_crash": is_crash,
        "error_type": error_type,
        "severity": severity,
        "rationale": rationale,
        "cascadeflow_escalated": escalated,
        "models_used": [classifier_model, "llama-3.3-70b-versatile"] if escalated else [classifier_model],
        "latency_ms": total_latency,
        "token_usage": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens
        },
        "cost_usd": total_cost,
        "financial_savings_delta": savings_delta,
        "hindsight_match": hindsight_match,
        "hindsight_score": hindsight_score,
        "slack_dispatched": slack_success
    }

    # Append record to data/audit_trail.json safely
    audit_trail_path = "data/audit_trail.json"
    try:
        os.makedirs("data", exist_ok=True)
        if os.path.exists(audit_trail_path):
            with open(audit_trail_path, "r", encoding="utf-8") as f:
                trail_data = json.load(f)
                if not isinstance(trail_data, list):
                    trail_data = []
            trail_data.append(audit_record)
        else:
            trail_data = [audit_record]
            
        with open(audit_trail_path, "w", encoding="utf-8") as f:
            json.dump(trail_data, f, indent=2)
        logger.info(f"Audit record written to {audit_trail_path}.")
    except Exception as e:
        logger.error(f"Failed to append to audit trail JSON: {e}")

    # Return structured result
    return {
        "status": "success" if escalated else "skipped",
        "severity": severity,
        "error_type": error_type,
        "rationale": rationale,
        "cascadeflow_escalated": escalated,
        "slack_dispatched": slack_success,
        "report_markdown": final_report_md,
        "financial_savings_delta": savings_delta,
        "latency_ms": total_latency,
        "audit_record": audit_record,
        "report_data": report_data
    }

@app.get("/api/audit-trail")
async def get_audit_trail():
    """
    Returns the accumulated SRE audit logs from data/audit_trail.json.
    """
    audit_trail_path = "data/audit_trail.json"
    if os.path.exists(audit_trail_path):
        try:
            with open(audit_trail_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@app.post("/api/process-log")
async def process_log(body: LogPayload):
    """
    Accepts a raw log string, runs the full DevMemory processing pipeline,
    and dispatches the SRE post-mortem report to Slack.
    """
    try:
        res = await process_log_pipeline(body.payload)
        return res
    except Exception as e:
        logger.exception("Error processing log via API")
        raise HTTPException(status_code=500, detail=str(e))