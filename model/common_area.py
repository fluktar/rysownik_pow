from PySide6.QtGui import QColor
from .area_object import AreaObject

class CommonArea(AreaObject):
    def __init__(self, points=None, color=QColor(200,200,0,120)):
        super().__init__(points, color)

    def to_dict(self):
        d = super().to_dict()
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        return obj
