from PySide6.QtGui import QColor
from .area_object import AreaObject

class TenantArea(AreaObject):
    def __init__(self, points=None, color=QColor(0,200,0,120), name="Najemca"):
        super().__init__(points, color)
        self.name = name

    def to_dict(self):
        d = super().to_dict()
        d['name'] = self.name
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj.name = data.get('name', 'Najemca')
        return obj
