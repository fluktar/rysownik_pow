from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QListWidget, QListWidgetItem, QInputDialog, QColorDialog
from PySide6.QtGui import QColor, QBrush, QPixmap, QPainter
from PySide6.QtCore import Qt, QTimer, QPoint

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
        self.wspolne_list.currentRowChanged.connect(self.highlight_common)
        # Usuwamy bezpośrednie podpięcie itemClicked do zmiany koloru
        # self.najemcy_list.itemClicked.connect(self._edit_tenant_color)
        # self.wspolne_list.itemClicked.connect(self._edit_common_color)
        self.najemcy_list.viewport().installEventFilter(self)
        self.wspolne_list.viewport().installEventFilter(self)
        self._highlight_timer = QTimer(self)
        self._highlight_timer.timeout.connect(self._toggle_highlight)
        self._highlight_state = False
        self._highlighted_idx = None
        self.najemcy_list.itemDoubleClicked.connect(self.edit_tenant_area)

    def set_building_surface(self, surface):
        self.building_label.setText(f"Powierzchnia: {surface:.2f} m²")

    def _get_canvas(self):
        # Szukaj canvas w hierarchii rodziców
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'canvas'):
                return parent.canvas
            parent = parent.parent() if hasattr(parent, 'parent') else None
        return None

    def setIconColor(self, item, color):
        pix = self._colored_square_pixmap(color)
        item.setIcon(pix)

    def set_tenants(self, tenants):
        self.najemcy_list.clear()
        try:
            self.najemcy_list.itemDoubleClicked.disconnect(self.edit_tenant_name)
        except RuntimeError:
            pass
        canvas = self._get_canvas()
        scale = canvas.scale if canvas else 1.0
        for tenant in tenants:
            item = QListWidgetItem(f"{tenant.name} | {tenant.area(scale):.2f} m²")
            self.setIconColor(item, tenant.color)
            self.najemcy_list.addItem(item)
        if not hasattr(self, '_tenant_signal_connected') or not self._tenant_signal_connected:
            self.najemcy_list.itemDoubleClicked.connect(self.edit_tenant_name)
            self._tenant_signal_connected = True

    def set_common_areas(self, common_areas):
        self.wspolne_list.clear()
        
        canvas = self._get_canvas()
        scale = canvas.scale if canvas else 1.0
        for area in common_areas:
            item = QListWidgetItem(f"Powierzchnia wspólna | {area.area(scale):.2f} m²")
            self.setIconColor(item, area.color)
            self.wspolne_list.addItem(item)

    def set_seeds(self, seeds):
        # ZACHOWANE DLA KOMPATYBILNOŚCI, NIE UŻYWAJ W NOWYM KODZIE
        tenants = []
        commons = []
        from model.tenant_area import TenantArea
        from model.common_area import CommonArea
        for seed in seeds:
            if seed['type'] == 'Najemca':
                color_val = seed.get('color', [0,200,0,120])
                if isinstance(color_val, QColor):
                    color = color_val
                elif isinstance(color_val, (list, tuple)):
                    color = QColor(*color_val)
                else:
                    # Jeśli to już QColor, nie rozpakowuj
                    color = QColor(color_val)
                t = TenantArea([QPoint(pt.x(), pt.y()) if hasattr(pt, 'x') else QPoint(*pt) for pt in seed['points']], color, seed.get('name', 'Najemca'))
                tenants.append(t)
            elif seed['type'] == 'Powierzchnia wspólna':
                c = CommonArea([QPoint(pt.x(), pt.y()) if hasattr(pt, 'x') else QPoint(*pt) for pt in seed['points']])
                commons.append(c)
        self.set_tenants(tenants)
        self.set_common_areas(commons)

    def edit_tenant_name(self, item):
        idx = self.najemcy_list.row(item)
        name, ok = QInputDialog.getText(self, 'Zmień nazwę najemcy', 'Nowa nazwa:')
        if ok and name:
            from gui.gui_canvas import Canvas
            canvas: Canvas = self._get_canvas()
            if canvas:
                tenant_objs = [o for o in canvas.objects if o.__class__.__name__ == 'TenantArea']
                if 0 <= idx < len(tenant_objs):
                    tenant_objs[idx].name = name
                    item.setText(f"{name} | {tenant_objs[idx].area(canvas.scale)::.2f} m²")

    def edit_tenant_area(self, item):
        idx = self.najemcy_list.row(item)
        canvas = self._get_canvas()
        if canvas:
            tenant_objs = [o for o in canvas.objects if o.__class__.__name__ == 'TenantArea']
            if 0 <= idx < len(tenant_objs):
                current = tenant_objs[idx].desired_area or tenant_objs[idx].area(canvas.scale)
                # Poprawne wywołanie getDouble bez min/max jako keyword
                val, ok = QInputDialog.getDouble(self, 'Zmień powierzchnię najemcy', 'Nowa powierzchnia (m²):', current, 1.0, 99999.0, 2)
                if ok:
                    tenant_objs[idx].desired_area = val
                    # Automatyczne rozpychanie
                    building = next((o for o in canvas.objects if o.__class__.__name__ == 'Building'), None)
                    others = [o for o in canvas.objects if o is not tenant_objs[idx]]
                    tenant_objs[idx].auto_expand_to_area(building, others, scale=canvas.scale)
                    canvas.update()

    def highlight_object(self, idx, obj_type='tenant'):
        """Mruganie dowolnego obiektu: najemca, powierzchnia wspólna, budynek."""
        from gui.gui_canvas import Canvas
        canvas: Canvas = self._get_canvas()
        self._highlighted_idx = idx
        self._highlighted_type = obj_type
        if idx >= 0 and canvas:
            self._highlight_state = True
            self._highlight_timer.start(400)
            canvas.set_highlighted_object(idx, obj_type)
        else:
            self._highlight_timer.stop()
            if canvas:
                canvas.set_highlighted_object(None, None)

    def _toggle_highlight(self):
        from gui.gui_canvas import Canvas
        canvas: Canvas = self._get_canvas()
        if canvas and self._highlighted_idx is not None and self._highlighted_idx >= 0:
            self._highlight_state = not self._highlight_state
            canvas.set_highlighted_object(self._highlighted_idx if self._highlight_state else None, self._highlighted_type)
        else:
            self._highlight_timer.stop()
            if canvas:
                canvas.set_highlighted_object(None, None)

    def highlight_tenant(self, idx):
        self.highlight_object(idx, obj_type='tenant')

    def highlight_common(self, idx):
        self.highlight_object(idx, obj_type='common')

    def _colored_square_pixmap(self, color):
        pix = QPixmap(16, 16)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(2, 2, 12, 12)
        painter.end()
        return pix

    def _edit_tenant_color(self, item):
        idx = self.najemcy_list.row(item)
        canvas = self._get_canvas()
        if canvas:
            tenant_objs = [o for o in canvas.objects if o.__class__.__name__ == 'TenantArea']
            if 0 <= idx < len(tenant_objs):
                color = QColorDialog.getColor(tenant_objs[idx].color, self, 'Wybierz kolor najemcy')
                if color.isValid():
                    tenant_objs[idx].color = color
                    self.setIconColor(item, color)
                    canvas.update()

    def _edit_common_color(self, item):
        idx = self.wspolne_list.row(item)
        canvas = self._get_canvas()
        if canvas:
            common_objs = [o for o in canvas.objects if o.__class__.__name__ == 'CommonArea']
            if 0 <= idx < len(common_objs):
                color = QColorDialog.getColor(common_objs[idx].color, self, 'Wybierz kolor powierzchni wspólnej')
                if color.isValid():
                    common_objs[idx].color = color
                    self.setIconColor(item, color)
                    canvas.update()

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.MouseButtonPress:
            pos = event.pos()
            if obj is self.najemcy_list.viewport():
                idx = self.najemcy_list.indexAt(pos).row()
                if idx >= 0:
                    rect = self.najemcy_list.visualItemRect(self.najemcy_list.item(idx))
                    # Kwadracik jest po lewej, 0-20px
                    if pos.x() - rect.x() < 20:
                        self._edit_tenant_color(self.najemcy_list.item(idx))
                        return True
            elif obj is self.wspolne_list.viewport():
                idx = self.wspolne_list.indexAt(pos).row()
                if idx >= 0:
                    rect = self.wspolne_list.visualItemRect(self.wspolne_list.item(idx))
                    if pos.x() - rect.x() < 20:
                        self._edit_common_color(self.wspolne_list.item(idx))
                        return True
        return super().eventFilter(obj, event)
