from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QListWidget, QListWidgetItem, QInputDialog

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
            if seed['type'] == 'Najemca':
                item = QListWidgetItem(f"{seed.get('name', 'Najemca')} | {seed['area']:.2f} m²")
                self.najemcy_list.addItem(item)
            else:
                item = QListWidgetItem(f"Powierzchnia wspólna | {seed['area']:.2f} m²")
                self.wspolne_list.addItem(item)
        # Edycja nazwy najemcy po dwukliku
        self.najemcy_list.itemDoubleClicked.connect(self.edit_tenant_name)

    def edit_tenant_name(self, item):
        idx = self.najemcy_list.row(item)
        name, ok = QInputDialog.getText(self, 'Zmień nazwę najemcy', 'Nowa nazwa:')
        if ok and name:
            # Zmień nazwę w obiekcie TenantArea
            from gui.gui_canvas import Canvas
            canvas: Canvas = self.parent().canvas if hasattr(self.parent(), 'canvas') else None
            if canvas:
                tenant_objs = [o for o in canvas.objects if o.__class__.__name__ == 'TenantArea']
                if 0 <= idx < len(tenant_objs):
                    tenant_objs[idx].name = name
                    item.setText(f"{name} | {tenant_objs[idx].area(canvas.scale):.2f} m²")
