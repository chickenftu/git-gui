from __future__ import annotations

from typing import List
from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant

from .git_backend import FileStatus

class FileStatusModel(QAbstractListModel):
    """Model to expose repository file status entries."""

    def __init__(self, statuses: List[FileStatus] | None = None) -> None:
        super().__init__()
        self._statuses: List[FileStatus] = statuses or []

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._statuses)):
            return QVariant()
        status = self._statuses[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{status.status}\t{status.path}"
        if role == Qt.ItemDataRole.UserRole:
            return status
        return QVariant()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self._statuses)

    def update_statuses(self, statuses: List[FileStatus]) -> None:
        self.beginResetModel()
        self._statuses = list(statuses)
        self.endResetModel()

    @property
    def statuses(self) -> List[FileStatus]:
        return list(self._statuses)

    def status_at(self, index: QModelIndex) -> FileStatus | None:
        if not index.isValid() or not (0 <= index.row() < len(self._statuses)):
            return None
        return self._statuses[index.row()]
