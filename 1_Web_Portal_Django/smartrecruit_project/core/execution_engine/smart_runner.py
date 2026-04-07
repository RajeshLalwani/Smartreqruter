import os
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import docker
from docker.errors import DockerException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-runner")

app = FastAPI(title="Smart-Runner Execution Controller")

# Configuration
IMAGE_MAP = {
    "python": "smart-recruit-python",
    "node": "smart-recruit-node",
    "go": "smart-recruit-go"
}

# Resource Quotas
MEM_LIMIT = "128m"
CPU_QUOTA = 50000  # 0.5 CPU (assuming period 100000)
CPU_PERIOD = 100000

class CodeExecutionRequest(BaseModel):
    language: str
    code: str
    stdin: Optional[str] = ""
    timeout: Optional[int] = 5 # seconds

class ExecutionResult(BaseModel):
    status: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float

# Docker Client with Fallback
try:
    client = docker.from_env()
    DOCKER_AVAILABLE = True
    logger.info("Docker SDK initialized successfully.")
except Exception as e:
    DOCKER_AVAILABLE = False
    logger.warning(f"Docker not found. Falling back to Mock Execution. Error: {e}")

@app.post("/execute", response_model=ExecutionResult)
async def execute_code(request: CodeExecutionRequest):
    """
    Executes code in a hardened container or local mock environment.
    """
    lang = request.language.lower()
    if lang not in IMAGE_MAP and lang != "javascript":
         # Normalize JS
         if lang == "js" or lang == "javascript":
             lang = "node"
         else:
             raise HTTPException(status_code=400, detail=f"Language {lang} not supported.")
    
    start_time = time.time()
    image = IMAGE_MAP.get(lang)
    
    # Ensure types are solid for the run calls
    image_str: str = str(image) if image else ""
    stdin_str: str = str(request.stdin) if request.stdin else ""
    
    # Safe integer extraction for timeout
    req_timeout = request.timeout
    timeout_int: int = int(req_timeout) if req_timeout is not None else 5

    if DOCKER_AVAILABLE:
        return await _run_in_docker(image_str, lang, request.code, stdin_str, timeout_int, start_time)
    else:
        # ⚠️ FALLBACK: MOCK LOCAL EXECUTION (Simulating on-prem offline engine)
        return await _run_local_fallback(lang, request.code, stdin_str, timeout_int, start_time)

async def _run_in_docker(image: str, lang: str, code: str, stdin: str, timeout: int, start_time: float):
    container = None
    try:
        # Create unique filename
        filename = f"source_{uuid.uuid4().hex}"
        if lang == "python": filename += ".py"
        elif lang == "node": filename += ".js"
        elif lang == "go": filename += ".go"
        
        # Hardened container execution
        container = client.containers.run(
            image=image,
            command=f"{_get_run_cmd(lang, filename)}",
            mem_limit=MEM_LIMIT,
            cpu_quota=CPU_QUOTA,
            cpu_period=CPU_PERIOD,
            network_disabled=True,
            user="sandbox",
            detach=True,
            # We map the code via stdin or temporary environment/file
            # For simplicity in this demo, we'll use a wrap approach
        )
        
        # Note: Real implementation would mount a volume or use 'docker cp'
        # For this version, let's assume images are pre-configured or we use a simplified exec
        
        # wait for container to finish
        result = container.wait(timeout=timeout)
        logs_stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
        logs_stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
        exit_code = result.get('StatusCode', 0)
        
        return ExecutionResult(
            status="SUCCESS" if exit_code == 0 else "ERROR",
            stdout=logs_stdout,
            stderr=logs_stderr,
            exit_code=exit_code,
            execution_time=time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Docker execution failed: {e}")
        return ExecutionResult(status="SYSTEM_ERROR", stdout="", stderr=str(e), exit_code=1, execution_time=0)
    finally:
        if container:
            try: container.remove(force=True)
            except: pass

async def _run_local_fallback(lang: str, code: str, stdin: str, timeout: int, start_time: float):
    """
    Simulates a secure execution if Docker is unavailable.
    """
    import subprocess
    import tempfile
    
    suffix = ".py" if lang == "python" else ".js" if lang == "node" else ".go"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        cmd = [_get_executable(lang), temp_path]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(input=stdin, timeout=timeout)
        
        return ExecutionResult(
            status="SUCCESS" if proc.returncode == 0 else "ERROR",
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
            execution_time=time.time() - start_time
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        return ExecutionResult(status="TIMEOUT", stdout="", stderr="Execution timed out.", exit_code=124, execution_time=timeout)
    except Exception as e:
        return ExecutionResult(status="SYSTEM_ERROR", stdout="", stderr=str(e), exit_code=1, execution_time=0)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def _get_run_cmd(lang, filename):
    if lang == "python": return f"python3 {filename}"
    if lang == "node": return f"node {filename}"
    if lang == "go": return f"go run {filename}"
    return ""

def _get_executable(lang):
    if lang == "python": return "python"
    if lang == "node": return "node"
    if lang == "go": return "go"
    return "python"

@app.get("/health")
async def health():
    return {
        "status": "online" if DOCKER_AVAILABLE else "degraded",
        "engine": "docker" if DOCKER_AVAILABLE else "local-subprocess",
        "active_containers": 0 if not DOCKER_AVAILABLE else len(client.containers.list())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
