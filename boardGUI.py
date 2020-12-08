from keyboard import KeyboardListener
from colors import *
from kivy.graphics import *
from kivy.uix.gridlayout import *
from kivy.uix.boxlayout import *
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.base import Builder

from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty


class Tile(AnchorLayout):
    couleur = ObjectProperty(WHITE)
    reverseOrder = BooleanProperty(False)
    xBoard = StringProperty('a')
    column = StringProperty('a')
    yBoard = NumericProperty(1)
    row = NumericProperty(1)

    def on_touch_down(self, touch):
        if(self.collide_point(touch.pos[0], touch.pos[1])):
            print(self.column + str(self.row))
        return super().on_touch_down(touch)
    pass


class Row(GridLayout):
    rowNumber = NumericProperty(0)
    reverseOrder = BooleanProperty(False)


class BoardWidget(GridLayout, KeyboardListener):
    pov = StringProperty('WHITE')

    def __init__(self, **kwargs):
        self.initKeyboard()
        self.bind_key('r', self.rotate)
        super().__init__(**kwargs)

    def rotate(self, key, modifiers):
        if(self.pov == 'WHITE'):
            self.pov = 'BLACK'
        else:
            self.pov = 'WHITE'
    pass
