from PySide6.QtGui import QColor
from .area_object import AreaObject

class Building(AreaObject):
    def __init__(self, points=None):
        super().__init__(points, QColor(0,0,255,60))
    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj.color = QColor(0,0,255,60)
        return obj
