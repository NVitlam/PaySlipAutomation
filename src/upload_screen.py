"""Screen 1: Upload Screen — file picker + month/year selection."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QFileDialog, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from datetime import datetime

from src.encryptor import HEBREW_MONTHS


class UploadScreen(QWidget):
    """Upload screen with drag-and-drop, month/year selection, and Process button."""

    process_requested = pyqtSignal(str, int, int)  # pdf_path, month, year

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._pdf_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 40, 60, 40)

        # Title
        title = QLabel("העלאת קובץ תלושי שכר")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Drop zone
        self.drop_zone = QFrame()
        self.drop_zone.setFrameShape(QFrame.Shape.Box)
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 3px dashed #aaa;
                border-radius: 12px;
                background-color: #f8f8f8;
                min-height: 180px;
            }
            QFrame:hover {
                border-color: #4a90d9;
                background-color: #eef5ff;
            }
        """)
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_label = QLabel("גרור קובץ PDF לכאן\nאו לחץ לבחירת קובץ")
        self.drop_label.setFont(QFont("Segoe UI", 13))
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("color: #666; border: none;")
        drop_layout.addWidget(self.drop_label)

        self.browse_btn = QPushButton("בחר קובץ PDF")
        self.browse_btn.setFont(QFont("Segoe UI", 11))
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
            }
            QPushButton:hover { background-color: #357abd; }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        drop_layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.drop_zone)

        # File info label
        self.file_label = QLabel("")
        self.file_label.setFont(QFont("Segoe UI", 10))
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #2d7d2d;")
        layout.addWidget(self.file_label)

        # Month / Year selection row
        selection_row = QHBoxLayout()
        selection_row.setSpacing(15)

        # Month dropdown
        month_label = QLabel("חודש:")
        month_label.setFont(QFont("Segoe UI", 12))
        selection_row.addWidget(month_label)

        self.month_combo = QComboBox()
        self.month_combo.setFont(QFont("Segoe UI", 11))
        self.month_combo.setMinimumWidth(120)
        for num, name in HEBREW_MONTHS.items():
            self.month_combo.addItem(name, num)
        # Default to current month
        now = datetime.now()
        self.month_combo.setCurrentIndex(now.month - 1)
        selection_row.addWidget(self.month_combo)

        selection_row.addSpacing(30)

        # Year spinner
        year_label = QLabel("שנה:")
        year_label.setFont(QFont("Segoe UI", 12))
        selection_row.addWidget(year_label)

        self.year_spin = QSpinBox()
        self.year_spin.setFont(QFont("Segoe UI", 11))
        self.year_spin.setRange(2020, 2040)
        self.year_spin.setValue(now.year)
        self.year_spin.setMinimumWidth(90)
        selection_row.addWidget(self.year_spin)

        selection_row.addStretch()
        layout.addLayout(selection_row)

        # Process button
        self.process_btn = QPushButton("עבד את הקובץ →")
        self.process_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.process_btn.setEnabled(False)
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 40px;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:disabled { background-color: #ccc; color: #888; }
        """)
        self.process_btn.clicked.connect(self._on_process)
        layout.addWidget(self.process_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "בחר קובץ PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._pdf_path = path
        filename = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        self.file_label.setText(f"נבחר: {filename}")
        self.process_btn.setEnabled(True)
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 3px solid #27ae60;
                border-radius: 12px;
                background-color: #efffef;
                min-height: 180px;
            }
        """)

    def _on_process(self):
        if self._pdf_path:
            month = self.month_combo.currentData()
            year = self.year_spin.value()
            self.process_requested.emit(self._pdf_path, month, year)

    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".pdf"):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(".pdf"):
                self._set_file(path)

    def reset(self):
        """Reset the screen for a new upload."""
        self._pdf_path = None
        self.file_label.setText("")
        self.process_btn.setEnabled(False)
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 3px dashed #aaa;
                border-radius: 12px;
                background-color: #f8f8f8;
                min-height: 180px;
            }
            QFrame:hover {
                border-color: #4a90d9;
                background-color: #eef5ff;
            }
        """)
