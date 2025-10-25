#!/usr/bin/env python3
import os, json, base64, yaml, requests
from datetime import datetime
from git import Repo
from rich import print


def write_locale_files(export_path, language, payload):
    """Recreate locale folder structure for a given language (2-level depth only)."""
    lang_path = os.path.join(export_path, language)
    os.makedirs(lang_path, exist_ok=True)

    for top_key, top_val in payload.items():
        folder_path = os.path.join(lang_path, top_key)
        os.makedirs(folder_path, exist_ok=True)

        if not isinstance(top_val, dict):
            continue

        for file_key, file_val in top_val.items():
            if not isinstance(file_val, dict):
                continue

            file_path = os.path.join(folder_path, f"{file_key}.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("const messages = ")
                json.dump(file_val, f, indent=2, ensure_ascii=False)
                f.write(";\nexport default { messages };")

            print(f"[green]✅ Wrote {language}/{top_key}/{file_key}.js[/green]")


def main():
    cfg_path = ".batre.yml"
    if not os.path.exists(cfg_path):
        print("[red]❌ Config file .batre.yml not found[/red]")
        return

    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    project_id = cfg["project_id"]
    repo_path = cfg.get("repo_path", ".")
    base_path = os.path.join(repo_path, cfg["base_path"])
    export_path = os.path.join(repo_path, cfg.get("export_path", "src/locales/dist"))

    print(f"[cyan]⬇️  Reading mock export_all.json for {project_id}...[/cyan]")
    with open("mock/export_all.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    translations = data.get("translations", {})
    if not translations:
        print("[yellow]⚠️ No translations found.[/yellow]")
        return

    os.makedirs(export_path, exist_ok=True)

    for lang, lang_data in translations.items():
        print(f"[cyan]📦 Processing {lang}...[/cyan]")
        decoded_raw = base64.b64decode(lang_data["payload_base64"]).decode("utf-8").strip()

        if decoded_raw.startswith("\ufeff"):
            decoded_raw = decoded_raw.encode().decode("utf-8-sig")

        try:
            decoded = json.loads(decoded_raw)
        except json.JSONDecodeError as e:
            print(f"[red]❌ JSON parse error in {lang}: {e}[/red]")
            with open("mock/debug_failed.json", "w", encoding="utf-8") as dbg:
                dbg.write(decoded_raw)
            print("[cyan]💾 Raw content saved to mock/debug_failed.json for inspection.[/cyan]")
            return

        write_locale_files(export_path, lang, decoded)

    print(f"[bold green]✅ Folder reconstruction complete in:[/bold green] {export_path}")

    # --------------------------------
    # 🌿 GIT INTEGRATION + MERGE REQUEST
    # --------------------------------
    branch_name = f"batre/export/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    base_branch = cfg.get("branch", "develop")
    gitlab_token = cfg.get("gitlab_token")
    repo_url = cfg.get("repo_url")

    repo = Repo(repo_path)
    repo.git.fetch()
    repo.git.checkout(base_branch)
    repo.git.pull()

    print(f"[cyan]🌿 Creating or switching to branch: {branch_name} (base: {base_branch})[/cyan]")
    try:
        existing_branches = [h.name for h in repo.heads]
        if branch_name in existing_branches:
            print(f"[yellow]⚠️ Branch {branch_name} already exists — switching to it.[/yellow]")
            repo.git.checkout(branch_name)
        else:
            repo.git.checkout("-b", branch_name)
    except Exception as e:
        print(f"[red]❌ Failed to create or switch branch: {e}[/red]")
        return

    # ✅ Git add (no sparse logic)
    try:
        rel_path = os.path.relpath(export_path, repo_path)
        os.makedirs(export_path, exist_ok=True)
        repo.git.add(rel_path)
        print(f"[green]✅ Added folder {rel_path} to index successfully.[/green]")
    except Exception as e:
        print(f"[red]❌ Git add failed: {e}[/red]")
        return

    commit_message = f"[Batre Translator] Exported translations {datetime.now().isoformat(timespec='minutes')}"
    commit_author = cfg.get("commit_author", "Batre Translator <bot@batre.io>")

    try:
        repo.git.commit("--author", commit_author, "-m", commit_message)
        print("[green]✅ Commit created successfully.[/green]")
    except Exception as e:
        print(f"[yellow]⚠️ Nothing to commit or commit failed: {e}[/yellow]")

    print("[cyan]🚀 Pushing branch to remote...[/cyan]")
    try:
        repo.git.push("--set-upstream", "origin", branch_name)
        print(f"[green]✅ Branch pushed successfully: {branch_name}[/green]")
    except Exception as e:
        print(f"[red]❌ Failed to push branch: {e}[/red]")
        return

    if not gitlab_token or not repo_url:
        print("[yellow]⚠️ Missing gitlab_token or repo_url — skipping MR creation.[/yellow]")
        return

    # --- choose correct VCS strategy ---
    vcs_provider = cfg.get("vcs") or "auto"
    repo_url = cfg.get("repo_url", "")

    if vcs_provider == "auto":
        if "gitlab.com" in repo_url:
            vcs_provider = "gitlab"
        elif "github.com" in repo_url:
            vcs_provider = "github"
        elif "bitbucket.org" in repo_url:
            vcs_provider = "bitbucket"

    print(f"[cyan]🧩 Using VCS strategy: {vcs_provider}[/cyan]")

    try:
        if vcs_provider == "gitlab":
            from batre.vcs.gitlab_strategy import GitLabStrategy
            strategy = GitLabStrategy(repo, cfg)
        elif vcs_provider == "github":
            from batre.vcs.github_strategy import GitHubStrategy
            strategy = GitHubStrategy(repo, cfg)
        elif vcs_provider == "bitbucket":
            from batre.vcs.bitbucket_strategy import BitbucketStrategy
            strategy = BitbucketStrategy(repo, cfg)
        else:
            print(f"[yellow]⚠️ Unknown VCS provider '{vcs_provider}', skipping MR creation.[/yellow]")
            return

        strategy.create_merge_request(branch_name, base_branch, commit_message)
    except Exception as e:
        print(f"[red]❌ Failed to create Merge Request: {e}[/red]")


if __name__ == "__main__":
    main()
