import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FileStatus:
    path: str
    status: str

def _run_git(cmd: List[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run([
        'git',
        *cmd
    ], cwd=cwd, check=False, capture_output=True, text=True)

class Repository:
    """Simple wrapper around git CLI commands."""

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        if not os.path.isdir(os.path.join(self.path, '.git')):
            raise ValueError(f"{path} is not a git repository")

    def status(self) -> List[FileStatus]:
        """Return status of repository files."""
        result = _run_git(['status', '--porcelain'], self.path)
        lines = result.stdout.splitlines()
        statuses = []
        for line in lines:
            status_code = line[:2].strip()
            file_path = line[3:]
            statuses.append(FileStatus(path=file_path, status=status_code))
        return statuses

    def stage(self, files: List[str]) -> None:
        if files:
            _run_git(['add', '--'] + files, self.path)

    def unstage(self, files: List[str]) -> None:
        if files:
            _run_git(['reset', 'HEAD', '--'] + files, self.path)

    def commit(self, message: str) -> None:
        _run_git(['commit', '-m', message], self.path)

    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        cmd = ['pull', remote]
        if branch:
            cmd.append(branch)
        _run_git(cmd, self.path)

    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        cmd = ['push', remote]
        if branch:
            cmd.append(branch)
        _run_git(cmd, self.path)

    def log(self, max_count: int = 20) -> str:
        result = _run_git(['log', f'--max-count={max_count}', '--oneline'], self.path)
        return result.stdout

    def current_branch(self) -> str:
        """Return the name of the current branch."""
        result = _run_git(['rev-parse', '--abbrev-ref', 'HEAD'], self.path)
        return result.stdout.strip()

    def push_review(self, remote: str = 'origin', branch: Optional[str] = None) -> str:
        """Return commits that would be pushed to the remote."""
        if branch is None:
            branch = self.current_branch()
        range_spec = f'{remote}/{branch}..HEAD'
        result = _run_git(['log', '--oneline', range_spec], self.path)
        return result.stdout
