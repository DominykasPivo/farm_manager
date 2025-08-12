from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtGui import QPixmap
import os, shutil

class AddFieldWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Add Field')
        self.setGeometry(150, 150, 350, 200)

        self.name_label = QLabel('Field Name:', self)
        self.name_label.move(20, 20)
        self.name_input = QLineEdit(self)
        self.name_input.move(120, 20)

        self.pic_label = QLabel('Picture:', self)
        self.pic_label.move(20, 60)
        self.pic_path = QLineEdit(self)
        self.pic_path.setReadOnly(True)
        self.pic_path.move(120, 60)
        self.pic_btn = QPushButton('Browse', self)
        self.pic_btn.move(250, 60)
        self.pic_btn.clicked.connect(self.browse_picture)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(120, 120)
        self.save_btn.clicked.connect(self.save_field)

    def browse_picture(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.pic_path.setText(file_path)

    def save_field(self):
        name = self.name_input.text()
        pic = self.pic_path.text()
        if name:
            fields_dir = 'fields'
            os.makedirs(fields_dir, exist_ok=True)

            field_folder = os.path.join(fields_dir, name)
            os.makedirs(field_folder, exist_ok=True)

            pic_dest = ""
            if pic and os.path.exists(pic):
                pic_ext = os.path.splitext(pic)[1]
                pic_dest = os.path.join(field_folder, f'picture{pic_ext}')
                shutil.copy2(pic, pic_dest)

            with open(os.path.join(field_folder, 'info.txt'), 'w', encoding='utf-8') as f:
                f.write(f"{name}|{pic}\n")
                f.write(f"Picture: {pic_dest}\n")
            self.close()
            from field_manager_window import Field_Manager
            Field_Manager.refresh_fields(self)


class ViewFieldWindow(QWidget):
    def __init__(self, field_name):
        super().__init__()
        self.setWindowTitle(f'Field: {field_name}')
        self.setGeometry(200, 200, 800, 700)
        info_path = os.path.join('fields', field_name, 'info.txt')
        pic_path = None
        info_text = ""

        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                info_text = "".join(lines)
                for line in lines:
                    if line.startswith("Picture:"):
                        pic_path = line.split("Picture:")[1].strip()
                        break

        info_label = QLabel(info_text, self)
        info_label.move(20, 20)
        info_label.resize(360, 60)

        if pic_path and os.path.exists(pic_path):
            pic_label = QLabel(self)
            pixmap = QPixmap(pic_path)
            pic_label.setPixmap(pixmap.scaled(200, 150))
            pic_label.move(100, 100)