from colors import *
from kivy.graphics import *
from kivy.uix.gridlayout import *
from kivy.uix.boxlayout import *
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.uix.image import *
from kivy.base import Builder
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty


class Tile(AnchorLayout):
    color = ObjectProperty(WHITE)
    bgColor = ObjectProperty(WHITE)
    circleColor = ObjectProperty(WHITE)
    displayedColor = ObjectProperty(WHITE)
    reverseOrder = BooleanProperty(False)
    selected = BooleanProperty(False)
    movableTo = BooleanProperty(False)
    played = BooleanProperty(False)
    xBoard = StringProperty('a')
    column = StringProperty('a')
    coords = StringProperty('a1')
    pieceSourceImg = StringProperty('')
    yBoard = NumericProperty(1)
    row = NumericProperty(1)
    square = NumericProperty(0)  # index of tile from a1 (0) to h8 (63)
    img = ObjectProperty(None, rebind=True)

    def on_pieceSourceImg(self, instance, value):
        if(self.pieceSourceImg == ''):
            self.img.size_hint_y = 0
            self.img.height = '0dp'
        else:
            self.img.size_hint = (1, 1)
            self.img.keep_data = True

    def reorder_widgets(self):
        imgWidget = None
        for child in self.children:
            if isinstance(child, Image):
                imgWidget = child
                self.remove_widget(imgWidget)
        children = list(self.children)
        self.clear_widgets()
        for elmt in children:
            self.add_widget(elmt)
        if imgWidget != None:
            self.add_widget(imgWidget)

    def on_kv_post(self, base_widget):
        self.on_pieceSourceImg(self, self.pieceSourceImg)
        self.reorder_widgets()
        return super().on_kv_post(base_widget)
