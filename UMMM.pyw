import os
import sys
import json
import subprocess
import shutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QIcon, QColor, QPalette
from PyQt6.QtCore import Qt

class ModManager(QWidget):
    def __init__(self):
        super().__init__()
        # --- Basic Setup ---
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(self.script_dir, "mods_folder_settings.json")
        self.dat_settings_file = os.path.join(self.script_dir, "dat_settings.json")
        self.backup_dir = os.path.join(self.script_dir, "backup")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.setWindowTitle("Umamusume Mod Manager")
        self.setGeometry(100, 100, 800, 600)

        # --- Load Settings ---
        self.settings = self.load_settings()
        self.dat_settings = self.load_dat_settings()

        # --- Auto-detect Folders ---
        self.autodetect_mods_folder()
        self.autodetect_dat_folder()

        # --- UI Setup ---
        self.set_windows11_dark_theme()
        self.init_ui()

        # --- Initial Load ---
        self.load_mods()

    def init_ui(self):
        """Initializes the main user interface layout and widgets."""
        main_layout = QVBoxLayout()

        # --- Folder Path Inputs ---
        # Mods folder
        mods_folder_layout = QHBoxLayout()
        mods_folder_layout.addWidget(QLabel("Mods Folder:"))
        self.folder_edit = QLineEdit(self.settings.get("mods_folder", ""))
        self.folder_edit.setPlaceholderText("Path to your mods folder")
        self.folder_edit.textChanged.connect(self.folder_path_changed)
        mods_folder_layout.addWidget(self.folder_edit)
        browse_mods_btn = QPushButton("Browse...")
        browse_mods_btn.clicked.connect(self.browse_mods_folder)
        mods_folder_layout.addWidget(browse_mods_btn)
        main_layout.addLayout(mods_folder_layout)

        # Dat folder
        dat_layout = QHBoxLayout()
        dat_layout.addWidget(QLabel("dat Folder:"))
        self.dat_edit = QLineEdit(self.dat_settings.get("dat_folder", ""))
        self.dat_edit.setPlaceholderText("Path to your dat folder")
        self.dat_edit.textChanged.connect(self.dat_path_changed)
        dat_layout.addWidget(self.dat_edit)
        browse_dat_btn = QPushButton("Browse...")
        browse_dat_btn.clicked.connect(self.browse_dat_folder)
        dat_layout.addWidget(browse_dat_btn)
        main_layout.addLayout(dat_layout)

        # --- Search and Refresh ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter mods by name...")
        self.search_edit.textChanged.connect(self.filter_mods)
        search_layout.addWidget(self.search_edit)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.search_edit.clear)
        search_layout.addWidget(clear_btn)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.load_mods)
        search_layout.addWidget(refresh_btn)
        main_layout.addLayout(search_layout)

        # --- Mods Table ---
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Mod Name", "Status", "Actions"])
        
        header = self.table_widget.horizontalHeader()
        # Set "Mod Name" to stretch, and other columns to fit their content
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.verticalHeader().setDefaultSectionSize(40)
        
        main_layout.addWidget(self.table_widget)
        self.setLayout(main_layout)

    def set_windows11_dark_theme(self):
        """Applies a dark theme to the application."""
        app = QApplication.instance()
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(32, 32, 32))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(120, 120, 120))
        app.setPalette(palette)

        app.setStyleSheet("""
            QWidget { font-family: "Segoe UI", Arial, sans-serif; font-size: 9pt; }
            QPushButton { background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 4px; padding: 5px 12px; min-width: 80px; }
            QPushButton:hover { background-color: #3d3d3d; border: 1px solid #4d4d4d; }
            QPushButton:pressed { background-color: #1d1d1d; }
            QLineEdit { background-color: #252525; padding: 5px; border: 1px solid #3d3d3d; border-radius: 4px; }
            QTableWidget { gridline-color: #3d3d3d; border: 1px solid #3d3d3d; }
            QHeaderView::section { background-color: #2d2d2d; padding: 5px; border: none; }
            QTableWidget::item { padding-left: 10px; }
            
            /* --- MODIFIED SCROLLBAR STYLES --- */
            QScrollBar:vertical {
                border: none;
                background: #202020; /* Matches Window color for the track */
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #0078d7; /* Blue */
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0078d7; /* Blue */
            }
            QScrollBar::handle:vertical:pressed {
                background: #0078d7; /* Blue */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar:horizontal {
                border: none;
                background: #202020; /* Matches Window color */
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #0078d7; /* Blue */
                min-width: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #0078d7; /* Blue */
            }
            QScrollBar::handle:horizontal:pressed {
                background: #0078d7; /* Blue */
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            /* --- END SCROLLBAR STYLES --- */

            QMessageBox { background-color: #202020; }
            QMessageBox QLabel { color: #f0f0f0; }
            QMessageBox QPushButton { background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 4px; padding: 5px 12px; min-width: 80px; }
            QMessageBox QPushButton:hover { background-color: #3d3d3d; border: 1px solid #4d4d4d; }
            QMessageBox QPushButton:pressed { background-color: #1d1d1d; }
        """)

    # --- Folder and Settings Logic ---

    def load_settings(self):
        """Loads mods folder settings from a JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"mods_folder": ""}
        return {"mods_folder": ""}

    def load_dat_settings(self):
        """Loads dat folder settings from a JSON file."""
        if os.path.exists(self.dat_settings_file):
            try:
                with open(self.dat_settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"dat_folder": ""}
        return {"dat_folder": ""}

    def save_settings(self):
        """Saves the current mods folder path to the settings file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def save_dat_settings(self):
        """Saves the current dat folder path to the settings file."""
        with open(self.dat_settings_file, 'w') as f:
            json.dump(self.dat_settings, f, indent=4)

    def autodetect_mods_folder(self):
        """Checks for a 'mods' folder in the script's directory."""
        local_mods_path = os.path.join(self.script_dir, 'mods')
        if os.path.isdir(local_mods_path):
            self.settings["mods_folder"] = local_mods_path
            self.save_settings()

    def autodetect_dat_folder(self):
        """Sets the default dat folder path if not already set."""
        if not self.dat_settings.get("dat_folder"):
            default_dat_path = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Cygames', 'Umamusume', 'dat')
            if os.path.isdir(default_dat_path):
                self.dat_settings["dat_folder"] = default_dat_path
                self.save_dat_settings()

    def browse_mods_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Mods Folder")
        if folder:
            self.folder_edit.setText(folder)

    def browse_dat_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select dat Folder")
        if folder:
            self.dat_edit.setText(folder)

    def folder_path_changed(self, text):
        self.settings["mods_folder"] = text
        self.save_settings()
        self.load_mods()

    def dat_path_changed(self, text):
        self.dat_settings["dat_folder"] = text
        self.save_dat_settings()
        self.load_mods()

    # --- Core Mod Logic ---

    def load_mods(self):
        """Scans the mods folder and populates the table with found mods."""
        self.table_widget.setRowCount(0)
        mods_folder = self.settings.get("mods_folder", "")

        if not os.path.isdir(mods_folder):
            if mods_folder: # Only show error if path is set but invalid
                print(f"Mods folder not found: {mods_folder}")
            return

        for mod_name in os.listdir(mods_folder):
            if os.path.isdir(os.path.join(mods_folder, mod_name)):
                self.add_mod_to_table(mod_name)
        
        self.filter_mods() # Re-apply search filter

    def add_mod_to_table(self, mod_name):
        """Adds a single mod entry to the UI table."""
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        status = self.check_mod_status(mod_name)

        # Column 0: Mod Name
        mod_name_item = QTableWidgetItem(mod_name)
        mod_name_item.setData(Qt.ItemDataRole.UserRole, mod_name) # Store mod name for actions
        mod_name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_widget.setItem(row_position, 0, mod_name_item)

        # Column 1: Status
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if status == "Active":
            status_item.setForeground(QColor("#00A36C"))  # Green
        elif status == "Inactive":
            status_item.setForeground(QColor("#C70039"))  # Red
        self.table_widget.setItem(row_position, 1, status_item)

        # Column 2: Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 15, 0)
        actions_layout.setSpacing(5)

        # Create the buttons
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(lambda _, m=mod_name: self.open_preview_image(m))

        action_btn = QPushButton("Activate" if status == "Inactive" else "Deactivate")
        if status == "Inactive":
            action_btn.clicked.connect(lambda _, m=mod_name: self.activate_mod(m))
        else:
            action_btn.clicked.connect(lambda _, m=mod_name: self.deactivate_mod(m))
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(lambda _, m=mod_name: self.open_mod_folder(m))

        # Add buttons and a stretch to align them left.
        actions_layout.addWidget(preview_btn)
        actions_layout.addWidget(action_btn)
        actions_layout.addWidget(open_folder_btn)
        actions_layout.addStretch()
        
        self.table_widget.setCellWidget(row_position, 2, actions_widget)

    def check_mod_status(self, mod_name):
        """
        Checks if a mod is active by comparing file sizes.
        A mod is 'Active' if any of its files match the size of the corresponding file in the dat folder.
        """
        mods_folder = self.settings.get("mods_folder")
        dat_folder = self.dat_settings.get("dat_folder")

        if not all([mods_folder, dat_folder, os.path.isdir(mods_folder), os.path.isdir(dat_folder)]):
            return "Unknown"

        mod_path = os.path.join(mods_folder, mod_name)
        
        # Walk through all files in the specific mod's folder
        for root, _, files in os.walk(mod_path):
            if not files: continue # Skip empty directories
            for file in files:
                # Skip preview images
                if file.lower() in ('preview.jpg', 'preview.png'):
                    continue
                
                mod_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(mod_file_path, mod_path)
                dat_file_path = os.path.join(dat_folder, relative_path)

                if os.path.exists(dat_file_path):
                    try:
                        # If mod file size matches the game file size, it's considered active
                        if os.path.getsize(mod_file_path) == os.path.getsize(dat_file_path):
                            return "Active"
                    except OSError as e:
                        print(f"Could not get size for {mod_file_path} or {dat_file_path}: {e}")
                        return "Error"
        
        return "Inactive"
    
    def get_mod_file_map(self, mod_name):
        """
        Generates a dictionary mapping relative file paths to their full paths for a given mod.
        Example: {'2R/file.dat': 'C:/.../mods/MyMod/2R/file.dat'}
        """
        file_map = {}
        mods_folder = self.settings.get("mods_folder")
        mod_path = os.path.join(mods_folder, mod_name)

        if not os.path.isdir(mod_path):
            return file_map

        for root, _, files in os.walk(mod_path):
            for file in files:
                # Skip preview images from the file map
                if file.lower() in ('preview.jpg', 'preview.png'):
                    continue
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, mod_path)
                file_map[relative_path] = full_path
        return file_map

    def activate_mod(self, mod_name):
        """Backs up original files and replaces them with modded files."""
        dat_folder = self.dat_settings.get("dat_folder")
        if not dat_folder or not os.path.isdir(dat_folder):
            QMessageBox.warning(self, "Error", "The 'dat' folder path is not valid. Please set it correctly.")
            return

        mod_files = self.get_mod_file_map(mod_name)
        if not mod_files:
            QMessageBox.warning(self, "Error", f"Mod '{mod_name}' contains no files.")
            return

        try:
            for rel_path, mod_file_path in mod_files.items():
                original_file_path = os.path.join(dat_folder, rel_path)
                backup_file_path = os.path.join(self.backup_dir, rel_path)

                if os.path.exists(original_file_path):
                    # Create backup directory and copy original file
                    os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                    shutil.copy2(original_file_path, backup_file_path)

                    # Copy modded file to dat folder
                    shutil.copy2(mod_file_path, original_file_path)
                else:
                    print(f"Original file not found, skipping backup: {original_file_path}")
                    # Still copy the mod file over
                    os.makedirs(os.path.dirname(original_file_path), exist_ok=True)
                    shutil.copy2(mod_file_path, original_file_path)


            QMessageBox.information(self, "Success", f"Mod '{mod_name}' activated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Activation Failed", f"An error occurred: {e}")
        
        # Store the current scroll position
        scrollbar = self.table_widget.verticalScrollBar()
        scroll_position = scrollbar.value()

        self.load_mods()

        # Restore the scroll position
        scrollbar.setValue(scroll_position)

    def deactivate_mod(self, mod_name):
        """Restores original files from the backup folder."""
        dat_folder = self.dat_settings.get("dat_folder")
        if not dat_folder or not os.path.isdir(dat_folder):
            QMessageBox.warning(self, "Error", "The 'dat' folder path is not valid. Please set it correctly.")
            return

        mod_files = self.get_mod_file_map(mod_name)
        if not mod_files:
            # This case is unlikely if deactivating, but good to have
            QMessageBox.warning(self, "Error", f"Could not find files for mod '{mod_name}' to deactivate.")
            return

        try:
            for rel_path in mod_files.keys():
                backup_file_path = os.path.join(self.backup_dir, rel_path)
                original_file_path = os.path.join(dat_folder, rel_path)

                if os.path.exists(backup_file_path):
                    # Restore original file from backup
                    shutil.copy2(backup_file_path, original_file_path)
                    # Remove the backed-up file
                    os.remove(backup_file_path)
                else:
                    print(f"Backup not found for {rel_path}. The original file cannot be restored.")
            
            # [MODIFIED] The empty directory cleanup loop has been removed to prevent conflicts.

            QMessageBox.information(self, "Success", f"Mod '{mod_name}' deactivated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Deactivation Failed", f"An error occurred: {e}")
        
        # Store the current scroll position
        scrollbar = self.table_widget.verticalScrollBar()
        scroll_position = scrollbar.value()

        self.load_mods()

        # Restore the scroll position
        scrollbar.setValue(scroll_position)

    def open_preview_image(self, mod_name):
        """Looks for and opens a preview image for the selected mod."""
        mods_folder = self.settings.get("mods_folder")
        if not mods_folder:
            QMessageBox.warning(self, "Error", "Mods folder path is not set.")
            return
        
        mod_path = os.path.join(mods_folder, mod_name)
        if not os.path.isdir(mod_path):
            QMessageBox.warning(self, "Error", f"Mod folder not found: {mod_path}")
            return

        preview_jpg = os.path.join(mod_path, "preview.jpg")
        preview_png = os.path.join(mod_path, "preview.png")
        
        image_path_to_open = None
        if os.path.exists(preview_jpg):
            image_path_to_open = preview_jpg
        elif os.path.exists(preview_png):
            image_path_to_open = preview_png

        if image_path_to_open:
            try:
                if sys.platform == "win32":
                    os.startfile(image_path_to_open)
                elif sys.platform == "darwin": # macOS
                    subprocess.run(["open", image_path_to_open])
                else: # linux
                    subprocess.run(["xdg-open", image_path_to_open])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open preview image: {e}")
        else:
            QMessageBox.information(self, "No Preview", f"No 'preview.jpg' or 'preview.png' found for mod '{mod_name}'.")

    def open_mod_folder(self, mod_name):
        """Opens the selected mod's folder in the file explorer."""
        mods_folder = self.settings.get("mods_folder")
        if not mods_folder:
            return
        
        path = os.path.join(mods_folder, mod_name)
        if os.path.isdir(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin": # macOS
                    subprocess.run(["open", path])
                else: # linux
                    subprocess.run(["xdg-open", path])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open folder: {e}")

    def filter_mods(self):
        """Hides or shows table rows based on the search text."""
        search_text = self.search_edit.text().lower()
        for row in range(self.table_widget.rowCount()):
            mod_name_item = self.table_widget.item(row, 0)
            if mod_name_item:
                is_match = search_text in mod_name_item.text().lower()
                self.table_widget.setRowHidden(row, not is_match)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set App Icon
    icon_path = "icon.png"
    if getattr(sys, 'frozen', False): # If running as a bundled exe
        icon_path = os.path.join(sys._MEIPASS, icon_path)
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    manager = ModManager()
    manager.show()
    sys.exit(app.exec())