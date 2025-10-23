from enum import Enum

class Tile(Enum):
    ALL = 0
    HORIZONTAL = 1
    VERTICAL = 2
    TOP_LEFT = 3
    TOP_RIGHT = 4
    BOTTOM_LEFT = 5
    BOTTOM_RIGHT = 6
    NONE = 7
