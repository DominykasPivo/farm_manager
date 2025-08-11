from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QComboBox


# second window for the entire application (practically the main window)
class Field_Manager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Field Manager')
        self.setGeometry(100, 100, 300, 200)
        label = QLabel('This is the field manager window!', self)
        label.move(60, 80)

        #add btn to field
        add_field_btn = QPushButton('Prideti Lauka', self)
        add_field_btn.move(100, 120)

        #remove btn to field
        remove_field_btn = QPushButton('Istrinti Lauka', self)
        remove_field_btn.move(100, 150)

        #back btn to main window
        back_btn = QPushButton('Grizti', self)
        back_btn.move(100, 180)

        all_fields_box = QComboBox(self)
        all_fields_box.addItems(['Field 1', 'Field 2', 'Field 3'])

        check_field_btn = QPushButton('Patikrinti Lauka', self)
        check_field_btn.move(100, 210)