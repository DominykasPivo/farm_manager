# Learning PyQt6 from a template

import sys
from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QPushButton

from field_manager_window import Field_Manager


class FarmManager(QWidget):
    def __init__(self):
        super().__init__()
        self.field_manager = None
        self.setupGUI()

    def setupGUI(self):
        self.setWindowTitle('Farm Manager')
        self.setGeometry(30, 30, 250, 90)

        pradeti_btn = QPushButton('Pradeti', self)
        pradeti_btn.move(90, 40)
        pradeti_btn.clicked.connect(self.openFieldManager)

    def openFieldManager(self):
        if self.field_manager is not None:
            self.field_manager.close()
        self.field_manager = Field_Manager()
        self.field_manager.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = FarmManager()
    form.show()

app.exec()
