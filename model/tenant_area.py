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

    def auto_expand_to_area_grid(self, building, others, scale=0.1, grid_size=None):
        """Rasteryzacyjne powiększanie: doklejanie wolnych kratek do bloku aż do zadanej powierzchni."""
        import sys
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QPolygon
        import collections
        from scipy.spatial import ConvexHull
        import numpy as np
        if not self.desired_area or len(self.points) < 3:
            print("[auto_expand_to_area_grid] brak desired_area lub za mało punktów", file=sys.stderr)
            return
        # Ustal grid_size na podstawie skali jeśli nie podano
        if grid_size is None:
            grid_size = 1.0 / scale
        # Rasteryzuj budynek
        building_poly = QPolygon(building.points) if building else None
        # Rasteryzuj zajęte kratki przez innych
        occupied = set()
        for other in others:
            if other is self or len(other.points) < 3:
                continue
            poly = QPolygon(other.points)
            min_x = min(p.x() for p in other.points)
            max_x = max(p.x() for p in other.points)
            min_y = min(p.y() for p in other.points)
            max_y = max(p.y() for p in other.points)
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
        # Rasteryzuj obecny blok
        poly = QPolygon(self.points)
        min_x = min(p.x() for p in self.points)
        max_x = max(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_y = max(p.y() for p in self.points)
        gx0 = int(min_x // grid_size)
        gx1 = int(max_x // grid_size) + 1
        gy0 = int(min_y // grid_size)
        gy1 = int(max_y // grid_size) + 1
        my_cells = set()
        for gx in range(gx0, gx1):
            for gy in range(gy0, gy1):
                cx = gx * grid_size + grid_size/2
                cy = gy * grid_size + grid_size/2
                pt = QPoint(int(cx), int(cy))
                if poly.containsPoint(pt, Qt.OddEvenFill):
                    my_cells.add((gx, gy))
        # BFS po wolnych kratkach sąsiadujących z blokiem
        area_per_cell = grid_size * grid_size * scale * scale
        need_cells = int(self.desired_area / area_per_cell + 0.5)
        print(f"[auto_expand_to_area_grid] cells: mam={len(my_cells)}, potrzebuję={need_cells}", file=sys.stderr)
        if len(my_cells) >= need_cells:
            print("[auto_expand_to_area_grid] już wystarczająca powierzchnia", file=sys.stderr)
            return
        # Zbierz wszystkie możliwe kratki w budynku
        all_cells = set()
        if building_poly:
            bmin_x = min(p.x() for p in building.points)
            bmax_x = max(p.x() for p in building.points)
            bmin_y = min(p.y() for p in building.points)
            bmax_y = max(p.y() for p in building.points)
            for gx in range(int(bmin_x // grid_size), int(bmax_x // grid_size) + 1):
                for gy in range(int(bmin_y // grid_size), int(bmax_y // grid_size) + 1):
                    cx = gx * grid_size + grid_size/2
                    cy = gy * grid_size + grid_size/2
                    pt = QPoint(int(cx), int(cy))
                    if building_poly.containsPoint(pt, Qt.OddEvenFill):
                        all_cells.add((gx, gy))
        else:
            # Brak budynku: pozwól na całą planszę
            for gx in range(gx0-10, gx1+10):
                for gy in range(gy0-10, gy1+10):
                    all_cells.add((gx, gy))
        # BFS
        queue = collections.deque(my_cells)
        visited = set(my_cells)
        while queue and len(visited) < need_cells:
            gx, gy = queue.popleft()
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                ng = (gx+dx, gy+dy)
                if ng in visited or ng in occupied or ng not in all_cells:
                    continue
                visited.add(ng)
                queue.append(ng)
        # Zaktualizuj wielokąt na podstawie nowych kratek (obwiednia)
        if len(visited) > len(my_cells):
            from scipy.spatial import ConvexHull
            import numpy as np
            pts = np.array([[gx*grid_size+grid_size/2, gy*grid_size+grid_size/2] for gx,gy in visited])
            hull = ConvexHull(pts)
            self.points = [QPoint(int(pts[i,0]), int(pts[i,1])) for i in hull.vertices]
            print(f"[auto_expand_to_area_grid] powiększono do {len(visited)} kratek", file=sys.stderr)
        else:
            print("[auto_expand_to_area_grid] nie udało się powiększyć (brak wolnych kratek)", file=sys.stderr)
