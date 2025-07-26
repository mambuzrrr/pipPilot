# landing.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QHBoxLayout, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
import shutil
import sys

def find_interpreters():
    seen = set()
    paths = []
    for exe in [sys.executable, "python", "python3", "py"]:
        path = shutil.which(exe)
        if path and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths

class LandingDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("pipPilot – Select Interpreter")
        self.setFixedSize(480, 280)

        # Stylesheet: nur was Qt sauber versteht
        self.setStyleSheet("""
            background-color: #282c34;
            color: white;
            font-family: "Segoe UI", sans-serif;

            /* Version & developer top left */
            #InfoLabel {
                font-size: 9pt;
                color: #888888;
            }

            /* Title pipPilot */
            #TitleLabel {
                font-size: 48pt;
                font-weight: bold;
                color: #61AFEF;
            }

            /* Description */
            #DescriptionLabel {
                font-size: 12pt;
                color: #CCCCCC;
            }

            /* ComboBox */
            QComboBox {
                font-size: 14pt;
                padding: 10px 14px;
                border: 1px solid #555555;
                border-radius: 6px;
                min-height: 42px;
                background-color: #3a3f4b;
            }
            QComboBox:hover {
                border-color: #61afef;
            }

            /* Continue Button */
            QPushButton#PrimaryBtn {
                font-size: 14pt;
                padding: 14px 34px;
                border-radius: 6px;
                background-color: #61afef;
                color: white;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #4b75b2;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Oberste Leiste mit Version + Entwickler ganz links
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.info_label = QLabel("Version 1.0 BETA | Developer: Rico")
        self.info_label.setObjectName("InfoLabel")
        top_layout.addWidget(self.info_label)

        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        top_layout.addItem(spacer)

        main_layout.addWidget(top_bar)

        # Großer Titel mittig
        self.title_label = QLabel("pipPILOT")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Beschreibung mittig
        self.desc_label = QLabel(
            "Select the Python interpreter you want to use for managing your packages."
        )
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("DescriptionLabel")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.desc_label)

        # ComboBox für Interpreter
        self.combo = QComboBox()
        self.interpreters = find_interpreters()
        self.combo.addItems(self.interpreters)
        main_layout.addWidget(self.combo)

        # Detektions-Status: Anzahl Interpreter
        status = f"Detected {len(self.interpreters)} interpreter(s)."
        self.detect_label = QLabel(status)
        self.detect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.detect_label)

        # Detektions-Status: Python vorhanden?
        python_status = "Detected Python: Yes" if self.interpreters else "Detected Python: No"
        self.python_detect_label = QLabel(python_status)
        self.python_detect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.python_detect_label)

        # Continue Button
        self.btn_continue = QPushButton("Continue")
        self.btn_continue.setObjectName("PrimaryBtn")
        self.btn_continue.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_continue.clicked.connect(self.accept)
        main_layout.addWidget(self.btn_continue)

    def exec_and_return(self):
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.combo.currentText()
        return None
