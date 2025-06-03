from PySide6.QtCore import QPoint, Qt
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
        return poly.containsPoint(point, Qt.OddEvenFill)

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

    def to_dict(self):
        return {
            'type': self.__class__.__name__,
            'points': [(pt.x(), pt.y()) for pt in self.points],
            'color': [self.color.red(), self.color.green(), self.color.blue(), self.color.alpha()]
        }

    @classmethod
    def from_dict(cls, data):
        from PySide6.QtCore import QPoint
        points = [QPoint(x, y) for x, y in data.get('points', [])]
        color = QColor(*data.get('color', [0,0,0,60]))
        # Wymuś typ klasy na podstawie pola 'type' jeśli to nie jest AreaObject
        if cls.__name__ == 'AreaObject' and 'type' in data:
            if data['type'] == 'Building':
                from model.building import Building
                return Building(points)
            elif data['type'] == 'CommonArea':
                from model.common_area import CommonArea
                return CommonArea(points)
            elif data['type'] == 'TenantArea':
                from model.tenant_area import TenantArea
                return TenantArea(points)
        obj = cls(points)
        obj.color = color
        return obj

    def snap_to_edges(self, building, others, snap_distance=10):
        # Przyciąganie do ścian budynku (odcinki, zamknięty wielokąt)
        if building and len(building.points) > 1:
            n = len(building.points)
            closed = (building.points[0] == building.points[-1])
            seg_count = n-1 if not closed else n-1
            for i, pt in enumerate(self.points):
                min_dist = snap_distance
                snap_pos = None
                for j in range(seg_count):
                    a = building.points[j]
                    b = building.points[(j + 1) % n]
                    ab = b - a
                    ap = pt - a
                    ab_len2 = ab.x()**2 + ab.y()**2
                    if ab_len2 == 0:
                        continue
                    t = max(0, min(1, (ap.x()*ab.x() + ap.y()*ab.y()) / ab_len2))
                    proj_x = a.x() + ab.x()*t
                    proj_y = a.y() + ab.y()*t
                    proj = QPoint(round(proj_x), round(proj_y))
                    dist = (pt - proj).manhattanLength()
                    if dist < min_dist:
                        min_dist = dist
                        snap_pos = proj
                if snap_pos is not None:
                    self.points[i] = snap_pos
        # Przyciąganie do ścian innych bloków (odcinki)
        for other in others:
            if other is self or len(other.points) < 2:
                continue
            n = len(other.points)
            closed = (other.points[0] == other.points[-1])
            seg_count = n-1 if not closed else n-1
            for i, pt in enumerate(self.points):
                min_dist = snap_distance
                snap_pos = None
                for j in range(seg_count):
                    a = other.points[j]
                    b = other.points[(j + 1) % n]
                    ab = b - a
                    ap = pt - a
                    ab_len2 = ab.x()**2 + ab.y()**2
                    if ab_len2 == 0:
                        continue
                    t = max(0, min(1, (ap.x()*ab.x() + ap.y()*ab.y()) / ab_len2))
                    proj_x = a.x() + ab.x()*t
                    proj_y = a.y() + ab.y()*t
                    proj = QPoint(round(proj_x), round(proj_y))
                    dist = (pt - proj).manhattanLength()
                    if dist < min_dist:
                        min_dist = dist
                        snap_pos = proj
                if snap_pos is not None:
                    self.points[i] = snap_pos
        # Przyciąganie do punktów innych bloków (jak dotychczas)
        for other in others:
            if other is self:
                continue
            for i, pt in enumerate(self.points):
                for opt in other.points:
                    if (pt - opt).manhattanLength() < snap_distance:
                        self.points[i] = QPoint(opt)
