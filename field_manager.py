from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox
from PyQt6.QtGui import QPixmap
import os, shutil
from field_logs import ViewLogsWindow

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
    def __init__(self, field_name, parent=None, main_window=None):
        super().__init__()

        self.field_name = field_name
        self.parent = parent
        self.main_window = main_window

        self.setWindowTitle(f'Field: {field_name}')
        self.setGeometry(200, 200, 1000, 600)
        info_path = os.path.join('fields', field_name, 'info.txt')
        pic_path = None
        info_text = ""

        #delete field
        remove_field_btn = QPushButton('Istrinti Lauka', self)
        remove_field_btn.move(340, 70)
        remove_field_btn.clicked.connect(self.remove_field)


        # Add this after the other buttons in ViewFieldWindow.__init__()
        self.view_logs_btn = QPushButton('View Logs', self)
        self.view_logs_btn.move(340, 90)
        self.view_logs_btn.clicked.connect(self.view_logs)

        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                info_text = "".join(lines)
                for line in lines:
                    if line.startswith("Picture:"):
                        pic_filename = line.split("Picture:")[1].strip()
                        if pic_filename:
                            pic_path = os.path.join('fields', field_name, pic_filename)
                        else:
                            pic_path = None
                        break

        info_label = QLabel(info_text, self)
        info_label.move(20, 20)
        info_label.resize(360, 60)

        if pic_path and os.path.exists(pic_path):
            if not os.path.isabs(pic_path):
                pic_path = os.path.join(os.getcwd(), pic_path)
            if os.path.exists(pic_path):
                pic_label = QLabel(self)
                pixmap = QPixmap(pic_path)
                pic_label.setPixmap(pixmap.scaled(300, 250))
                pic_label.move(50, 150)

        self.field_name = field_name

        self.edit_field_btn = QPushButton('Edit', self)
        self.edit_field_btn.move(340, 40)
        self.edit_field_btn.clicked.connect(self.edit_field)

        self.back_btn = QPushButton('Back', self)
        self.back_btn.move(340, 20)
        self.back_btn.clicked.connect(self.go_back)

        self.parent = parent

    def view_logs(self):
        self.logs_window = ViewLogsWindow(self.field_name, self)
        self.logs_window.show()

    def remove_field(self):
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the field '{self.field_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            fields_dir = 'fields'
            field_folder = os.path.join(fields_dir, self.field_name)

            if os.path.exists(field_folder) and os.path.isdir(field_folder):
                try:
                    shutil.rmtree(field_folder)  # deletes folder + picture
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not delete field: {e}")
                    return

            self.close()
            if self.main_window:
                self.main_window.refresh_fields()
                self.main_window.show()

    def go_back(self):
        self.close()
        if self.main_window:
            self.main_window.show()
            self.main_window.refresh_fields()  
            

    def edit_field(self):
        edit_window = EditFieldWindow(self.field_name, parent=self, main_window=self.main_window)
        edit_window.exec()

        # After editing, reload the updated field name
        new_field_name = edit_window.name_input.text().strip()
        self.close()

        if new_field_name:
            new_view_window = ViewFieldWindow(new_field_name, parent=None, main_window=self.main_window)
            new_view_window.show()

class EditFieldWindow(QDialog):
    def __init__(self, field_name, parent=None, main_window=None):
        super().__init__()

        self.setWindowTitle(f'Field: {field_name}')
        self.setGeometry(200, 200, 800, 700)

        self.field_name = field_name #store original name
        self.parent = parent
        self.main_window = main_window

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

            # Load previous picture filename from info.txt
            prev_pic_filename = ""
            info_path = os.path.join(field_folder, 'info.txt')
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("Picture:"):
                            prev_pic_filename = line.replace("Picture:", "").strip()
                            break

            prev_pic_path = os.path.join(field_folder, prev_pic_filename) if prev_pic_filename else ""

            # Handle new picture
            pic_filename = prev_pic_filename
            if pic and os.path.exists(pic) and os.path.abspath(pic) != os.path.abspath(prev_pic_path):
                # Delete old picture if different
                if prev_pic_path and os.path.exists(prev_pic_path):
                    try:
                        os.remove(prev_pic_path)
                    except Exception:
                        pass
                # Copy new picture into folder
                pic_ext = os.path.splitext(pic)[1]
                pic_filename = f'picture{pic_ext}'
                pic_dest = os.path.join(field_folder, pic_filename)
                shutil.copy2(pic, pic_dest)

            elif renamed and prev_pic_path and os.path.exists(prev_pic_path):
                # If only renamed, move old picture to new folder
                pic_ext = os.path.splitext(prev_pic_path)[1]
                new_pic_dest = os.path.join(field_folder, f'picture{pic_ext}')
                if prev_pic_path != new_pic_dest:
                    shutil.move(prev_pic_path, new_pic_dest)
                pic_filename = os.path.basename(new_pic_dest)

            # Save updated info
            with open(os.path.join(field_folder, 'info.txt'), 'w', encoding='utf-8') as f:
                f.write(f"{name}\n")
                f.write(f"Hectares: {hectares}\n")
                f.write(f"Type: {field_type}\n")
                f.write(f"Picture: {pic_filename}\n")

            self.close()
            if self.main_window:
                self.main_window.refresh_fields()

                
