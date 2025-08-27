# src/services/log_service.py
from datetime import datetime
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter
import re

class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = {
            r"\[INFO\]": QColor("#edf014"),
            r"\[WARNING\]": QColor("#FFA500"),
            r"\[ERROR\]": QColor("#FF0000"),
            r"\[DEBUG\]": QColor("#00BFFF")
        }

    def highlightBlock(self, text: str):
        for pattern, color in self.rules.items():
            for match in re.finditer(pattern, text):
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                self.setFormat(match.start(), match.end() - match.start(), fmt)

class LogService:
    def __init__(self, text_widget):
        self.widget = text_widget
        self.highlighter = LogHighlighter(self.widget.document())

    def append(self, message: str, level: str = "INFO"):
        ts = datetime.now().strftime("[%H:%M:%S]")
        line = f"{ts} [{level.upper()}] {message}\n"
        self.widget.insertPlainText(line)

    def clear(self):
        self.widget.clear()
