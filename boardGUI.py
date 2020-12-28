from typing import Optional
import chess
from kivy.uix.widget import Widget
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
    coords = StringProperty('a1')
    square = NumericProperty(0)  # index of tile from a1 (0) to h8 (63)

    pass


class Row(GridLayout):
    rowNumber = NumericProperty(0)
    reverseOrder = BooleanProperty(False)


class BoardWidget(GridLayout, KeyboardListener):
    pov = StringProperty('WHITE')
    board: Optional[chess.Board] = ObjectProperty(chess.Board(), True)

    def __init__(self, **kwargs):
        self.initKeyboard()
        self.bind_key('r', self.rotate)

        super().__init__(**kwargs)

    def rotate(self, key, modifiers):
        if(self.pov == 'WHITE'):
            self.pov = 'BLACK'
        else:
            self.pov = 'WHITE'

    def on_touch_down(self, touch):
        for row in self.children:
            for tile in row.children:
                if(tile.collide_point(touch.pos[0], touch.pos[1])):
                    print(tile.coords, tile.square,
                          self.board.piece_at(tile.square))
        return super().on_touch_down(touch)

    def on_board(self, instance, value):

        pass
    pass
