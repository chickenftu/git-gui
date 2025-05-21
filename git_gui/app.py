from __future__ import annotations

import os
from typing import List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListView,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QToolBar,
    QWidget,
    QVBoxLayout,
)

from .git_backend import Repository, FileStatus
from .models import FileStatusModel
from .diff_highlighter import DiffHighlighter
from .diff_viewer import DiffViewer

class GitGuiApp(QMainWindow):
    def __init__(self, repo_path: str) -> None:
        super().__init__()
        self.setWindowTitle("Git GUI")
        self.resize(800, 600)

        self.repo = Repository(repo_path)

        self.status_model = FileStatusModel()
        self.status_view = QListView()
        self.status_view.setModel(self.status_model)
        self.status_view.doubleClicked.connect(self._show_diff_index)
        self.status_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.status_view.customContextMenuRequested.connect(self._show_status_menu)
        self.commit_msg = QTextEdit()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self._diff_highlighter = DiffHighlighter(self.log_view.document())
        self.branch_box = QComboBox()
        self.branch_box.activated[str].connect(self._checkout_branch)
        self._diff_viewer = DiffViewer(self)

        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.branch_box)
        layout.addWidget(self.status_view)
        layout.addWidget(QLabel("Commit message:"))
        layout.addWidget(self.commit_msg)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_view)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._create_menu()
        self._create_toolbar()
        self.refresh()

    def _create_menu(self) -> None:
        menu_bar = QMenuBar()
        file_menu = QMenu("File", self)
        open_action = file_menu.addAction("Open Repository")
        open_action.triggered.connect(self.open_repo)
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        menu_bar.addMenu(file_menu)

        git_menu = QMenu("Git", self)
        commit_action = git_menu.addAction("Commit")
        commit_action.triggered.connect(self.commit)
        pull_action = git_menu.addAction("Pull")
        pull_action.triggered.connect(self.pull)
        push_action = git_menu.addAction("Push")
        push_action.triggered.connect(self.push)
        review_action = git_menu.addAction("Push Review")
        review_action.triggered.connect(self.push_review)
        menu_bar.addMenu(git_menu)

        self.setMenuBar(menu_bar)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        refresh_action = toolbar.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh)
        pull_action = toolbar.addAction("Pull")
        pull_action.triggered.connect(self.pull)
        push_action = toolbar.addAction("Push")
        push_action.triggered.connect(self.push)

    def open_repo(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Repository", os.getcwd())
        if path:
            try:
                self.repo = Repository(path)
                self.refresh()
            except ValueError as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def refresh(self) -> None:
        statuses = self.repo.status()
        self.status_model.update_statuses(statuses)
        self.log_view.setPlainText(self.repo.log())
        self._populate_branches()

    def _current_branch(self) -> str:
        return self.repo.current_branch()

    def _populate_branches(self) -> None:
        branches = self.repo.branches()
        current = self._current_branch()
        self.branch_box.blockSignals(True)
        self.branch_box.clear()
        self.branch_box.addItems(branches)
        if current in branches:
            self.branch_box.setCurrentText(current)
        self.branch_box.blockSignals(False)

    def _checkout_branch(self, branch: str) -> None:
        if branch:
            self.repo.checkout(branch)
            self.refresh()

    def _show_diff_index(self, index) -> None:
        status = self.status_model.status_at(index)
        if status:
            self._display_diff(status.path)

    def _display_diff(self, path: str) -> None:
        diff = self.repo.diff(path)
        if not diff.strip():
            diff = 'No changes'
        self._diff_viewer.set_diff(diff)
        self._diff_viewer.show()

    def _show_status_menu(self, pos) -> None:
        index = self.status_view.indexAt(pos)
        item = None
        if index.isValid():
            item = self.status_model.status_at(index)
        if item is None:
            return
        status = item
        menu = QMenu(self)

        index_state = status.status[0] if len(status.status) > 0 else ' '
        work_state = status.status[1] if len(status.status) > 1 else ' '

        stage_action = None
        unstage_action = None
        add_action = None
        ignore_action = None

        if status.status == '??':
            add_action = menu.addAction("Add File to Repo")
            ignore_action = menu.addAction("Ignore File")
        else:
            if work_state != ' ':
                stage_action = menu.addAction("Stage File")
            if index_state != ' ':
                unstage_action = menu.addAction("Unstage File")

        diff_action = menu.addAction("Show Diff")
        action = menu.exec(self.status_view.mapToGlobal(pos))

        if action == stage_action:
            self.repo.stage([status.path])
            self.refresh()
        elif action == unstage_action:
            self.repo.unstage([status.path])
            self.refresh()
        elif action == add_action:
            self.repo.stage([status.path])
            self.refresh()
        elif action == ignore_action:
            self.repo.ignore([status.path])
            self.refresh()
        elif action == diff_action:
            self._display_diff(status.path)

    def commit(self) -> None:
        message = self.commit_msg.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Warning", "Commit message is empty")
            return
        paths = [s.path for s in self.status_model.statuses]
        self.repo.stage(paths)
        self.repo.commit(message)
        self.commit_msg.clear()
        self.refresh()

    def pull(self) -> None:
        self.repo.pull()
        self.refresh()

    def push(self) -> None:
        self.repo.push()
        self.refresh()

    def push_review(self) -> None:
        review = self.repo.push_review()
        if not review.strip():
            review = 'No commits to push'
        QMessageBox.information(self, 'Push Review', review)


def run(repo_path: str) -> None:
    app = QApplication([])
    window = GitGuiApp(repo_path)
    window.show()
    app.exec()
