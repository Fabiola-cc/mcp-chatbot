import subprocess
import os

WORKSPACE = "workspace"

def run_git_command(command, cwd=WORKSPACE):
    """Ejecuta comando git y devuelve salida"""
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True
    )
    if result.returncode == 0:
        return result.stdout.strip() or f"✅ {' '.join(command)}"
    else:
        return f"❌ Error: {result.stderr.strip()}"

def git_init():
    return run_git_command(["git", "init"])

def git_add():
    return run_git_command(["git", "add", "."])

def git_commit(message: str):
    return run_git_command(["git", "commit", "-m", message])