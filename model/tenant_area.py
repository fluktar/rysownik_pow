from PySide6.QtGui import QColor
from .area_object import AreaObject

class TenantArea(AreaObject):
    def __init__(self, points=None):
        super().__init__(points, QColor(0,200,0,120))
    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj.color = QColor(0,200,0,120)
        return obj
