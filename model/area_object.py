from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon

class AreaObject:
    def __init__(self, points=None, color=QColor(0,0,0,60)):
        self.points = points or []  # lista QPoint
        self.color = color
        self.selected_vertex = None
        self.drag_offset = QPoint(0,0)

    def draw(self, painter: QPainter, offset=QPoint(0,0), highlight=False):
        if len(self.points) < 2:
            return
        poly = QPolygon([pt + offset for pt in self.points])
        painter.setBrush(self.color)
        painter.setPen(QPen(self.color.darker() if not highlight else QColor(255,0,0), 2))
        painter.drawPolygon(poly)
        for pt in self.points:
            painter.setBrush(QColor(255,0,0) if highlight else self.color)
            painter.drawEllipse(pt + offset, 4, 4)

    def move(self, delta: QPoint):
        self.points = [pt + delta for pt in self.points]

    def hit_test(self, point: QPoint, offset=QPoint(0,0)):
        # Czy kliknięto w środek obiektu
        poly = QPolygon([pt + offset for pt in self.points])
        return poly.containsPoint(point, 0)

    def hit_vertex(self, point: QPoint, offset=QPoint(0,0)):
        # Zwraca indeks wierzchołka jeśli kliknięto blisko
        for idx, pt in enumerate(self.points):
            if (point - (pt + offset)).manhattanLength() < 10:
                return idx
        return None

    def move_vertex(self, idx, new_pos: QPoint, offset=QPoint(0,0)):
        self.points[idx] = new_pos - offset

    def area(self, scale=0.1):
        if len(self.points) < 3:
            return 0.0
        area = 0.0
        n = len(self.points)
        for i in range(n - 1):
            x1, y1 = self.points[i].x(), self.points[i].y()
            x2, y2 = self.points[i + 1].x(), self.points[i + 1].y()
            area += (x1 * y2 - x2 * y1)
        area = abs(area) / 2.0
        return area * (scale ** 2)
