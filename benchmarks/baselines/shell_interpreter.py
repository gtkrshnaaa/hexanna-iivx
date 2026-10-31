import subprocess
from typing import Dict, Any

class ShellInterpreterBaseline:
    """Simulates an unconstrained shell-based autonomous agent executing bash pipes."""

    def execute_bash_command(self, cmd: str) -> Dict[str, Any]:
        process = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return {
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
