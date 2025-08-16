from PyQt6.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox
from PyQt6.QtGui import QPixmap
import os, shutil

class AddFieldWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Add Field')
        self.setGeometry(150, 150, 350, 300)

        self.name_label = QLabel('Field Name:', self)
        self.name_label.move(20, 20)
        self.name_input = QLineEdit(self)
        self.name_input.move(120, 20)


        self.hectares_label = QLabel('Hectares:', self)
        self.hectares_label.move(20, 60)
        self.hectares_input = QLineEdit(self)
        self.hectares_input.move(120, 60)

        self.field_type = QComboBox(self)
        self.field_type.addItems(['Z. mieziai', 'kvieciai', 'Z. kvieciai', 'Rapsas', 'Z. rapsas'])
        self.field_type.move(120, 100)

        self.pic_label = QLabel('Picture:', self)
        self.pic_label.move(20, 140)
        self.pic_path = QLineEdit(self)
        self.pic_path.setReadOnly(True)
        self.pic_path.move(120, 140)

        self.pic_btn = QPushButton('Browse', self)
        self.pic_btn.move(250, 140)
        self.pic_btn.clicked.connect(self.browse_picture)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(120, 180)
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
                f.write(f"{name}\n")
                f.write(f"Hectares: {float(self.hectares_input.text())}\n")
                f.write(f"Type: {self.field_type.currentText()}\n")
                f.write(f"Picture: {pic_dest}\n")
            self.close()
            


class ViewFieldWindow(QWidget):
    def __init__(self, field_name, parent=None):
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

        self.field_name = field_name

        self.edit_field_btn = QPushButton('Edit', self)
        self.edit_field_btn.move(340, 180)
        self.edit_field_btn.clicked.connect(self.edit_field)

        self.back_btn = QPushButton('Back', self)
        self.back_btn.move(340, 220)
        self.back_btn.clicked.connect(self.go_back)

        self.parent = parent

    def go_back(self):
        self.close()
        
        from field_manager_window import Field_Manager
        main_window = Field_Manager()
        main_window.show()
            

    def edit_field(self):
        edit_window = EditFieldWindow(self.field_name, parent=self)
        edit_window.exec()
        # After editing, get the new field name from the edit window
        new_field_name = edit_window.name_input.text().strip()
        self.close()  # Close the old view window
        # Open a new view window with the updated field name
        new_view_window = ViewFieldWindow(new_field_name)
        new_view_window.show()

class EditFieldWindow(QDialog):
    def __init__(self, field_name, parent=None):
        super().__init__()

        self.setWindowTitle(f'Field: {field_name}')
        self.setGeometry(200, 200, 800, 700)

        self.field_name = field_name #store original name
        self.parent = parent

        self.name_label = QLabel('Field Name:', self)
        self.name_label.move(20, 20)
        self.name_input = QLineEdit(self)
        self.name_input.move(120, 20)


        self.hectares_label = QLabel('Hectares:', self)
        self.hectares_label.move(20, 60)
        self.hectares_input = QLineEdit(self)
        self.hectares_input.move(120, 60)

        self.field_type = QComboBox(self)
        self.field_type.addItems(['', 'Z. mieziai', 'kvieciai', 'Z. kvieciai', 'Rapsas', 'Z. rapsas'])
        self.field_type.move(120, 100)

        self.pic_label = QLabel('Picture:', self)
        self.pic_label.move(20, 140)
        self.pic_path = QLineEdit(self)
        self.pic_path.setReadOnly(True)
        self.pic_path.move(120, 140)

        self.pic_btn = QPushButton('Browse', self)
        self.pic_btn.move(250, 140)
        self.pic_btn.clicked.connect(self.browse_picture)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(120, 180)
        self.save_btn.clicked.connect(self.edit_save_field)

        # Load existing info
        info_path = os.path.join('fields', field_name, 'info.txt')
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    self.name_input.setText(lines[0].strip())
                if len(lines) > 1:
                    self.hectares_input.setText(lines[1].replace("Hectares:", "").strip())
                if len(lines) > 2:
                    self.field_type.setCurrentText(lines[2].replace("Type:", "").strip())
                if len(lines) > 3:
                    self.pic_path.setText(lines[3].replace("Picture:", "").strip())

    def browse_picture(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.pic_path.setText(file_path)    


    def edit_save_field(self):
        name = self.name_input.text().strip()
        hectares = self.hectares_input.text().strip()
        field_type = self.field_type.currentText()
        pic = self.pic_path.text().strip()

        if name:
            fields_dir = 'fields'
            os.makedirs(fields_dir, exist_ok=True)

            # If field name changed, rename folder
            old_folder = os.path.join(fields_dir, self.field_name)
            new_folder = os.path.join(fields_dir, name)
            renamed = False 
            if old_folder != new_folder and os.path.exists(old_folder):
                os.rename(old_folder, new_folder)
                renamed = True

            field_folder = new_folder
            os.makedirs(field_folder, exist_ok=True)

            # Load previous picture path from info.txt
            prev_pic_dest = ""
            info_path = os.path.join(field_folder, 'info.txt')
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("Picture:"):
                            prev_pic_dest = line.replace("Picture:", "").strip()
                            break

            # Determine if the picture was changed
            pic_dest = prev_pic_dest
            if pic and os.path.exists(pic) and (os.path.abspath(pic) != os.path.abspath(prev_pic_dest)):
                # Remove previous picture if it exists and is different
                if prev_pic_dest and os.path.exists(prev_pic_dest):
                    try:
                        os.remove(prev_pic_dest)
                    except Exception:
                        pass
                pic_ext = os.path.splitext(pic)[1]
                pic_dest = os.path.join(field_folder, f'picture{pic_ext}')
                shutil.copy2(pic, pic_dest)
            elif renamed and prev_pic_dest and os.path.exists(prev_pic_dest):
                # Move previous picture to new folder if field was renamed and picture not changed
                pic_ext = os.path.splitext(prev_pic_dest)[1]
                new_pic_dest = os.path.join(field_folder, f'picture{pic_ext}')
                shutil.move(prev_pic_dest, new_pic_dest)
                pic_dest = new_pic_dest

            with open(os.path.join(field_folder, 'info.txt'), 'w', encoding='utf-8') as f:
                f.write(f"{name}\n")
                f.write(f"Hectares: {hectares}\n")
                f.write(f"Type: {field_type}\n")
                f.write(f"Picture: {pic_dest}\n")

            self.close()

            self.view_field_window = ViewFieldWindow(name, parent=self)
            self.view_field_window.show()
