from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QListWidget, QListWidgetItem

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
        self.najemcy_list = QListWidget()
        self.wspolne_list = QListWidget()
        self.layout.addWidget(QLabel("Najemcy:"))
        self.layout.addWidget(self.najemcy_list)
        self.layout.addWidget(QLabel("Powierzchnie wspólne:"))
        self.layout.addWidget(self.wspolne_list)
        self.layout.addStretch()

    def set_building_surface(self, surface):
        self.building_label.setText(f"Powierzchnia: {surface:.2f} m²")

    def set_seeds(self, seeds):
        self.najemcy_list.clear()
        self.wspolne_list.clear()
        for seed in seeds:
            item = QListWidgetItem(f"{seed['type']} | {seed['area']:.2f} m²")
            if seed['type'] == 'Najemca':
                self.najemcy_list.addItem(item)
            else:
                self.wspolne_list.addItem(item)
