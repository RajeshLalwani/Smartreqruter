import docker
import os
import time
import logging

logger = logging.getLogger(__name__)

class DockerSandbox:
    IMAGE_NAME = "smartrecruit-worker:latest"
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None

    def run_code(self, code, language="python"):
        """
        Runs code in a temporary Docker container with strict constraints.
        """
        if not self.client:
            return {"error": "Docker client not initialized"}

        # 1. Prepare Execution Command
        if language in ["python", "python3"]:
            command = ["python3", "-c", code]
        elif language in ["javascript", "js", "node"]:
            # Note: worker image would need node installed for this
            command = ["node", "-e", code]
        else:
            return {"error": f"Language {language} not supported in local sandbox"}

        try:
            # 2. Launch Container
            # remove=True ensures cleanup
            # network_disabled=True prevents external calls
            # mem_limit='128m', cpu_period=50000, cpu_quota=25000 (0.5 cores)
            container = self.client.containers.run(
                image=self.IMAGE_NAME,
                command=command,
                network_disabled=True,
                mem_limit='128m',
                nano_cpus=500000000, # 0.5 CPU
                detach=False,
                remove=True,
                stdout=True,
                stderr=True,
                user="sandboxuser"
            )
            
            # 3. Capture Result
            return {
                "stdout": container.decode('utf-8'),
                "stderr": "",
                "status": "ACCEPTED"
            }

        except docker.errors.ContainerError as ce:
            return {
                "stdout": "",
                "stderr": ce.stderr.decode('utf-8'),
                "status": "RUNTIME_ERROR"
            }
        except Exception as e:
            logger.error(f"Sandbox Error: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "status": "ERROR"
            }

def run_code_in_sandbox(code, language):
    sandbox = DockerSandbox()
    return sandbox.run_code(code, language)

def get_system_load():
    """Returns basic host and container stats for the monitor."""
    try:
        client = docker.from_env()
        active_containers = len(client.containers.list())
        # Mocking host CPU for now, usually requires psutil
        import psutil
        cpu_usage = psutil.cpu_percent()
        return {
            "active_containers": active_containers,
            "cpu_usage": cpu_usage,
            "status": "NOMINAL" if cpu_usage < 80 else "HEAVY"
        }
    except:
        return {"active_containers": 0, "cpu_usage": 0, "status": "OFFLINE"}
