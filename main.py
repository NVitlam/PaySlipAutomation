"""PayslipApp — Entry point."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyle("Fusion")

    # Set global stylesheet
    app.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QToolTip {
            background-color: #2c3e50;
            color: white;
            border: 1px solid #34495e;
            padding: 4px;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
