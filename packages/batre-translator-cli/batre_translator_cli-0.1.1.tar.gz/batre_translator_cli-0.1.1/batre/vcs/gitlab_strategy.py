import requests
from rich import print
from datetime import datetime

from .base_strategy import BaseVCSStrategy

class GitLabStrategy(BaseVCSStrategy):
    def create_merge_request(self, branch_name, base_branch, commit_message):
        repo_url = self.cfg.get("repo_url")
        token = self.cfg.get("gitlab_token")

        if not token or not repo_url:
            print("[yellow]⚠️ Missing GitLab credentials – skipping MR creation.[/yellow]")
            return

        group_repo = repo_url.replace("git@gitlab.com:", "").replace(".git", "")
        api_url = f"https://gitlab.com/api/v4/projects/{group_repo.replace('/', '%2F')}/merge_requests"

        headers = {"PRIVATE-TOKEN": token}
        payload = {
            "source_branch": branch_name,
            "target_branch": base_branch,
            "title": f"[Batre Translator] Update translations {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": commit_message,
            "remove_source_branch": True,
            "labels": ["batre-translator", "auto-export"],
        }

        try:
            r = requests.post(api_url, headers=headers, data=payload)
            if r.status_code == 201:
                mr_url = r.json().get("web_url")
                print(f"[green]✅ Merge Request created successfully![/green]")
                print(f"🔗 {mr_url}")
            else:
                print(f"[yellow]⚠️ Failed to create MR ({r.status_code}): {r.text}[/yellow]")
        except Exception as e:
            print(f"[red]❌ GitLab API error: {e}[/red]")
