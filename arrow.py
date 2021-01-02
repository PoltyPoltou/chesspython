from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.widget import Widget


class Arrow(Widget):
    tileTo = ObjectProperty(None, rebind=True)
    tileFrom = ObjectProperty(None, rebind=True)
    vertical = BooleanProperty(False)
    horizontal = BooleanProperty(False)
    diagonal = BooleanProperty(False)
    # defines the angles function of the horizontal and vertical flip (in this order)
    diagonalAngle = [[45, -45], [135, 225]]


def arrow_factory(tileFrom, tileTo) -> Arrow:
    vertical = tileTo.column == tileFrom.column
    horizontal = tileTo.row == tileFrom.row
    diagonal = (abs(tileTo.row - tileFrom.row) ==
                abs(ord(tileTo.column) - ord(tileFrom.column)))
    if(not (tileFrom.coords == tileTo.coords) and (vertical or horizontal or diagonal)):
        arr = Arrow()
        arr.vertical = vertical
        arr.horizontal = horizontal
        arr.diagonal = diagonal
        arr.tileFrom = tileFrom
        arr.tileTo = tileTo
        return arr
    else:  # No matching pattern found for the arrow so we delete affectation
        return None
