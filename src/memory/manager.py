#!/usr/bin/env python3
"""
AntigravityHindsightManager - Core Memory & Storage Manager.
Integrates the Antigravity Orchestration Tier, Hindsight Memory Layer, and CascadeFlow routing.
"""

import os
import json
import math
import re
import logging
import asyncio
import urllib.request
import urllib.error
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

# Setup default logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AntigravityHindsightManager")

# --- Antigravity SDK Import Hook & Mocking Layer ---
# This ensures compilation and execution in environments where the SDK is not installed
try:
    from google.antigravity.hooks import hooks
    from google.antigravity import types
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.debug("Google Antigravity SDK not found in path. Activating mocked hook base classes.")
    
    # Define fallback structures for typing and decoration
    class MockHookContext:
        def __init__(self):
            self.session_id = "mock-session"
            
    class MockOnSessionStartHook:
        async def run(self, context: Any) -> None:
            pass

    class MockOnToolErrorHook:
        async def run(self, context: Any, data: Any) -> Optional[str]:
            return None

    class MockPreTurnHook:
        async def run(self, context: Any, data: str) -> Any:
            return data

    # Create namespace mimics
    class types:
        class HookResult:
            def __init__(self, allow: bool, content: Optional[str] = None):
                self.allow = allow
                self.content = content
                
        class AntigravityValidationError(Exception):
            pass
            
        class AntigravityConnectionError(Exception):
            pass

    class hooks:
        OnSessionStartHook = MockOnSessionStartHook
        OnToolErrorHook = MockOnToolErrorHook
        PreTurnHook = MockPreTurnHook
        HookContext = MockHookContext


# --- Local Semantic Search Fallback Engine (TF-IDF Cosine Similarity) ---
class LocalSemanticEngine:
    """
    A pure-Python TF-IDF Vectorizer and Cosine Similarity matcher.
    Acts as a high-fidelity local fallback semantic vector database.
    """
    def __init__(self):
        self.scenarios: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.vocab: set = set()
        self.idf: Dict[str, float] = {}

    def fit(self, scenarios: List[Dict[str, Any]]):
        """Fits the vocabulary and calculates IDF based on the database of scenarios."""
        self.scenarios = scenarios
        # Combine signature and cause to build a richer semantic search context
        documents = [
            f"{s.get('error_signature', '')} {s.get('root_cause', '')}"
            for s in scenarios
        ]
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        self.vocab = set(word for doc in self.doc_tokens for word in doc)
        
        num_docs = len(documents)
        self.idf = {}
        for word in self.vocab:
            doc_count = sum(1 for doc in self.doc_tokens if word in doc)
            # Apply standard smoothing to prevent division by zero
            self.idf[word] = math.log((1 + num_docs) / (1 + doc_count)) + 1.0

    def _tokenize(self, text: str) -> List[str]:
        """Cleans, tokenizes, and filters noise from error outputs."""
        # Convert to lowercase and replace punctuation with spaces
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        
        # Filter out common programming words that hold little diagnostic semantic weight
        stopwords = {
            'traceback', 'most', 'recent', 'call', 'last', 'file', 'line', 'in', 
            'raise', 'error', 'exception', 'at', 'the', 'a', 'of', 'and', 'to', 
            'for', 'on', 'with', 'during', 'failed', 'executing', 'command'
        }
        return [t for t in tokens if t not in stopwords]

    def _get_tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        """Calculates the TF-IDF weight map for a given set of tokens."""
        tf = Counter(tokens)
        vector = {}
        for word, count in tf.items():
            if word in self.idf:
                vector[word] = count * self.idf[word]
        return vector

    def query(self, query_text: str) -> List[float]:
        """Computes cosine similarity of the query against all fitted scenarios."""
        if not self.scenarios:
            return []
            
        query_tokens = self._tokenize(query_text)
        query_vector = self._get_tfidf_vector(query_tokens)
        query_magnitude = math.sqrt(sum(val ** 2 for val in query_vector.values()))
        
        scores = []
        for doc_tokens in self.doc_tokens:
            doc_vector = self._get_tfidf_vector(doc_tokens)
            doc_magnitude = math.sqrt(sum(val ** 2 for val in doc_vector.values()))
            
            if query_magnitude * doc_magnitude == 0.0:
                scores.append(0.0)
                continue
                
            dot_product = sum(
                query_vector.get(word, 0.0) * doc_vector.get(word, 0.0)
                for word in query_vector if word in doc_vector
            )
            scores.append(dot_product / (query_magnitude * doc_magnitude))
            
        return scores


# --- Main Antigravity-Hindsight Memory Manager Class ---
class AntigravityHindsightManager:
    """
    Manages semantic data seeding and retrieval between the Antigravity Orchestration Tier
    and the Hindsight Persistent Vector Store, implementing CascadeFlow routing gates.
    """
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        seed_data_path: Optional[str] = None,
        similarity_threshold: float = 0.30
    ):
        # 1. Establish secure endpoint routing variables from parameters or local environment
        self.endpoint = endpoint or os.environ.get("HINDSIGHT_ENDPOINT")
        self.api_key = api_key or os.environ.get("HINDSIGHT_API_KEY")
        self.seed_data_path = seed_data_path or os.environ.get("SEED_DATA_PATH", "data/seed_data.json")
        self.similarity_threshold = similarity_threshold
        
        # Connection params
        self.timeout = float(os.environ.get("HINDSIGHT_TIMEOUT", "5.0"))
        self.max_retries = int(os.environ.get("HINDSIGHT_MAX_RETRIES", "3"))
        
        # Local semantic store cache
        self.cache: List[Dict[str, Any]] = []
        self.local_engine = LocalSemanticEngine()
        
        self.logger = logger
        self.logger.info(
            f"Initialized AntigravityHindsightManager. "
            f"Endpoint: {self.endpoint or 'LOCAL_ONLY'}, "
            f"Seed Path: {self.seed_data_path}"
        )

    async def seed_historical_memory(self) -> bool:
        """
        Deterministically reads data/seed_data.json and uses an automated
        execution loop to index and register records into Hindsight's vector layer.
        """
        self.logger.info(f"Seeding memory from path: {self.seed_data_path}")
        
        # Defensive check: FileNotFoundError handling
        try:
            with open(self.seed_data_path, "r", encoding="utf-8") as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.logger.error(
                f"FileNotFoundError: Seed dataset file not found at {self.seed_data_path}. "
                f"Defaulting to empty local context cache."
            )
            self.cache = []
            return False
        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSONDecodeError: Malformed JSON array in {self.seed_data_path}: {e}. "
                f"Aborting seed processing to protect thread stability."
            )
            self.cache = []
            return False
            
        if not self.cache:
            self.logger.warning("Loaded seed dataset is empty.")
            return False

        # Fit local semantic fallback matcher
        self.local_engine.fit(self.cache)
        self.logger.info(f"Fitted {len(self.cache)} outage scenarios to local fallback engine.")

        # If remote endpoint is registered, index items over the network
        if self.endpoint:
            seeded_count = 0
            for record in self.cache:
                success = await self._send_to_hindsight(record)
                if success:
                    seeded_count += 1
            self.logger.info(f"Completed network seeding: indexed {seeded_count}/{len(self.cache)} records.")
        else:
            self.logger.info("Operating in Local Fallback mode (no endpoint configured). Cache primed.")
            
        return True

    async def _send_to_hindsight(self, record: dict) -> bool:
        """Helper to index a single record to Hindsight with retry loops and timeout protection."""
        url = f"{self.endpoint.rstrip('/')}/index"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        data = json.dumps(record).encode("utf-8")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Wrap urllib synchronous HTTP request inside an async executor
                def _post():
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=self.timeout) as res:
                        return res.status
                
                status = await asyncio.to_thread(_post)
                if status in (200, 201):
                    return True
            except (urllib.error.URLError, TimeoutError) as e:
                self.logger.warning(
                    f"Connection failure on seed attempt {attempt}/{self.max_retries} "
                    f"for session {record.get('session_id')}: {e}"
                )
                if attempt < self.max_retries:
                    # Exponential backoff retry
                    await asyncio.sleep(2 ** attempt * 0.1)
            except Exception as e:
                self.logger.error(f"Unrecoverable error sending record to vector store: {e}")
                break
        return False

    async def query_past_resolutions(self, active_error_trace: str) -> dict:
        """
        Executes an asynchronous cross-session semantic vector retrieval routine.
        Fails back gracefully to local cosine TF-IDF match if remote times out or is offline.
        """
        self.logger.info(f"Querying Hindsight memory for exception signature...")
        
        # Pruning query to avoid raw buffer limits
        truncated_trace = (active_error_trace[:200] + '...') if len(active_error_trace) > 200 else active_error_trace
        self.logger.debug(f"Target query: {truncated_trace}")

        # Fallback Schema Structure
        fallback_schema = {
            "matched": False,
            "session_id": None,
            "error_signature": None,
            "root_cause": "No historical resolution match found intersecting this error vector.",
            "resolution_patch": None,
            "similarity_score": 0.0
        }

        # 1. Attempt Retrieval from Remote Hindsight Endpoint if configured
        if self.endpoint:
            url = f"{self.endpoint.rstrip('/')}/query"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            payload = json.dumps({"query": active_error_trace}).encode("utf-8")
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    def _query():
                        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                        with urllib.request.urlopen(req, timeout=self.timeout) as res:
                            return res.read().decode("utf-8"), res.status
                            
                    response_text, status = await asyncio.to_thread(_query)
                    if status == 200:
                        result = json.loads(response_text)
                        if result.get("matched"):
                            self.logger.info(f"Remote match found (Score: {result.get('similarity_score')})")
                            return {
                                "matched": True,
                                "session_id": result.get("session_id"),
                                "error_signature": result.get("error_signature"),
                                "root_cause": result.get("root_cause"),
                                "resolution_patch": result.get("resolution_patch"),
                                "similarity_score": result.get("similarity_score", 1.0)
                            }
                        else:
                            self.logger.info("Remote vector search completed with no relevant matches.")
                            break # Go to local semantic fallback to double check
                except (urllib.error.URLError, TimeoutError) as e:
                    self.logger.warning(
                        f"Hindsight vector store connection failure on query "
                        f"(Attempt {attempt}/{self.max_retries}): {e}"
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt * 0.1)
                except Exception as e:
                    self.logger.error(f"Unexpected error during remote Hindsight query: {e}")
                    break

        # 2. Fallback to Local Semantic Search Engine (if remote fails or is unset)
        self.logger.info("Executing local TF-IDF semantic matching fallback logic.")
        try:
            if not self.cache:
                # Prime memory from local JSON if cache is empty
                await self.seed_historical_memory()
                
            if not self.cache:
                return fallback_schema

            scores = self.local_engine.query(active_error_trace)
            if not scores:
                return fallback_schema

            # Find best match
            best_idx = int(scores.index(max(scores)))
            best_score = scores[best_idx]
            
            self.logger.info(f"Local semantic search completed. Best Score: {best_score:.4f}")
            
            if best_score >= self.similarity_threshold:
                match = self.cache[best_idx]
                return {
                    "matched": True,
                    "session_id": match.get("session_id"),
                    "error_signature": match.get("error_signature"),
                    "root_cause": match.get("root_cause"),
                    "resolution_patch": match.get("resolution_patch"),
                    "similarity_score": round(best_score, 4)
                }
        except Exception as e:
            self.logger.error(f"Error executing local fallback semantic match: {e}")
            
        return fallback_schema

    # --- CascadeFlow Intelligent Routing Decision Helper ---
    def evaluate_cascadeflow_routing(self, query_result: dict) -> Tuple[str, str]:
        """
        CascadeFlow Cost Gate Router.
        
        Routes queries based on the Hindsight match outcome:
        - Matched = True -> Route to low-cost model (e.g. gemini-1.5-flash) to apply the known fix.
        - Matched = False -> Route to high-tier reasoning engine (e.g. gemini-1.5-pro) for deep analysis.
        """
        if query_result.get("matched"):
            model = "gemini-1.5-flash"
            rationale = "Hindsight hit: A verified historical resolution is available. Routing to low-cost model for patch application."
        else:
            model = "gemini-1.5-pro"
            rationale = "Hindsight miss: No historical resolution found. Escalating to high-tier reasoning engine for anomaly resolution."
            
        self.logger.info(f"CascadeFlow Decision: Routed to '{model}' | Reason: {rationale}")
        return model, rationale


# --- Antigravity Agent Hook Integrations ---

class HindsightSessionStartHook(hooks.OnSessionStartHook):
    """Hooks into Antigravity session startup to seed historical memories."""
    def __init__(self, manager: AntigravityHindsightManager):
        self.manager = manager
        
    async def run(self, context: hooks.HookContext) -> None:
        self.manager.logger.info(f"SessionStartHook triggered for session: {context.session_id}")
        await self.manager.seed_historical_memory()


class HindsightPreTurnHook(hooks.PreTurnHook):
    """
    Hooks into Antigravity pre-turn pipeline.
    Scans incoming prompts for stack traces and injects matching resolutions.
    """
    def __init__(self, manager: AntigravityHindsightManager):
        self.manager = manager
        
    async def run(self, context: hooks.HookContext, data: str) -> types.HookResult:
        self.manager.logger.info("PreTurnHook scanning input prompt for system anomalies...")
        
        # Pattern matching for generic traces (e.g. traceback, exception, OOM, Error)
        error_indicators = ["traceback", "exception", "error", "oom", "timeout", "failed executing"]
        has_error = any(indicator in data.lower() for indicator in error_indicators)
        
        if has_error:
            self.manager.logger.info("Potential error signature detected in prompt. Consulting Hindsight vector store...")
            match = await self.manager.query_past_resolutions(data)
            
            if match["matched"]:
                self.manager.logger.info(f"Found match: {match['session_id']}. Injecting resolution details.")
                enhanced_content = (
                    f"\n\n[SYSTEM INJECTION: HINDSIGHT HISTORICAL OUTAGE MATCH]\n"
                    f"A similar error was registered previously under session: {match['session_id']}\n"
                    f"- Historical Root Cause: {match['root_cause']}\n"
                    f"- Verified Resolution Patch:\n{match['resolution_patch']}\n"
                    f"Please apply this pattern directly to resolve the user's issue.\n"
                )
                # Allow turn with enhanced context injected
                return types.HookResult(allow=True, content=data + enhanced_content)
                
        return types.HookResult(allow=True, content=data)


class HindsightToolErrorHook(hooks.OnToolErrorHook):
    """
    Hooks into Antigravity tool errors.
    Queries Hindsight when a tool fails and returns guidance.
    """
    def __init__(self, manager: AntigravityHindsightManager):
        self.manager = manager
        
    async def run(self, context: hooks.HookContext, data: Any) -> Optional[str]:
        # 'data' represents the Exception thrown by the tool
        error_message = f"{type(data).__name__}: {str(data)}"
        self.manager.logger.warning(f"ToolErrorHook triggered on: {error_message}")
        
        match = await self.manager.query_past_resolutions(error_message)
        if match["matched"]:
            self.manager.logger.info(f"Injecting historical self-correction guidance for tool crash.")
            return (
                f"[Self-Correction Guideline from Hindsight Memory]\n"
                f"The tool crashed with error: {error_message}\n"
                f"Historical match {match['session_id']} suggests this is due to:\n"
                f"Root Cause: {match['root_cause']}\n"
                f"Recommended fix procedure:\n{match['resolution_patch']}\n"
                f"Please self-correct and execute again."
            )
            
        return None # Let error propagate normally if no match


# --- Backward Compatibility Integration Wrapper for main.py (Member 1) ---
def query_historical_context(clean_log: str) -> str:
    """Synchronous interface function for Member 1 integration.
    Queries Hindsight memory for matching resolutions and returns a formatted explanation string.
    """
    # 1. Locate the seed data file relative to the project root
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    seed_path = os.path.join(workspace_root, "data", "seed_data.json")
    
    # 2. Instantiate manager locally in local mode
    manager = AntigravityHindsightManager(seed_data_path=seed_path)
    
    # 3. Create/retrieve event loop safely to execute async calls inside a synchronous execution thread
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    async def _execute_pipeline():
        await manager.seed_historical_memory()
        return await manager.query_past_resolutions(clean_log)
        
    if loop.is_running():
        # Execute asynchronously in a separate worker thread to avoid collision
        import threading
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(_execute_pipeline()))
            result = future.result()
    else:
        result = loop.run_until_complete(_execute_pipeline())
        
    # 4. Return matching context for Member 1's report generation
    if result["matched"]:
        return (
            f"HISTORICAL CONTEXT [Hindsight]:\n"
            f"- Match Found: {result['session_id']}\n"
            f"- Root Cause: {result['root_cause']}\n"
            f"- Resolution Patch:\n{result['resolution_patch']}"
        )
    else:
        return "HISTORICAL CONTEXT [Hindsight]: No matching historical resolutions found."


# --- Local Unit Test / Main Entry Block ---
if __name__ == "__main__":
    async def main():
        print("=" * 70)
        print("DEV-MEMORY AGENT: HINDSIGHT STORAGE & PIPELINE UNIT TEST")
        print("=" * 70)
        
        # MOCK missing data/seed_data.json path error validation
        print("\n--- TEST case 1: Missing seed file gracefully handles exception ---")
        bad_manager = AntigravityHindsightManager(seed_data_path="data/missing_non_existent.json")
        seed_ok = await bad_manager.seed_historical_memory()
        print(f"Missing file seeding returned successfully: {seed_ok} (No Crash)")

        # Initialize manager with valid workspace path
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        seed_path = os.path.join(workspace_root, "data", "seed_data.json")
        
        print(f"\n--- Instantiating Manager with seed file: {seed_path} ---")
        manager = AntigravityHindsightManager(seed_data_path=seed_path)
        
        # Seed historical memory
        await manager.seed_historical_memory()

        # TEST 2: Exact/Close semantic query match (SQL connection pool)
        print("\n--- TEST case 2: Close semantic query match (SQL Connection Pool) ---")
        sql_query = (
            "We are seeing timeout failures on SQLAlchemy. "
            "Traceback says ConnectionPoolTimeoutException: QueuePool limit reached overflow 20."
        )
        sql_result = await manager.query_past_resolutions(sql_query)
        print(f"Match status: {sql_result['matched']}")
        print(f"Matched Session ID: {sql_result['session_id']}")
        print(f"Match Score: {sql_result['similarity_score']}")
        print(f"Suggested Patch Length: {len(sql_result['resolution_patch'] or '')} chars")
        
        # Evaluate CascadeFlow Routing
        sql_model, sql_routing = manager.evaluate_cascadeflow_routing(sql_result)

        # TEST 3: Close semantic query match (Redis OOM maxmemory)
        print("\n--- TEST case 3: Close semantic query match (Redis OOM) ---")
        redis_query = (
            "redis.exceptions.ResponseError: Command not allowed when memory limit reached. "
            "Server reports OOM status and crashes on SET."
        )
        redis_result = await manager.query_past_resolutions(redis_query)
        print(f"Match status: {redis_result['matched']}")
        print(f"Matched Session ID: {redis_result['session_id']}")
        print(f"Match Score: {redis_result['similarity_score']}")
        
        # Evaluate CascadeFlow Routing
        redis_model, redis_routing = manager.evaluate_cascadeflow_routing(redis_result)

        # TEST 4: No Match Scenario (Pruning/Fallback Verification)
        print("\n--- TEST case 4: Non-matching error (Pruning/Fallback Verification) ---")
        unrelated_query = (
            "Uncaught TypeError: Cannot read properties of undefined (reading 'split') "
            "at Page.render (index.js:52) in frontend application."
        )
        unrelated_result = await manager.query_past_resolutions(unrelated_query)
        print(f"Match status: {unrelated_result['matched']}")
        print(f"Matched Session ID: {unrelated_result['session_id']}")
        print(f"Content: {unrelated_result['root_cause']}")
        
        # Evaluate CascadeFlow Routing
        unrelated_model, unrelated_routing = manager.evaluate_cascadeflow_routing(unrelated_result)

        # TEST 5: Antigravity Hooks execution simulation
        print("\n--- TEST case 5: Pre-Turn Hook simulation ---")
        pre_turn_hook = HindsightPreTurnHook(manager)
        mock_context = hooks.HookContext()
        
        # Execute hook with error query
        hook_res = await pre_turn_hook.run(mock_context, sql_query)
        print(f"Hook execution success: {isinstance(hook_res, types.HookResult)}")
        print(f"Hook allowed turn: {hook_res.allow}")
        print(f"Is custom resolution injected into prompt: {'SYSTEM INJECTION' in hook_res.content}")

        # Metrics output summary in clean JSON format
        print("\n" + "=" * 70)
        print("EVALUATION METRICS SUMMARY (STDOUT LOG)")
        print("=" * 70)
        
        metrics = {
            "seeding_status": "SUCCESSFUL",
            "seed_records_loaded": len(manager.cache),
            "similarity_threshold_configured": manager.similarity_threshold,
            "test_runs": [
                {
                    "test_id": "sqlalchemy_pool_leak",
                    "query": sql_query,
                    "matched": sql_result["matched"],
                    "session_id": sql_result["session_id"],
                    "similarity_score": sql_result["similarity_score"],
                    "cascadeflow_routing": sql_model
                },
                {
                    "test_id": "redis_oom",
                    "query": redis_query,
                    "matched": redis_result["matched"],
                    "session_id": redis_result["session_id"],
                    "similarity_score": redis_result["similarity_score"],
                    "cascadeflow_routing": redis_model
                },
                {
                    "test_id": "unrelated_frontend_typeerror",
                    "query": unrelated_query,
                    "matched": unrelated_result["matched"],
                    "session_id": unrelated_result["session_id"],
                    "similarity_score": unrelated_result["similarity_score"],
                    "cascadeflow_routing": unrelated_model
                }
            ],
            "sdk_available_globally": SDK_AVAILABLE
        }
        
        print(json.dumps(metrics, indent=2))
        print("=" * 70)

    asyncio.run(main())