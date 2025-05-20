from __future__ import annotations

import os
from typing import List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QTextEdit,
    QToolBar,
    QWidget,
    QVBoxLayout,
    QLabel,
)

from .git_backend import Repository, FileStatus
from .diff_highlighter import DiffHighlighter
from .diff_viewer import DiffViewer

class GitGuiApp(QMainWindow):
    def __init__(self, repo_path: str) -> None:
        super().__init__()
        self.setWindowTitle("Git GUI")
        self.resize(800, 600)

        self.repo = Repository(repo_path)

        self.status_list = QListWidget()
        self.status_list.itemDoubleClicked.connect(self._show_diff)
        self.status_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.status_list.customContextMenuRequested.connect(self._show_status_menu)
        self.commit_msg = QTextEdit()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self._diff_highlighter = DiffHighlighter(self.log_view.document())
        self.branch_label = QLabel()
        self._diff_viewer = DiffViewer(self)

        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.branch_label)
        layout.addWidget(self.status_list)
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
        self.status_list.clear()
        for status in self.repo.status():
            item = QListWidgetItem(f"{status.status}\t{status.path}")
            # store the FileStatus object so we can inspect its state later
            item.setData(Qt.ItemDataRole.UserRole, status)
            self.status_list.addItem(item)
        self.log_view.setPlainText(self.repo.log())
        branch = self._current_branch()
        self.branch_label.setText(f"Branch: {branch}")

    def _current_branch(self) -> str:
        return self.repo.current_branch()

    def _show_diff(self, item: QListWidgetItem) -> None:
        status: FileStatus = item.data(Qt.ItemDataRole.UserRole)
        self._display_diff(status.path)

    def _display_diff(self, path: str) -> None:
        diff = self.repo.diff(path)
        if not diff.strip():
            diff = 'No changes'
        self._diff_viewer.set_diff(diff)
        self._diff_viewer.show()

    def _show_status_menu(self, pos) -> None:
        item = self.status_list.itemAt(pos)
        if item is None:
            return
        status: FileStatus = item.data(Qt.ItemDataRole.UserRole)
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
        action = menu.exec(self.status_list.mapToGlobal(pos))

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
        paths = [self.status_list.item(i).data(Qt.ItemDataRole.UserRole).path for i in range(self.status_list.count())]
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
