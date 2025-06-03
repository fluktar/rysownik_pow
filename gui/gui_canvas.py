from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QMouseEvent, QPainterPath
from PySide6.QtCore import Qt, QPoint
import math

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # Lista punktów obrysu budynku
        self.closed = False  # Czy obrys jest zamknięty
        self.setMouseTracking(True)
        self.scale = 0.1  # 1 piksel = 0.1 m (10 cm)
        self.surface = 0.0
        self.on_building_closed = None  # callback do panelu bocznego
        self.dragging_idx = None  # indeks przesuwanego punktu
        self.drag_offset = QPoint(0, 0)
        self.zoom = 1.0  # zoom (1.0 = 100%)
        self.moving_building = False
        self.move_start = None
        self.seeds = []  # lista ziaren (najemcy, pow. wspólne)
        self.building_offset = QPoint(0, 0)  # przesunięcie budynku i ziaren
        self.last_building_center = None

    def set_zoom(self, zoom):
        self.zoom = zoom
        self.update()

    def zoom_in(self):
        self.zoom *= 1.2
        self.update()

    def zoom_out(self):
        self.zoom /= 1.2
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            point = (event.position() / self.zoom).toPoint()
            if self.closed:
                # Sprawdź czy kliknięto w punkt
                for idx, pt in enumerate(self.points[:-1]):
                    if (point - pt).manhattanLength() < 10:
                        self.dragging_idx = idx
                        self.drag_offset = pt - point
                        break
                else:
                    # Sprawdź czy kliknięto wewnątrz budynku
                    if self.is_point_in_polygon(point):
                        self.moving_building = True
                        self.move_start = point
                        self.building_offset_start = QPoint(self.building_offset)
            elif not self.closed:
                if self.points and (point - self.points[0]).manhattanLength() < 10 and len(self.points) > 2:
                    self.closed = True
                    self.points.append(self.points[0])
                    self.surface = self.calculate_surface()
                    if self.on_building_closed:
                        self.on_building_closed(self.surface)
                else:
                    self.points.append(point)
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.closed:
            if self.dragging_idx is not None:
                new_pos = (event.position() / self.zoom).toPoint() + self.drag_offset
                self.points[self.dragging_idx] = new_pos
                if self.dragging_idx == 0:
                    self.points[-1] = new_pos
                elif self.dragging_idx == len(self.points) - 1:
                    self.points[0] = new_pos
                self.surface = self.calculate_surface()
                if self.on_building_closed:
                    self.on_building_closed(self.surface)
                self.update()
            elif self.moving_building and self.move_start is not None:
                new_point = (event.position() / self.zoom).toPoint()
                delta = new_point - self.move_start
                self.points = [pt + delta for pt in self.points]
                self.move_start = new_point
                self.building_offset = self.building_offset_start + delta
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.closed:
            if self.dragging_idx is not None:
                self.dragging_idx = None
            if self.moving_building:
                self.moving_building = False
                self.move_start = None
                self.building_offset_start = None

    def calculate_surface(self):
        if len(self.points) < 3:
            return 0.0
        area = 0.0
        n = len(self.points)
        for i in range(n - 1):
            x1, y1 = self.points[i].x(), self.points[i].y()
            x2, y2 = self.points[i + 1].x(), self.points[i + 1].y()
            area += (x1 * y2 - x2 * y1)
        area = abs(area) / 2.0
        area_m2 = (area * (self.scale ** 2))
        return area_m2

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.scale(self.zoom, self.zoom)
            # Rysuj ziarna względem przesunięcia budynku
            for seed in self.seeds:
                painter.setBrush(seed['color'])
                painter.setPen(QPen(seed['color'].darker(), 2))
                offset = self.building_offset if self.closed else QPoint(0, 0)
                points = [pt + offset for pt in seed['points']]
                painter.drawPolygon(*points)
            pen = QPen(QColor(0, 0, 255), 2)
            painter.setPen(pen)
            if self.points and all(isinstance(pt, QPoint) for pt in self.points):
                for i in range(len(self.points) - 1):
                    painter.drawLine(self.points[i], self.points[i + 1])
                for pt in self.points:
                    if 0 <= pt.x() < 10000 and 0 <= pt.y() < 10000:  # zabezpieczenie przed rysowaniem poza ekranem
                        painter.setBrush(QColor(0, 0, 255))
                        painter.drawEllipse(pt, 4, 4)
            if self.closed and len(self.points) > 2:
                # Rysuj tylko jeśli punkty są poprawne
                if all(isinstance(pt, QPoint) for pt in self.points):
                    painter.setBrush(QColor(0, 0, 255, 60))
                    try:
                        painter.drawPolygon(*self.points)
                    except Exception:
                        pass
        except Exception:
            pass

    def is_point_in_polygon(self, point):
        if len(self.points) < 3:
            return False
        path = QPainterPath()
        path.moveTo(self.points[0])
        for pt in self.points[1:]:
            path.lineTo(pt)
        return path.contains(point)

    def add_seed_area(self, typ, area):
        if area <= 0:
            return
        import random
        side_m = area ** 0.5
        side_px = int(side_m / self.scale)
        # Umieść ziarno na środku budynku lub okna
        if self.closed and self.points:
            # środek budynku
            xs = [pt.x() for pt in self.points]
            ys = [pt.y() for pt in self.points]
            cx = sum(xs) // len(xs)
            cy = sum(ys) // len(ys)
        else:
            cx = self.width() // 2
            cy = self.height() // 2
        x0 = cx - side_px // 2 + random.randint(-10, 10)
        y0 = cy - side_px // 2 + random.randint(-10, 10)
        color = QColor(0, 200, 0, 120) if typ == "Najemca" else QColor(200, 200, 0, 120)
        rect = [QPoint(x0, y0), QPoint(x0 + side_px, y0), QPoint(x0 + side_px, y0 + side_px), QPoint(x0, y0 + side_px), QPoint(x0, y0)]
        self.seeds.append({'type': typ, 'area': area, 'points': rect, 'color': color})
        self.update()

    def to_dict(self):
        return {
            'points': [(pt.x(), pt.y()) for pt in self.points],
            'closed': self.closed,
            'scale': self.scale
        }

    def from_dict(self, data):
        self.points = [QPoint(x, y) for x, y in data.get('points', [])]
        self.closed = data.get('closed', False)
        self.scale = data.get('scale', 0.1)
        self.surface = self.calculate_surface()
        self.update()
        if self.closed and self.on_building_closed:
            self.on_building_closed(self.surface)
