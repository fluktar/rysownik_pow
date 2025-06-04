import json
from PySide6.QtWidgets import QMainWindow, QDockWidget, QToolBar, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .gui_canvas import Canvas
from .gui_side_panel import SidePanel

class AddAreaDialog(QDialog):
    def __init__(self, parent=None, default_type=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj powierzchnię")
        layout = QVBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Powierzchnia wspólna", "Najemca"])
        if default_type:
            idx = self.type_combo.findText(default_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        layout.addWidget(QLabel("Typ powierzchni:"))
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("Powierzchnia (m²):"))
        self.area_edit = QLineEdit()
        layout.addWidget(self.area_edit)
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Anuluj")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.setLayout(layout)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        return self.type_combo.currentText(), self.area_edit.text()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rysownik powierzchni - Zarządca")
        self.resize(1200, 800)

        # Toolbar
        toolbar = QToolBar("Narzędzia", self)
        self.addToolBar(toolbar)
        self.action_building = QAction("Budynek", self)
        self.action_common = QAction("Powierzchnia wspólna", self)
        self.action_tenant = QAction("Najemca", self)
        self.action_zoom_in = QAction("Zoom +", self)
        self.action_zoom_out = QAction("Zoom -", self)
        toolbar.addAction(self.action_building)
        toolbar.addAction(self.action_common)
        toolbar.addAction(self.action_tenant)
        toolbar.addSeparator()
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_building.triggered.connect(lambda: self.set_draw_mode('building'))
        self.action_common.triggered.connect(lambda: self.set_draw_mode('common'))
        self.action_tenant.triggered.connect(lambda: self.set_draw_mode('tenant'))

        # Menu Plik
        menu = self.menuBar().addMenu("Plik")
        action_save = QAction("Zapisz projekt", self)
        action_open = QAction("Otwórz projekt", self)
        menu.addAction(action_save)
        menu.addAction(action_open)
        action_save.triggered.connect(self.save_project)
        action_open.triggered.connect(self.open_project)

        # Canvas (centralny widget)
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.add_shortcuts_menu(self.menuBar())

        # Panel boczny
        self.side_panel = SidePanel(self)
        dock = QDockWidget("Panel boczny", self)
        dock.setWidget(self.side_panel)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Połącz canvas z panelem bocznym
        self.canvas.on_building_closed = self.side_panel.set_building_surface
        self.canvas.on_seeds_changed = self.side_panel.set_seeds
        self.side_panel.set_seeds(self.canvas.get_all_seeds())

    def set_draw_mode(self, mode):
        self.canvas.set_draw_mode(mode)

    def zoom_in(self):
        self.canvas.zoom_in()

    def zoom_out(self):
        self.canvas.zoom_out()

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz projekt", "", "Pliki JSON (*.json)")
        if path:
            data = self.canvas.to_dict()
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "Błąd zapisu", str(e))

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Otwórz projekt", "", "Pliki JSON (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.canvas.from_dict(data)
            except Exception as e:
                QMessageBox.critical(self, "Błąd odczytu", str(e))
