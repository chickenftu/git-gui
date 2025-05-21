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

    def test_diff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            self.create_repo(repo_path)
            file_path = repo_path / 'file.txt'
            file_path.write_text('hello world')
            repo = Repository(str(repo_path))
            diff = repo.diff('file.txt')
            self.assertIn('-hello', diff)
            self.assertIn('+hello world', diff)

    def test_ignore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            self.create_repo(repo_path)
            (repo_path / 'temp.log').write_text('temp')
            repo = Repository(str(repo_path))
            repo.ignore(['temp.log'])
            gitignore = (repo_path / '.gitignore').read_text()
            self.assertIn('temp.log', gitignore)
            statuses = repo.status()
            self.assertFalse(any(s.path == 'temp.log' for s in statuses))

    def test_branch_and_tag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            self.create_repo(repo_path)
            repo = Repository(str(repo_path))
            repo.create_branch('feature')
            repo.checkout('feature')
            (repo_path / 'feature.txt').write_text('data')
            repo.stage(['feature.txt'])
            repo.commit('add feature')
            repo.create_tag('v1.0')
            repo.checkout('master')
            branches = repo.branches()
            self.assertIn('feature', branches)
            repo.delete_branch('feature', force=True)
            self.assertNotIn('feature', repo.branches())
            repo.delete_tag('v1.0')

    def test_search_commits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            self.create_repo(repo_path)
            repo = Repository(str(repo_path))
            (repo_path / 'new.txt').write_text('change')
            repo.stage(['new.txt'])
            repo.commit('search target')
            result = repo.search_commits('search target')
            self.assertIn('search target', result)

if __name__ == '__main__':
    unittest.main()
