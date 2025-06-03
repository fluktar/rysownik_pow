from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox

class SidePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.building_group = QGroupBox("Budynek")
        self.building_layout = QVBoxLayout()
        self.building_label = QLabel("Powierzchnia: - m²")
        self.building_layout.addWidget(self.building_label)
        self.building_group.setLayout(self.building_layout)
        self.layout.addWidget(self.building_group)
        self.layout.addStretch()

    def set_building_surface(self, surface):
        self.building_label.setText(f"Powierzchnia: {surface:.2f} m²")
