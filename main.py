import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from app.db.database import init_database
from app.ui.main_window import MainWindow


def main():
    init_database()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
