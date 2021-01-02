from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.widget import Widget


class Arrow(Widget):
    clr = ObjectProperty((1, 170/255, 0, 0.8))
    rectangleWidth = NumericProperty(15)
    tileSize = NumericProperty(90)
    tileTo = ObjectProperty(None, rebind=True)
    tileFrom = ObjectProperty(None, rebind=True)
    nullTest = BooleanProperty(False)
    flipped = BooleanProperty(True)
    delta_x = NumericProperty(0)
    delta_y = NumericProperty(0)
    # defines the angles function of the horizontal and vertical flip (in this order)
    diagonalAngle = [[45, -45], [135, 225]]

    def setTiles(self, tileFrom, tileTo) -> None:
        self.tileTo = tileTo
        self.tileFrom = tileFrom
        if(self.tileTo.xBoard == self.tileFrom.xBoard):
            self.vertical = True
            self.horizontal = False
            self.diagonal = False
        elif(self.tileTo.yBoard == self.tileFrom.yBoard):
            self.vertical = False
            self.horizontal = True
            self.diagonal = False
        else:
            self.vertical = False
            self.horizontal = False
            self.diagonal = True

    def on_touch_down(self, touch):
        if(self.collide_point(touch.pos[0], touch.pos[1])):
            print(self.tileFrom.y > self.tileTo.y * self.vertical)
        return super().on_touch_down(touch)
