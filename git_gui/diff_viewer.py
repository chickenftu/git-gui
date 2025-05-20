from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser


class DiffViewer(QDialog):
    """Simple dialog that displays a diff using HTML styling."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diff View")
        self.resize(700, 500)
        self.browser = QTextBrowser()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def set_diff(self, diff: str) -> None:
        lines = []
        for line in diff.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                color = 'darkgreen'
            elif line.startswith('-') and not line.startswith('---'):
                color = 'red'
            elif line.startswith('@@') or line.startswith('diff') or line.startswith('index'):
                color = 'blue'
            else:
                color = 'black'
            lines.append(f'<pre style="color: {color}; margin:0;">{line}</pre>')
        html = '<html><body style="font-family: monospace;">' + ''.join(lines) + '</body></html>'
        self.browser.setHtml(html)
