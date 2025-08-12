from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QComboBox
from field_manager import AddFieldWindow, ViewFieldWindow   
import os, shutil

# second window for the entire application (practically the main window)
class Field_Manager(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Field Manager')
        self.setGeometry(100, 100, 300, 300)
        label = QLabel('This is the field manager window!', self)
        label.move(60, 80)

        #add btn to field
        add_field_btn = QPushButton('Prideti Lauka', self)
        add_field_btn.move(100, 120)
        add_field_btn.clicked.connect(self.open_add_field_window)

        #remove btn to field
        remove_field_btn = QPushButton('Istrinti Lauka', self)
        remove_field_btn.move(100, 150)

        #back btn to main window
        back_btn = QPushButton('Grizti', self)
        back_btn.move(100, 180)

        self.all_fields_box = QComboBox(self)
        self.all_fields_box.move(100, 210)
        self.refresh_fields()

        check_field_btn = QPushButton('Patikrinti Lauka', self)
        check_field_btn.move(100, 240)
        check_field_btn.clicked.connect(self.view_selected_field)

        self.add_field_window = None
        self.view_field_window = None

    def refresh_fields(self):
        fields_dir = 'fields'
        field_names = []
        if os.path.exists(fields_dir) and len(os.listdir(fields_dir)) > 0:
            field_names = [name for name in os.listdir(fields_dir)
                      if os.path.isdir(os.path.join(fields_dir, name))]
        else:
            field_names = ["None"]
        self.all_fields_box.clear()
        self.all_fields_box.addItems(field_names)

    def open_add_field_window(self):
        if self.add_field_window is None or not self.add_field_window.isVisible():
            self.add_field_window = AddFieldWindow()
            self.add_field_window.show()
    
    def view_selected_field(self):
        field_name = self.all_fields_box.currentText()
        if field_name and field_name != "None":
            self.view_field_window = ViewFieldWindow(field_name)
            self.view_field_window.show()

