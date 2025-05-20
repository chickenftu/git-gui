import os
from dataclasses import dataclass
from typing import List, Optional

from git import Repo, GitCommandError


@dataclass
class FileStatus:
    path: str
    status: str

class Repository:
    """Wrapper around git operations using GitPython."""

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        try:
            self.repo = Repo(self.path)
        except GitCommandError as exc:
            raise ValueError(f"{path} is not a git repository") from exc
        if self.repo.bare:
            raise ValueError(f"{path} is not a git repository")

    def status(self) -> List[FileStatus]:
        """Return status of repository files."""
        output = self.repo.git.status('--porcelain')
        lines = output.splitlines()
        statuses: List[FileStatus] = []
        for line in lines:
            status_code = line[:2].strip()
            file_path = line[3:]
            statuses.append(FileStatus(path=file_path, status=status_code))
        return statuses

    def stage(self, files: List[str]) -> None:
        if files:
            self.repo.git.add('--', *files)

    def unstage(self, files: List[str]) -> None:
        if files:
            self.repo.git.reset('HEAD', '--', *files)

    def commit(self, message: str) -> None:
        self.repo.git.commit('-m', message)

    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        if branch:
            self.repo.git.pull(remote, branch)
        else:
            self.repo.git.pull(remote)

    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        if branch:
            self.repo.git.push(remote, branch)
        else:
            self.repo.git.push(remote)

    def log(self, max_count: int = 20) -> str:
        output = self.repo.git.log(f'--max-count={max_count}', '--oneline')
        return output

    def current_branch(self) -> str:
        """Return the name of the current branch."""
        return self.repo.active_branch.name

    def push_review(self, remote: str = 'origin', branch: Optional[str] = None) -> str:
        """Return commits that would be pushed to the remote."""
        if branch is None:
            branch = self.current_branch()
        range_spec = f'{remote}/{branch}..HEAD'
        output = self.repo.git.log('--oneline', range_spec)
        return output

    def diff(self, path: str, cached: bool = False) -> str:
        """Return diff for a given file."""
        if cached:
            return self.repo.git.diff('--cached', '--', path)
        return self.repo.git.diff('--', path)
