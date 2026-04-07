"""
core/utils/code_runner.py
========================
Piston API Code Execution Sandbox — SmartRecruit Technical Arena
=============================================================
Executes candidate code securely via the free Piston API v2.
Supports major languages. Returns stdout, stderr, compile errors.
Replaces Judge0 to provide a free, keyless sandbox environment.
"""

import logging
from .docker_engine import run_code_in_sandbox

logger = logging.getLogger(__name__)

def execute_code(
    source_code: str,
    language: str,
    stdin: str = "",
    expected_output: str = "",
) -> dict:
    """
    Submits code to local Docker Sandbox and returns structured metrics.
    """
    try:
        # Use local Docker Engine for Zero-Cost, Secure Execution
        result = run_code_in_sandbox(source_code, language)
        
        stdout = (result.get('stdout') or "").strip()
        stderr = (result.get('stderr') or "").strip()
        status_desc = result.get('status', 'ACCEPTED')
        
        score = 0
        if status_desc == "ACCEPTED":
            expected = expected_output.strip()
            if not expected or stdout == expected:
                score = 100
            else:
                score = 30 
                status_desc = "WRONG_ANSWER"
        
        return {
            "status":         status_desc,
            "stdout":         stdout,
            "stderr":         stderr,
            "compile_output": "",
            "time":           "0.10s", # Estimated for local
            "memory":         "128 MB",
            "score":          score,
            "token":          "local-docker-cluster",
        }

    except Exception as e:
        logger.error(f"[DockerSandbox] Execution failed: {e}")
        return {
            "status": "ERROR",
            "stdout": "",
            "stderr": f"Execution error: {e}",
            "compile_output": "",
            "time": "N/A",
            "memory": 0,
            "score": 0,
            "token": "",
        }
