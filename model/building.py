from PySide6.QtGui import QColor
from .area_object import AreaObject

class Building(AreaObject):
    def __init__(self, points=None):
        super().__init__(points, QColor(0,0,255,60))
