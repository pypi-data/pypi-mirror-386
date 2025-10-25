from abc import ABC, abstractmethod

class BaseVCSStrategy(ABC):
    def __init__(self, repo, cfg):
        self.repo = repo
        self.cfg = cfg

    @abstractmethod
    def create_merge_request(self, branch_name, base_branch, commit_message):
        pass
