"""Screen 2: Preview Grid — displays payslip thumbnails with employee assignment."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QComboBox, QFrame, QDialog,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QImage

from src.employee_db import Employee
from src.splitter import render_thumbnail, render_full_page


class ZoomDialog(QDialog):
    """Full-page zoom view of a payslip page."""

    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("תצוגה מוגדלת")
        self.setMinimumSize(700, 900)

        layout = QVBoxLayout(self)
        label = QLabel()
        png_data = render_full_page(page, dpi=150)
        pixmap = QPixmap()
        pixmap.loadFromData(png_data)
        label.setPixmap(pixmap.scaledToWidth(
            650, Qt.TransformationMode.SmoothTransformation
        ))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        close_btn = QPushButton("סגור")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class PayslipCard(QFrame):
    """Single card showing a payslip thumbnail and employee assignment."""

    assignment_changed = pyqtSignal(int)  # card index

    # Card states
    STATE_CONFIRMED = "confirmed"
    STATE_UNASSIGNED = "unassigned"
    STATE_MANUAL = "manual"

    BORDER_COLORS = {
        STATE_CONFIRMED: "#27ae60",   # green
        STATE_UNASSIGNED: "#f39c12",  # yellow/orange
        STATE_MANUAL: "#3498db",      # blue
    }

    def __init__(self, index: int, page, thumbnail_data: bytes,
                 employees: dict[str, Employee], auto_id: str | None,
                 parent=None):
        super().__init__(parent)
        self.index = index
        self.page = page
        self.employees = employees
        self.auto_id = auto_id
        self.assigned_employee: Employee | None = None

        self.setFixedWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self._setup_ui(thumbnail_data)
        self._apply_auto_assignment()

    def _setup_ui(self, thumbnail_data: bytes):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Thumbnail
        self.thumb_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(thumbnail_data)
        scaled = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
        self.thumb_label.setPixmap(scaled)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.thumb_label.mousePressEvent = lambda _: self._show_zoom()
        layout.addWidget(self.thumb_label)

        # Page number
        page_label = QLabel(f"עמוד {self.index + 1}")
        page_label.setFont(QFont("Segoe UI", 9))
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_label.setStyleSheet("color: #888;")
        layout.addWidget(page_label)

        # Status / employee name
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Employee dropdown
        self.combo = QComboBox()
        self.combo.setFont(QFont("Segoe UI", 9))
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.setPlaceholderText("בחר עובד...")
        self._populate_combo()
        self.combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo)

    def _populate_combo(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("-- בחר עובד --", None)
        for emp_id, emp in sorted(self.employees.items(), key=lambda x: x[1].name):
            self.combo.addItem(f"{emp.name} ({emp.id})", emp_id)
        self.combo.blockSignals(False)

    def _apply_auto_assignment(self):
        if self.auto_id and self.auto_id in self.employees:
            emp = self.employees[self.auto_id]
            self.assigned_employee = emp
            # Select matching combo item
            for i in range(self.combo.count()):
                if self.combo.itemData(i) == self.auto_id:
                    self.combo.blockSignals(True)
                    self.combo.setCurrentIndex(i)
                    self.combo.blockSignals(False)
                    break
            self._set_state(self.STATE_CONFIRMED)
        else:
            self._set_state(self.STATE_UNASSIGNED)

    def _on_combo_changed(self, idx):
        emp_id = self.combo.itemData(idx)
        if emp_id and emp_id in self.employees:
            self.assigned_employee = self.employees[emp_id]
            if emp_id == self.auto_id:
                self._set_state(self.STATE_CONFIRMED)
            else:
                self._set_state(self.STATE_MANUAL)
        else:
            self.assigned_employee = None
            self._set_state(self.STATE_UNASSIGNED)
        self.assignment_changed.emit(self.index)

    def _set_state(self, state: str):
        self.state = state
        color = self.BORDER_COLORS[state]
        self.setStyleSheet(f"""
            PayslipCard {{
                border: 3px solid {color};
                border-radius: 8px;
                background-color: white;
            }}
        """)
        if state == self.STATE_CONFIRMED:
            self.status_label.setText(f"✓ {self.assigned_employee.name}")
            self.status_label.setStyleSheet("color: #27ae60;")
        elif state == self.STATE_MANUAL:
            self.status_label.setText(f"✏ {self.assigned_employee.name}")
            self.status_label.setStyleSheet("color: #3498db;")
        else:
            self.status_label.setText("⚠ לא שויך")
            self.status_label.setStyleSheet("color: #f39c12;")

    def _show_zoom(self):
        dialog = ZoomDialog(self.page, self)
        dialog.exec()

    def refresh_employees(self, employees: dict[str, Employee]):
        """Refresh the employee list in the dropdown."""
        self.employees = employees
        current_id = self.assigned_employee.id if self.assigned_employee else None
        self._populate_combo()
        if current_id and current_id in employees:
            for i in range(self.combo.count()):
                if self.combo.itemData(i) == current_id:
                    self.combo.blockSignals(True)
                    self.combo.setCurrentIndex(i)
                    self.combo.blockSignals(False)
                    break

    def is_assigned(self) -> bool:
        return self.assigned_employee is not None


class PreviewGrid(QWidget):
    """Preview grid screen showing all payslip cards."""

    confirm_requested = pyqtSignal()  # all cards assigned, user confirmed
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: list[PayslipCard] = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)

        # Top bar
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← חזור")
        self.back_btn.setFont(QFont("Segoe UI", 11))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(self.back_btn)

        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Segoe UI", 11))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(self.info_label, stretch=1)

        self.confirm_btn = QPushButton("אשר והמשך →")
        self.confirm_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:disabled { background-color: #ccc; color: #888; }
        """)
        self.confirm_btn.clicked.connect(self.confirm_requested.emit)
        top_bar.addWidget(self.confirm_btn)

        main_layout.addLayout(top_bar)

        # Scroll area with grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.scroll.setWidget(self.grid_widget)

        main_layout.addWidget(self.scroll)

    def load_pages(self, pages, page_bytes_list, extracted_ids, employees):
        """Populate the grid with PayslipCards."""
        # Clear existing cards
        self.cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        columns = 4
        for i, (page, extracted_id) in enumerate(zip(pages, extracted_ids)):
            thumb_data = render_thumbnail(page, width=200)
            card = PayslipCard(i, page, thumb_data, employees, extracted_id)
            card.assignment_changed.connect(self._on_assignment_changed)
            self.cards.append(card)
            row, col = divmod(i, columns)
            self.grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)

        self._update_status()

    def _on_assignment_changed(self, index):
        self._update_status()

    def _update_status(self):
        total = len(self.cards)
        assigned = sum(1 for c in self.cards if c.is_assigned())
        self.info_label.setText(f"שויכו {assigned} מתוך {total} תלושים")
        self.confirm_btn.setEnabled(assigned == total)

    def get_assignments(self) -> list[tuple[int, Employee]]:
        """Return list of (page_index, Employee) for all assigned cards."""
        return [(c.index, c.assigned_employee) for c in self.cards if c.is_assigned()]

    def refresh_employees(self, employees):
        """Refresh employee list in all cards."""
        for card in self.cards:
            card.refresh_employees(employees)
        self._update_status()
