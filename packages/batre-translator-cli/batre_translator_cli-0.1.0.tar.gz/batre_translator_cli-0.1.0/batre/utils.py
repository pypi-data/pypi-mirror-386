import os
import subprocess
import yaml
from rich import print


def run(cmd, cwd=None):
    """Pomocnicze uruchomienie komendy z logowaniem."""
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    cmd_str = " ".join(cmd)

    if result.returncode != 0:
        print(f"[red]❌ Command failed:[/red] {cmd_str}")
        print(result.stderr.strip())
    else:
        # tylko krótkie logi dla fetch/pull, nie spamuj wszystkiego
        if result.stdout.strip():
            print(result.stdout.strip())

    return result.returncode == 0

def update_repo(repo_path):
    """Zaktualizuj lub sklonuj tylko wskazany folder z repo (sparse checkout)."""
    config_path = ".batre.yml"
    if not os.path.exists(config_path):
        print("[red]❌ Config file .batre.yml not found[/red]")
        return

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    repo_url = cfg.get("repo_url")
    branch = cfg.get("branch", "main")
    sparse_path = cfg.get("base_path", None)  # np. src/locales/en-GB
    if not repo_url or not sparse_path:
        print("[red]❌ repo_url or base_path missing in .batre.yml[/red]")
        return

    repo_path = os.path.abspath(repo_path)

    if not os.path.exists(repo_path):
        print(f"[cyan]📦 Sparse cloning {sparse_path} from {repo_url} (branch: {branch})...[/cyan]")
        os.makedirs(repo_path, exist_ok=True)

        # Sparse clone = tylko wybrany katalog i ostatni commit
        run(["git", "init"], cwd=repo_path)
        run(["git", "remote", "add", "origin", repo_url], cwd=repo_path)
        run(["git", "config", "core.sparseCheckout", "true"], cwd=repo_path)
        run(["git", "sparse-checkout", "set", sparse_path], cwd=repo_path)
        run(["git", "pull", "--depth", "1", "origin", branch], cwd=repo_path)
    else:
        print(f"[cyan]🔄 Updating sparse repo at {repo_path} (branch: {branch})...[/cyan]")
        run(["git", "fetch", "--depth", "1", "origin", branch], cwd=repo_path)
        run(["git", "checkout", branch], cwd=repo_path)
        run(["git", "pull", "--depth", "1", "--rebase", "origin", branch], cwd=repo_path)

    print(f"[green]✅ Sparse repository ready: only '{sparse_path}' downloaded[/green]")

