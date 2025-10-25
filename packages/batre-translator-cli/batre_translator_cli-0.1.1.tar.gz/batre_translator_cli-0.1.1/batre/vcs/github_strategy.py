import requests
from rich import print
from datetime import datetime
from .base_strategy import BaseVCSStrategy

class GitHubStrategy(BaseVCSStrategy):
    def create_merge_request(self, branch_name, base_branch, commit_message):
        print("[cyan]📬 Creating Pull Request on GitHub (not yet implemented)[/cyan]")
        # tu będzie POST /repos/{owner}/{repo}/pulls
