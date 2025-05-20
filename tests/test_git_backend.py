import subprocess
import tempfile
import unittest
from pathlib import Path

from git_gui.git_backend import Repository

class TestRepository(unittest.TestCase):
    def create_repo(self, directory: Path) -> Path:
        subprocess.run(['git', 'init'], cwd=directory, check=True)
        (directory / 'file.txt').write_text('hello')
        subprocess.run(['git', 'add', 'file.txt'], cwd=directory, check=True)
        subprocess.run(['git', 'commit', '-m', 'init'], cwd=directory, check=True)
        return directory

    def test_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            self.create_repo(repo_path)
            (repo_path / 'new.txt').write_text('new')
            repo = Repository(str(repo_path))
            statuses = repo.status()
            self.assertTrue(any(s.path == 'new.txt' and s.status == '??' for s in statuses))

    def test_push_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / 'local'
            remote_path = Path(tmpdir) / 'remote'
            repo_path.mkdir()
            remote_path.mkdir()
            subprocess.run(['git', 'init', '--bare'], cwd=remote_path, check=True)
            self.create_repo(repo_path)
            subprocess.run(['git', 'remote', 'add', 'origin', str(remote_path)], cwd=repo_path, check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'master'], cwd=repo_path, check=True)
            (repo_path / 'new.txt').write_text('change')
            subprocess.run(['git', 'add', 'new.txt'], cwd=repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'new commit'], cwd=repo_path, check=True)
            repo = Repository(str(repo_path))
            review = repo.push_review(remote='origin', branch='master')
            self.assertIn('new commit', review)

if __name__ == '__main__':
    unittest.main()
