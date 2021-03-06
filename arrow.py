from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty, ColorProperty
from kivy.uix.widget import Widget
from kivy.base import Builder
Builder.load_file("./kv/arrows.kv")


class Arrow(Widget):
    clr = ColorProperty((1, 2/3, 0, 0.8))
    tileTo = ObjectProperty(None, rebind=True)
    tileFrom = ObjectProperty(None, rebind=True)
    vertical = BooleanProperty(False)
    horizontal = BooleanProperty(False)
    diagonal = BooleanProperty(False)
    rotated = BooleanProperty(False)
    # defines the angles function of the horizontal and vertical flip (in this order)
    diagonalAngle = [[45, -45], [135, 225]]


class ArrowKnight(Widget):
    clr = ColorProperty((1, 2/3, 0, 0.8))
    tileTo = ObjectProperty(None, rebind=True)
    tileFrom = ObjectProperty(None, rebind=True)
    rotated = BooleanProperty(False)
    angleDict = {(1, 2): 0, (-2, 1): 90, (-1, -2): 180,
                 (2, -1): 270, (-1, 2): 0, (2, 1): 270, (1, -2): 180, (-2, -1): 90}
    flipDict = {(1, 2): False, (-2, 1): False, (-1, -2): False,
                (2, -1): False, (2, 1): True, (1, -2): True, (-2, -1): True, (-1, 2): True}

    def on_touch_down(self, touch):
        return super().on_touch_down(touch)


def arrow_factory(tileFrom, tileTo) -> Widget:
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
    elif((not vertical) and (not horizontal) and (abs(tileTo.row - tileFrom.row) + abs(ord(tileTo.column) - ord(tileFrom.column))) == 3):
        arr = ArrowKnight()
        arr.tileFrom = tileFrom
        arr.tileTo = tileTo
        return arr
    else:  # No matching pattern found for the arrow so we delete affectation
        return None


class ArrowManager:
    def __init__(self, widgetToAddArrows) -> None:
        self.arrowList = []
        self.widgetToAddArrows: Widget = widgetToAddArrows
        self.engineArrow = None

    def addArrow(self, tileFrom, tileTo, color=None):
        arrowToDraw = arrow_factory(tileFrom, tileTo)
        if(arrowToDraw != None):
            arrowToRemove = None
            for arr in self.arrowList:
                if(arr.tileFrom.coords == arrowToDraw.tileFrom.coords and arr.tileTo.coords == arrowToDraw.tileTo.coords):
                    arrowToRemove = arr
                    break
            if(arrowToRemove == None):
                self.widgetToAddArrows.add_widget(arrowToDraw)
                if(color is not None):
                    arrowToDraw.clr = color
                self.arrowList.append(arrowToDraw)
                return arrowToDraw
            else:
                self.widgetToAddArrows.remove_widget(arrowToRemove)
                self.arrowList.remove(arrowToRemove)
        return None

    def addEngineArrow(self, tileFrom, tileTo):
        if(self.engineArrow is not None):
            if(self.engineArrow.tileFrom.coords != tileFrom.coords or self.engineArrow.tileTo.coords != tileTo.coords):
                self.removeEngineArrow()
                arrowToDraw = arrow_factory(tileFrom, tileTo)
                arrowToDraw.clr = (0, 0, 1, 0.8)
                self.widgetToAddArrows.add_widget(arrowToDraw)
                self.engineArrow = arrowToDraw
        else:
            self.removeEngineArrow()
            arrowToDraw = arrow_factory(tileFrom, tileTo)
            arrowToDraw.clr = (0, 0, 1, 0.8)
            self.widgetToAddArrows.add_widget(arrowToDraw)
            self.engineArrow = arrowToDraw

    def directAddArrow(self, tileFrom, tileTo, color=None):
        arrowToDraw = arrow_factory(tileFrom, tileTo)
        if(arrowToDraw is not None):
            if(color is not None):
                arrowToDraw.clr = color
            self.widgetToAddArrows.add_widget(arrowToDraw)
            self.arrowList.append(arrowToDraw)
        return arrowToDraw

    def removeEngineArrow(self):
        if(self.engineArrow is not None):
            self.widgetToAddArrows.remove_widget(self.engineArrow)
            self.engineArrow = None

    def removeOneArrow(self, arr):
        if(arr in self.widgetToAddArrows.children):
            self.widgetToAddArrows.remove_widget(arr)

    def removeArrows(self):
        for arr in self.arrowList:
            self.widgetToAddArrows.remove_widget(arr)
        self.arrowList = []

    def rotateBoard(self):
        for arr in self.arrowList:
            arr.rotated = not arr.rotated
