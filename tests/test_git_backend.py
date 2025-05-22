import tempfile
import unittest
from pathlib import Path

from git import Repo
from git_gui.git_backend import Repository

class TestRepository(unittest.TestCase):
    def create_repo(self, directory: Path) -> Path:
        repo = Repository.init(str(directory))
        (directory / 'file.txt').write_text('hello')
        repo.stage(['file.txt'])
        repo.commit('init')
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
            Repo.init(remote_path, bare=True)
            self.create_repo(repo_path)
            local_repo = Repo(repo_path)
            local_repo.create_remote('origin', str(remote_path))
            local_repo.remotes.origin.push('master:master')
            (repo_path / 'new.txt').write_text('change')
            local_repo.index.add(['new.txt'])
            local_repo.index.commit('new commit')
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
