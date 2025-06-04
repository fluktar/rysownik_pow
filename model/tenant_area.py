from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
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

    def auto_expand_to_area(self, building, others, scale=0.1, max_iter=1200):
        """Automatycznie powiększ blok do zadanej powierzchni (desired_area), nie kolidując z innymi."""
        import sys
        print(f"[auto_expand_to_area] start: desired_area={self.desired_area}, current_area={self.area(scale):.2f}", file=sys.stderr)
        if not self.desired_area or len(self.points) < 3:
            print("[auto_expand_to_area] brak desired_area lub za mało punktów", file=sys.stderr)
            return
        from PySide6.QtCore import QPoint
        import random
        for iter_num in range(max_iter):
            current_area = self.area(scale)
            if current_area >= self.desired_area:
                print(f"[auto_expand_to_area] osiągnięto powierzchnię: {current_area:.2f} >= {self.desired_area}", file=sys.stderr)
                break
            cx = sum(p.x() for p in self.points) / len(self.points)
            cy = sum(p.y() for p in self.points) / len(self.points)
            expanded = False
            for i, pt in enumerate(self.points):
                dx = pt.x() - cx
                dy = pt.y() - cy
                length = (dx**2 + dy**2) ** 0.5 or 1
                # Testuj 16 kierunków, nie tylko 8
                for try_dir in range(16):
                    angle = (2 * 3.14159 * try_dir) / 16
                    step = 12 + 6*random.random()
                    ddx = step * math.cos(angle)
                    ddy = step * math.sin(angle)
                    new_pt = QPoint(round(pt.x() + ddx), round(pt.y() + ddy))
                    old = self.points[i]
                    self.points[i] = new_pt
                    valid = True
                    if building and not QPolygon(building.points).containsPoint(new_pt, Qt.OddEvenFill):
                        valid = False
                    for other in others:
                        if other is self:
                            continue
                        if QPolygon(other.points).containsPoint(new_pt, Qt.OddEvenFill):
                            valid = False
                            break
                    if not valid:
                        self.points[i] = old
                    else:
                        expanded = True
                        break
            if not expanded:
                print(f"[auto_expand_to_area] iter={iter_num}: nie udało się powiększyć żadnego wierzchołka, próbuję całość", file=sys.stderr)
                for i, pt in enumerate(self.points):
                    dx = pt.x() - cx
                    dy = pt.y() - cy
                    length = (dx**2 + dy**2) ** 0.5 or 1
                    step = 4
                    new_pt = QPoint(round(pt.x() + dx/length*step), round(pt.y() + dy/length*step))
                    old = self.points[i]
                    self.points[i] = new_pt
                    valid = True
                    if building and not QPolygon(building.points).containsPoint(new_pt, Qt.OddEvenFill):
                        valid = False
                    for other in others:
                        if other is self:
                            continue
                        if QPolygon(other.points).containsPoint(new_pt, Qt.OddEvenFill):
                            valid = False
                            break
                    if not valid:
                        self.points[i] = old
                if self.area(scale) <= current_area:
                    print(f"[auto_expand_to_area] iter={iter_num}: nie da się już powiększyć (area={self.area(scale):.2f})", file=sys.stderr)
                    break
        print(f"[auto_expand_to_area] koniec: area={self.area(scale):.2f}", file=sys.stderr)
