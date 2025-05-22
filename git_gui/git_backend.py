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
        """Return status of repository files using GitPython objects."""
        statuses: List[FileStatus] = []

        # staged changes compared to HEAD
        for diff in self.repo.index.diff('HEAD'):
            path = diff.b_path or diff.a_path
            code = diff.change_type
            status = {
                'A': 'A ',
                'D': 'D ',
                'R': 'R ',
                'M': 'M ',
            }.get(code, 'M ')
            statuses.append(FileStatus(path=path, status=status))

        # unstaged changes in working tree
        staged_paths = {s.path for s in statuses}
        for diff in self.repo.index.diff(None):
            path = diff.b_path or diff.a_path
            code = diff.change_type
            status = {
                'A': ' A',
                'D': ' D',
                'R': ' R',
                'M': ' M',
            }.get(code, ' M')
            if path in staged_paths:
                for s in statuses:
                    if s.path == path:
                        s.status = s.status[0] + status[1]
                        break
            else:
                statuses.append(FileStatus(path=path, status=status))

        # untracked files
        for path in self.repo.untracked_files:
            statuses.append(FileStatus(path=path, status='??'))

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
        self.repo.index.add([gitignore_path])

    def stage(self, files: List[str]) -> None:
        if files:
            self.repo.index.add(files)

    def unstage(self, files: List[str]) -> None:
        if files:
            self.repo.index.reset(files)

    def commit(self, message: str) -> None:
        self.repo.index.commit(message)

    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        remote_obj = self.repo.remotes[remote]
        if branch:
            remote_obj.pull(branch)
        else:
            remote_obj.pull()

    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        remote_obj = self.repo.remotes[remote]
        if branch:
            remote_obj.push(branch)
        else:
            remote_obj.push()

    def log(self, max_count: int = 20) -> str:
        commits = list(self.repo.iter_commits(max_count=max_count))
        return "\n".join(f"{c.hexsha[:7]} {c.summary}" for c in commits)

    def current_branch(self) -> str:
        """Return the name of the current branch."""
        return self.repo.active_branch.name

    def push_review(self, remote: str = 'origin', branch: Optional[str] = None) -> str:
        """Return commits that would be pushed to the remote."""
        if branch is None:
            branch = self.current_branch()
        range_spec = f"{remote}/{branch}..HEAD"
        commits = list(self.repo.iter_commits(range_spec))
        return "\n".join(f"{c.hexsha[:7]} {c.summary}" for c in commits)

    def diff(self, path: str, cached: bool = False) -> str:
        """Return diff for a given file."""
        if cached:
            diffs = self.repo.index.diff('HEAD', paths=[path])
        else:
            diffs = self.repo.index.diff(None, paths=[path])
        return "".join(d.diff.decode('utf-8', errors='replace') for d in diffs)

    def branches(self) -> List[str]:
        """Return a list of branch names."""
        return [head.name for head in self.repo.heads]

    def checkout(self, branch: str) -> None:
        """Switch to the given branch."""
        self.repo.heads[branch].checkout()

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
        self.repo.create_head(name, start_point or "HEAD")

    def rename_branch(self, old: str, new: str) -> None:
        """Rename a branch."""
        self.repo.heads[old].rename(new)

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch by name."""
        self.repo.delete_head(name, force=force)

    def reflog(self) -> str:
        """Return the repository reflog."""
        log_path = os.path.join(self.repo.git_dir, 'logs', 'HEAD')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as fh:
                return fh.read()
        return ''

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
        self.repo.tags[name].checkout()

    # ------------------------------------------------------------------
    # Submodule helpers

    def add_submodule(self, url: str, path: str, name: Optional[str] = None) -> None:
        """Add a submodule to the repository."""
        self.repo.create_submodule(name or path, path, url)

    def update_submodules(self) -> None:
        """Update all submodules."""
        self.repo.submodule_update(init=True, recursive=True)

    def sync_submodules(self) -> None:
        """Sync submodule URLs."""
        for sm in self.repo.submodules:
            sm.update(recursive=True)

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
        rev = f"--grep={pattern}"
        if author:
            rev += f" --author={author}"
        commits = list(self.repo.iter_commits(rev))
        return "\n".join(f"{c.hexsha[:7]} {c.summary}" for c in commits)

    def filter_statuses(self, path_filter: str) -> List[FileStatus]:
        """Filter status entries by path prefix."""
        return [s for s in self.status() if s.path.startswith(path_filter)]
