"""Main Window — ties all screens together with navigation."""

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.upload_screen import UploadScreen
from src.preview_grid import PreviewGrid
from src.send_panel import SendPanel
from src.dialogs import TemplateEditorDialog, EmployeeManagerDialog, AddEmployeeDialog, GmailSettingsDialog
from src.config import load_config, save_config
from src.employee_db import load_employees, save_employees
from src.splitter import split_pdf, get_page_objects
from src.extractor import extract_id
from src.encryptor import process_payslip


class MainWindow(QMainWindow):
    """Main application window with stacked screens."""

    SCREEN_UPLOAD = 0
    SCREEN_PREVIEW = 1
    SCREEN_SEND = 2

    def __init__(self):
        super().__init__()
        self.employees = load_employees()
        self._page_bytes: list[bytes] = []
        self._doc = None
        self._pages = []
        self._extracted_ids: list[str | None] = []
        self._month = 1
        self._year = 2025

        config = load_config()
        self.setWindowTitle("PayslipApp — שליחת תלושי שכר")
        self.setMinimumSize(900, 650)
        self.resize(config.get("window_width", 1100), config.get("window_height", 750))

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #2c3e50; padding: 6px 15px;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 6, 15, 6)

        app_title = QLabel("PayslipApp")
        app_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        app_title.setStyleSheet("color: white;")
        top_bar_layout.addWidget(app_title)

        top_bar_layout.addStretch()

        # Employee management button
        emp_btn = QPushButton("ניהול עובדים")
        emp_btn.setFont(QFont("Segoe UI", 10))
        emp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        emp_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; border-radius: 5px; padding: 6px 16px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        emp_btn.clicked.connect(self._open_employee_manager)
        top_bar_layout.addWidget(emp_btn)

        # Template editor button
        template_btn = QPushButton("תבנית אימייל")
        template_btn.setFont(QFont("Segoe UI", 10))
        template_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        template_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white;
                border: none; border-radius: 5px; padding: 6px 16px;
            }
            QPushButton:hover { background-color: #7d3c98; }
        """)
        template_btn.clicked.connect(self._open_template_editor)
        top_bar_layout.addWidget(template_btn)

        # Gmail settings
        self.gmail_btn = QPushButton("Gmail Settings")
        self.gmail_btn.setFont(QFont("Segoe UI", 10))
        self.gmail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gmail_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                border: none; border-radius: 5px; padding: 6px 16px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.gmail_btn.clicked.connect(self._open_gmail_settings)
        top_bar_layout.addWidget(self.gmail_btn)

        main_layout.addWidget(top_bar)

        # Stacked screens
        self.stack = QStackedWidget()

        self.upload_screen = UploadScreen()
        self.upload_screen.process_requested.connect(self._on_process)
        self.stack.addWidget(self.upload_screen)

        self.preview_grid = PreviewGrid()
        self.preview_grid.confirm_requested.connect(self._on_confirm)
        self.preview_grid.back_requested.connect(self._go_to_upload)
        self.stack.addWidget(self.preview_grid)

        self.send_panel = SendPanel()
        self.send_panel.back_requested.connect(self._go_to_preview)
        self.stack.addWidget(self.send_panel)

        main_layout.addWidget(self.stack)

        self._update_gmail_status()

    def _on_process(self, pdf_path: str, month: int, year: int):
        """Handle PDF processing — split, extract IDs, show preview grid."""
        self._month = month
        self._year = year

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # Split PDF
            self._page_bytes = split_pdf(pdf_path)

            # Get page objects for rendering
            if self._doc:
                self._doc.close()
            self._doc, self._pages = get_page_objects(pdf_path)

            # Extract IDs
            self._extracted_ids = []
            for page in self._pages:
                self._extracted_ids.append(extract_id(page))

            # Reload employees (may have changed)
            self.employees = load_employees()

            # Load preview grid
            self.preview_grid.load_pages(
                self._pages, self._page_bytes,
                self._extracted_ids, self.employees
            )

            self.stack.setCurrentIndex(self.SCREEN_PREVIEW)

        except Exception as e:
            QMessageBox.critical(
                self, "שגיאה בעיבוד",
                f"שגיאה בפתיחת קובץ ה-PDF:\n{e}"
            )
        finally:
            QApplication.restoreOverrideCursor()

    def _on_confirm(self):
        """User confirmed all assignments — encrypt and move to send panel."""
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            assignments = self.preview_grid.get_assignments()
            payslip_data = []

            for page_idx, emp in assignments:
                filename, encrypted = process_payslip(
                    self._page_bytes[page_idx],
                    emp.name, emp.id,
                    self._month, self._year,
                )
                payslip_data.append((emp, filename, encrypted))

            self.send_panel.load_payslips(payslip_data, self._month, self._year)
            self.stack.setCurrentIndex(self.SCREEN_SEND)

        except Exception as e:
            QMessageBox.critical(
                self, "שגיאה בהכנה",
                f"שגיאה בהצפנת הקבצים:\n{e}"
            )
        finally:
            QApplication.restoreOverrideCursor()

    def _go_to_upload(self):
        self.stack.setCurrentIndex(self.SCREEN_UPLOAD)

    def _go_to_preview(self):
        self.stack.setCurrentIndex(self.SCREEN_PREVIEW)

    def _open_employee_manager(self):
        dialog = EmployeeManagerDialog(self)
        dialog.employees_changed.connect(self._on_employees_changed)
        dialog.exec()

    def _on_employees_changed(self):
        self.employees = load_employees()
        if self.stack.currentIndex() == self.SCREEN_PREVIEW:
            self.preview_grid.refresh_employees(self.employees)

    def _open_template_editor(self):
        dialog = TemplateEditorDialog(self)
        dialog.exec()

    def _open_gmail_settings(self):
        dialog = GmailSettingsDialog(self)
        dialog.connection_changed.connect(self._update_gmail_status)
        dialog.exec()

    def _update_gmail_status(self):
        from src.gmail_sender import is_authenticated
        if is_authenticated():
            self.gmail_btn.setText("Gmail Connected")
            self.gmail_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white;
                    border: none; border-radius: 5px; padding: 6px 16px;
                }
                QPushButton:hover { background-color: #219a52; }
            """)
        else:
            self.gmail_btn.setText("Gmail Settings")
            self.gmail_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22; color: white;
                    border: none; border-radius: 5px; padding: 6px 16px;
                }
                QPushButton:hover { background-color: #d35400; }
            """)

    def closeEvent(self, event):
        # Save window size
        config = load_config()
        config["window_width"] = self.width()
        config["window_height"] = self.height()
        save_config(config)

        # Close PDF doc
        if self._doc:
            self._doc.close()

        event.accept()
