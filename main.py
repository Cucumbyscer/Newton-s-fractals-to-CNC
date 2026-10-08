import sys
import traceback

from PyQt5.QtWidgets import QApplication
from qss import DARK_QSS

from UIX import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    try:
        w = MainWindow()
        w.showMaximized()
        sys.exit(app.exec_())
    except Exception:
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
