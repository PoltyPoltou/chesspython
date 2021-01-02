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

    def setTiles(self, tileFrom, tileTo) -> None:
        if(tileTo.column == tileFrom.column):
            self.vertical = True
            self.horizontal = False
            self.diagonal = False
            self.tileTo = tileTo
            self.tileFrom = tileFrom
        elif(tileTo.row == tileFrom.row):
            self.vertical = False
            self.horizontal = True
            self.diagonal = False
            self.tileTo = tileTo
            self.tileFrom = tileFrom
        elif(abs(tileTo.row - tileFrom.row) == abs(ord(tileTo.column) - ord(tileFrom.column))):
            self.vertical = False
            self.horizontal = False
            self.diagonal = True
            self.tileTo = tileTo
            self.tileFrom = tileFrom
        else:  # No matching pattern found for the arrow so we delete affectation
            self.vertical = False
            self.horizontal = False
            self.diagonal = False

    def isValid(self) -> bool:
        return self.vertical or self.horizontal or self.diagonal
