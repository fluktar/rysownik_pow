from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtGui import QPolygon
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

    def auto_expand_to_area(self, building, others, scale=0.1, max_iter=100):
        """Automatycznie powiększ blok do zadanej powierzchni (desired_area), nie kolidując z innymi."""
        if not self.desired_area or len(self.points) < 3:
            return
        import random
        from PySide6.QtCore import QPoint
        for _ in range(max_iter):
            current_area = self.area(scale)
            if current_area >= self.desired_area:
                break
            # Spróbuj rozepchnąć każdy wierzchołek na zewnątrz
            for i, pt in enumerate(self.points):
                # Kierunek: od środka masy na zewnątrz
                cx = sum(p.x() for p in self.points) / len(self.points)
                cy = sum(p.y() for p in self.points) / len(self.points)
                dx = pt.x() - cx
                dy = pt.y() - cy
                length = (dx**2 + dy**2) ** 0.5 or 1
                step = 2 + random.random()  # losowy krok
                new_pt = QPoint(round(pt.x() + dx/length*step), round(pt.y() + dy/length*step))
                old = self.points[i]
                self.points[i] = new_pt
                # Sprawdź kolizje z budynkiem i innymi blokami
                if building and not QPolygon(building.points).containsPoint(new_pt, Qt.OddEvenFill):
                    self.points[i] = old
                    continue
                collision = False
                for other in others:
                    if other is self:
                        continue
                    if QPolygon(other.points).containsPoint(new_pt, Qt.OddEvenFill):
                        collision = True
                        break
                if collision:
                    self.points[i] = old
