from PySide6.QtWidgets import QWidget, QColorDialog, QInputDialog
from PySide6.QtGui import QPainter, QPen, QColor, QMouseEvent, QPainterPath, QPolygon
from PySide6.QtCore import Qt, QPoint
import math
from model.building import Building
from model.tenant_area import TenantArea
from model.common_area import CommonArea
from model.area_object import AreaObject

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.objects = []  # lista wszystkich obiektów (budynek, najemcy, pow. wspólne)
        self.scale = 0.1
        self.zoom = 1.0
        self.selected_obj = None
        self.selected_vertex = None
        self.drag_offset = QPoint(0,0)
        self.draw_mode = 'building'  # 'building', 'common', 'tenant'
        self.temp_points = []
        self.on_building_closed = None
        self.on_seeds_changed = None
        self.setMouseTracking(True)
        self.highlighted_tenant_idx = None

    def set_zoom(self, zoom):
        self.zoom = zoom
        self.update()

    def zoom_in(self):
        self.zoom *= 1.2
        self.update()

    def zoom_out(self):
        self.zoom /= 1.2
        self.update()

    def set_draw_mode(self, mode):
        self.draw_mode = mode
        self.temp_points = []
        self.selected_obj = None
        self.selected_vertex = None
        self.update()

    def set_highlighted_tenant(self, idx):
        self.highlighted_tenant_idx = idx
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        point = (event.position() / self.zoom).toPoint()
        # Edycja wierzchołka lub przesuwanie istniejącego obiektu
        for obj in reversed(self.objects):
            idx = obj.hit_vertex(point)
            if idx is not None:
                self.selected_obj = obj
                self.selected_vertex = idx
                self.drag_offset = obj.points[idx] - point
                return
            if obj.hit_test(point):
                self.selected_obj = obj
                self.selected_vertex = None
                self.drag_offset = obj.points[0] - point
                return
        # Rysowanie nowego obiektu
        if self.draw_mode == 'building' and not any(isinstance(o, Building) for o in self.objects):
            if self.temp_points and (point - self.temp_points[0]).manhattanLength() < 10 and len(self.temp_points) > 2:
                self.temp_points.append(self.temp_points[0])
                self.objects.append(Building(list(self.temp_points)))
                if self.on_building_closed:
                    self.on_building_closed(self.objects[-1].area(self.scale))
                self.temp_points = []
                self.update()
            else:
                self.temp_points.append(point)
                self.update()
        elif self.draw_mode == 'common':
            if self.temp_points and (point - self.temp_points[0]).manhattanLength() < 10 and len(self.temp_points) > 2:
                self.temp_points.append(self.temp_points[0])
                self.objects.append(CommonArea(list(self.temp_points)))
                self.temp_points = []
                if self.on_seeds_changed:
                    self.on_seeds_changed(self.get_all_seeds())
                self.update()
            else:
                self.temp_points.append(point)
                self.update()
        elif self.draw_mode == 'tenant':
            if self.temp_points and (point - self.temp_points[0]).manhattanLength() < 10 and len(self.temp_points) > 2:
                self.temp_points.append(self.temp_points[0])
                # Dialog wyboru koloru i nazwy
                color = QColorDialog.getColor(QColor(0,200,0,120), self, 'Wybierz kolor najemcy')
                if not color.isValid():
                    color = QColor(0,200,0,120)
                name, ok = QInputDialog.getText(self, 'Nazwa najemcy', 'Podaj nazwę najemcy:')
                if not ok or not name:
                    name = 'Najemca'
                self.objects.append(TenantArea(list(self.temp_points), color, name))
                self.temp_points = []
                if self.on_seeds_changed:
                    self.on_seeds_changed(self.get_all_seeds())
                self.update()
            else:
                self.temp_points.append(point)
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        point = (event.position() / self.zoom).toPoint()
        if self.selected_obj and self.selected_vertex is not None:
            self.selected_obj.move_vertex(self.selected_vertex, point)
            if self.on_seeds_changed:
                self.on_seeds_changed(self.get_all_seeds())
            self.update()
        elif self.selected_obj:
            delta = point - self.selected_obj.points[0]
            self.selected_obj.move(delta)
            # Jeśli przesuwamy budynek, przesuwamy wszystkie inne obiekty
            if isinstance(self.selected_obj, Building):
                for obj in self.objects:
                    if obj is not self.selected_obj:
                        obj.move(delta)
            if self.on_seeds_changed:
                self.on_seeds_changed(self.get_all_seeds())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.selected_obj = None
        self.selected_vertex = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.zoom, self.zoom)
        tenant_idx = 0
        for obj in self.objects:
            highlight = (obj is self.selected_obj)
            # Mruganie najemcy
            if obj.__class__.__name__ == 'TenantArea' and self.highlighted_tenant_idx is not None:
                if tenant_idx == self.highlighted_tenant_idx:
                    highlight = True
                tenant_idx += 1
            obj.draw(painter, highlight=highlight)
        # Rysowanie aktualnie rysowanego obiektu
        if self.temp_points:
            color = QColor(0,0,255,60) if self.draw_mode == 'building' else QColor(200,200,0,120) if self.draw_mode == 'common' else QColor(0,200,0,120)
            pen = QPen(color.darker(), 2)
            painter.setBrush(color)
            painter.setPen(pen)
            painter.drawPolyline(QPolygon(self.temp_points))
            for pt in self.temp_points:
                painter.setBrush(color)
                painter.drawEllipse(pt, 4, 4)

    def get_all_seeds(self):
        seeds = []
        for obj in self.objects:
            if isinstance(obj, CommonArea):
                seeds.append({'type': 'Powierzchnia wspólna', 'area': obj.area(self.scale), 'points': obj.points, 'color': obj.color})
            elif isinstance(obj, TenantArea):
                seeds.append({'type': 'Najemca', 'area': obj.area(self.scale), 'points': obj.points, 'color': obj.color})
        return seeds

    def to_dict(self):
        return {
            'objects': [obj.to_dict() for obj in self.objects],
            'scale': self.scale
        }

    def from_dict(self, data):
        self.objects = []
        for obj_data in data.get('objects', []):
            obj_type = obj_data.get('type')
            if obj_type == 'Building':
                obj = Building.from_dict(obj_data)
            elif obj_type == 'CommonArea':
                obj = CommonArea.from_dict(obj_data)
            elif obj_type == 'TenantArea':
                obj = TenantArea.from_dict(obj_data)
            else:
                continue
            self.objects.append(obj)
        self.scale = data.get('scale', 0.1)
        self.update()
        if any(isinstance(obj, Building) for obj in self.objects) and self.on_building_closed:
            self.on_building_closed(self.objects[0].area(self.scale))
        if self.on_seeds_changed:
            self.on_seeds_changed(self.get_all_seeds())

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
