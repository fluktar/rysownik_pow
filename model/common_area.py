from PySide6.QtGui import QColor
from .area_object import AreaObject

class CommonArea(AreaObject):
    def __init__(self, points=None):
        super().__init__(points, QColor(200,200,0,120))
    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj.color = QColor(200,200,0,120)
        return obj
