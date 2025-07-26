# run.py
import sys
from PyQt6.QtWidgets import QApplication
from landing import LandingDialog
from main import GlobalPipPilot

def main():
    app = QApplication(sys.argv)

    dlg = LandingDialog()
    interpreter = dlg.exec_and_return()
    if not interpreter:
        sys.exit(0)

    win = GlobalPipPilot(interpreter)
    win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
