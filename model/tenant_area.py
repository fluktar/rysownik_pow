from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPolygon
import math
from .area_object import AreaObject

class TenantArea(AreaObject):
    def __init__(self, points=None, color=QColor(0,200,0,120), name="Najemca", desired_area=None):
        super().__init__(points, color)
        self.name = name
        self.desired_area = desired_area  # w m2

    def to_dict(self):
        d = super().to_dict()
        d['name'] = self.name
        if self.desired_area is not None:
            d['desired_area'] = self.desired_area
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj.name = data.get('name', 'Najemca')
        obj.desired_area = data.get('desired_area', None)
        return obj

    def insert_vertex(self, pos: QPoint, threshold=10):
        """Dodaje nowy wierzchołek na najbliższej krawędzi, jeśli kliknięcie jest blisko odcinka."""
        min_dist = float('inf')
        insert_idx = None
        n = len(self.points)
        for i in range(n):
            a = self.points[i]
            b = self.points[(i+1)%n]
            # Rzutowanie punktu na odcinek ab
            ab = b - a
            ap = pos - a
            ab_len2 = ab.x()**2 + ab.y()**2
            if ab_len2 == 0:
                continue
            t = max(0, min(1, (ap.x()*ab.x() + ap.y()*ab.y()) / ab_len2))
            proj_x = a.x() + ab.x()*t
            proj_y = a.y() + ab.y()*t
            proj = QPoint(round(proj_x), round(proj_y))
            dist = (pos - proj).manhattanLength()
            if dist < min_dist and dist < threshold:
                min_dist = dist
                insert_idx = i+1
                insert_pt = proj
        if insert_idx is not None:
            self.points.insert(insert_idx, insert_pt)
            return True
        return False

    # def auto_expand_to_area(self, building, others, scale=0.1, max_iter=1200):
    #     ...existing code...
    # def auto_expand_to_area_grid(self, building, others, scale=0.1, grid_size=None):
    #     ...existing code...
