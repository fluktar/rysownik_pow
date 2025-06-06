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
        self.highlighted_idx = None
        self.highlighted_type = None
        self.show_grid = True  # widoczność siatki
        self.grid_base = 1.0   # podstawowa wielkość kratki w metrach
        self.grid_color = QColor(180, 180, 255, 60)
        self.snap_to_grid = True
        # tryb interakcji: 'default', 'add_vertex', 'move_vertex'
        self.interaction_mode = 'default'

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

    def set_highlighted_object(self, idx, obj_type):
        self.highlighted_idx = idx
        self.highlighted_type = obj_type
        self.update()

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()

    def set_interaction_mode(self, mode):
        self.interaction_mode = mode
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_N:
            self.set_interaction_mode('add_vertex')
        elif event.key() == Qt.Key_P:
            self.set_interaction_mode('move_vertex')
        elif event.key() == Qt.Key_Escape:
            self.set_interaction_mode('default')
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        point = (event.position() / self.zoom).toPoint()
        # Dodawanie punktu do najemcy po kliknięciu na krawędź (tryb add_vertex)
        if self.interaction_mode == 'add_vertex':
            for obj in reversed(self.objects):
                if isinstance(obj, TenantArea):
                    before = len(obj.points)
                    if obj.insert_vertex(point, threshold=10):
                        min_idx = None
                        min_dist = float('inf')
                        for idx, pt in enumerate(obj.points):
                            dist = (pt - point).manhattanLength()
                            if dist < min_dist:
                                min_dist = dist
                                min_idx = idx
                        if min_idx is not None and min_dist < 15:
                            self.selected_obj = obj
                            self.selected_vertex = min_idx
                        else:
                            self.selected_obj = obj
                            self.selected_vertex = None
                        if self.on_seeds_changed:
                            self.on_seeds_changed(self.get_all_seeds())
                        self.update()
                        return
        # Przesuwanie punktu tylko w trybie move_vertex
        if self.interaction_mode == 'move_vertex':
            for obj in reversed(self.objects):
                idx = obj.hit_vertex(point)
                if idx is not None:
                    self.selected_obj = obj
                    self.selected_vertex = idx
                    self.drag_offset = obj.points[idx] - point
                    return
        # Przesuwanie całego obiektu: tylko środkowy przycisk lub lewy + Ctrl
        if (event.button() == Qt.MiddleButton) or (event.button() == Qt.LeftButton and (event.modifiers() & Qt.ControlModifier)):
            for obj in reversed(self.objects):
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
            # SNAP: przyciąganie do krawędzi
            building = next((o for o in self.objects if isinstance(o, Building)), None)
            others = [o for o in self.objects if o is not self.selected_obj]
            self.selected_obj.snap_to_edges(building, others)
            if self.on_seeds_changed:
                self.on_seeds_changed(self.get_all_seeds())
            self.update()
        elif self.selected_obj:
            delta = point - self.selected_obj.points[0]
            self.selected_obj.move(delta)
            # SNAP: przyciąganie do krawędzi
            building = next((o for o in self.objects if isinstance(o, Building)), None)
            others = [o for o in self.objects if o is not self.selected_obj]
            self.selected_obj.snap_to_edges(building, others)
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
        # Rysowanie siatki i podświetlanie zajętych kratek (wariant 2)
        highlight_cells = self._get_occupied_cells() if self.show_grid and hasattr(self, 'show_occupied') and self.show_occupied else None
        if self.show_grid:
            self._draw_grid(painter, highlight_cells=highlight_cells)
        tenant_idx = 0
        common_idx = 0
        for obj in self.objects:
            highlight = (obj is self.selected_obj)
            # Mruganie dowolnego obiektu
            if self.highlighted_type == 'tenant' and obj.__class__.__name__ == 'TenantArea':
                if tenant_idx == self.highlighted_idx:
                    highlight = True
                tenant_idx += 1
            elif self.highlighted_type == 'common' and obj.__class__.__name__ == 'CommonArea':
                if common_idx == self.highlighted_idx:
                    highlight = True
                common_idx += 1
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

    def _draw_grid(self, painter, highlight_cells=None):
        # Wyznacz rozmiar kratki w pikselach na podstawie skali i zoomu
        grid_size = self.grid_base / self.scale
        grid_size_px = grid_size * self.zoom
        rect = self.rect()
        painter.save()
        painter.setPen(QPen(self.grid_color, 1))
        # Rysuj pionowe linie
        x = 0
        while x < rect.width() / self.zoom:
            painter.drawLine(int(x), 0, int(x), int(rect.height() / self.zoom))
            x += grid_size
        # Rysuj poziome linie
        y = 0
        while y < rect.height() / self.zoom:
            painter.drawLine(0, int(y), int(rect.width() / self.zoom), int(y))
            y += grid_size
        # Opcjonalnie podświetl zajęte kratki
        if highlight_cells:
            painter.setBrush(QColor(255, 200, 0, 60))
            painter.setPen(Qt.NoPen)
            for gx, gy in highlight_cells:
                painter.drawRect(int(gx*grid_size), int(gy*grid_size), int(grid_size), int(grid_size))
        painter.restore()

    def _get_occupied_cells(self):
        # Rasteryzacja: zwraca zbiór (gx, gy) zajętych przez obiekty TenantArea i CommonArea
        grid_size = self.grid_base / self.scale
        occupied = set()
        for obj in self.objects:
            if isinstance(obj, (TenantArea, CommonArea)):
                poly = QPolygon(obj.points)
                # Wyznacz bounding box
                min_x = min(p.x() for p in obj.points)
                max_x = max(p.x() for p in obj.points)
                min_y = min(p.y() for p in obj.points)
                max_y = max(p.y() for p in obj.points)
                gx0 = int(min_x // grid_size)
                gx1 = int(max_x // grid_size) + 1
                gy0 = int(min_y // grid_size)
                gy1 = int(max_y // grid_size) + 1
                for gx in range(gx0, gx1):
                    for gy in range(gy0, gy1):
                        cx = gx * grid_size + grid_size/2
                        cy = gy * grid_size + grid_size/2
                        if poly.containsPoint(QPoint(int(cx), int(cy)), Qt.OddEvenFill):
                            occupied.add((gx, gy))
        return occupied

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

    def add_shortcuts_menu(self, menubar):
        menu = menubar.addMenu('Instrukcje')
        menu.addAction('N - Tryb dodawania punktów (modelowanie najemcy)')
        menu.addAction('P - Tryb przesuwania punktów')
        menu.addAction('Esc - Tryb domyślny (brak specjalnej akcji)')
        menu.addAction('Ctrl + Lewy przycisk myszy lub środkowy przycisk - przesuwanie całego obiektu')
        menu.addAction('Rysowanie nowych obiektów - tryb domyślny, lewy przycisk myszy')
