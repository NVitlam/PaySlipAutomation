"""Dialogs — Template Editor, Employee Management, Add Employee popup, Gmail Settings."""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QGroupBox,
    QFormLayout, QWidget, QPlainTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from src.employee_db import Employee, load_employees, save_employees, add_employee
from src.config import load_config, save_config


class TemplateEditorDialog(QDialog):
    """Email template editor with variable substitution preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("עריכת תבנית אימייל")
        self.setMinimumSize(550, 500)
        self._setup_ui()
        self._load_current()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Variables reference
        ref_box = QGroupBox("משתנים זמינים")
        ref_layout = QHBoxLayout(ref_box)
        for var in ["{name}", "{month}", "{year}", "{id}"]:
            lbl = QLabel(var)
            lbl.setStyleSheet(
                "background-color: #eef; padding: 4px 10px; border-radius: 4px; "
                "font-family: Consolas;"
            )
            ref_layout.addWidget(lbl)
        ref_layout.addStretch()
        layout.addWidget(ref_box)

        # Subject
        layout.addWidget(QLabel("נושא:"))
        self.subject_edit = QLineEdit()
        self.subject_edit.setFont(QFont("Segoe UI", 11))
        self.subject_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.subject_edit)

        # Body
        layout.addWidget(QLabel("גוף ההודעה:"))
        self.body_edit = QTextEdit()
        self.body_edit.setFont(QFont("Segoe UI", 11))
        self.body_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.body_edit)

        # Preview button
        preview_btn = QPushButton("תצוגה מקדימה")
        preview_btn.clicked.connect(self._preview)
        layout.addWidget(preview_btn)

        # Preview area
        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(
            "background-color: #f5f5f5; padding: 10px; border-radius: 6px;"
        )
        self.preview_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.preview_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("ביטול")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("שמור")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px; padding: 8px 25px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_current(self):
        config = load_config()
        self.subject_edit.setText(config["subject_template"])
        self.body_edit.setPlainText(config["body_template"])

    def _preview(self):
        subject = self.subject_edit.text()
        body = self.body_edit.toPlainText()
        try:
            s = subject.format(name="ישראל ישראלי", month="ינואר", year="2025", id="123456789")
            b = body.format(name="ישראל ישראלי", month="ינואר", year="2025", id="123456789")
            self.preview_label.setText(f"נושא: {s}\n\n{b}")
        except KeyError as e:
            self.preview_label.setText(f"שגיאה בתבנית: משתנה לא מוכר {e}")

    def _save(self):
        config = load_config()
        config["subject_template"] = self.subject_edit.text()
        config["body_template"] = self.body_edit.toPlainText()
        save_config(config)
        self.accept()


class AddEmployeeDialog(QDialog):
    """Dialog for adding a new employee."""

    employee_added = pyqtSignal(object)  # Employee

    def __init__(self, prefill_id: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("הוספת עובד חדש")
        self.setMinimumWidth(400)
        self._setup_ui(prefill_id)

    def _setup_ui(self, prefill_id: str):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.id_edit = QLineEdit(prefill_id)
        self.id_edit.setPlaceholderText("9 ספרות")
        self.id_edit.setMaxLength(9)
        layout.addRow("תעודת זהות:", self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("שם מלא")
        self.name_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addRow("שם:", self.name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        layout.addRow("אימייל:", self.email_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("050-1234567 (אופציונלי)")
        layout.addRow("טלפון:", self.phone_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("ביטול")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("שמור")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px; padding: 8px 25px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addRow(btn_layout)

    def _save(self):
        emp_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        phone = self.phone_edit.text().strip()

        # Validate
        if not re.match(r'^\d{9}$', emp_id):
            QMessageBox.warning(self, "שגיאה", "תעודת זהות חייבת להכיל 9 ספרות בדיוק.")
            return
        if not name:
            QMessageBox.warning(self, "שגיאה", "יש להזין שם.")
            return
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            QMessageBox.warning(self, "שגיאה", "כתובת אימייל לא תקינה.")
            return

        emp = Employee(id=emp_id, name=name, email=email, phone=phone)
        self.employee_added.emit(emp)
        self.accept()


class EmployeeManagerDialog(QDialog):
    """Full employee management dialog with CRUD operations."""

    employees_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ניהול עובדים")
        self.setMinimumSize(700, 500)
        self.employees = load_employees()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("חיפוש:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("חפש לפי שם או ת.ז...")
        self.search_edit.textChanged.connect(self._filter_table)
        self.search_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ת.ז", "שם", "אימייל", "טלפון"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("הוסף עובד")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        add_btn.clicked.connect(self._add_employee)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("ערוך")
        edit_btn.clicked.connect(self._edit_employee)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("מחק")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                border: none; border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        delete_btn.clicked.connect(self._delete_employee)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("סגור")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _refresh_table(self):
        self.table.setRowCount(len(self.employees))
        for row, emp in enumerate(sorted(self.employees.values(), key=lambda e: e.name)):
            self.table.setItem(row, 0, QTableWidgetItem(emp.id))
            self.table.setItem(row, 1, QTableWidgetItem(emp.name))
            self.table.setItem(row, 2, QTableWidgetItem(emp.email))
            self.table.setItem(row, 3, QTableWidgetItem(emp.phone))

    def _filter_table(self, text):
        text = text.strip().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _add_employee(self):
        dialog = AddEmployeeDialog(parent=self)
        dialog.employee_added.connect(self._on_employee_added)
        dialog.exec()

    def _on_employee_added(self, emp):
        self.employees[emp.id] = emp
        save_employees(self.employees)
        self._refresh_table()
        self.employees_changed.emit()

    def _edit_employee(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "עריכה", "בחר עובד לעריכה.")
            return

        emp_id = self.table.item(row, 0).text()
        emp = self.employees.get(emp_id)
        if not emp:
            return

        dialog = AddEmployeeDialog(prefill_id=emp.id, parent=self)
        dialog.setWindowTitle("עריכת עובד")
        dialog.name_edit.setText(emp.name)
        dialog.email_edit.setText(emp.email)
        dialog.phone_edit.setText(emp.phone)
        dialog.id_edit.setReadOnly(True)

        def on_edited(updated_emp):
            self.employees[updated_emp.id] = updated_emp
            save_employees(self.employees)
            self._refresh_table()
            self.employees_changed.emit()

        dialog.employee_added.connect(on_edited)
        dialog.exec()

    def _delete_employee(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "מחיקה", "בחר עובד למחיקה.")
            return

        emp_id = self.table.item(row, 0).text()
        emp = self.employees.get(emp_id)
        if not emp:
            return

        reply = QMessageBox.question(
            self, "אישור מחיקה",
            f"האם למחוק את {emp.name} ({emp.id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.employees[emp_id]
            save_employees(self.employees)
            self._refresh_table()
            self.employees_changed.emit()


class _TestConnectionWorker(QThread):
    """Runs Gmail connection test in background thread."""
    log_message = pyqtSignal(str)
    finished_result = pyqtSignal(bool, str)

    def run(self):
        from src.gmail_sender import test_connection
        success, msg = test_connection(log_callback=self._emit_log)
        self.finished_result.emit(success, msg)

    def _emit_log(self, msg):
        self.log_message.emit(msg)


class GmailSettingsDialog(QDialog):
    """Gmail OAuth2 credentials setup with test connection and log."""

    connection_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gmail Settings")
        self.setMinimumSize(620, 580)
        self._worker = None
        self._setup_ui()
        self._load_saved()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Instructions
        info = QLabel(
            "Enter your Google Cloud OAuth2 credentials below.\n"
            "You can get these from: Google Cloud Console > APIs & Services > Credentials\n"
            "Create an OAuth 2.0 Client ID of type 'Desktop app'."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #eef5ff; padding: 10px; border-radius: 6px;")
        info.setFont(QFont("Segoe UI", 9))
        layout.addWidget(info)

        # Credentials form
        form_box = QGroupBox("OAuth2 Credentials")
        form_layout = QFormLayout(form_box)
        form_layout.setSpacing(8)

        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("xxxx.apps.googleusercontent.com")
        self.client_id_edit.setFont(QFont("Consolas", 10))
        form_layout.addRow("Client ID:", self.client_id_edit)

        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setPlaceholderText("GOCSPX-xxxxxxxxxxxx")
        self.client_secret_edit.setFont(QFont("Consolas", 10))
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Client Secret:", self.client_secret_edit)

        # Toggle secret visibility
        show_secret_btn = QPushButton("Show/Hide")
        show_secret_btn.setFixedWidth(80)
        show_secret_btn.clicked.connect(self._toggle_secret)
        form_layout.addRow("", show_secret_btn)

        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText("my-project-12345 (optional)")
        self.project_id_edit.setFont(QFont("Consolas", 10))
        form_layout.addRow("Project ID:", self.project_id_edit)

        layout.addWidget(form_box)

        # Buttons row
        btn_row = QHBoxLayout()

        self.save_btn = QPushButton("Save Credentials")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px; padding: 9px 22px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        self.save_btn.clicked.connect(self._save_credentials)
        btn_row.addWidget(self.save_btn)

        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; border-radius: 6px; padding: 9px 22px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self.test_btn)

        self.clear_token_btn = QPushButton("Clear Token")
        self.clear_token_btn.setToolTip("Remove saved login token (forces re-login on next use)")
        self.clear_token_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                border: none; border-radius: 6px; padding: 9px 18px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.clear_token_btn.clicked.connect(self._clear_token)
        btn_row.addWidget(self.clear_token_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Connection status indicator
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Log area
        log_label = QLabel("Connection Log:")
        log_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(log_label)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        self.log_area.setMaximumBlockCount(200)
        self.log_area.setStyleSheet(
            "background-color: #1e1e1e; color: #dcdcdc; padding: 8px; border-radius: 6px;"
        )
        layout.addWidget(self.log_area)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _load_saved(self):
        from src.gmail_sender import load_saved_credentials, is_authenticated
        saved = load_saved_credentials()
        self.client_id_edit.setText(saved["client_id"])
        self.client_secret_edit.setText(saved["client_secret"])
        self.project_id_edit.setText(saved["project_id"])

        if is_authenticated():
            self._set_status("Connected", True)
        elif saved["client_id"]:
            self._set_status("Credentials saved — not yet connected", None)
        else:
            self._set_status("Not configured", False)

    def _toggle_secret(self):
        if self.client_secret_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _save_credentials(self):
        client_id = self.client_id_edit.text().strip()
        client_secret = self.client_secret_edit.text().strip()
        project_id = self.project_id_edit.text().strip()

        if not client_id:
            QMessageBox.warning(self, "Missing Field", "Client ID is required.")
            return
        if not client_secret:
            QMessageBox.warning(self, "Missing Field", "Client Secret is required.")
            return

        from src.gmail_sender import save_credentials
        save_credentials(client_id, client_secret, project_id)
        self._log("Credentials saved successfully.")
        self._set_status("Credentials saved — click Test Connection", None)
        self.connection_changed.emit()

    def _test_connection(self):
        self.log_area.clear()
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        self._set_status("Testing...", None)

        self._worker = _TestConnectionWorker()
        self._worker.log_message.connect(self._log)
        self._worker.finished_result.connect(self._on_test_done)
        self._worker.start()

    @pyqtSlot(str)
    def _log(self, msg: str):
        self.log_area.appendPlainText(msg)
        # Auto-scroll to bottom
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    @pyqtSlot(bool, str)
    def _on_test_done(self, success: bool, msg: str):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test Connection")
        self._set_status(msg, success)
        self.connection_changed.emit()
        self._worker = None

    def _clear_token(self):
        from src.gmail_sender import clear_token
        clear_token()
        self._log("Token cleared. You will need to re-authenticate.")
        self._set_status("Token cleared — re-auth required", None)
        self.connection_changed.emit()

    def _set_status(self, text: str, success: bool | None):
        self.status_label.setText(text)
        if success is True:
            self.status_label.setStyleSheet(
                "color: #27ae60; background-color: #efffef; padding: 6px; border-radius: 6px;"
            )
        elif success is False:
            self.status_label.setStyleSheet(
                "color: #e74c3c; background-color: #fff0f0; padding: 6px; border-radius: 6px;"
            )
        else:
            self.status_label.setStyleSheet(
                "color: #e67e22; background-color: #fff8ee; padding: 6px; border-radius: 6px;"
            )
