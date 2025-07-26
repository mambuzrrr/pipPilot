# main.py
import sys, subprocess, requests
from functools import partial
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QScrollArea, QLineEdit, QCheckBox,
    QMessageBox
)
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pipmanager import get_installed_packages

class LoaderThread(QThread):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter

    def run(self):
        pkgs = get_installed_packages(self.interpreter)
        total = len(pkgs)
        result = []
        for i, (name, ver) in enumerate(pkgs.items(), 1):
            if "-" in name or "." in name:
                self.progress.emit(int(i / total * 100))
                continue
            try:
                res = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=5)
                latest = res.json()["info"]["version"]
            except:
                latest = ver
            result.append((name, ver, ver == latest, latest))
            self.progress.emit(int(i / total * 100))
        self.finished.emit(result)

class InstallThread(QThread):
    log_line = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, interpreter, package, uninstall=False):
        super().__init__()
        self.interpreter = interpreter
        self.package = package
        self.uninstall = uninstall

    def run(self):
        if self.uninstall:
            cmd = [self.interpreter, "-m", "pip", "uninstall", "-y", self.package]
            self.log_line.emit(f"🗑️ Uninstalling '{self.package}'...\n")
        else:
            cmd = [self.interpreter, "-m", "pip", "install", "--upgrade", self.package, "--disable-pip-version-check", "--no-cache-dir"]
            self.log_line.emit(f"🔄 Starting installation/update of '{self.package}'...\n")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                self.log_line.emit(line.rstrip())
            process.stdout.close()
            retcode = process.wait()
            if retcode == 0:
                action = "uninstalled" if self.uninstall else "installed/updated"
                self.log_line.emit(f"✅ '{self.package}' successfully {action}.\n")
                self.finished.emit(True)
            else:
                self.log_line.emit(f"❌ {('Uninstall' if self.uninstall else 'Install/update')} failed with exit code {retcode}.\n")
                self.finished.emit(False)
        except Exception as e:
            self.log_line.emit(f"❌ Exception during {'uninstall' if self.uninstall else 'install/update'}: {e}\n")
            self.finished.emit(False)

class GlobalPipPilot(QMainWindow):
    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter
        self.setWindowTitle("pipPilot – Package Overview")
        self.resize(1000, 700)
        self._setup_palette()
        self._init_ui()
        self._load_packages()

    def _setup_palette(self):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor("#20232A"))
        p.setColor(QPalette.ColorRole.Base, QColor("#1E2127"))
        p.setColor(QPalette.ColorRole.Text, QColor("white"))
        self.setPalette(p)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top bar (search + refresh + sort toggle)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search packages...")
        self.search.textChanged.connect(self._filter)
        top.addWidget(self.search)

        self.sort_toggle = QCheckBox("🔃 Show outdated first")
        self.sort_toggle.stateChanged.connect(self._refresh_package_list)
        top.addWidget(self.sort_toggle)

        self.btn_refresh = QPushButton("🔁 Refresh")
        self.btn_refresh.clicked.connect(self._load_packages)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Install Package
        install_layout = QHBoxLayout()
        self.install_input = QLineEdit()
        self.install_input.setPlaceholderText("Enter package name to install...")
        self.install_input.returnPressed.connect(self._install_package)
        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self._install_package)
        install_layout.addWidget(self.install_input)
        install_layout.addWidget(self.install_btn)
        layout.addLayout(install_layout)

        # Output label + clear
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output:")
        self.output_label.setFont(QFont("Segoe UI", 10, weight=QFont.Weight.Bold))
        output_layout.addWidget(self.output_label)
        output_layout.addStretch()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(70)
        self.clear_btn.clicked.connect(self._clear_console)
        output_layout.addWidget(self.clear_btn)
        layout.addLayout(output_layout)

        # Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        self.console.setFont(QFont("Consolas", 10))
        layout.addWidget(self.console)

        # Progress
        self.progress = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress)
        self.progress.hide()

    def _clear_console(self):
        self.console.clear()

    def _log(self, text):
        self.console.append(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def _load_packages(self):
        self.btn_refresh.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        self.scroll_clear()
        self.thread = LoaderThread(self.interpreter)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self._on_loaded)
        self.thread.start()

    def _on_loaded(self, packages):
        self.progress.hide()
        self.btn_refresh.setEnabled(True)
        self.packages = packages
        self._refresh_package_list()

    def scroll_clear(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def _refresh_package_list(self):
        pkgs = self.packages
        if self.sort_toggle.isChecked():
            pkgs = sorted(pkgs, key=lambda x: x[2])  # outdated first
        else:
            pkgs = sorted(pkgs)

        self.scroll_clear()
        self.package_rows = {}

        for name, ver, uptodate, latest in pkgs:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(4, 2, 4, 2)

            # Name
            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("Segoe UI", 10))
            h.addWidget(name_lbl, 2)

            # Info Button
            info_btn = QPushButton("Info")
            info_btn.setFixedWidth(60)
            info_btn.setStyleSheet(
                "QPushButton { background-color: #555; color: white; }"
                "QPushButton:hover { background-color: #777; }"
            )
            info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            info_btn.clicked.connect(partial(self._show_package_info, name))
            h.addWidget(info_btn, 1)

            # Uninstall Button
            uninstall_btn = QPushButton("Uninstall")
            uninstall_btn.setFixedWidth(80)
            uninstall_btn.setStyleSheet(
                "QPushButton { background-color: #b34040; color: white; }"
                "QPushButton:hover { background-color: #d04e4e; }"
            )
            uninstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            uninstall_btn.clicked.connect(partial(self._confirm_uninstall, name))
            h.addWidget(uninstall_btn, 1)

            # Status
            stat = QLabel("Up-to-date" if uptodate else f"{ver} → {latest}")
            stat.setStyleSheet(f"color:{'#98C379' if uptodate else '#E5C07B'}")
            h.addWidget(stat, 2)

            # Update Button
            update_btn = QPushButton("Update")
            update_btn.setEnabled(not uptodate)
            if uptodate:
                update_btn.setStyleSheet("QPushButton { background-color: #444; color: white; }")
            else:
                update_btn.setStyleSheet(
                    "QPushButton { background-color: #98C379; color: white; }"
                    "QPushButton:hover { background-color: #85a363; }"
                )
                update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            update_btn.clicked.connect(partial(self._update_package, name))
            h.addWidget(update_btn, 1)

            self.scroll_layout.addWidget(row)
            self.package_rows[name.lower()] = row

        self._add_pip_block()

    def _confirm_uninstall(self, name):
        reply = QMessageBox.question(
            self, "Confirm Uninstall",
            f"Are you sure you want to uninstall '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._uninstall_package(name)

    def _uninstall_package(self, name):
        if hasattr(self, "install_thread") and self.install_thread.isRunning():
            self._log("⚠️ Another operation is running, please wait...\n")
            return
        self._log(f"🗑️ Uninstalling: {name}\n")
        self.install_thread = InstallThread(self.interpreter, name, uninstall=True)
        self.install_thread.log_line.connect(self._log)
        self.install_thread.finished.connect(self._on_update_finished)
        self.btn_refresh.setEnabled(False)
        self.install_thread.start()

    def _add_pip_block(self):
        try:
            out = subprocess.run(
                [self.interpreter, "-m", "pip", "--version"],
                capture_output=True, text=True
            ).stdout.strip()
            current = out.split()[-1]
            latest = requests.get("https://pypi.org/pypi/pip/json", timeout=5).json()["info"]["version"]
            uptodate = current == latest
        except:
            current, latest, uptodate = "?", "?", True

        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 2, 4, 2)

        pip_lbl = QLabel(f"pip ({current})")
        pip_lbl.setFont(QFont("Segoe UI", 10))
        h.addWidget(pip_lbl, 3)

        pip_status = QLabel("Up-to-date" if uptodate else f"Update → {latest}")
        pip_status.setStyleSheet(f"color:{'#98C379' if uptodate else '#E5C07B'}")
        h.addWidget(pip_status, 2)

        pip_btn = QPushButton("Update pip")
        pip_btn.setEnabled(not uptodate)
        if uptodate:
            pip_btn.setStyleSheet("QPushButton { background-color: #444; color: white; }")
        else:
            pip_btn.setStyleSheet(
                "QPushButton { background-color: #98C379; color: white; }"
                "QPushButton:hover { background-color: #85a363; }"
            )
            pip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pip_btn.clicked.connect(lambda: self._update_package("pip"))
        h.addWidget(pip_btn, 1)

        self.scroll_layout.addWidget(row)

    def _update_package(self, name):
        if hasattr(self, "install_thread") and self.install_thread.isRunning():
            self._log("⚠️ An update/install is already running, please wait...\n")
            return
        self._log(f"🚀 Starting update/install for: {name}\n")
        self.install_thread = InstallThread(self.interpreter, name)
        self.install_thread.log_line.connect(self._log)
        self.install_thread.finished.connect(self._on_update_finished)
        self.btn_refresh.setEnabled(False)
        self.install_thread.start()

    def _on_update_finished(self, success):
        if success:
            self._log("🔄 Refreshing package list...\n")
            self._load_packages()
        else:
            self._log("❌ Operation failed. See logs above.\n")
            self.btn_refresh.setEnabled(True)

    def _install_package(self):
        pkg_name = self.install_input.text().strip()
        if not pkg_name:
            self._log("⚠️ Please enter a package name to install.\n")
            return
        self.install_input.clear()
        self._update_package(pkg_name)

    def _filter(self, text):
        text = text.strip().lower()
        for name, row in self.package_rows.items():
            row.setVisible(text in name)

    def _show_package_info(self, name):
        try:
            output = subprocess.check_output(
                [self.interpreter, "-m", "pip", "show", name], text=True
            )
            QMessageBox.information(self, f"Package Info – {name}", output)
        except subprocess.CalledProcessError:
            QMessageBox.warning(self, "Info", f"No information found for {name}.")