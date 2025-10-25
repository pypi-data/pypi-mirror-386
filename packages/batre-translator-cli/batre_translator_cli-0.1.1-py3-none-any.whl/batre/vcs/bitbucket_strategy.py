from rich import print
from .base_strategy import BaseVCSStrategy

class BitbucketStrategy(BaseVCSStrategy):
    def create_merge_request(self, branch_name, base_branch, commit_message):
        print("[cyan]📬 Creating Pull Request on Bitbucket (not yet implemented)[/cyan]")
