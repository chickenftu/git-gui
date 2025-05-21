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
            # keep the two character XY status to allow more detailed checks
            status_code = line[:2]
            file_path = line[3:]
            statuses.append(FileStatus(path=file_path, status=status_code))
        return statuses

    def ignore(self, files: List[str]) -> None:
        """Add files to .gitignore and stage the file."""
        if not files:
            return
        gitignore_path = os.path.join(self.path, '.gitignore')
        existing: List[str] = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as fh:
                existing = [line.strip() for line in fh if line.strip()]
        with open(gitignore_path, 'a', encoding='utf-8') as fh:
            for f in files:
                if f not in existing:
                    fh.write(f + '\n')
        # stage the .gitignore so it does not appear as untracked
        self.repo.git.add(gitignore_path)

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

    def branches(self) -> List[str]:
        """Return a list of branch names."""
        return [head.name for head in self.repo.heads]

    def checkout(self, branch: str) -> None:
        """Switch to the given branch."""
        self.repo.git.checkout(branch)

    # ------------------------------------------------------------------
    # Repository management helpers

    @staticmethod
    def clone(url: str, path: str) -> "Repository":
        """Clone a repository and return a Repository instance."""
        Repo.clone_from(url, path)
        return Repository(path)

    @staticmethod
    def init(path: str) -> "Repository":
        """Initialize a new repository at *path* and return it."""
        Repo.init(path)
        return Repository(path)

    def add_remote(self, name: str, url: str) -> None:
        """Add a remote if it does not already exist."""
        if name not in [r.name for r in self.repo.remotes]:
            self.repo.create_remote(name, url)

    def configure_user(self, name: str, email: str) -> None:
        """Set the repository user name and email."""
        with self.repo.config_writer() as cw:
            cw.set_value("user", "name", name)
            cw.set_value("user", "email", email)

    # ------------------------------------------------------------------
    # Branching helpers

    def create_branch(self, name: str, start_point: Optional[str] = None) -> None:
        """Create a branch from *start_point* (default HEAD)."""
        self.repo.git.branch(name, start_point or "HEAD")

    def rename_branch(self, old: str, new: str) -> None:
        """Rename a branch."""
        self.repo.git.branch("-m", old, new)

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch by name."""
        args = ["-D" if force else "-d", name]
        self.repo.git.branch(*args)

    def reflog(self) -> str:
        """Return the repository reflog."""
        return self.repo.git.reflog()

    # ------------------------------------------------------------------
    # Tag helpers

    def create_tag(self, name: str, message: Optional[str] = None) -> None:
        """Create a lightweight or annotated tag."""
        if message:
            self.repo.create_tag(name, message=message)
        else:
            self.repo.create_tag(name)

    def delete_tag(self, name: str) -> None:
        """Delete a tag."""
        self.repo.delete_tag(name)

    def checkout_tag(self, name: str) -> None:
        """Checkout a tag."""
        self.repo.git.checkout(name)

    # ------------------------------------------------------------------
    # Submodule helpers

    def add_submodule(self, url: str, path: str, name: Optional[str] = None) -> None:
        """Add a submodule to the repository."""
        self.repo.create_submodule(name or path, path, url)

    def update_submodules(self) -> None:
        """Update all submodules."""
        self.repo.git.submodule("update", "--init", "--recursive")

    def sync_submodules(self) -> None:
        """Sync submodule URLs."""
        self.repo.git.submodule("sync", "--recursive")

    def remove_submodule(self, path: str) -> None:
        """Remove a submodule from the repository."""
        self.repo.git.submodule("deinit", "-f", "--", path)
        module_path = os.path.join(self.path, path)
        if os.path.exists(module_path):
            self.repo.git.rm("-f", path)
            self.repo.git.clean("-fd", module_path)

    # ------------------------------------------------------------------
    # Search helpers

    def search_commits(self, pattern: str, author: Optional[str] = None) -> str:
        """Search commits by message pattern and optionally by author."""
        args = ["--grep", pattern]
        if author:
            args += ["--author", author]
        return self.repo.git.log("--oneline", *args)

    def filter_statuses(self, path_filter: str) -> List[FileStatus]:
        """Filter status entries by path prefix."""
        return [s for s in self.status() if s.path.startswith(path_filter)]
