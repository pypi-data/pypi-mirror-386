import os
import subprocess
import yaml
from rich import print


def run(cmd, cwd=None):
    """Helper to run shell command with pretty logging."""
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    cmd_str = " ".join(cmd)

    if result.returncode != 0:
        print(f"[red]❌ Command failed:[/red] {cmd_str}")
        print(result.stderr.strip())
    else:
        if result.stdout.strip():
            print(result.stdout.strip())

    return result.returncode == 0


def update_repo(repo_path):
    """Clone or update the full repository (no sparse-checkout)."""
    config_path = ".batre.yml"
    if not os.path.exists(config_path):
        print("[red]❌ Config file .batre.yml not found[/red]")
        return

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    repo_url = cfg.get("repo_url")
    branch = cfg.get("branch", "develop")

    if not repo_url:
        print("[red]❌ repo_url missing in .batre.yml[/red]")
        return

    repo_path = os.path.abspath(repo_path)
    repo_exists = os.path.exists(os.path.join(repo_path, ".git"))

    # --- Full clone if not exists ---
    if not repo_exists:
        print(f"[cyan]📦 Cloning full repository from {repo_url} (branch: {branch})...[/cyan]")
        os.makedirs(repo_path, exist_ok=True)
        ok = run(["git", "clone", "--branch", branch, repo_url, repo_path])
        if not ok:
            print("[red]❌ Clone failed![/red]")
            return
        print("[green]✅ Repository cloned successfully (full checkout).[/green]")
        return

    # --- If exists, pull full repo ---
    print(f"[cyan]🔄 Updating full repository at {repo_path} (branch: {branch})...[/cyan]")

    # Disable sparse-checkout if previously enabled
    run(["git", "sparse-checkout", "disable"], cwd=repo_path)

    # Clean and pull everything
    run(["git", "fetch", "--all", "--prune"], cwd=repo_path)
    run(["git", "reset", "--hard", f"origin/{branch}"], cwd=repo_path)
    run(["git", "clean", "-fdx"], cwd=repo_path)
    run(["git", "checkout", branch], cwd=repo_path)

    print(f"[green]✅ Full repository updated successfully (no sparse-checkout).[/green]")
