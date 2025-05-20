from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QRegularExpression


class DiffHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for git diff output."""

    def __init__(self, parent):
        super().__init__(parent)
        self.add_format = QTextCharFormat()
        self.add_format.setForeground(QColor('darkgreen'))
        self.remove_format = QTextCharFormat()
        self.remove_format.setForeground(QColor('red'))
        self.header_format = QTextCharFormat()
        self.header_format.setForeground(QColor('blue'))

    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
        if text.startswith('+') and not text.startswith('+++'):
            self.setFormat(0, len(text), self.add_format)
        elif text.startswith('-') and not text.startswith('---'):
            self.setFormat(0, len(text), self.remove_format)
        elif text.startswith('@@') or text.startswith('diff') or text.startswith('index'):
            self.setFormat(0, len(text), self.header_format)
