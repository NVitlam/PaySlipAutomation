"""Screen 3: Send Panel — email sending with status tracking."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QCheckBox, QAbstractItemView, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from src.employee_db import Employee
from src.encryptor import HEBREW_MONTHS


class SendWorker(QThread):
    """Background thread for sending emails."""
    progress = pyqtSignal(int, bool, str)  # row_index, success, error_msg
    finished_all = pyqtSignal()

    def __init__(self, service, send_list, subject_template, body_template, month, year):
        super().__init__()
        self.service = service
        self.send_list = send_list  # list of (row_idx, employee, filename, encrypted_bytes)
        self.subject_template = subject_template
        self.body_template = body_template
        self.month = month
        self.year = year

    def run(self):
        from src.gmail_sender import send_payslip, render_template

        month_str = HEBREW_MONTHS[self.month]
        year_str = str(self.year)

        for row_idx, emp, filename, enc_bytes in self.send_list:
            try:
                subject = render_template(
                    self.subject_template, emp.name, month_str, year_str, emp.id
                )
                body = render_template(
                    self.body_template, emp.name, month_str, year_str, emp.id
                )
                success = send_payslip(
                    self.service, emp.email, subject, body, enc_bytes, filename
                )
                self.progress.emit(row_idx, success, "" if success else "שגיאה בשליחה")
            except Exception as e:
                self.progress.emit(row_idx, False, str(e))

        self.finished_all.emit()


class SendPanel(QWidget):
    """Send panel with email table, status column, and send controls."""

    back_requested = pyqtSignal()

    # Columns
    COL_CHECK = 0
    COL_NAME = 1
    COL_EMAIL = 2
    COL_FILE = 3
    COL_STATUS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._payslip_data = []  # (employee, filename, encrypted_bytes)
        self._month = 1
        self._year = 2025
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Top bar
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← חזור")
        self.back_btn.setFont(QFont("Segoe UI", 11))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(self.back_btn)

        title = QLabel("שליחת תלושי שכר")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title, stretch=1)

        top_bar.addSpacing(80)  # balance the back button
        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "שם עובד", "אימייל", "קובץ", "סטטוס"])
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_NAME, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_EMAIL, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_FILE, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COL_CHECK, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("בחר הכל")
        self.select_all_btn.setFont(QFont("Segoe UI", 10))
        self.select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("בטל בחירה")
        self.deselect_all_btn.setFont(QFont("Segoe UI", 10))
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()

        self.send_selected_btn = QPushButton("שלח נבחרים")
        self.send_selected_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.send_selected_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.send_selected_btn.clicked.connect(self._send_selected)
        btn_layout.addWidget(self.send_selected_btn)

        self.send_all_btn = QPushButton("שלח הכל")
        self.send_all_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.send_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.send_all_btn.clicked.connect(self._send_all)
        btn_layout.addWidget(self.send_all_btn)

        self.retry_btn = QPushButton("נסה שוב נכשלים")
        self.retry_btn.setFont(QFont("Segoe UI", 11))
        self.retry_btn.setVisible(False)
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.retry_btn.clicked.connect(self._retry_failed)
        btn_layout.addWidget(self.retry_btn)

        layout.addLayout(btn_layout)

    def load_payslips(self, payslip_data, month, year):
        """Load prepared payslip data into the table.

        payslip_data: list of (Employee, filename, encrypted_bytes)
        """
        self._payslip_data = payslip_data
        self._month = month
        self._year = year
        self._statuses = ["ממתין"] * len(payslip_data)

        self.table.setRowCount(len(payslip_data))
        for row, (emp, filename, _) in enumerate(payslip_data):
            # Checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, self.COL_CHECK, chk_widget)

            self.table.setItem(row, self.COL_NAME, QTableWidgetItem(emp.name))
            self.table.setItem(row, self.COL_EMAIL, QTableWidgetItem(emp.email))
            self.table.setItem(row, self.COL_FILE, QTableWidgetItem(filename))

            status_item = QTableWidgetItem("ממתין")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, self.COL_STATUS, status_item)

        self.progress_bar.setVisible(False)
        self.retry_btn.setVisible(False)

    def _get_checkbox(self, row) -> QCheckBox | None:
        widget = self.table.cellWidget(row, self.COL_CHECK)
        if widget:
            return widget.findChild(QCheckBox)
        return None

    def _select_all(self):
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk:
                chk.setChecked(True)

    def _deselect_all(self):
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk:
                chk.setChecked(False)

    def _get_selected_rows(self) -> list[int]:
        selected = []
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isChecked():
                selected.append(row)
        return selected

    def _send_selected(self):
        rows = self._get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "אין נבחרים", "בחר לפחות תלוש אחד לשליחה.")
            return
        self._do_send(rows)

    def _send_all(self):
        rows = list(range(self.table.rowCount()))
        self._do_send(rows)

    def _retry_failed(self):
        rows = [r for r in range(self.table.rowCount())
                if self._statuses[r].startswith("✗")]
        if rows:
            self._do_send(rows)

    def _do_send(self, rows: list[int]):
        from src.gmail_sender import get_gmail_service
        from src.config import load_config

        try:
            service = get_gmail_service()
        except Exception as e:
            QMessageBox.critical(
                self, "שגיאת Gmail",
                f"לא ניתן להתחבר ל-Gmail:\n{e}\n\nוודא שיש קובץ credentials.json"
            )
            return

        config = load_config()

        # Build send list
        send_list = []
        for row in rows:
            emp, filename, enc_bytes = self._payslip_data[row]
            send_list.append((row, emp, filename, enc_bytes))
            self._set_status(row, "שולח...", "#f39c12")

        self.progress_bar.setMaximum(len(send_list))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._set_buttons_enabled(False)

        self._worker = SendWorker(
            service, send_list,
            config["subject_template"],
            config["body_template"],
            self._month, self._year,
        )
        self._worker.progress.connect(self._on_send_progress)
        self._worker.finished_all.connect(self._on_send_finished)
        self._worker.start()

    @pyqtSlot(int, bool, str)
    def _on_send_progress(self, row, success, error_msg):
        if success:
            self._set_status(row, "✓ נשלח", "#27ae60")
            self._statuses[row] = "✓ נשלח"
        else:
            self._set_status(row, f"✗ נכשל: {error_msg}", "#e74c3c")
            self._statuses[row] = f"✗ {error_msg}"
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _on_send_finished(self):
        self._set_buttons_enabled(True)
        has_failures = any(s.startswith("✗") for s in self._statuses)
        self.retry_btn.setVisible(has_failures)
        self._worker = None

    def _set_status(self, row, text, color):
        item = self.table.item(row, self.COL_STATUS)
        if item:
            item.setText(text)
            item.setForeground(Qt.GlobalColor.black)

    def _set_buttons_enabled(self, enabled):
        self.send_all_btn.setEnabled(enabled)
        self.send_selected_btn.setEnabled(enabled)
        self.back_btn.setEnabled(enabled)
        self.retry_btn.setEnabled(enabled)
