from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QListWidget, QListWidgetItem, QInputDialog
from PySide6.QtGui import QColor, QBrush, QPixmap, QPainter
from PySide6.QtCore import Qt, QTimer

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
        self.najemcy_list.currentRowChanged.connect(self.highlight_tenant)
        self._highlight_timer = QTimer(self)
        self._highlight_timer.timeout.connect(self._toggle_highlight)
        self._highlight_state = False
        self._highlighted_idx = None

    def set_building_surface(self, surface):
        self.building_label.setText(f"Powierzchnia: {surface:.2f} m²")

    def set_seeds(self, seeds):
        self.najemcy_list.clear()
        self.wspolne_list.clear()
        # Odłącz sygnał tylko jeśli był już podłączony
        try:
            self.najemcy_list.itemDoubleClicked.disconnect(self.edit_tenant_name)
        except (TypeError, RuntimeError):
            pass
        for seed in seeds:
            if seed['type'] == 'Najemca':
                item = QListWidgetItem(f"{seed.get('name', 'Najemca')} | {seed['area']:.2f} m²")
                # Dodaj kolorowy kwadracik
                color_val = seed.get('color', [0,200,0,120])
                if isinstance(color_val, QColor):
                    color = color_val
                else:
                    color = QColor(*color_val)
                pix = self._colored_square_pixmap(color)
                item.setIcon(pix)
                self.najemcy_list.addItem(item)
            else:
                item = QListWidgetItem(f"Powierzchnia wspólna | {seed['area']:.2f} m²")
                self.wspolne_list.addItem(item)
        # Podłącz sygnał tylko raz
        if not hasattr(self, '_tenant_signal_connected') or not self._tenant_signal_connected:
            self.najemcy_list.itemDoubleClicked.connect(self.edit_tenant_name)
            self._tenant_signal_connected = True

    def edit_tenant_name(self, item):
        idx = self.najemcy_list.row(item)
        name, ok = QInputDialog.getText(self, 'Zmień nazwę najemcy', 'Nowa nazwa:')
        if ok and name:
            from gui.gui_canvas import Canvas
            canvas: Canvas = self.parent().canvas if hasattr(self.parent(), 'canvas') else None
            if canvas:
                tenant_objs = [o for o in canvas.objects if o.__class__.__name__ == 'TenantArea']
                if 0 <= idx < len(tenant_objs):
                    tenant_objs[idx].name = name
                    item.setText(f"{name} | {tenant_objs[idx].area(canvas.scale):.2f} m²")

    def highlight_tenant(self, idx):
        from gui.gui_canvas import Canvas
        canvas: Canvas = self.parent().canvas if hasattr(self.parent(), 'canvas') else None
        self._highlighted_idx = idx
        if idx >= 0 and canvas:
            self._highlight_state = True
            self._highlight_timer.start(400)  # mruganie co 400ms
            canvas.set_highlighted_tenant(idx)
        else:
            self._highlight_timer.stop()
            if canvas:
                canvas.set_highlighted_tenant(None)

    def _toggle_highlight(self):
        from gui.gui_canvas import Canvas
        canvas: Canvas = self.parent().canvas if hasattr(self.parent(), 'canvas') else None
        if canvas and self._highlighted_idx is not None and self._highlighted_idx >= 0:
            self._highlight_state = not self._highlight_state
            canvas.set_highlighted_tenant(self._highlighted_idx if self._highlight_state else None)
        else:
            self._highlight_timer.stop()
            if canvas:
                canvas.set_highlighted_tenant(None)

    def _colored_square_pixmap(self, color):
        pix = QPixmap(16, 16)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(2, 2, 12, 12)
        painter.end()
        return pix
